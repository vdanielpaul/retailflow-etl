.PHONY: help install lint format type-check test run-pipeline clean

PYTHON ?= python3
PIP ?= pip

help:
	@echo "RetailFlow ETL Development Commands:"
	@echo "  make install       Install dependencies in editable mode"
	@echo "  make lint          Run linter checks (ruff)"
	@echo "  make format        Auto-format code (ruff)"
	@echo "  make type-check    Run static type analysis (mypy)"
	@echo "  make test          Run pytest test suite"
	@echo "  make run-pipeline  Execute RetailFlow ETL pipeline"
	@echo "  make clean         Remove build artifacts and pycache"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

type-check:
	mypy src/

test:
	pytest tests/

run-pipeline:
	$(PYTHON) -m retailflow.main --config config/development.yaml

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
