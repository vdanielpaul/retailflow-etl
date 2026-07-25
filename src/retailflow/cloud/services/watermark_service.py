# Watermark database service abstractions

from abc import ABC, abstractmethod

class BaseWatermarkService(ABC):
    """Abstract interface defining database watermark status queries."""
    
    @abstractmethod
    def is_duplicate_hash(self, file_hash: str) -> bool:
        """Query if the file hash has already been processed.

        Args:
            file_hash: Calculated SHA-256 hash of GCS object.

        Returns:
            True if hash already exists in metadata logs, False otherwise.
        """
        pass

    @abstractmethod
    def register_ingestion(self, file_hash: str, filename: str, run_id: str) -> None:
        """Register the file ingestion details into the watermark database.

        Args:
            file_hash: Calculated SHA-256 hash of GCS object.
            filename: GCS object name path.
            run_id: Unique execution tracking identifier.
        """
        pass

class BigQueryWatermarkService(BaseWatermarkService):
    """Production implementation of WatermarkService interacting with BigQuery metadata logs."""
    
    def __init__(self, project_id: str, dataset_id: str) -> None:
        self.project_id = project_id
        self.dataset_id = dataset_id

    def is_duplicate_hash(self, file_hash: str) -> bool:
        # To be implemented in Task 2.3
        raise NotImplementedError("BigQuery duplicate hash lookup not implemented yet.")

    def register_ingestion(self, file_hash: str, filename: str, run_id: str) -> None:
        # To be implemented in Task 2.3
        raise NotImplementedError("BigQuery watermark persistence not implemented yet.")
