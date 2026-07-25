# Google BigQuery datasets configuration
# Defines the Medallion architecture datasets: bronze, silver, gold, and metadata.
# Naming convention: retailflow_${var.environment}_${purpose} to conform to BigQuery dataset ID constraints (only letters, numbers, and underscores).

#-------------------------------------------------------------------------------
# 1. Bronze Dataset
# Staging dataset for raw ingestion tables.
#-------------------------------------------------------------------------------
resource "google_bigquery_dataset" "bronze" {
  dataset_id                 = "retailflow_${var.environment}_bronze"
  project                    = var.project_id
  location                   = var.region
  description                = "Bronze layer dataset holding raw, immutable incoming store POS transactional table records."
  delete_contents_on_destroy = var.delete_contents_on_destroy

  # For raw temporary ingest data, set a default partition/table expiration to 30 days to limit long-term storage charges.
  default_partition_expiration_ms = 2592000000 # 30 days in milliseconds
  default_table_expiration_ms     = 2592000000 # 30 days in milliseconds

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })
}

#-------------------------------------------------------------------------------
# 2. Silver Dataset
# Validated, cleaned, and schema-enforced canonical table records.
#-------------------------------------------------------------------------------
resource "google_bigquery_dataset" "silver" {
  dataset_id                 = "retailflow_${var.environment}_silver"
  project                    = var.project_id
  location                   = var.region
  description                = "Silver layer dataset containing cleaned, validated, and schema-compliant Canonical Data Model (CDM) records."
  delete_contents_on_destroy = var.delete_contents_on_destroy

  # Silver tables do not set default expiration; data is retained indefinitely for operational analysis.

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })
}

#-------------------------------------------------------------------------------
# 3. Gold Dataset
# Dimensional warehouse star schema models (fact and dimensions).
#-------------------------------------------------------------------------------
resource "google_bigquery_dataset" "gold" {
  dataset_id                 = "retailflow_${var.environment}_gold"
  project                    = var.project_id
  location                   = var.region
  description                = "Gold layer dataset containing the final dimensional Star Schema warehouse models (fact_sales, dim_customer, etc.)."
  delete_contents_on_destroy = var.delete_contents_on_destroy

  # Gold analytics tables retain data indefinitely.

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })
}

#-------------------------------------------------------------------------------
# 4. Metadata Dataset
# Watermarks, audit logs, and execution monitoring telemetry.
#-------------------------------------------------------------------------------
resource "google_bigquery_dataset" "metadata" {
  dataset_id                 = "retailflow_${var.environment}_metadata"
  project                    = var.project_id
  location                   = var.region
  description                = "Metadata layer dataset containing etl_watermark, etl_audit_log, and execution tracking tables."
  delete_contents_on_destroy = var.delete_contents_on_destroy

  # Metadata tables do not set default expiration.

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = "confidential" # Audit trail logs are confidential
  })
}
