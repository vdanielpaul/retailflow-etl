# Pub/Sub Module

This Terraform module provisions the Google Cloud Pub/Sub topic and subscription resources required by the event-driven ingestion flow.

---

## Purpose
The module creates:
1. **Ingest Trigger Topic**: Publishes file metadata payloads when objects land in GCS.
2. **Ingest Trigger Subscription (Pull)**: Exposes a pull delivery queue for operational testing and buffer controls.

---

## Design Decisions
- **Naming Conventions**: Resources are named using `retailflow-${var.environment}-${resource_type}` (e.g. `retailflow-dev-ingest-trigger-topic`).
- **Retention Strategy**: Unacknowledged messages are retained for 7 days (`604800s`), preventing data loss during downstream pipeline downtime.
- **Processing Time Window**: Set the acknowledgment deadline (`ack_deadline_seconds`) to 60 seconds to allow downstream Cloud Functions or workers sufficient time to process records before redelivery occurs.

---

## Inputs

| Name | Type | Default | Description |
|---|---|---|---|
| `project_id` | `string` | Required | Target GCP Project ID. |
| `environment` | `string` | Required | Environment label (`dev`, `staging`, `prod`). |
| `owner` | `string` | `"unknown"` | Responsible engineering team or cost owner. |
| `common_labels` | `map(string)` | `{}` | Key-value pairs for metadata labeling. |

---

## Outputs

| Name | Type | Description |
|---|---|---|
| `topic_name` | `string` | Name of the trigger topic. |
| `topic_id` | `string` | Full GCP ID of the topic. |
| `subscription_name` | `string` | Name of the pull subscription. |
| `subscription_id` | `string` | Full GCP ID of the subscription. |

---

## Example Usage

```hcl
module "pubsub" {
  source = "./modules/pubsub"

  project_id  = "my-gcp-project"
  environment = "dev"
  owner       = "data-ops-team"

  common_labels = {
    project = "retailflow-etl"
  }
}
```

---

## Limitations
- **Pull Subscription Delivery**: The default subscription uses Pull delivery. Push configuration or subscription filters require custom configuration additions.
