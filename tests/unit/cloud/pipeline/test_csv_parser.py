# Unit tests validating CSV parsing and Canonical Data Model mapping transforms

import pytest
import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to
from retailflow.cloud.pipeline.transforms.csv_parser import ParseAndCanonicalizeCsvFn, TAG_MALFORMED

def test_csv_parser_valid_record():
    """Verifies valid CSV rows are correctly parsed and mapped to the CDM layout."""
    valid_csv = "tx-12345,store-99,prod-100,cust-555,emp-777,5,15.50,1.25,2026-07-25T13:00:00Z"
    
    mock_args = [
        "--quarantine_bucket", "test-quarantine",
        "--input_file", "dummy.csv",
        "--silver_dataset", "test_silver",
        "--metadata_dataset", "test_metadata",
        "--correlation_id", "corr-test"
    ]
    
    with TestPipeline(argv=mock_args) as p:
        lines = p | beam.Create([valid_csv])
        
        parsed = (
            lines
            | beam.ParDo(ParseAndCanonicalizeCsvFn()).with_outputs(TAG_MALFORMED, main="valid")
        )
        
        expected = [{
            "transaction_id": "tx-12345",
            "store_id": "store-99",
            "product_id": "prod-100",
            "customer_id": "cust-555",
            "employee_id": "emp-777",
            "quantity": 5,
            "unit_price": 15.5,
            "discount_amount": 1.25,
            "transaction_time": "2026-07-25T13:00:00+00:00"
        }]
        
        assert_that(parsed["valid"], equal_to(expected))

def test_csv_parser_empty_optional_fields():
    """Verifies that missing optional fields (customer_id, discount_amount) default correctly."""
    csv_line = "tx-12345,store-99,prod-100,,emp-777,5,15.50,,2026-07-25T13:00:00Z"
    
    mock_args = [
        "--quarantine_bucket", "test-quarantine",
        "--input_file", "dummy.csv",
        "--silver_dataset", "test_silver",
        "--metadata_dataset", "test_metadata",
        "--correlation_id", "corr-test"
    ]
    
    with TestPipeline(argv=mock_args) as p:
        lines = p | beam.Create([csv_line])
        
        parsed = (
            lines
            | beam.ParDo(ParseAndCanonicalizeCsvFn()).with_outputs(TAG_MALFORMED, main="valid")
        )
        
        expected = [{
            "transaction_id": "tx-12345",
            "store_id": "store-99",
            "product_id": "prod-100",
            "customer_id": None,
            "employee_id": "emp-777",
            "quantity": 5,
            "unit_price": 15.5,
            "discount_amount": 0.0,
            "transaction_time": "2026-07-25T13:00:00+00:00"
        }]
        
        assert_that(parsed["valid"], equal_to(expected))

def test_csv_parser_malformed_columns_count():
    """Verifies that rows with mismatched columns are routed to the malformed side-output."""
    invalid_cols = "tx-123,store-99,prod-100,5,15.50"
    
    mock_args = [
        "--quarantine_bucket", "test-quarantine",
        "--input_file", "dummy.csv",
        "--silver_dataset", "test_silver",
        "--metadata_dataset", "test_metadata",
        "--correlation_id", "corr-test"
    ]
    
    with TestPipeline(argv=mock_args) as p:
        lines = p | beam.Create([invalid_cols])
        
        parsed = (
            lines
            | beam.ParDo(ParseAndCanonicalizeCsvFn()).with_outputs(TAG_MALFORMED, main="valid")
        )
        
        assert_that(parsed["valid"], equal_to([]))
        
        def assert_malformed(elements):
            assert len(elements) == 1
            assert "raw_line" in elements[0]
            assert "error" in elements[0]
            assert "Schema Column mismatch" in elements[0]["error"]
            
        assert_that(parsed[TAG_MALFORMED], assert_malformed)

def test_csv_parser_invalid_datatypes():
    """Verifies that rows with invalid datatypes are caught by validation and routed to malformed side-output."""
    invalid_types = "tx-12345,store-99,prod-100,cust-555,emp-777,abc,xyz,0.00,2026-07-25T13:00:00Z"
    
    mock_args = [
        "--quarantine_bucket", "test-quarantine",
        "--input_file", "dummy.csv",
        "--silver_dataset", "test_silver",
        "--metadata_dataset", "test_metadata",
        "--correlation_id", "corr-test"
    ]
    
    with TestPipeline(argv=mock_args) as p:
        lines = p | beam.Create([invalid_types])
        
        parsed = (
            lines
            | beam.ParDo(ParseAndCanonicalizeCsvFn()).with_outputs(TAG_MALFORMED, main="valid")
        )
        
        assert_that(parsed["valid"], equal_to([]))
        
        def assert_validation_error(elements):
            assert len(elements) == 1
            assert "Validation Error" in elements[0]["error"]
            
        assert_that(parsed[TAG_MALFORMED], assert_validation_error)

