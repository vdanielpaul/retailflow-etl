# Main infrastructure entry point for RetailFlow ETL v2.0
# Calls the environment modules to provision GCS storage, BigQuery, and Pub/Sub resources.

#-------------------------------------------------------------------------------
# 1. Core Platform Modules
#-------------------------------------------------------------------------------
module "storage" {
  source = "./modules/storage"

  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  force_destroy       = var.environment == "prod" ? false : true
  owner               = var.owner
  data_classification = var.data_classification
  common_labels       = local.common_labels
}

module "bigquery" {
  source = "./modules/bigquery"

  project_id                 = var.project_id
  region                     = var.region
  environment                = var.environment
  delete_contents_on_destroy = var.environment == "prod" ? false : true
  owner                      = var.owner
  data_classification        = var.data_classification
  common_labels              = local.common_labels
}

module "pubsub" {
  source = "./modules/pubsub"

  project_id    = var.project_id
  environment   = var.environment
  owner         = var.owner
  common_labels = local.common_labels
}

#-------------------------------------------------------------------------------
# 2. Ingestion Triggers & IAM Integrations
#-------------------------------------------------------------------------------

# Retrieve the system-managed GCS service account for GCS-to-Pub/Sub notifications IAM permissions
data "google_storage_project_service_account" "gcs_account" {
  project = var.project_id
}

# Authorize GCS Service Account to publish raw ingest event messages to our raw ingestion topic
resource "google_pubsub_topic_iam_member" "gcs_publisher" {
  topic   = module.pubsub.ingestion_events_topic_name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
  project = var.project_id
}

# Configure GCS Object Notification to trigger whenever files are successfully uploaded (OBJECT_FINALIZE)
resource "google_storage_notification" "raw_upload_notification" {
  bucket         = module.storage.raw_bucket_name
  payload_format = "JSON_API_V1"
  topic          = module.pubsub.ingestion_events_topic_id
  event_types    = ["OBJECT_FINALIZE"]

  # Explicit dependency guarantees IAM permissions exist before notification registration is attempted by GCS
  depends_on = [google_pubsub_topic_iam_member.gcs_publisher]
}
