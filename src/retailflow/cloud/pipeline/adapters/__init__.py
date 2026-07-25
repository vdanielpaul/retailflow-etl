"""Beam pipeline adapters package for RetailFlow ETL v2.0.

Adapters translate between Beam element representations and the v1.0 business
logic interfaces. They are framework-agnostic — no Beam, GCP, or cloud-specific
imports belong here. The same adapters can be used in local CLI execution,
integration tests, or future streaming pipelines.
"""

from retailflow.cloud.pipeline.adapters.business_rule_adapter import (
    BusinessRuleAdapter,
    ValidationCheckResult,
)
from retailflow.cloud.pipeline.adapters.transformation_adapter import (
    TransformationAdapter,
    TransformationResult,
)

__all__ = [
    "BusinessRuleAdapter",
    "ValidationCheckResult",
    "TransformationAdapter",
    "TransformationResult",
]
