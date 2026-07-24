# Chapter 21: Local PostgreSQL Database Setup & Ingestion Verification

This chapter provides a detailed, step-by-step guide to starting, configuring, and verifying your local PostgreSQL database on macOS to test real database writes and schema ingestion.

---

## 1. Step 1: Install & Start PostgreSQL on macOS

If you do not have PostgreSQL installed, install it using Homebrew:
```bash
brew install postgresql@14
```

To start the PostgreSQL background service so that it runs continuously:
```bash
brew services start postgresql@14
```
*(If you installed a different version, replace `postgresql@14` with your installed version, e.g. `postgresql` or `postgresql@15`)*

To verify that PostgreSQL is running locally and listening on port `5432`:
```bash
pg_isready
```

---

## 2. Step 2: Create the Target Database

Create the central data warehouse database `retailflow_dw` using the PostgreSQL utility:
```bash
createdb retailflow_dw
```

To verify the database exists, connect to it using the interactive terminal:
```bash
psql -d retailflow_dw -c "\conninfo"
```

---

## 3. Step 3: Load Schema DDL Scripts

Apply the SQL DDL scripts included in the repository to create target table schemas, partitions, indexes, constraints, views, and audit tables.

### 1. Apply the Target Warehouse Schema DDL
Creates the analytical dimension and fact tables (`dim_customer`, `dim_product`, `dim_store`, `dim_employee`, `dim_date`, and partitioned `fact_sales`):
```bash
psql -d retailflow_dw -f sql/ddl/01_create_warehouse_schema.sql
```

### 2. Apply the Metadata Schema DDL
Creates operational tables (`metadata.etl_audit_log` and `metadata.etl_watermark`):
```bash
psql -d retailflow_dw -f sql/ddl/02_create_metadata_schema.sql
```

### 3. Verify Table Schemas Exist
To confirm schemas were created, list the tables inside the database:
```bash
psql -d retailflow_dw -c "\dt warehouse.*"
psql -d retailflow_dw -c "\dt metadata.*"
```

---

## 4. Step 4: Configure Credentials & Environment Variables

The configuration profiles under `config/` look for database authentication credentials.

### Resolving "fe_sendauth: no password supplied"
If your local PostgreSQL superuser requires password authentication, set the `POSTGRES_PASSWORD` environment variable in your terminal session before executing the pipeline:
```bash
export POSTGRES_PASSWORD="your_postgres_password"
```

### Config Profile Configuration
In `config/development.yaml`, verify the database config block matches your local credentials:
```yaml
database:
  host: "localhost"
  port: 5432
  name: "retailflow_dw"
  user: "postgres"
  password: "env_var:POSTGRES_PASSWORD"
```

---

## 5. Step 5: Run Ingestion & Verify Database Insertion

Now that the database is configured, start the full end-to-end pipeline run:

```bash
python -m retailflow.cli --file sample_data/small/sales_1k.csv
```

### Verification Queries
Verify that sales data was successfully loaded into your central partitioned fact table:
```bash
# Check fact sales count
psql -d retailflow_dw -c "SELECT COUNT(*) FROM warehouse.fact_sales;"

# View recent execution run metadata in audit logs
psql -d retailflow_dw -c "SELECT pipeline_run_id, status, rows_loaded, start_time FROM metadata.etl_audit_log LIMIT 5;"
```
