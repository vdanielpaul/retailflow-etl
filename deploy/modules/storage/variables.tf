# Input variables for the GCS Storage module
# Defines configuration parameters for application and state buckets.

variable "project_id" {
  type        = string
  nullable    = false
  description = "The target Google Cloud Platform (GCP) Project ID."
}

variable "region" {
  type        = string
  nullable    = false
  description = "The primary region where GCS buckets will be created."
}

variable "environment" {
  type        = string
  nullable    = false
  description = "The target deployment environment (dev, staging, or prod)."

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment must be one of: dev, staging, prod."
  }
}

variable "force_destroy" {
  type        = bool
  default     = true
  nullable    = false
  description = "Allows Terraform to delete GCS buckets containing objects. Highly recommended to set to false for production environments."
}

variable "owner" {
  type        = string
  default     = "data-platform-team"
  nullable    = false
  description = "The engineering team or department owner responsible for managing these resources."
}

variable "data_classification" {
  type        = string
  default     = "confidential"
  nullable    = false
  description = "The security classification of data stored in the GCS buckets (e.g. public, internal, confidential)."
}

variable "common_labels" {
  type        = map(string)
  default     = {}
  nullable    = false
  description = "Common metadata labels to apply to all provisioned storage buckets."
}
