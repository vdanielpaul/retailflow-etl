# Google Cloud Storage (GCS) resources configuration
# Defines the application buckets (raw, archive, quarantine) and the dedicated Terraform state bucket.
# Naming convention: ${var.project_id}-retailflow-${var.environment}-${purpose} to ensure global uniqueness.

#-------------------------------------------------------------------------------
# 1. Raw Ingestion Bucket
# Holds daily raw POS CSV uploads before processing.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-retailflow-${var.environment}-raw"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })

  versioning {
    enabled = false # No versioning to save space on single-write POS logs
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30 # Retain raw CSV uploads for 30 days before cleanup
    }
  }
}

#-------------------------------------------------------------------------------
# 2. Archive Ingestion Bucket
# Holds processed raw feeds for historical comparison and replay scenarios.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "archive" {
  name                        = "${var.project_id}-retailflow-${var.environment}-archive"
  location                    = var.region
  storage_class               = "NEARLINE" # Low-cost class for backups written once and rarely read
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })

  versioning {
    enabled = false
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 180 # Retain backups for 180 days (6 months operational window)
    }
  }
}

#-------------------------------------------------------------------------------
# 3. Quarantine (Bad Records) Bucket
# Holds quarantined invalid feeds and diagnostic validation reports.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "quarantine" {
  name                        = "${var.project_id}-retailflow-${var.environment}-quarantine"
  location                    = var.region
  storage_class               = "STANDARD" # Hot access for troubleshooting and debugging
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })

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
}

#-------------------------------------------------------------------------------
# 4. Dedicated Terraform State Bucket
# --- BOOTSTRAP INFRASTRUCTURE ONLY ---
# This bucket is strictly used to store Terraform backend state files.
# It is NOT part of the RetailFlow application ingestion data flow.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "tfstate" {
  name                        = "${var.project_id}-retailflow-${var.environment}-tfstate"
  location                    = var.region
  storage_class               = "STANDARD" # Hot access for state tracking
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = "confidential" # Sensitive Terraform configurations metadata
    purpose             = "terraform-state"
  })

  versioning {
    enabled = true # Versioning enabled to protect state files from accidental deletion
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 10 # Retain only the 10 most recent versions of state files
    }
  }
}
