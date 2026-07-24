# ADR-003: Hierarchical YAML Configuration System

## Status
Accepted

## Context
Enterprise data pipelines require configuration management for environment settings (development vs staging vs production), database credentials, directory paths, validation thresholds, and logging controls. We needed a clean, human-readable format supporting nested parameters.

## Decision
We adopted a layered **YAML configuration framework** (`base.yaml`, `development.yaml`, `production.yaml`) integrated with Pydantic settings models and dynamic environment variable resolution (`env_var:NAME`).

## Alternatives Considered
1. **INI Files (`configparser`)**: Standard library configuration.
   - *Pros*: Built-in Python support.
   - *Cons*: Flat structure, lacks type enforcement, nested dictionary mappings are verbose and fragile.
2. **Environment Variables Only (.env)**:
   - *Pros*: Standard 12-factor app practice.
   - *Cons*: Unwieldy for complex validation rule definitions, schema specifications, and nested batch settings.

## Consequences
- **Positive**: Clear human-readable hierarchical structure, clean separation of environment overrides from base parameters, secret protection via runtime environment variable interpolation.
- **Negative**: Adds PyYAML and Pydantic runtime dependencies.
