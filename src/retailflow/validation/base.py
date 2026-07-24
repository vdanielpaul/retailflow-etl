"""Abstract Base Validator interface for RetailFlow data quality engine."""

from __future__ import annotations

from abc import ABC, abstractmethod

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
    def validate(self, df: pd.DataFrame, context: PipelineContext) -> ValidationResult:
        """Execute validation against Pandas DataFrame.

        Args:
            df: Target input DataFrame to evaluate.
            context: Shared pipeline execution context.

        Returns:
            ValidationResult object containing evaluation metrics.
        """
        pass
