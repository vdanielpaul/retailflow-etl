#!/bin/bash
# Shell script running terraform plans against targeted environment profiles.
# Usage: ./scripts/terraform_plan.sh <env>
# Example: ./scripts/terraform_plan.sh dev

set -e
ENV=$1

if [ -z "$ENV" ]; then
  echo "Error: Missing environment argument. Usage: ./terraform_plan.sh [dev|staging|prod]"
  exit 1
fi

cd "$(dirname "$0")/.."

if [ ! -f "environments/${ENV}.tfvars" ]; then
  echo "Error: Environment file environments/${ENV}.tfvars not found!"
  exit 1
fi

echo "Running terraform plan for environment: ${ENV}..."
terraform plan -var-file="environments/${ENV}.tfvars"
