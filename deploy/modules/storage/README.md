# GCS Storage Module

This Terraform module provisions the Google Cloud Storage (GCS) buckets required for the RetailFlow data platform.

---

## Purpose
The module encapsulates the creation of:
1. **Raw Ingest Bucket**: Staging landing zone for raw POS CSV uploads.
2. **Archive Bucket**: Persistent cold backup storage for processed feeds.
3. **Quarantine Bucket**: Storage directory for validation failure feeds and scorecards.
4. **Terraform State Bucket**: Dedicated, infrastructure-only bucket used for remote state backend storage.

---

## Design Decisions

- **Naming Convention**: Buckets are named using the structure `${var.project_id}-retailflow-${var.environment}-${var.bucket_purpose}` to ensure global naming uniqueness in the GCS namespace.
- **Storage Class Optimization**: The Archive bucket uses `NEARLINE` storage to reduce costs (archives are written daily but rarely read). Raw and Quarantine buckets use `STANDARD` for frequent hot data access.
- **Security Posture**: Enforces `uniform_bucket_level_access = true` and `public_access_prevention = "enforced"` across all buckets.
- **Versioning**: Enabled on the `tfstate` bucket to safeguard state metadata files from accidental loss. Disabled on data buckets to minimize duplicate storage overhead.

---

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_id` | `string` | Required | Target GCP Project ID. |
| `region` | `string` | Required | Target GCP region for GCS bucket storage. |
| `environment` | `string` | Required | Environment label (`dev`, `staging`, `prod`). |
| `force_destroy` | `bool` | `true` | Allows deleting GCS buckets containing data objects. |
| `owner` | `string` | `"unknown"` | Responsible engineering team or cost owner. |
| `data_classification` | `string` | `"internal"` | Security classification label for bucket data. |
| `common_labels` | `map(string)` | `{}` | Key-value pairs for metadata labeling. |

---

## Outputs

| Name | Type | Description |
|---|---|---|
| `raw_bucket_name` | `string` | Name of the raw ingestion bucket. |
| `archive_bucket_name` | `string` | Name of the processed archive bucket. |
| `quarantine_bucket_name` | `string` | Name of the quarantine bucket. |
| `tfstate_bucket_name` | `string` | Name of the dedicated Terraform state bucket. |

---

## Example Usage

```hcl
module "storage" {
  source = "./modules/storage"

  project_id          = "my-gcp-project"
  region              = "us-central1"
  environment         = "dev"
  force_destroy       = true
  owner               = "data-ops-team"
  data_classification = "internal"

  common_labels = {
    project = "retailflow-etl"
  }
}
```

---

## Limitations
- **Globally Unique Naming**: If `project_id` or `environment` parameters contain characters not supported by GCS naming rules, bucket creation will fail.
- **Location Constraints**: Regional buckets are not replicated across geographical zones outside their designated region, meaning disaster recovery depends on local regional zone durability.
