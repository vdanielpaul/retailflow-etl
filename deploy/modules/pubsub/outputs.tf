# Outputs for the Pub/Sub module
# Exposes topic and subscription names/ids for ingestion notifications linking.

output "topic_name" {
  value       = google_pubsub_topic.ingest_trigger.name
  description = "The name of the GCS ingest trigger Pub/Sub topic."
}

output "topic_id" {
  value       = google_pubsub_topic.ingest_trigger.id
  description = "The ID of the GCS ingest trigger Pub/Sub topic."
}

output "subscription_name" {
  value       = google_pubsub_subscription.ingest_trigger_sub.name
  description = "The name of the Pub/Sub pull subscription."
}

output "subscription_id" {
  value       = google_pubsub_subscription.ingest_trigger_sub.id
  description = "The ID of the Pub/Sub pull subscription."
}
