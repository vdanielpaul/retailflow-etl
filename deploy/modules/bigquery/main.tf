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
  description                = "Stores immutable raw business data ingested from operational source systems."
  delete_contents_on_destroy = var.delete_contents_on_destroy

  # Dataset-level table and partition expiration properties removed per best practices.
  # Expiration controls are managed on individual staging/log tables during creation.

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
    layer               = "bronze"
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
  description                = "Stores validated and standardized business entities used for downstream transformations."
  delete_contents_on_destroy = var.delete_contents_on_destroy

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
    layer               = "silver"
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
  description                = "Stores curated analytical models optimized for reporting and business intelligence workloads."
  delete_contents_on_destroy = var.delete_contents_on_destroy

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
    layer               = "gold"
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
  description                = "Stores operational metadata supporting pipeline execution, auditing, monitoring, and lineage."
  delete_contents_on_destroy = var.delete_contents_on_destroy

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = "confidential" # Pipeline credentials logs require confidential classification
    layer               = "metadata"
  })
}
