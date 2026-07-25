# Input variable definitions with strict validation and descriptions.

variable "project_id" {
  type        = string
  nullable    = false
  description = "The target Google Cloud Platform (GCP) Project ID."

  validation {
    condition     = length(var.project_id) > 4
    error_message = "The project_id must be a valid GCP project identifier longer than 4 characters."
  }
}

variable "region" {
  type        = string
  nullable    = false
  default     = "us-central1"
  description = "The primary GCP region where serverless compute and storage resources will be deployed."

  validation {
    condition     = can(regex("^[a-z]+-[a-z]+[0-9]$", var.region))
    error_message = "The region variable must be a valid GCP region string format (e.g. us-central1)."
  }
}

variable "environment" {
  type        = string
  nullable    = false
  description = "Target deployment environment profile (dev, staging, or prod)."

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment variable must be one of: dev, staging, prod."
  }
}
