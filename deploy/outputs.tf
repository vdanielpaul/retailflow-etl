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
