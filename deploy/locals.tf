# Local values managing naming conventions and common metadata tags.
# Follows the standard convention: retailflow-{environment}-{resource_name}

locals {
  name_prefix = "retailflow-${var.environment}"

  common_labels = {
    project     = "retailflow-etl"
    environment = var.environment
    managed_by  = "terraform"
    version     = "2.0.0"
  }
}
