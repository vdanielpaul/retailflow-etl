"""Change classification engine evaluating incoming feed files against historical watermarks."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from retailflow.incremental.watermark import WatermarkManager
from retailflow.models.incremental import FileClassification

logger = logging.getLogger(__name__)


class ChangeDetector:
    """Classifies incoming feed files into change categories."""

    def __init__(self, watermark_manager: WatermarkManager) -> None:
        self.watermark_manager = watermark_manager

    def classify_file(
        self, file_path: Path, is_manual_replay: bool = False
    ) -> tuple[FileClassification, str]:
        """Evaluate file against historical watermarks and return classification.

        Args:
            file_path: Path to target feed file.
            is_manual_replay: Flag indicating operator requested manual replay.

        Returns:
            Tuple of (FileClassification, SHA-256 file hash).
        """
        if not file_path.exists():
            return FileClassification.STALE, ""

        file_bytes = file_path.read_bytes()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        if is_manual_replay:
            logger.info(f"File {file_path.name} marked for REPROCESS via manual replay flag.")
            return FileClassification.REPROCESS, file_hash

        if self.watermark_manager.is_file_processed(file_hash):
            logger.info(f"File {file_path.name} (hash={file_hash[:8]}) is DUPLICATE. Skipping processing.")
            return FileClassification.DUPLICATE, file_hash

        return FileClassification.NEW, file_hash
