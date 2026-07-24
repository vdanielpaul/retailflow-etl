# RetailFlow ETL - Scalability & Future Architecture Review

## Overview
This document evaluates the current architectural bounds of RetailFlow ETL and outlines the scaling roadmap to transition from a single-node Pandas/PostgreSQL pipeline into a distributed cloud-native data platform.

---

## Current Architecture Scalability Limits

| Component | Current Single-Node Limit | Scalability Bottleneck |
|---|---|---|
| **Pandas Feed Ingestion** | ~10 GB per feed file | In-memory DataFrame allocation bound by worker node RAM |
| **PostgreSQL Bulk Load** | ~50,000 rows/sec | Single database writer connection & transaction log write locks |
| **In-Memory Key Lookup** | ~5,000,000 dimension keys | Process heap memory allocation for dictionary caches |

---

## Scale-Out Architecture Roadmap

### 1. PySpark Migration Strategy
- **Decoupled Business Logic**: Because data cleaning, validation rules, and financial calculations are decoupled via a Canonical Data Model, Pandas operations can be replaced with PySpark DataFrames.
- **Distributed Transformation**: Distribute validation and metric calculation across an EMR / Databricks Spark cluster, scaling to multi-terabyte feeds.

### 2. Streaming & Kafka Integration
- **Micro-Batch Streaming**: Replace nightly batch CSV exports with continuous event streaming via Apache Kafka / AWS Kinesis.
- **Real-Time Data Quality**: Apply `ValidationEngine` checks on Kafka event streams using Spark Structured Streaming.

### 3. Change Data Capture (CDC)
- Implement Debezium CDC on POS transactional databases to capture real-time row-level inserts, updates, and deletes directly into Kafka topics.
