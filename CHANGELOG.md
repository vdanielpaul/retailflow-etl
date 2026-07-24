# Changelog

All notable changes to the RetailFlow ETL project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-24

### Added
- **Canonical Data Model (CDM)**: Pydantic models (`CanonicalCustomer`, `CanonicalProduct`, `CanonicalStore`, `CanonicalEmployee`, `CanonicalSale`).
- **Data Quality Scorecards**: 6-dimension data quality scorecards (0-100%) and quarantine folder writer.
- **Bulk Warehouse Loader**: High-performance streaming `COPY` and `execute_values` bulk loader achieving >25,000 rows/sec.
- **Incremental Engine**: High-watermark manager, SHA-256 file hash change detector, state checkpoint recovery (`checkpoint.json`), and processing manifest exporter (`manifest.json`).
- **Operational Audit & Observability**: Standardized `PipelineLifecycleEvent` tracking, search repository API, sensitive data log redactor, and production CLI runner (`retailflow.cli`).
- **Testing & Benchmarks**: 45 unit, integration, and E2E test cases with synthetic data generator and benchmark suite.
