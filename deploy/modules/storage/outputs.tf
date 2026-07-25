# Outputs for the GCS Storage module
# Exposes bucket names to downstream configurations.

output "raw_bucket_name" {
  value       = google_storage_bucket.raw.name
  description = "The name of the GCS raw ingestion bucket."
}

output "archive_bucket_name" {
  value       = google_storage_bucket.archive.name
  description = "The name of the GCS processed archive bucket."
}

output "quarantine_bucket_name" {
  value       = google_storage_bucket.quarantine.name
  description = "The name of the GCS quarantine bucket."
}

output "tfstate_bucket_name" {
  value       = google_storage_bucket.tfstate.name
  description = "The name of the GCS dedicated Terraform state bucket."
}
