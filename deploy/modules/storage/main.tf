# Google Cloud Storage (GCS) resources configuration
# Defines the application buckets (raw, archive, quarantine) and the dedicated Terraform state bucket.
# Naming convention: ${var.project_id}-retailflow-${var.environment}-${purpose} to ensure global uniqueness.

#-------------------------------------------------------------------------------
# 1. Raw Ingestion Bucket
# Holds daily raw POS CSV uploads before processing.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "raw" {
  name          = "${var.project_id}-retailflow-${var.environment}-raw"
  location      = var.region
  force_destroy = var.force_destroy

  storage_class               = "STANDARD" # Hot storage for nightly execution reads
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"

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

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })
}

#-------------------------------------------------------------------------------
# 2. Archive Ingestion Bucket
# Holds processed raw feeds for historical audit and replay scenarios.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "archive" {
  name          = "${var.project_id}-retailflow-${var.environment}-archive"
  location      = var.region
  force_destroy = var.force_destroy

  # NEARLINE storage class selected. Archives are written once daily but rarely read
  # except in emergency recovery or verification re-run scenarios.
  storage_class               = "NEARLINE" 
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
      age = 180 # Retain backups for 180 days (6 months operational window)
    }
  }

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })
}

#-------------------------------------------------------------------------------
# 3. Quarantine (Bad Records) Bucket
# Holds quarantined invalid feeds and diagnostic validation scorecards.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "quarantine" {
  name          = "${var.project_id}-retailflow-${var.environment}-quarantine"
  location      = var.region
  force_destroy = var.force_destroy

  storage_class               = "STANDARD" # Hot access for active developer debugging
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

  labels = merge(var.common_labels, {
    owner               = var.owner
    data_classification = var.data_classification
  })
}

#-------------------------------------------------------------------------------
# 4. Dedicated Terraform State Bucket
# --- BOOTSTRAP INFRASTRUCTURE ONLY ---
# This bucket is strictly used to store Terraform backend state files.
# It is NOT part of the RetailFlow application ingestion data flow.
#-------------------------------------------------------------------------------
resource "google_storage_bucket" "tfstate" {
  name          = "${var.project_id}-retailflow-${var.environment}-tfstate"
  location      = var.region
  force_destroy = var.force_destroy

  storage_class               = "STANDARD" # Accessed frequently on plan/apply runs
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"

  versioning {
    enabled = true # Versioning enabled to protect backend state files from corruption
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
    owner               = var.owner
    data_classification = "confidential"
    purpose             = "terraform-state"
  })
}
