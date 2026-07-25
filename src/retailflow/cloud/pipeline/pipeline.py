# Assembles the Apache Beam execution graph for RetailFlow ETL processing

import logging
import apache_beam as beam
from retailflow.cloud.pipeline.options import RetailFlowPipelineOptions
from retailflow.cloud.pipeline.dependencies import PipelineDependencyContainer
from retailflow.cloud.pipeline.transforms.csv_parser import ParseAndCanonicalizeCsvFn, TAG_MALFORMED

logger = logging.getLogger("retailflow-pipeline-builder")

def build_pipeline(
    pipeline: beam.Pipeline,
    options: RetailFlowPipelineOptions,
    dependencies: PipelineDependencyContainer
) -> tuple[beam.PCollection, beam.PCollection]:
    """Assembles PTransforms onto the provided Beam pipeline graph context.

    Args:
        pipeline: The active beam.Pipeline context object.
        options: Custom RetailFlowPipelineOptions settings.
        dependencies: Container holding metadata repository and database clients.

    Returns:
        A tuple of (valid_records_pcollection, malformed_records_pcollection)
    """
    input_path = options.input_file
    correlation_id = options.correlation_id

    logger.info(f"Building pipeline steps for correlation ID: {correlation_id}")

    # 1. Read GCS input file text lines
    raw_lines = (
        pipeline
        | "Read Raw GCS File" >> beam.io.ReadFromText(input_path, validate=False)
        | "Filter Header" >> beam.Filter(lambda line: not line.startswith("transaction_id"))
    )

    # 2. Parse CSV rows and map to Canonical Data Model
    parsed_results = (
        raw_lines
        | "Parse & Canonicalize CSV" >> beam.ParDo(
            ParseAndCanonicalizeCsvFn()
        ).with_outputs(TAG_MALFORMED, main="valid_sales")
    )

    valid_sales = parsed_results["valid_sales"]
    malformed_rows = parsed_results[TAG_MALFORMED]

    # Log operational statistics (scaffolding check)
    _ = (
        valid_sales
        | "Count Valid Sales" >> beam.combiners.Count.Globally()
        | "Log Valid Count" >> beam.Map(
            lambda count: logger.info(
                f"[Stage: CDM_MAPPING] [Trace: {correlation_id}] Successfully mapped {count} canonical records."
            )
        )
    )

    _ = (
        malformed_rows
        | "Count Malformed Rows" >> beam.combiners.Count.Globally()
        | "Log Malformed Count" >> beam.Map(
            lambda count: logger.warning(
                f"[Stage: CDM_MAPPING] [Trace: {correlation_id}] Flagged {count} malformed rows during CSV parsing."
            )
        )
    )

    return valid_sales, malformed_rows
