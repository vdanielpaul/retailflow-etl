# RetailFlow ETL v2.0 — Infrastructure Deployment Guide

This directory contains the Terraform configuration files for provisioning and managing the Google Cloud Platform (GCP) resources required by the modernized Cloud-Native data platform.

---

## 📁 Directory Structure
```text
deploy/
├── README.md                 # This deployment guide
├── versions.tf               # Terraform and GCP provider versions constraints
├── providers.tf              # GCP Provider parameters configuration
├── backend.tf                # Local/Remote state tracking configuration
├── variables.tf              # Typed input variable definitions
├── locals.tf                 # Naming prefixes and common labels
├── outputs.tf                # Exposed resource identifier exports
├── terraform.tfvars.example  # Local setup template config
├── environments/             # Environment override files
│   ├── dev.tfvars            # Development overrides
│   ├── staging.tfvars        # Staging overrides
│   └── prod.tfvars           # Production overrides
├── modules/                  # Resource module configurations
│   ├── storage/              # GCS buckets module configuration
│   │   ├── main.tf           # App & state bucket resources
│   │   ├── variables.tf      # Storage module inputs
│   │   └── outputs.tf        # Storage module outputs
│   ├── bigquery/
│   ├── pubsub/
│   ├── iam/
│   ├── monitoring/
│   └── cloud_functions/
└── scripts/                  # Automated verification shell scripts
    ├── terraform_fmt.sh      # Format compliance check script
    ├── terraform_validate.sh # Syntax validation verify script
    └── terraform_plan.sh     # Targeted execution planner script
```

---

## 🛠️ Prerequisites

1. **Terraform CLI**: Download and install Terraform `>= 1.5.0` from [terraform.io](https://www.terraform.io/downloads).
2. **Google Cloud SDK (gcloud)**: Download and install the gcloud SDK from [cloud.google.com/sdk](https://cloud.google.com/sdk).

---

## 🔑 Google Cloud Authentication

Authenticate the `gcloud` CLI and set up Application Default Credentials (ADC) so that Terraform can access your GCP project:

```bash
# Log in to your Google Account
gcloud auth login

# Set the active project context
gcloud config set project your-project-id

# Set up local application default credentials
gcloud auth application-default login
```

---

## 🚀 Execution Workflow

All commands must be executed from inside the `deploy/` directory:
```bash
cd deploy/
```

### 1. Initialization
Downloads provider plugins and initializes the state backend:
```bash
terraform init
```

### 2. Formatting & Standards
Ensure all files conform to canonical Terraform styles:
```bash
# Check format
terraform fmt -check -recursive

# Automatically fix format issues
terraform fmt -recursive
```

### 3. Syntax Validation
Verify that code is syntactically valid and internally consistent:
```bash
terraform validate
```

### 4. Planning (Targeted Environments)
Generate execution plans showing what resources will be created. Always specify the targeted environment file:
```bash
# Plan for Development
terraform plan -var-file="environments/dev.tfvars"

# Plan for Production
terraform plan -var-file="environments/prod.tfvars"
```

### 5. Applying (Targeted Environments)
Apply the plan to deploy resources to GCP:
```bash
terraform apply -var-file="environments/dev.tfvars"
```

### 6. Destroying (Targeted Environments)
Teardown all resources managed by the current workspace:
```bash
terraform destroy -var-file="environments/dev.tfvars"
```

---

## 🔒 Lock File Strategy (`.terraform.lock.hcl`)

In this project, we **commit the `.terraform.lock.hcl` lock file** to the Git repository.
- **Why?**: Committing the provider lock file is an enterprise best practice. It records the exact provider version and checksum hash used during initial development, guaranteeing that CI/CD runners and other developers install identical provider binaries and preventing unexpected schema drift.

---

## 🔄 Migrating to a GCS Remote Backend

For local development, states are stored locally in `deploy/terraform.tfstate`. To migrate to a secure, shared GCS backend:
1. Create a GCS bucket (e.g. `retailflow-dev-tfstate`) with Versioning enabled.
2. In `backend.tf`, uncomment the `backend "gcs"` block and populate the bucket name.
3. Remove or comment out the `backend "local"` block.
4. Run the migration command:
   ```bash
   terraform init -migrate-state
   ```

---

## 📡 Future Platform Compatibility

The storage configuration is designed to integrate seamlessly with downstream GCP serverless services:
- **Cloud Functions Triggers**: The raw bucket is prepared to emit object creation notification events that trigger Cloud Functions.
- **Eventarc**: Buckets support GCP Eventarc triggers (`google.cloud.storage.object.v1.finalized`) using standard storage configuration.
- **Dataflow (Apache Beam)**: Workers access raw and quarantine paths using regional service account credentials.
- **Pub/Sub Notifications**: GCS supports linking notification configurations (`google_storage_notification`) directly to buckets, triggering messages on object changes.
