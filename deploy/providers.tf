# Google Cloud Platform Provider configuration
# Connects Terraform workspace to the target GCP project and region.

provider "google" {
  project = var.project_id
  region  = var.region
}
