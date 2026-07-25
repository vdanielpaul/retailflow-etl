# Outputs for the Pub/Sub module
# Exposes topic and subscription parameters for ingestion triggers linking.

output "ingestion_events_topic_name" {
  value       = google_pubsub_topic.ingestion_events.name
  description = "The name of the GCS raw ingestion events topic."
}

output "ingestion_events_topic_id" {
  value       = google_pubsub_topic.ingestion_events.id
  description = "The ID of the GCS raw ingestion events topic."
}

output "processing_events_topic_name" {
  value       = google_pubsub_topic.processing_events.name
  description = "The name of the validated processing events topic."
}

output "processing_events_topic_id" {
  value       = google_pubsub_topic.processing_events.id
  description = "The ID of the validated processing events topic."
}

output "processing_events_subscription_name" {
  value       = google_pubsub_subscription.processing_events_sub.name
  description = "The name of the processing events pull subscription."
}

output "processing_events_subscription_id" {
  value       = google_pubsub_subscription.processing_events_sub.id
  description = "The ID of the processing events pull subscription."
}
