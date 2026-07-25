#!/bin/bash
# Shell script verifying terraform syntax validation.

set -e
cd "$(dirname "$0")/.."

echo "Initializing terraform validation workspace..."
terraform init -backend=false

echo "Validating terraform syntax configurations..."
terraform validate
echo "Terraform syntax validation checks passed!"
