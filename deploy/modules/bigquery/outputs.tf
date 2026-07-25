# Outputs for the BigQuery module
# Exposes dataset identifiers to downstream configurations.

output "bronze_dataset_id" {
  value       = google_bigquery_dataset.bronze.dataset_id
  description = "The ID of the Bronze raw ingestion dataset."
}

output "silver_dataset_id" {
  value       = google_bigquery_dataset.silver.dataset_id
  description = "The ID of the Silver canonical dataset."
}

output "gold_dataset_id" {
  value       = google_bigquery_dataset.gold.dataset_id
  description = "The ID of the Gold warehouse dataset."
}

output "metadata_dataset_id" {
  value       = google_bigquery_dataset.metadata.dataset_id
  description = "The ID of the Metadata audit dataset."
}
