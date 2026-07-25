# Input variables for the Pub/Sub module
# Defines configuration parameters for trigger topics and subscriptions.

variable "project_id" {
  type        = string
  nullable    = false
  description = "The target Google Cloud Platform (GCP) Project ID."
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

variable "owner" {
  type        = string
  default     = "unknown"
  nullable    = false
  description = "The engineering team or department owner responsible for this topic."
}

variable "common_labels" {
  type        = map(string)
  default     = {}
  nullable    = false
  description = "Common metadata labels to apply to Pub/Sub resources."
}
