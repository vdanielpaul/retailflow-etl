"""Pipeline execution state manager saving checkpoints for partial failure recovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StateManager:
    """Manages step checkpoints for restarting interrupted pipeline runs."""

    def __init__(self, processed_dir: Path | str = Path("data/processed")) -> None:
        self.processed_dir = Path(processed_dir)

    def save_checkpoint(self, run_id: str, stage_name: str, state_data: dict[str, Any]) -> Path:
        """Save stage checkpoint to data/processed/<run_id>/checkpoint.json.

        Args:
            run_id: Pipeline run identifier.
            stage_name: Name of completed execution stage.
            state_data: Step state metadata.

        Returns:
            Path to saved checkpoint JSON file.
        """
        run_dir = self.processed_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_path = run_dir / "checkpoint.json"
        payload = {
            "run_id": run_id,
            "last_successful_stage": stage_name,
            "state": state_data,
        }
        checkpoint_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return checkpoint_path

    def load_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        """Load saved checkpoint JSON file if present."""
        checkpoint_path = self.processed_dir / run_id / "checkpoint.json"
        if not checkpoint_path.exists():
            return None
        try:
            return json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception:
            return None
