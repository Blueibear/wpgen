"""Tests for model deprecation warnings."""

import pytest

from wpgen.utils.model_deprecation import (
    check_model_deprecation,
    log_model_deprecation_warning,
)


def test_deprecated_gpt4_turbo_preview():
    """Test detection of deprecated GPT-4 Turbo preview model."""
    is_dep, warning, suggested = check_model_deprecation("gpt-4-turbo-preview", "openai")

    assert is_dep is True
    assert "deprecated" in warning.lower() or "preview" in warning.lower()
    assert suggested == "gpt-4-turbo"


def test_deprecated_gpt4_vision_preview():
    """Test detection of deprecated GPT-4 Vision preview model."""
    is_dep, warning, suggested = check_model_deprecation("gpt-4-vision-preview", "openai")

    assert is_dep is True
    assert suggested is not None


def test_deprecated_claude2():
    """Test detection of deprecated Claude 2 models."""
    is_dep, warning, suggested = check_model_deprecation("claude-2.1", "anthropic")

    assert is_dep is True
    assert "claude-3" in suggested


def test_stable_model_not_deprecated():
    """Test that stable models are not flagged as deprecated."""
    is_dep, warning, suggested = check_model_deprecation("gpt-4-turbo", "openai")

    assert is_dep is False
    assert warning is None
    assert suggested is None


def test_stable_claude_not_deprecated():
    """Test that stable Claude model is not flagged."""
    is_dep, warning, suggested = check_model_deprecation("claude-3-5-sonnet-20241022", "anthropic")

    assert is_dep is False


def test_pattern_match_preview_suffix():
    """Test pattern matching for -preview suffix."""
    is_dep, warning, suggested = check_model_deprecation("some-new-model-preview", "openai")

    assert is_dep is True
    assert "preview" in warning.lower()


def test_pattern_match_dated_snapshot():
    """Test pattern matching for dated snapshot models."""
    is_dep, warning, suggested = check_model_deprecation("gpt-3.5-turbo-0125", "openai")

    assert is_dep is True
    assert "dated" in warning.lower() or "snapshot" in warning.lower()


def test_empty_model_name():
    """Test handling of empty model name."""
    is_dep, warning, suggested = check_model_deprecation("", "openai")

    assert is_dep is False
    assert warning is None


def test_none_model_name():
    """Test handling of None model name."""
    is_dep, warning, suggested = check_model_deprecation(None, "openai")

    assert is_dep is False


def test_log_deprecation_warning(caplog):
    """Test logging of deprecation warnings."""
    import logging
    caplog.set_level(logging.WARNING)

    log_model_deprecation_warning("gpt-4-turbo-preview", "openai")

    assert any("deprecated" in record.message.lower() or "preview" in record.message.lower()
               for record in caplog.records)


def test_log_no_warning_for_stable(caplog):
    """Test no warning logged for stable models."""
    import logging
    caplog.set_level(logging.WARNING)

    log_model_deprecation_warning("gpt-4-turbo", "openai")

    # Should have no warning records
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    # Filter out only deprecation-related warnings
    deprecation_warnings = [r for r in warning_records if "deprecated" in r.message.lower()]
    assert len(deprecation_warnings) == 0
