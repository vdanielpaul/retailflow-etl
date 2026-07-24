"""Processed file registry maintaining SHA-256 hashes and replay metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileRegistry:
    """Registry maintaining file processing history, SHA-256 content hashes, and execution manifests."""

    def __init__(self, processed_dir: Path | str = Path("data/processed")) -> None:
        self.processed_dir = Path(processed_dir)

    def write_manifest(self, run_id: str, manifest_data: dict[str, Any]) -> Path:
        """Write manifest.json artifact under data/processed/<run_id>/manifest.json.

        Args:
            run_id: Pipeline run identifier.
            manifest_data: Manifest dictionary.

        Returns:
            Path to written manifest file.
        """
        run_dir = self.processed_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = run_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        return manifest_path
