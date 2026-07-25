# Input variables for the BigQuery module
# Defines configuration parameters for datasets.

variable "project_id" {
  type        = string
  nullable    = false
  description = "The target Google Cloud Platform (GCP) Project ID."
}

variable "region" {
  type        = string
  nullable    = false
  description = "The location region where BigQuery datasets will be created (e.g. us-central1)."
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

variable "delete_contents_on_destroy" {
  type        = bool
  default     = true
  nullable    = false
  description = "If true, delete all tables in the dataset when destroying the dataset resource via Terraform. Set to false for production."
}

variable "owner" {
  type        = string
  default     = "unknown"
  nullable    = false
  description = "The engineering team or department owner responsible for these datasets."
}

variable "data_classification" {
  type        = string
  default     = "internal"
  nullable    = false
  description = "The security classification of data stored in these datasets."
}

variable "common_labels" {
  type        = map(string)
  default     = {}
  nullable    = false
  description = "Common metadata labels to apply to all provisioned BigQuery datasets."
}
