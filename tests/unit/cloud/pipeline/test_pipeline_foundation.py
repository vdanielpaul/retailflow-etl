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
    verified_sales, invalid_records, malformed_rows = build_pipeline(pipeline, custom_options, dependency_container)

    # Assert all three PCollections are produced
    assert pipeline is not None
    assert verified_sales is not None
    assert invalid_records is not None
    assert malformed_rows is not None



def test_local_direct_runner_execution():
    """Verifies that build_pipeline() executes successfully on DirectRunner with local files.

    Calls build_pipeline() directly (not run()) to avoid the GCS WriteToText
    sinks wired in runner.py, which require a real GCS bucket. The test
    exercises the full transform graph — read, parse, validate — and confirms
    the pipeline completes in DONE state.
    """
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as temp_file:
        # Write rows that will parse but fail canonical mapping (wrong column count)
        # so the full graph exercises both valid_sales and malformed_rows paths.
        temp_file.write("transaction_id,store_id,amount\n")
        temp_file.write("tx-001,store-10,120.50\n")
        temp_file.flush()

        args = [
            "--input_file", temp_file.name,
            "--silver_dataset", "test_silver",
            "--metadata_dataset", "test_metadata",
            "--quarantine_bucket", "test-quarantine",
            "--correlation_id", "corr-local-test",
            "--runner", "DirectRunner",
        ]

        options = PipelineOptions(args)
        custom_options = options.view_as(RetailFlowPipelineOptions)
        deps = PipelineDependencyContainer("test-project", "test_metadata")

        pipeline = beam.Pipeline(options=options)
        verified_sales, invalid_records, malformed_rows = build_pipeline(
            pipeline, custom_options, deps
        )

        result = pipeline.run()
        result.wait_until_finish()

        assert str(result.state) == "DONE"
