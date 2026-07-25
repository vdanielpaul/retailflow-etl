# Google Pub/Sub topic and subscription resources configuration
# Separates raw ingestion storage notification alerts from validated processing trigger events.
# Naming convention: retailflow-${var.environment}-${resource_name}

#-------------------------------------------------------------------------------
# 1. Ingestion Events Topic & Subscription (Raw storage alerts)
#-------------------------------------------------------------------------------
resource "google_pubsub_topic" "ingestion_events" {
  name    = "retailflow-${var.environment}-ingestion-events"
  project = var.project_id

  labels = merge(var.common_labels, {
    owner = var.owner
  })
}

resource "google_pubsub_subscription" "ingestion_events_sub" {
  name    = "retailflow-${var.environment}-ingestion-events-sub"
  project = var.project_id
  topic   = google_pubsub_topic.ingestion_events.name

  message_retention_duration = "604800s" # 7 days
  retain_acked_messages      = false
  ack_deadline_seconds       = 60

  labels = merge(var.common_labels, {
    owner = var.owner
  })
}

#-------------------------------------------------------------------------------
# 2. Processing Events Topic & Subscription (Post-duplicate verification trigger)
#-------------------------------------------------------------------------------
resource "google_pubsub_topic" "processing_events" {
  name    = "retailflow-${var.environment}-processing-events"
  project = var.project_id

  labels = merge(var.common_labels, {
    owner = var.owner
  })
}

resource "google_pubsub_subscription" "processing_events_sub" {
  name    = "retailflow-${var.environment}-processing-events-sub"
  project = var.project_id
  topic   = google_pubsub_topic.processing_events.name

  message_retention_duration = "604800s" # 7 days
  retain_acked_messages      = false
  ack_deadline_seconds       = 600 # Extended processing timeout for Dataflow workers (10 minutes)

  labels = merge(var.common_labels, {
    owner = var.owner
  })
}
