# RetailFlow ETL v2.0 — Milestone 1 Retrospective & Architecture Review

This document summarizes the architectural outcomes, engineering accomplishments, and lessons learned during the implementation of Milestone 1 (Foundation Infrastructure & Storage Setup).

---

## 1. What Was Built
We successfully bootstrapped the Terraform workspace and defined the foundation storage and database layers on Google Cloud Platform:
- **Terraform Directory Layout**: Implemented an enterprise-grade split configuration workspace structure (environments, modules, automation scripts).
- **GCS Storage Module**: Created the raw, archive, and quarantine application buckets, alongside a dedicated, isolated `tfstate` state bootstrap bucket.
- **BigQuery Datasets Module**: Created the `bronze`, `silver`, `gold`, and `metadata` database containers to map the target Medallion architecture.

---

## 2. Key Architectural Decisions Made
- **Prefix Naming Strategy**: Set up `${var.project_id}-retailflow-${var.environment}-${var.bucket_purpose}` naming for GCS buckets to guarantee global uniqueness.
- **Co-Location Constraint**: Enforced that all datasets and storage buckets reside in the same GCP region (e.g. `us-central1`) to prevent inter-region data transfer latency and cross-region egress charges.
- **Archive Nearline Tier**: Transitioned the Archive bucket to the `NEARLINE` storage class. Archives are write-heavy, read-light operational recovery logs, making Nearline the optimal choice to reduce storage costs by over 50%.
- **Medallion Schema Separation**: Separated Bronze staging from Silver clean canonical tables and Gold reporting facts/dimensions to enable full data replay and auditability directly via SQL.

---

## 3. Architecture Decision Records (ADRs) Added
Five ADRs have been written under `docs/adr/` following the standard template:
- **`ADR-008`**: Storage Naming Strategy.
- **`ADR-009`**: GCS Storage Design.
- **`ADR-010`**: Terraform Bootstrap Strategy.
- **`ADR-011`**: BigQuery Adoption (Postgres to BigQuery Migration).
- **`ADR-014`**: Medallion Dataset Architecture.

---

## 4. Technical Debt Introduced
- **Local State Backend**: Currently, state files are local. This is a deliberate Phase 1 bootstrap decision. Once these resources are applied in a live environment, the `tfstate` bucket will be available, enabling backend migration.
- **Default Permissions**: GCS buckets and BigQuery datasets use default IAM roles. Service account roles are deferred to Task 1.4 (IAM Setup).

---

## 5. Lessons Learned
- **BigQuery Expirations**: Setting partition/table expirations at the dataset level can cause problems. It is much safer to define expirations on individual staging tables during creation to protect reporting tables.
- **GCS Name Conflicts**: Prefixing names with project IDs guarantees global uniqueness in shared environments.

---

## 6. Readiness for Task 1.4
Milestone 1 Task 1.3 is complete and ready. All code has been merged into `develop` and tagged as `v2.0.0-m1.3`. The project is fully ready to transition to **Task 1.4 (Google Cloud IAM Service Accounts Setup)**.
