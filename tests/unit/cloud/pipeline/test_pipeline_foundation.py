# Unit tests validating the Apache Beam Dataflow Ingestion Pipeline foundation

import pytest
import tempfile
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from retailflow.cloud.pipeline.options import RetailFlowPipelineOptions
from retailflow.cloud.pipeline.dependencies import PipelineDependencyContainer
from retailflow.cloud.pipeline.pipeline import build_pipeline
from retailflow.cloud.pipeline.runner import run

def test_pipeline_options_argparse():
    """Verifies custom arguments are parsed and mapped correctly."""
    args = [
        "--input_file", "gs://test-bucket/sales.csv",
        "--silver_dataset", "retailflow_dev_silver",
        "--metadata_dataset", "retailflow_dev_metadata",
        "--quarantine_bucket", "retailflow-dev-quarantine",
        "--correlation_id", "corr-test-999",
        "--environment", "staging",
        "--project", "test-project"
    ]
    
    options = PipelineOptions(args)
    custom_options = options.view_as(RetailFlowPipelineOptions)
    
    assert custom_options.input_file.get() == "gs://test-bucket/sales.csv"
    assert custom_options.silver_dataset.get() == "retailflow_dev_silver"
    assert custom_options.metadata_dataset.get() == "retailflow_dev_metadata"
    assert custom_options.quarantine_bucket.get() == "retailflow-dev-quarantine"
    assert custom_options.correlation_id.get() == "corr-test-999"
    assert custom_options.environment.get() == "staging"
    assert options.get_all_options().get("project") == "test-project"

def test_pipeline_options_missing_required():
    """Verifies ValueError is raised when required settings are missing."""
    with pytest.raises(ValueError) as exc_info:
        run(["--environment", "staging"])
    assert "Pipeline option" in str(exc_info.value)


def test_pipeline_graph_assembly():
    """Verifies build_pipeline successfully maps graph transformations without throwing errors."""
    args = [
        "--input_file", "dummy.csv",
        "--silver_dataset", "test_silver",
        "--metadata_dataset", "test_metadata",
        "--quarantine_bucket", "test-quarantine",
        "--correlation_id", "corr-test",
    ]

    options = PipelineOptions(args)
    custom_options = options.view_as(RetailFlowPipelineOptions)
    dependency_container = PipelineDependencyContainer("test-project", "test_metadata")
    
    pipeline = beam.Pipeline(options=options)
    build_pipeline(pipeline, custom_options, dependency_container)
    
    # Assert pipeline builds successfully without raising exceptions
    assert pipeline is not None


def test_local_direct_runner_execution():
    """Verifies that the runner executes successfully on DirectRunner with local files."""
    # Create temporary local mock data to act as input stream
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as temp_file:
        temp_file.write("transaction_id,store_id,amount\n")
        temp_file.write("tx-001,store-10,120.50\n")
        temp_file.write("tx-002,store-12,45.00\n")
        temp_file.flush()
        
        args = [
            "--input_file", temp_file.name,
            "--silver_dataset", "test_silver",
            "--metadata_dataset", "test_metadata",
            "--quarantine_bucket", "test-quarantine",
            "--correlation_id", "corr-local-test",
            "--runner", "DirectRunner"
        ]
        
        # Execute the pipeline with parameters
        result = run(args)
        
        # Verify the pipeline completed in DONE state
        assert str(result.state) == "DONE"
