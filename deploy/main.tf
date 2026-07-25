# Main infrastructure entry point for RetailFlow ETL v2.0
# Calls the environment modules to provision GCS storage resources.

module "storage" {
  source = "./modules/storage"

  project_id    = var.project_id
  region        = var.region
  environment   = var.environment
  force_destroy = var.environment == "prod" ? false : true
  common_labels = local.common_labels
}
