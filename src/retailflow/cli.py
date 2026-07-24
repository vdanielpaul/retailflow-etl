"""Production Command-Line Interface (CLI) runner for RetailFlow ETL pipeline."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from retailflow.audit.engine import AuditEngine
from retailflow.audit.models import AuditSeverity, PipelineLifecycleEvent
from retailflow.config.loader import load_config
from retailflow.database.connection import DatabaseManager
from retailflow.exceptions.exceptions import (
    AuditError,
    ConfigurationError,
    DatabaseError,
    RetailFlowError,
    ValidationError,
)
from retailflow.health.checker import HealthChecker
from retailflow.incremental.engine import IncrementalEngine
from retailflow.incremental.watermark import WatermarkManager
from retailflow.loader.engine import WarehouseLoaderEngine
from retailflow.models.incremental import FileClassification
from retailflow.pipeline.context import PipelineContext
from retailflow.transformation.engine import TransformationEngine
from retailflow.utils.logger import set_log_context, setup_logger
from retailflow.validation.engine import ValidationEngine

# Standardized Operational Exit Codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILURE = 1
EXIT_CONFIG_FAILURE = 2
EXIT_DATABASE_FAILURE = 3
EXIT_INCREMENTAL_FAILURE = 4
EXIT_AUDIT_FAILURE = 5
EXIT_UNKNOWN_FAILURE = 6


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for pipeline execution options."""
    parser = argparse.ArgumentParser(
        prog="retailflow",
        description="RetailFlow ETL - Enterprise Sales Data Warehouse Pipeline",
    )
    parser.add_argument(
        "-c", "--config", type=str, default="config/development.yaml", help="Path to YAML configuration file."
    )
    parser.add_argument(
        "-e", "--env", type=str, choices=["development", "production", "testing"], help="Environment mode override."
    )
    parser.add_argument(
        "-b", "--batch-size", type=int, help="Batch page size override for warehouse loading."
    )
    parser.add_argument(
        "--file", type=str, help="Target feed CSV file path to process."
    )
    parser.add_argument(
        "--replay", action="store_true", help="Force manual replay of target feed file, ignoring watermark."
    )
    parser.add_argument(
        "--replay-run-id", type=str, help="Replay historical execution by run ID."
    )
    parser.add_argument(
        "--replay-file-hash", type=str, help="Replay historical execution by SHA-256 file hash."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry-run mode: executes validation and transformation without database writes."
    )
    parser.add_argument(
        "--validation-only", action="store_true", help="Execute validation stage only and exit."
    )
    parser.add_argument(
        "--transformation-only", action="store_true", help="Execute validation and transformation stages without warehouse loading."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose DEBUG level logging."
    )
    return parser


