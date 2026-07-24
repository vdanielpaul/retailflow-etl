# Project Overview: RetailFlow ETL

## Business Context
RetailFlow is a national retail chain operating over 250 store locations across multiple regions. Each night, point-of-sale (POS) systems across all stores export transactional CSV files containing sales headers, line items, customer details, product updates, and employee shift associations.

Without a centralized, automated data pipeline, business leadership faced:
- Delayed reporting and analytics.
- Data inconsistency due to unvalidated POS store feed updates.
- Inability to perform cross-store revenue, inventory, and employee performance benchmarking.

---

## Technical Solution
RetailFlow ETL provides an enterprise Python & PostgreSQL data warehousing pipeline that automates:
1. Automated file ingestion from file landing zones.
2. Robust schema enforcement and multi-pass data quality validation.
3. Automated bad record quarantining without crashing batch execution.
4. SCD Type 1 dimension updates and Star Schema data model maintenance.
5. End-to-end audit logging, execution metrics, and incremental watermarking.

---

## Core Technical Objectives
- **Zero Data Loss**: Valid records are processed immediately while invalid records are safely quarantined with exact metadata for operational remediation.
- **Enterprise Code Quality**: Object-oriented modular design adhering to PEP 8 standards, typed signatures, unit testing with pytest, and structured YAML configuration.
- **Dimensional Modeling**: Scalable PostgreSQL Star Schema model implementing surrogate keys (`BIGINT`) and indexed join paths optimized for OLAP query workloads.
