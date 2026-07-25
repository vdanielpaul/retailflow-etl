# Assembles the Apache Beam execution graph for RetailFlow ETL processing

import logging
import apache_beam as beam
from retailflow.cloud.pipeline.options import RetailFlowPipelineOptions
from retailflow.cloud.pipeline.dependencies import PipelineDependencyContainer

logger = logging.getLogger("retailflow-pipeline-builder")

def build_pipeline(
    pipeline: beam.Pipeline,
    options: RetailFlowPipelineOptions,
    dependencies: PipelineDependencyContainer
) -> None:
    """Assembles PTransforms onto the provided Beam pipeline graph context.

    Args:
        pipeline: The active beam.Pipeline context object.
        options: Custom RetailFlowPipelineOptions settings.
        dependencies: Container holding metadata repository and database clients.
    """
    input_path = options.input_file
    correlation_id = options.correlation_id

    logger.info(f"Building pipeline steps for correlation ID: {correlation_id}")

    # Build the execution DAG steps (Task 3.1 Scaffolding)
    raw_rows = (
        pipeline
        | "Read Raw GCS File" >> beam.io.ReadFromText(input_path, validate=False)
        | "Filter Header" >> beam.Filter(lambda line: not line.startswith("transaction_id"))
    )

    
    _ = (
        raw_rows
        | "Count Raw Elements" >> beam.combiners.Count.Globally()
        | "Log Ingest Row Count" >> beam.Map(
            lambda count: logger.info(
                f"[Stage: INGEST_STATS] [Trace: {correlation_id}] Foundation verified. Found {count} rows in input stream."
            )
        )
    )
