# Google Pub/Sub topic and subscription resources configuration
# Used to publish and buffer storage file finalized events.
# Naming convention: retailflow-${var.environment}-${resource_type}

#-------------------------------------------------------------------------------
# 1. Ingestion Trigger Topic
# Publishes events when raw files are finalized in GCS.
#-------------------------------------------------------------------------------
resource "google_pubsub_topic" "ingest_trigger" {
  name    = "retailflow-${var.environment}-ingest-trigger-topic"
  project = var.project_id

  labels = merge(var.common_labels, {
    owner = var.owner
  })
}

#-------------------------------------------------------------------------------
# 2. Ingestion Trigger Subscription (Pull Delivery)
# Used for operational testing, validation checks, and pipeline buffering.
#-------------------------------------------------------------------------------
resource "google_pubsub_subscription" "ingest_trigger_sub" {
  name    = "retailflow-${var.environment}-ingest-trigger-sub"
  project = var.project_id
  topic   = google_pubsub_topic.ingest_trigger.name

  # Message retention and delivery settings suitable for batch ingestion
  message_retention_duration = "604800s" # Retain unacknowledged messages for 7 days
  retain_acked_messages      = false
  ack_deadline_seconds       = 60 # Set processing acknowledgment deadline to 1 minute

  labels = merge(var.common_labels, {
    owner = var.owner
  })
}
