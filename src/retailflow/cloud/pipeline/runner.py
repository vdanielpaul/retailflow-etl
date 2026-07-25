# Command-line CLI entrypoint for Dataflow Pipeline runner execution

import sys
import logging
from typing import Any
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from retailflow.cloud.pipeline.options import RetailFlowPipelineOptions
from retailflow.cloud.pipeline.dependencies import PipelineDependencyContainer
from retailflow.cloud.pipeline.pipeline import build_pipeline

def run(argv=None) -> Any:
    """Invokes parsing of option parameters and triggers pipeline DAG execution.

    Args:
        argv: Optional CLI arguments list.

    Returns:
        The pipeline execution result.
    """
    # 1. Parse custom and standard execution options
    pipeline_options = PipelineOptions(argv)
    custom_options = pipeline_options.view_as(RetailFlowPipelineOptions)

    # Enforce options validations programmatically (prevents argparse failures in test suites)
    args_list = argv if argv is not None else sys.argv
    required_options = ["input_file", "silver_dataset", "metadata_dataset", "quarantine_bucket", "correlation_id"]
    for opt_name in required_options:
        flag = f"--{opt_name}"
        if not any(arg == flag or arg.startswith(f"{flag}=") for arg in args_list):
            raise ValueError(f"Pipeline option --{opt_name} is required but was not provided.")


    # Configure logs
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("retailflow-runner")

    # 2. Extract standard GCP parameters
    all_opts = pipeline_options.get_all_options()
    project_id = all_opts.get("project", "retailflow-dev-project")
    environment = all_opts.get("environment", "dev")

    
    # Resolve value provider safely depending on whether we are in execution context
    metadata_dataset = (
        custom_options.metadata_dataset.get()
        if hasattr(custom_options.metadata_dataset, "is_accessible") and custom_options.metadata_dataset.is_accessible()
        else all_opts.get("metadata_dataset") or "retailflow_metadata_placeholder"
    )


    logger.info(f"Runner entrypoint starting. Project context: {project_id}")

    # 3. Setup infrastructure dependencies
    dependency_container = PipelineDependencyContainer(
        project_id=project_id,
        metadata_dataset=str(metadata_dataset),
        environment=str(environment)
    )

    # 4. Construct and execute the Beam pipeline graph
    pipeline = beam.Pipeline(options=pipeline_options)
    build_pipeline(pipeline, custom_options, dependency_container)

    # Execute execution graph blocks synchronously
    result = pipeline.run()
    result.wait_until_finish()
    
    logger.info("Runner entrypoint execution finished.")
    return result

if __name__ == "__main__":
    run(sys.argv)
