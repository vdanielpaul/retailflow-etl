# Key Architectural Design Decisions & Tradeoffs

## ADR 001: Configuration Format Selection (YAML vs INI vs Environment Variables)
- **Status**: Approved
- **Context**: Need a maintainable, structured format for pipeline configuration containing nested schemas, folder paths, and validation rules.
- **Decision**: Adopted YAML (`config/config.yaml`) coupled with Pydantic typed models and dynamic environment variable resolution (`env_var:NAME`).
- **Tradeoffs**: Requires PyYAML dependency, but offers vastly superior readability and hierarchical structuring over INI files.

---

## ADR 002: Validation Strategy (Fail-Fast vs Quarantine Isolation)
- **Status**: Approved
- **Context**: Raw store CSV feeds from 250+ stores often contain minor data corruption or bad row formatting.
- **Decision**: Implemented Quarantine Isolation. Bad rows are extracted into JSON files in `data/bad_records/` with metadata, allowing remaining clean rows to proceed.
- **Tradeoffs**: Increases processing logic complexity compared to fail-fast, but prevents whole-feed pipeline blockages over isolated bad rows.

---

## ADR 003: Surrogate Key Generation Strategy (Database-Generated vs Python Hashing)
- **Status**: Approved
- **Context**: Warehouse tables require unique surrogate keys for fast dimensional joins.
- **Decision**: Used PostgreSQL native `BIGINT GENERATED ALWAYS AS IDENTITY` surrogate keys.
- **Tradeoffs**: Requires database round-trips for natural-to-surrogate key lookups, but guarantees monotonic sequence integrity without risk of hash collisions.
