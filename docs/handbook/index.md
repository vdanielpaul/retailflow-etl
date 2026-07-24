# RetailFlow ETL — Developer & Interview Handbook

Welcome to the **RetailFlow ETL Engineering Handbook**. This guide is written specifically for developers mastering Data Engineering concepts and preparing for technical interviews.

---

## 📚 Handbook Navigation Index

- 📖 [**Chapter 1: What is RetailFlow ETL?**](01_introduction.md) — Fundamental problems solved by ETL and dimensional warehousing in retail enterprise environments.
- 📖 [**Chapter 2: Complete Pipeline Overview**](02_pipeline_overview.md) — High-level lifecycle of a CSV feed file from store export to warehouse load.
- 📖 [**Chapter 3: Repository Tour**](03_repository_tour.md) — Comprehensive guide to every folder, file, and module responsibility.
- 📖 [**Chapter 4: Configuration & PipelineContext**](04_configuration.md) — Layered YAML configs, dependency injection, and `PipelineContext`.
- 📖 [**Chapter 5: Data Quality Validation Engine**](05_validation_engine.md) — Modular validators, data quality rules, and bad record quarantine.
- 📖 [**Chapter 6: Canonical Data Model (CDM)**](06_canonical_data_model.md) — Source decoupling pattern, Pydantic schemas, and enterprise design rationale.
- 📖 [**Chapter 7: Modular Transformation Pipeline**](07_transformation_pipeline.md) — Cleaning, normalizer, enricher, surrogate key resolution, and SCD Type 1.
- 📖 [**Chapter 8: Data Warehouse & Star Schema Design**](08_data_warehouse.md) — Fact tables, dimension tables, primary vs surrogate keys, and SCD Type 1.
- 📖 [**Chapter 9: High-Performance Warehouse Loader**](09_loader.md) — PostgreSQL `COPY` streaming, `execute_values`, transaction scope, and `SAVEPOINT`s.
- 📖 [**Chapter 10: Incremental Processing, Watermarks & Replay**](10_incremental_processing.md) — High-watermark tracking, SHA-256 change detection, operator replay, and checkpoints.
- 📖 [**Chapter 11: Operational Audit & Observability System**](11_audit_system.md) — Lifecycle events, telemetry publishers, search APIs, and dashboard summaries.
- 📖 [**Chapter 12: Testing Architecture & Harness**](12_testing.md) — Unit, integration, E2E test suites, synthetic data generators, and test assertions.
- 📖 [**Chapter 13: Performance Optimization & Benchmarking**](13_performance.md) — Vectorized Pandas, bulk load throughput, memory profiling (`tracemalloc`), and benchmark analysis.
- 📖 [**Chapter 14: Step-by-Step Data Walkthrough**](14_complete_walkthrough.md) — End-to-end trace of a single CSV line item through every pipeline stage.
- 📖 [**Chapter 15: Master Interview Preparation (100 Q&As)**](15_interview_preparation.md) — 100 technical interview questions with senior-level model answers.
- 📖 [**Chapter 16: Big Picture & Future Cloud Evolution**](16_big_picture.md) — Scaling to PySpark, Apache Kafka, Airflow, Databricks, and AWS Cloud Data Lakes.
- 📖 [**Chapter 17: Lessons Learned & Architectural Trade-Offs**](17_lessons_learned.md) — Trade-off evaluations, design reflections, and v2 improvements.
- 📖 [**Chapter 18: Comprehensive Data Engineering Glossary**](18_glossary.md) — Definitions for key Data Engineering terminology.
- 📖 [**Chapter 19: Visual Learning & System Architecture Diagrams**](19_visual_learning.md) — Complete collection of Mermaid sequence and architecture diagrams.
- 📖 [**Chapter 20: Final Summary**](20_summary.md) — Concise executive summary of RetailFlow ETL.
- 📖 [**Chapter 21: Local PostgreSQL Database Setup**](21_database_setup.md) — Setting up, running, and verifying your local PostgreSQL database schemas.

