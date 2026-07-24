"""Shared Pipeline Context object holding run state and dependency instances."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from retailflow.config.settings import Settings
from retailflow.constants.constants import ExecutionStage
from retailflow.database.connection import DatabaseManager
from retailflow.metrics.collector import MetricsCollector


@dataclass
class PipelineContext:
    """Shared execution context passed across all pipeline stages."""

    configuration: Settings
    database: DatabaseManager
    logger: logging.Logger
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    batch_id: str = field(default_factory=lambda: f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    pipeline_name: str = "retailflow-sales-pipeline"
    environment: str = "development"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_file: Path | None = None
    metrics: MetricsCollector = field(default_factory=MetricsCollector)
    execution_state: str = ExecutionStage.INITIALIZATION.value
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_stage(self, stage: ExecutionStage | str) -> None:
        """Update current pipeline execution stage state."""
        self.execution_state = str(stage)
        self.logger.debug(f"Pipeline context updated to stage: {self.execution_state}")
