# Terraform State Backend Configuration
# Currently configured for local development state tracking.
# Refer to deploy/README.md for instructions on migrating to a secure GCS remote backend.

terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}

# --- Migration to Remote GCS Backend Template ---
# Once the raw or dedicated terraform state GCS bucket is created,
# uncomment the block below and remove the "local" backend configuration above.
# Run `terraform init -migrate-state` to migrate local state.
#
# terraform {
#   backend "gcs" {
#     bucket = "retailflow-dev-tfstate"
#     prefix = "terraform/state"
#   }
# }
