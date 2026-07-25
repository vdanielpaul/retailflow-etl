# Output variable definitions exposing resource identifiers.
# These will be populated in subsequent milestones as physical GCS and BQ resources are added.

output "project_id" {
  value       = var.project_id
  description = "The target GCP Project ID."
}

output "region" {
  value       = var.region
  description = "The primary GCP deployment region."
}

output "environment" {
  value       = var.environment
  description = "The deployment environment profile (dev, staging, or prod)."
}

output "name_prefix" {
  value       = local.name_prefix
  description = "The prefix string format used for resource naming: retailflow-{environment}."
}

output "raw_bucket_name" {
  value       = module.storage.raw_bucket_name
  description = "The name of the GCS raw ingestion bucket."
}

output "archive_bucket_name" {
  value       = module.storage.archive_bucket_name
  description = "The name of the GCS processed archive bucket."
}

output "quarantine_bucket_name" {
  value       = module.storage.quarantine_bucket_name
  description = "The name of the GCS quarantine bucket."
}

output "tfstate_bucket_name" {
  value       = module.storage.tfstate_bucket_name
  description = "The name of the GCS dedicated Terraform state bucket."
}

output "bronze_dataset_id" {
  value       = module.bigquery.bronze_dataset_id
  description = "The ID of the Bronze raw ingestion dataset."
}

output "silver_dataset_id" {
  value       = module.bigquery.silver_dataset_id
  description = "The ID of the Silver canonical dataset."
}

output "gold_dataset_id" {
  value       = module.bigquery.gold_dataset_id
  description = "The ID of the Gold warehouse dataset."
}

output "metadata_dataset_id" {
  value       = module.bigquery.metadata_dataset_id
  description = "The ID of the Metadata audit dataset."
}

output "ingestion_events_topic_name" {
  value       = module.pubsub.ingestion_events_topic_name
  description = "The name of the GCS raw ingestion events topic."
}

output "ingestion_events_topic_id" {
  value       = module.pubsub.ingestion_events_topic_id
  description = "The ID of the GCS raw ingestion events topic."
}

output "processing_events_topic_name" {
  value       = module.pubsub.processing_events_topic_name
  description = "The name of the validated processing events topic."
}

output "processing_events_topic_id" {
  value       = module.pubsub.processing_events_topic_id
  description = "The ID of the validated processing events topic."
}

output "processing_events_subscription_name" {
  value       = module.pubsub.processing_events_subscription_name
  description = "The name of the processing events pull subscription."
}

output "processing_events_subscription_id" {
  value       = module.pubsub.processing_events_subscription_id
  description = "The ID of the processing events pull subscription."
}
