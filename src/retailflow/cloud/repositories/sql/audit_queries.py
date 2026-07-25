# BigQuery SQL query constants for ETL auditing

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
