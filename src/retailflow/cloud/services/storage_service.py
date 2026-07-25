# Storage bucket operations and hash computation abstractions

import hashlib
from abc import ABC, abstractmethod
from google.cloud import storage
from google.api_core.exceptions import GoogleAPICallError
from retailflow.cloud.exceptions import IngestionError

class StorageService(ABC):
    """Abstract interface defining operations on Cloud Storage objects."""
    
    @abstractmethod
    def calculate_sha256(self, bucket_name: str, object_name: str) -> str:
        """Stream object content in chunks to calculate its SHA-256 checksum.

        Args:
            bucket_name: GCS bucket containing the target object.
            object_name: The file path name of the object.

        Returns:
            The calculated hexadecimal SHA-256 checksum string.
        """
        pass

class GcsStorageService(StorageService):
    """Production implementation of GCS object operations using google-cloud-storage."""
    
    def __init__(self, client: storage.Client) -> None:
        self.client = client

    def calculate_sha256(self, bucket_name: str, object_name: str) -> str:
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            
            # Use streaming chunk-based reads to avoid high memory overhead for large files
            sha256_hash = hashlib.sha256()
            
            # 256 KB chunks match Google Cloud Storage API default streaming sizes
            chunk_size = 256 * 1024
            
            with blob.open("rb") as f:
                while chunk := f.read(chunk_size):
                    sha256_hash.update(chunk)
                    
            return sha256_hash.hexdigest()
        except GoogleAPICallError as err:
            raise IngestionError(f"GCS API failure reading object gs://{bucket_name}/{object_name}: {str(err)}") from err
        except Exception as err:
            raise IngestionError(f"Unexpected error calculating file hash: {str(err)}") from err
