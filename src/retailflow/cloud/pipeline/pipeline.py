# Assembles the Apache Beam execution graph for RetailFlow ETL processing

import logging
from typing import Tuple

import apache_beam as beam

from retailflow.cloud.pipeline.options import RetailFlowPipelineOptions
from retailflow.cloud.pipeline.dependencies import PipelineDependencyContainer
from retailflow.cloud.pipeline.transforms.csv_parser import ParseAndCanonicalizeCsvFn, TAG_MALFORMED
from retailflow.cloud.pipeline.transforms.validation_transform import ValidateSaleRecordFn, TAG_INVALID
from retailflow.cloud.pipeline.transforms.transformation_transform import ApplyTransformationFn, TAG_TRANSFORM_ERROR

logger = logging.getLogger("retailflow-pipeline-builder")

def build_pipeline(
    pipeline: beam.Pipeline,
    options: RetailFlowPipelineOptions,
    dependencies: PipelineDependencyContainer,
) -> Tuple[beam.PCollection, beam.PCollection, beam.PCollection, beam.PCollection]:
    """Assembles PTransforms onto the provided Beam pipeline graph context.

    Responsibilities:
      1. Read raw text lines from GCS (or local path for DirectRunner)
      2. Parse CSV rows and map to Canonical Data Model
      3. Apply business rule validation via BusinessRuleAdapter
      4. Apply three-stage transformation via TransformationAdapter

    The caller (runner.py) is responsible for attaching I/O sinks (e.g.,
    WriteToText for quarantine output). build_pipeline() only constructs the
    transform graph and returns the output PCollections.

    Args:
        pipeline: The active beam.Pipeline context object.
        options: Custom RetailFlowPipelineOptions settings.
        dependencies: Container holding metadata repository and database clients.

    Returns:
        A tuple of:
          - transformed_sales: Enriched records that passed all stages (→ Task 3.5 Silver load).
          - transform_errors: Records that failed the transformation stage.
          - invalid_records: Records that failed business rule validation.
          - malformed_rows: Records that failed CSV parsing.
    """
    input_path = options.input_file
    correlation_id = options.correlation_id

    logger.info(f"Building pipeline steps for correlation ID: {correlation_id}")

    # -------------------------------------------------------------------------
    # Stage 1: Read GCS input file text lines
    # -------------------------------------------------------------------------
    raw_lines = (
        pipeline
        | "Read Raw GCS File" >> beam.io.ReadFromText(input_path, validate=False)
        | "Filter Header" >> beam.Filter(lambda line: not line.startswith("transaction_id"))
    )

    # -------------------------------------------------------------------------
    # Stage 2: Parse CSV rows and map to Canonical Data Model
    # -------------------------------------------------------------------------
    parsed_results = (
        raw_lines
        | "Parse & Canonicalize CSV" >> beam.ParDo(
            ParseAndCanonicalizeCsvFn()
        ).with_outputs(TAG_MALFORMED, main="valid_sales")
    )

    valid_sales = parsed_results["valid_sales"]
    malformed_rows = parsed_results[TAG_MALFORMED]

    # -------------------------------------------------------------------------
    # Stage 3: Business rule validation via BusinessRuleAdapter
    #
    # The ValidateSaleRecordFn delegates entirely to BusinessRuleAdapter, which
    # invokes the existing BusinessRuleValidator without modification.
    # Beam is responsible only for routing — business logic remains in v1.0.
    # -------------------------------------------------------------------------
    validated_results = (
        valid_sales
        | "Apply Business Rules" >> beam.ParDo(
            ValidateSaleRecordFn(
                correlation_id=str(correlation_id),
                run_id=dependencies.run_id,
                filename=str(input_path),
            )
        ).with_outputs(TAG_INVALID, main="verified_sales")
    )

    verified_sales = validated_results["verified_sales"]
    invalid_records = validated_results[TAG_INVALID]

# -------------------------------------------------------------------------
    # Stage 4: Three-stage transformation via TransformationAdapter
    #
    # The ApplyTransformationFn delegates entirely to TransformationAdapter,
    # which invokes clean_dataframe, normalize_dataframe, and enrich_sales_dataframe
    # without modification. Stages 4–5 (surrogate keys, fact payload) are Task 3.5.
    # -------------------------------------------------------------------------
    transformation_results = (
        verified_sales
        | "Apply Transformation" >> beam.ParDo(
            ApplyTransformationFn(
                correlation_id=str(correlation_id),
                run_id=dependencies.run_id,
                filename=str(input_path),
            )
        ).with_outputs(TAG_TRANSFORM_ERROR, main="transformed_sales")
    )

    transformed_sales = transformation_results["transformed_sales"]
    transform_errors = transformation_results[TAG_TRANSFORM_ERROR]

    # -------------------------------------------------------------------------
    # Operational statistics — logged per pipeline run for observability
    # -------------------------------------------------------------------------
    _ = (
        transformed_sales
        | "Count Transformed Sales" >> beam.combiners.Count.Globally()
        | "Log Transformed Count" >> beam.Map(
            lambda count: logger.info(
                f"[Stage: TRANSFORMATION] [Trace: {correlation_id}] {count} records successfully transformed."
            )
        )
    )

    _ = (
        transform_errors
        | "Count Transform Errors" >> beam.combiners.Count.Globally()
        | "Log Transform Error Count" >> beam.Map(
            lambda count: logger.warning(
                f"[Stage: TRANSFORMATION] [Trace: {correlation_id}] {count} records failed transformation."
            )
        )
    )

    _ = (
        invalid_records
        | "Count Invalid Records" >> beam.combiners.Count.Globally()
        | "Log Invalid Count" >> beam.Map(
            lambda count: logger.warning(
                f"[Stage: VALIDATION] [Trace: {correlation_id}] {count} records failed business rule validation and were quarantined."
            )
        )
    )

    _ = (
        malformed_rows
        | "Count Malformed Rows" >> beam.combiners.Count.Globally()
        | "Log Malformed Count" >> beam.Map(
            lambda count: logger.warning(
                f"[Stage: CDM_MAPPING] [Trace: {correlation_id}] {count} malformed rows quarantined during CSV parsing."
            )
        )
    )

    return transformed_sales, transform_errors, invalid_records, malformed_rows
