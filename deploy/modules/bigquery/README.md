# BigQuery Module

This Terraform module provisions the Google BigQuery datasets required for the RetailFlow ETL platform.

---

## Purpose
The module encapsulates the creation of the Medallion architecture datasets:
1. **Bronze Layer Dataset**: Holds raw, append-only staging data.
2. **Silver Layer Dataset**: Holds validated and cleaned canonical records.
3. **Gold Layer Dataset**: Holds final analytical Star Schema facts and dimensions.
4. **Metadata Dataset**: Holds watermarks and audit pipeline logs.

---

## Design Decisions
- **Dataset Naming**: Uses `retailflow_${var.environment}_${var.layer}` naming structure to ensure compliance with BigQuery ID constraints (only alphanumeric characters and underscores are allowed).
- **Deletion Protection**: Exposes `delete_contents_on_destroy` so that datasets can be cleanly torn down in dev/staging environments, while protecting production tables from accidental drop commands.
- **Expiration Policies**: Enforces a default 30-day table/partition expiration policy on the **Bronze** dataset to clean up raw staging files automatically and limit storage costs. Silver, Gold, and Metadata tables are retained indefinitely.
- **Location Alignment**: Datasets are co-located in the primary region alongside storage and compute to eliminate inter-region network charges and latency.

---

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_id` | `string` | Required | Target GCP Project ID. |
| `region` | `string` | Required | Target GCP region for BigQuery dataset storage. |
| `environment` | `string` | Required | Environment label (`dev`, `staging`, `prod`). |
| `delete_contents_on_destroy` | `bool` | `true` | If true, delete tables when destroying dataset resource. |
| `owner` | `string` | `"unknown"` | Responsible engineering team or cost owner. |
| `data_classification` | `string` | `"internal"` | Security classification label for dataset data. |
| `common_labels` | `map(string)` | `{}` | Key-value pairs for metadata labeling. |

---

## Outputs

| Name | Type | Description |
|---|---|---|
| `bronze_dataset_id` | `string` | The ID of the Bronze dataset. |
| `silver_dataset_id` | `string` | The ID of the Silver dataset. |
| `gold_dataset_id` | `string` | The ID of the Gold dataset. |
| `metadata_dataset_id` | `string` | The ID of the Metadata dataset. |

---

## Example Usage

```hcl
module "bigquery" {
  source = "./modules/bigquery"

  project_id                 = "my-gcp-project"
  region                     = "us-central1"
  environment                = "dev"
  delete_contents_on_destroy = true
  owner                      = "data-platform-team"
  data_classification        = "internal"

  common_labels = {
    project = "retailflow-etl"
  }
}
```

---

## Limitations
- **ID Restrictions**: BigQuery dataset IDs cannot contain dashes (`-`). Ensure that `environment` variables do not contain characters other than alphanumeric and underscores.
- **Location Modifications**: Location region parameters cannot be changed after dataset creation. Changing region variables triggers a destructive resource recreation.
