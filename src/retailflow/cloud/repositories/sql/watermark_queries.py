# BigQuery SQL query constants for watermarks

# Query to check if a specific file hash has already been processed in the watermarks table
# Selects tracking metadata if matched
CHECK_DUPLICATE_HASH = """
SELECT 
    file_hash,
    filename,
    ingested_at,
    run_id
FROM `{project_id}.{dataset_id}.etl_watermark`
WHERE file_hash = @file_hash
LIMIT 1
"""

# Query to register a new file watermark execution row
INSERT_WATERMARK = """
INSERT INTO `{project_id}.{dataset_id}.etl_watermark` (
    file_hash, 
    filename, 
    ingested_at, 
    run_id
)
VALUES (
    @file_hash, 
    @filename, 
    @ingested_at, 
    @run_id
)
"""
