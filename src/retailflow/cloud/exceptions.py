# Domain-specific exceptions for the Ingestion Subsystem

class IngestionError(Exception):
    """Base exception for all ingestion-related processing errors."""
    pass

class InvalidEventError(IngestionError):
    """Raised when an incoming Pub/Sub envelope or GCS metadata schema is invalid."""
    pass

class DuplicateFileError(IngestionError):
    """Raised when a file upload is detected as a duplicate and processing must stop."""
    pass

class WatermarkLookupError(IngestionError):
    """Raised when querying the metadata store for watermarks fails."""
    pass

class MetadataPersistenceError(IngestionError):
    """Raised when writing the run metadata or audit log to the database fails."""
    pass

class PublishEventError(IngestionError):
    """Raised when publishing the downstream processing event fails."""
    pass
