"""Unit tests for RetailFlow ETL custom exception hierarchy."""


from retailflow.constants.constants import ErrorCode, ExecutionStage
from retailflow.exceptions.exceptions import (
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseError,
    RetailFlowError,
    RowValidationError,
    SchemaValidationError,
    ValidationError,
)


def test_exception_inheritance() -> None:
    """Test inheritance hierarchy of domain exceptions."""
    assert issubclass(ConfigurationError, RetailFlowError)
    assert issubclass(DatabaseError, RetailFlowError)
    assert issubclass(DatabaseConnectionError, DatabaseError)
    assert issubclass(ValidationError, RetailFlowError)
    assert issubclass(SchemaValidationError, ValidationError)
    assert issubclass(RowValidationError, ValidationError)


def test_exception_serialization() -> None:
    """Test exception serialization to dict via to_dict()."""
    err = DatabaseConnectionError(
        user_message="Failed to connect to host",
        technical_message="psycopg2.OperationalError: Connection refused",
        details={"host": "localhost", "port": 5432},
    )

    data = err.to_dict()
    assert data["user_message"] == "Failed to connect to host"
    assert data["technical_message"] == "psycopg2.OperationalError: Connection refused"
    assert data["error_code"] == ErrorCode.ERR_DB_CONNECTION.value
    assert data["retryable"] is True
    assert data["stage"] == ExecutionStage.INITIALIZATION.value
    assert data["details"]["host"] == "localhost"
