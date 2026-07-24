-- ============================================================================
-- RetailFlow Data Warehouse - Schema Initialization
-- Script: 01_create_schema.sql
-- Description: Creates isolated warehouse and metadata schemas
-- ============================================================================

-- Analytical Data Warehouse Schema (Dimensions & Facts)
CREATE SCHEMA IF NOT EXISTS warehouse;

-- Operational & Lineage Metadata Schema (Audit Logs, Watermarks)
CREATE SCHEMA IF NOT EXISTS metadata;

-- Enable UUID extension for run identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set default search path
SET search_path TO warehouse, metadata, public;
