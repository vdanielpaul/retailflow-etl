# Parameterized BigQuery SQL query constants for the Metadata Repository

# Query to check if a specific file hash has already been processed in the watermarks table
CHECK_DUPLICATE_HASH = """
SELECT 1 
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

# Query to insert/log an ETL pipeline run execution audit record
INSERT_AUDIT_LOG = """
INSERT INTO `{project_id}.{dataset_id}.etl_audit_log` (
    run_id, 
    status, 
    rows_read, 
    rows_loaded, 
    rows_rejected, 
    duration_ms, 
    error_message, 
    updated_at
)
VALUES (
    @run_id, 
    @status, 
    @rows_read, 
    @rows_loaded, 
    @rows_rejected, 
    @duration_ms, 
    @error_message, 
    @updated_at
)
"""
