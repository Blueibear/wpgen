"""Tests for log redaction of sensitive data."""

import logging
import pytest
from wpgen.utils.logger import (
    redact_sensitive_data,
    SecretRedactingFilter,
    setup_logger,
)


def test_redact_api_key():
    """Test API key redaction."""
    message = 'Using api_key: "sk-1234567890abcdef"'
    redacted = redact_sensitive_data(message)

    assert "sk-1234567890abcdef" not in redacted
    assert "***" in redacted
    assert "api_key" in redacted  # Key name should remain


def test_redact_token():
    """Test token redaction."""
    message = "token=abc123def456"
    redacted = redact_sensitive_data(message)

    assert "abc123def456" not in redacted
    assert "***" in redacted
    assert "token" in redacted


def test_redact_password():
    """Test password redaction."""
    message = 'password: "my_secret_pass"'
    redacted = redact_sensitive_data(message)

    assert "my_secret_pass" not in redacted
    assert "***" in redacted
    assert "password" in redacted


def test_redact_authorization_header():
    """Test Authorization header redaction."""
    message = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    redacted = redact_sensitive_data(message)

    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
    assert "***" in redacted
    assert "Authorization" in redacted


def test_redact_github_token():
    """Test GitHub token redaction."""
    message = "Pushing with token ghp_1234567890abcdefghij1234567890abcdef"
    redacted = redact_sensitive_data(message)

    assert "ghp_1234567890abcdefghij1234567890abcdef" not in redacted
    assert "***" in redacted


def test_redact_openai_key():
    """Test OpenAI API key redaction."""
    message = "OpenAI key: sk-proj-abcdef1234567890"
    redacted = redact_sensitive_data(message)

    assert "sk-proj-abcdef1234567890" not in redacted
    assert "***" in redacted


def test_redact_multiple_secrets():
    """Test multiple secrets in one message."""
    message = 'api_key="sk-123" and token="ghp_456" and password="secret"'
    redacted = redact_sensitive_data(message)

    assert "sk-123" not in redacted
    assert "ghp_456" not in redacted
    assert "secret" not in redacted
    assert redacted.count("***") == 3


def test_no_false_positives():
    """Test that normal text is not redacted."""
    message = "This is a normal log message about tokens and keys"
    redacted = redact_sensitive_data(message)

    assert redacted == message  # Should be unchanged


def test_secret_filter_on_log_record():
    """Test SecretRedactingFilter on log records."""
    filter_instance = SecretRedactingFilter()

    # Create a log record with a secret
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='Using api_key: "sk-secret123"',
        args=(),
        exc_info=None,
    )

    # Apply filter
    result = filter_instance.filter(record)

    assert result is True  # Filter should allow record through
    assert "sk-secret123" not in record.msg
    assert "***" in record.msg


def test_secret_filter_with_args():
    """Test SecretRedactingFilter redacts args too."""
    filter_instance = SecretRedactingFilter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Token is %s",
        args=("ghp_secrettoken123",),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert "ghp_secrettoken123" not in str(record.args)
    assert "***" in record.args[0]


def test_logger_applies_redaction(tmp_path):
    """Test that setup_logger applies redaction filter."""
    log_file = tmp_path / "test.log"

    logger = setup_logger(
        "test_redaction",
        log_file=str(log_file),
        level="INFO",
        console_output=False,
    )

    # Log a message with a secret
    logger.info('API Key: "sk-secret123456789"')

    # Read log file
    log_content = log_file.read_text()

    assert "sk-secret123456789" not in log_content
    assert "***" in log_content


def test_json_logs_redaction(tmp_path):
    """Test redaction works with JSON log format."""
    log_file = tmp_path / "test.jsonl"

    logger = setup_logger(
        "test_json_redaction",
        log_file=str(log_file),
        level="INFO",
        format_type="json",
        console_output=False,
    )

    logger.info("Using token: ghp_mysecrettoken123")

    log_content = log_file.read_text()

    assert "ghp_mysecrettoken123" not in log_content
    assert "***" in log_content


def test_redact_preserves_structure():
    """Test that redaction preserves message structure."""
    message = 'Config: {"api_key": "sk-123", "model": "gpt-4"}'
    redacted = redact_sensitive_data(message)

    assert "sk-123" not in redacted
    assert "***" in redacted
    assert '"model": "gpt-4"' in redacted  # Non-secret preserved
    assert "api_key" in redacted  # Key name preserved
