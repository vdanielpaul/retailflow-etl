# Ingestion batch processing pipeline execution runner

import sys
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from retailflow.cloud.pipeline.options import RetailFlowPipelineOptions
from retailflow.cloud.pipeline.dependencies import PipelineDependencyContainer

from typing import Any

def run(argv=None) -> Any:

    """Builds and executes the Apache Beam batch processing pipeline.

    Args:
        argv: Optional list of command-line argument strings.

    Returns:
        The pipeline execution result.
    """
    # 1. Parse custom and standard execution options
    pipeline_options = PipelineOptions(argv)
    custom_options = pipeline_options.view_as(RetailFlowPipelineOptions)

    # 2. Extract values from ValueProviders or parameters
    # Note: ValueProvider values can only be accessed inside transforms at runtime,
    # but standard options (like project or runner) can be read immediately.
    project_id = pipeline_options.get_all_options().get("project", "retailflow-dev-project")
    environment = custom_options.environment
    metadata_dataset = custom_options.metadata_dataset.get() if hasattr(custom_options.metadata_dataset, "get") else custom_options.metadata_dataset
    
    # Configure logs
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("retailflow-dataflow-pipeline")
    logger.info(
        f"Initializing pipeline execution. Project: {project_id}, Env: {environment}, Trace ID: {custom_options.correlation_id}"
    )

    # 3. Setup infrastructure dependencies
    dependency_container = PipelineDependencyContainer(
        project_id=project_id,
        metadata_dataset=str(metadata_dataset),
        environment=str(environment)
    )

    # 4. Construct the Apache Beam pipeline
    # DirectRunner or DataflowRunner is configured based on standard Beam options (--runner)
    with beam.Pipeline(options=pipeline_options) as pipeline:
        # Task 3.1: Scaffolding placeholder pipeline
        # Reads the configured GCS raw input text file, counts rows, and logs completion
        input_path = custom_options.input_file
        
        raw_rows = (
            pipeline
            | "Read Raw GCS File" >> beam.io.ReadFromText(input_path)
            | "Filter Header" >> beam.Filter(lambda line: not line.startswith("transaction_id"))
        )
        
        # Count pipeline element statistics (scaffolding check)
        _ = (
            raw_rows
            | "Count Raw Elements" >> beam.combiners.Count.Globally()
            | "Log Ingest Row Count" >> beam.Map(
                lambda count: logger.info(f"Pipeline foundation verified. Found {count} rows in input stream.")
            )
        )

    logger.info("Pipeline execution complete.")
    return pipeline.result

if __name__ == "__main__":
    run(sys.argv)