def run_pipeline(args: list[str] | None = None) -> int:
    """Main CLI execution entry point returning exit code integer.

    Args:
        args: Command-line arguments tuple or list.

    Returns:
        Integer exit code.
    """
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    start_time = time.perf_counter()
    log_level = "DEBUG" if parsed_args.verbose else "INFO"
    is_offline_mode = parsed_args.dry_run or parsed_args.validation_only or parsed_args.transformation_only

    try:
        # Stage 1: Configuration Loading
        config = load_config(parsed_args.config)
        if parsed_args.env:
            config.pipeline.environment = parsed_args.env
        if parsed_args.batch_size:
            config.pipeline.batch_size = parsed_args.batch_size

        logger = setup_logger(
            name="retailflow",
            log_level=log_level,
            log_dir=config.paths.log_dir,
        )

        db_manager = DatabaseManager(config.database)
        source_file = Path(parsed_args.file) if parsed_args.file else (Path(config.paths.raw_dir) / "sample_sales.csv")

        context = PipelineContext(
            configuration=config,
            database=db_manager if not is_offline_mode else None,
            logger=logger,
            environment=config.pipeline.environment,
            source_file=source_file,
        )
        set_log_context(
            run_id=context.run_id,
            batch_id=context.batch_id,
            filename=source_file.name,
            environment=context.environment,
        )

        audit_engine = AuditEngine()
        audit_engine.audit_service.record_event(
            run_id=context.run_id,
            event_name=PipelineLifecycleEvent.PIPELINE_STARTED,
            severity=AuditSeverity.INFO,
            stage="INITIALIZATION",
            message=f"Starting RetailFlow ETL run {context.run_id} in {context.environment} mode.",
        )

        # Stage 2: Pre-flight Health Checks (Bypassed in offline modes)
        if not is_offline_mode:
            health_checker = HealthChecker(config, db_manager)
            health_result = health_checker.run_all_checks()
            if not health_result.is_healthy:
                logger.error(f"Health checks failed: {health_result.failures}")
                return EXIT_CONFIG_FAILURE

        audit_engine.audit_service.record_event(
            run_id=context.run_id,
            event_name=PipelineLifecycleEvent.HEALTH_CHECK_COMPLETED,
            severity=AuditSeverity.INFO,
            stage="HEALTH_CHECK",
            message="Health checks completed successfully.",
        )

        # Stage 3: Incremental Evaluation
        if is_offline_mode:
            classification = FileClassification.NEW
            file_hash = "offline-mode-hash"
        else:
            watermark_mgr = WatermarkManager(db_manager)
            inc_engine = IncrementalEngine(watermark_mgr)
            classification, file_hash = inc_engine.evaluate_feed_file(
                source_file, is_manual_replay=parsed_args.replay
            )

            if classification.value == "DUPLICATE" and not parsed_args.replay:
                logger.info(f"File {source_file.name} is DUPLICATE. Skipping processing cleanly.")
                inc_engine.generate_manifest_and_report(context, classification, file_hash, start_time)
                return EXIT_SUCCESS

        # Read CSV Feed
        if not source_file.exists():
            logger.error(f"Feed file not found: {source_file}")
            return EXIT_VALIDATION_FAILURE

        import pandas as pd
        raw_df = pd.read_csv(source_file)

        # Stage 4: Data Quality Validation
        audit_engine.audit_service.record_event(
            run_id=context.run_id,
            event_name=PipelineLifecycleEvent.VALIDATION_STARTED,
            severity=AuditSeverity.INFO,
            stage="VALIDATION",
            message=f"Validating {len(raw_df)} rows from {source_file.name}.",
        )

        val_engine = ValidationEngine()
        clean_df, val_report = val_engine.validate_feed(raw_df, context)

        if not val_report.is_valid:
            logger.error(f"Validation failed with error rate {val_report.failure_rate_pct:.2f}%.")
            return EXIT_VALIDATION_FAILURE

        if parsed_args.validation_only:
            logger.info("Validation-only mode requested. Exiting successfully.")
            return EXIT_SUCCESS

        # Stage 5: Transformation & Key Resolution
        audit_engine.audit_service.record_event(
            run_id=context.run_id,
            event_name=PipelineLifecycleEvent.TRANSFORMATION_STARTED,
            severity=AuditSeverity.INFO,
            stage="TRANSFORMATION",
            message=f"Transforming {len(clean_df)} validated rows.",
        )

        trans_engine = TransformationEngine()

        if parsed_args.transformation_only or parsed_args.dry_run:
            logger.info("Dry-run / Transformation-only mode requested. Skipping database load.")
            return EXIT_SUCCESS

        # Stage 6: Warehouse Bulk Loading
        audit_engine.audit_service.record_event(
            run_id=context.run_id,
            event_name=PipelineLifecycleEvent.LOADING_STARTED,
            severity=AuditSeverity.INFO,
            stage="LOADING",
            message=f"Loading {len(clean_df)} records into PostgreSQL warehouse.",
        )

        fact_df, _ = trans_engine.transform_sales_feed(clean_df, context)
        loader_engine = WarehouseLoaderEngine()
        loader_engine.load_warehouse(fact_df, context)

        watermark_mgr = WatermarkManager(db_manager)
        inc_engine = IncrementalEngine(watermark_mgr)
        inc_engine.generate_manifest_and_report(context, classification, file_hash, start_time)
        summary = audit_engine.build_execution_summary(context, start_time)

        logger.info(
            f"RetailFlow ETL completed successfully: {summary.rows_loaded} rows loaded in {summary.duration_ms:.2f}ms."
        )
        return EXIT_SUCCESS

    except ConfigurationError as e:
        sys.stderr.write(f"Configuration Error: {e}\n")
        return EXIT_CONFIG_FAILURE
    except ValidationError as e:
        sys.stderr.write(f"Validation Error: {e}\n")
        return EXIT_VALIDATION_FAILURE
    except DatabaseError as e:
        sys.stderr.write(f"Database Error: {e}\n")
        return EXIT_DATABASE_FAILURE
    except AuditError as e:
        sys.stderr.write(f"Audit Error: {e}\n")
        return EXIT_AUDIT_FAILURE
    except RetailFlowError as e:
        sys.stderr.write(f"Pipeline Error: {e}\n")
        return EXIT_INCREMENTAL_FAILURE
    except Exception as e:
        sys.stderr.write(f"Unexpected Fatal Error: {e}\n")
        return EXIT_UNKNOWN_FAILURE


if __name__ == "__main__":
    sys.exit(run_pipeline())
