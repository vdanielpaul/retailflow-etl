# Custom Beam DoFns for safe CSV line parsing and Canonical Data Model mapping

import csv
import logging
from typing import Generator, Tuple, Dict, Any, Optional, Union
import apache_beam as beam
from pydantic import ValidationError
from retailflow.models.canonical import CanonicalSale

logger = logging.getLogger("csv-parser")

# Define Beam side-output tags for routing malformed/failed rows
TAG_MALFORMED = "malformed_rows"

class ParseAndCanonicalizeCsvFn(beam.DoFn):
    """Parses raw CSV lines and converts them into CanonicalSale model representations.

    Outputs valid canonical dictionaries to the main output stream, and routes
    any malformed rows or parsing validation failures to the TAG_MALFORMED side output.
    """

    def __init__(self, expected_columns: Optional[list[str]] = None) -> None:
        self.expected_columns = expected_columns or [
            "transaction_id",
            "store_id",
            "product_id",
            "customer_id",
            "employee_id",
            "quantity",
            "unit_price",
            "discount_amount",
            "transaction_time"
        ]

    def process(self, element: str) -> Generator[Union[Dict[str, Any], beam.pvalue.TaggedOutput], None, None]:

        """Parses a CSV text line, runs type validation, and yields canonical dicts or tagged errors.

        Args:
            element: Raw text line string.
        """
        # Skip header lines safely if they slip past the filter stage
        if element.startswith("transaction_id"):
            return

        try:
            # Parse line using python's standard csv parser
            reader = csv.reader([element])
            row = next(reader)
        except Exception as e:
            logger.warning(f"Failed to parse raw CSV row line: {element}. Error: {str(e)}")
            yield beam.pvalue.TaggedOutput(TAG_MALFORMED, {"raw_line": element, "error": f"CSV Parse Error: {str(e)}"})
            return

        # Check column count bounds matching expected schema layout
        if len(row) != len(self.expected_columns):
            error_msg = f"Schema Column mismatch. Expected {len(self.expected_columns)} columns, got {len(row)}."
            yield beam.pvalue.TaggedOutput(TAG_MALFORMED, {"raw_line": element, "error": error_msg})
            return

        # Map row values to expected schema labels
        row_dict = dict(zip(self.expected_columns, row))

        # Handle empty fields for optional columns
        if not row_dict.get("customer_id") or row_dict["customer_id"].strip() == "":
            row_dict["customer_id"] = None
        if not row_dict.get("discount_amount") or row_dict["discount_amount"].strip() == "":
            row_dict["discount_amount"] = "0.00"

        try:
            # Instantiate the v1.0 Pydantic model to enforce types and structure
            canonical_sale = CanonicalSale(**row_dict)
            
            # Convert decimal/datetime fields to standard primitive types for BigQuery compatibility
            sale_dict = canonical_sale.model_dump()
            sale_dict["unit_price"] = float(canonical_sale.unit_price)
            sale_dict["discount_amount"] = float(canonical_sale.discount_amount)
            sale_dict["transaction_time"] = canonical_sale.transaction_time.isoformat()
            
            yield sale_dict
            
        except ValidationError as val_err:
            error_details = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in val_err.errors()])
            logger.debug(f"Row failed canonical schema mapping constraints: {element}. Reason: {error_details}")
            yield beam.pvalue.TaggedOutput(TAG_MALFORMED, {"raw_line": element, "error": f"Validation Error: {error_details}"})
        except Exception as ex:
            yield beam.pvalue.TaggedOutput(TAG_MALFORMED, {"raw_line": element, "error": f"Type Conversion Error: {str(ex)}"})
