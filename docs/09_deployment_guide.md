# Deployment & Execution Guide

## System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ / RHEL 8+) or macOS (12+)
- **Python**: Python 3.10+
- **Database**: PostgreSQL 14+

---

## Installation & Environment Setup

```bash
# 1. Clone Repository
git clone https://github.com/your-org/retailflow-etl.git
cd retailflow-etl

# 2. Create Python Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Package & Dependencies
pip install --upgrade pip
pip install -e ".[dev]"

# 4. Set Environment Variables
export POSTGRES_USER="retailflow_user"
export POSTGRES_PASSWORD="secure_password_here"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT=5432
export POSTGRES_DB="retailflow_dw"
```

---

## Database Initialization
Run the DDL scripts to create schema, dimension tables, fact tables, and audit logs:

```bash
# Initialize schema and tables
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f sql/ddl/01_create_tables.sql
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f sql/ddl/02_create_indexes.sql
```

---

## Production Execution
To trigger a manual or cron-scheduled batch pipeline execution:

```bash
# Run pipeline with default configuration
python -m retailflow.main --config config/config.yaml
```
