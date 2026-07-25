# Custom Apache Beam pipeline options configuration for RetailFlow ETL v2.0
# Separates infrastructure runner options from business datasets configurations.

from apache_beam.options.pipeline_options import PipelineOptions

class RetailFlowPipelineOptions(PipelineOptions):
    """Custom execution parameters passed to the Apache Beam pipeline runner."""
    
    @classmethod
    def _add_argparse_args(cls, parser):
        #-----------------------------------------------------------------------
        # 1. Infrastructure Runner Options
        #-----------------------------------------------------------------------
        parser.add_value_provider_argument(
            "--quarantine_bucket",
            type=str,
            required=True,
            help="The GCS bucket name where quarantined records will be saved."
        )
        parser.add_value_provider_argument(
            "--environment",
            type=str,
            default="dev",
            help="The deployment environment profile stage (dev, staging, or prod)."
        )

        #-----------------------------------------------------------------------
        # 2. Business Pipeline Config Options
        #-----------------------------------------------------------------------
        parser.add_value_provider_argument(
            "--input_file",
            type=str,
            required=True,
            help="The GCS file URI of the raw input CSV to process."
        )
        parser.add_value_provider_argument(
            "--silver_dataset",
            type=str,
            required=True,
            help="The target BigQuery Silver canonical dataset ID."
        )
        parser.add_value_provider_argument(
            "--metadata_dataset",
            type=str,
            required=True,
            help="The BigQuery Metadata dataset ID for watermarks and audits."
        )
        parser.add_value_provider_argument(
            "--correlation_id",
            type=str,
            required=True,
            help="The correlation trace identifier linking pipeline execution logs."
        )
