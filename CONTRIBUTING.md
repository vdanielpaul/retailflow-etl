# Contributing to RetailFlow ETL

Thank you for your interest in contributing to RetailFlow ETL!

## Development Workflow

1. Fork the repository and create a feature branch (`git checkout -b feature/amazing-feature`).
2. Set up the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run tests before submitting pull requests:
   ```bash
   pytest tests/unit tests/integration tests/e2e
   ```
4. Adhere to PEP8 coding standards and run static analysis:
   ```bash
   ruff check src tests
   ```
5. Submit a detailed Pull Request describing your changes and verification steps.
