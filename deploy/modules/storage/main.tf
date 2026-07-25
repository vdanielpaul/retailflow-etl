# Google Cloud Storage (GCS) resources configuration
# Defines the application buckets (raw, archive, quarantine) and the dedicated Terraform state bucket.

#-------------------------------------------------------------------------------
# 1. Raw Ingestion Bucket
# Holds daily raw POS CSV uploads before processing.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "raw" {
  name          = "retailflow-${var.environment}-raw"
  location      = var.region
  force_destroy = var.force_destroy

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"

  versioning {
    enabled = false # No versioning required for raw ingest files (reduces cost overhead)
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30 # Retain raw CSV files for 30 days before automatic deletion
    }
  }

  labels = var.common_labels
}

#-------------------------------------------------------------------------------
# 2. Archive Ingestion Bucket
# Holds copies of successfully processed POS CSV logs.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "archive" {
  name          = "retailflow-${var.environment}-archive"
  location      = var.region
  force_destroy = var.force_destroy

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"

  versioning {
    enabled = false
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90 # Retain historical archives for 90 days before automatic deletion
    }
  }

  labels = var.common_labels
}

#-------------------------------------------------------------------------------
# 3. Quarantine (Bad Records) Bucket
# Holds quarantined invalid records and failure reports.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "quarantine" {
  name          = "retailflow-${var.environment}-quarantine"
  location      = var.region
  force_destroy = var.force_destroy

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"

  versioning {
    enabled = false
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90 # Retain bad records for 90 days for investigation
    }
  }

  labels = var.common_labels
}

#-------------------------------------------------------------------------------
# 4. Dedicated Terraform State Bucket
# --- BOOTSTRAP INFRASTRUCTURE ONLY ---
# This bucket is strictly used to store Terraform backend state files.
# It is NOT part of the RetailFlow application ingestion data flow.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "tfstate" {
  name          = "retailflow-${var.environment}-tfstate"
  location      = var.region
  force_destroy = var.force_destroy

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"

  versioning {
    enabled = true # Versioning enabled to protect against accidental state deletion or corruption
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 10 # Retain only the 10 most recent versions of state files
    }
  }

  labels = merge(var.common_labels, {
    purpose = "terraform-state"
  })
}
