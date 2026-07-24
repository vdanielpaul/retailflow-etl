-- ============================================================================
-- RetailFlow Data Warehouse - Operational & Audit Control Tables (metadata Schema)
-- Script: 04_create_audit_tables.sql
-- Description: DDL for metadata.etl_audit_log and metadata.etl_watermark
-- ============================================================================

SET search_path TO metadata, public;

-- ----------------------------------------------------------------------------
-- 1. etl_audit_log (Pipeline Execution Audit & Metric Tracking)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.etl_audit_log (
    run_id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pipeline_run_id     UUID         NOT NULL,
    batch_id            VARCHAR(100) NOT NULL,
    source_filename     VARCHAR(255) NOT NULL,
    source_file_hash    VARCHAR(64)  NOT NULL,
    execution_stage     VARCHAR(50)  NOT NULL,
    records_read        BIGINT       NOT NULL DEFAULT 0,
    records_valid       BIGINT       NOT NULL DEFAULT 0,
    records_rejected    BIGINT       NOT NULL DEFAULT 0,
    records_loaded      BIGINT       NOT NULL DEFAULT 0,
    execution_status    VARCHAR(20)  NOT NULL CHECK (execution_status IN ('RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL_SUCCESS')),
    started_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at        TIMESTAMP,
    duration_ms         BIGINT,
    executed_by         VARCHAR(100) NOT NULL DEFAULT CURRENT_USER,
    application_version VARCHAR(20)  NOT NULL,
    error_summary       TEXT
);

-- ----------------------------------------------------------------------------
-- 2. etl_watermark (Incremental Ingestion State Tracker)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metadata.etl_watermark (
    watermark_id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entity_name              VARCHAR(100) NOT NULL,
    store_id                 VARCHAR(20)  NOT NULL,
    source_file              VARCHAR(255) NOT NULL,
    file_hash                VARCHAR(64)  NOT NULL,
    last_processed_timestamp TIMESTAMP    NOT NULL,
    processing_status        VARCHAR(20)  NOT NULL CHECK (processing_status IN ('SUCCESS', 'FAILED')),
    pipeline_version         VARCHAR(20)  NOT NULL,
    processed_at             TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_audit_run_id        BIGINT       REFERENCES metadata.etl_audit_log(run_id),
    CONSTRAINT uq_watermark_entity_store UNIQUE (entity_name, store_id)
);
