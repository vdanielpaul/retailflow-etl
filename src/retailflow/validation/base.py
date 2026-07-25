"""Abstract Base Validator interface for RetailFlow data quality engine.

Design note: context is Optional to allow validators to run outside the v1.0
PipelineContext (e.g., inside Beam adapters, unit tests, or future streaming
pipelines). Only FileValidator requires context; all business rule validators
operate on the DataFrame alone.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from retailflow.models.validation import ValidationResult
from retailflow.pipeline.context import PipelineContext


class BaseValidator(ABC):
    """Abstract Base Class for modular dataset and row-level validators."""

    @property
    @abstractmethod
    def validator_name(self) -> str:
        """Unique identifier name for the validator implementation."""
        pass

    @abstractmethod
    def validate(
        self,
        df: pd.DataFrame,
        context: Optional[PipelineContext] = None,
    ) -> ValidationResult:
        """Execute validation against Pandas DataFrame.

        Args:
            df: Target input DataFrame to evaluate.
            context: Optional shared pipeline execution context. Required only
                by validators that access filesystem or pipeline metadata
                (e.g., FileValidator). Business rule validators do not use it.

        Returns:
            ValidationResult object containing evaluation metrics.
        """
        pass
