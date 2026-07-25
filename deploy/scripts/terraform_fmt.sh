#!/bin/bash
# Shell script running terraform format verification.
# Exits with non-zero status if files are not properly formatted.

set -e
cd "$(dirname "$0")/.."

echo "Running terraform format check..."
terraform fmt -check -recursive
echo "Terraform formatting checks passed!"
