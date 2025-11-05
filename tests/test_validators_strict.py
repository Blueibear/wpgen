"""Tests for validator strict mode behavior."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from wpgen.utils.code_validator import CodeValidator
from wpgen.utils.theme_validator import ThemeValidator


def test_code_validator_strict_mode_php_missing():
    """Test CodeValidator fails in strict mode when PHP is missing."""
    with patch("subprocess.run") as mock_run:
        # Simulate PHP not available
        mock_run.side_effect = FileNotFoundError("php not found")

        validator = CodeValidator(strict=True)
        assert validator.php_available is False

        # Validate PHP code - should fail in strict mode
        is_valid, message, is_warning = validator.validate_php_syntax("<?php echo 'test'; ?>")

        assert is_valid is False
        assert "PHP binary not found" in message
        assert is_warning is True


def test_code_validator_non_strict_php_missing():
    """Test CodeValidator warns but passes in non-strict mode when PHP is missing."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("php not found")

        validator = CodeValidator(strict=False)
        assert validator.php_available is False

        # Validate PHP code - should pass with warning in non-strict mode
        is_valid, message, is_warning = validator.validate_php_syntax("<?php echo 'test'; ?>")

        assert is_valid is True
        assert "PHP binary not found" in message
        assert is_warning is True


def test_code_validator_syntax_error():
    """Test CodeValidator detects syntax errors."""
    with patch("subprocess.run") as mock_run:
        # PHP available check
        mock_run.return_value = Mock(returncode=0, stdout="PHP 8.0.0")

        validator = CodeValidator(strict=False)

        # Reset mock for syntax check
        mock_run.reset_mock()
        mock_run.return_value = Mock(
            returncode=1,
            stderr="Parse error: syntax error, unexpected end of file",
            stdout=""
        )

        is_valid, message, is_warning = validator.validate_php_syntax("<?php echo 'test'")

        assert is_valid is False
        assert "syntax error" in message.lower()
        assert is_warning is False


def test_code_validator_valid_syntax():
    """Test CodeValidator passes valid PHP code."""
    with patch("subprocess.run") as mock_run:
        # PHP available check
        mock_run.return_value = Mock(returncode=0, stdout="PHP 8.0.0")

        validator = CodeValidator(strict=False)

        # Reset for syntax check
        mock_run.reset_mock()
        mock_run.return_value = Mock(returncode=0, stdout="No syntax errors detected")

        is_valid, message, is_warning = validator.validate_php_syntax("<?php echo 'test'; ?>")

        assert is_valid is True
        assert message is None
        assert is_warning is False


def test_theme_validator_strict_mode_missing_php():
    """Test ThemeValidator strict mode fails when PHP is missing."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("php not found")

        validator = ThemeValidator(strict=True, php_path="php")
        assert validator.php_available is False


def test_theme_validator_missing_required_files(tmp_path):
    """Test ThemeValidator detects missing required files."""
    theme_dir = tmp_path / "test-theme"
    theme_dir.mkdir()

    # Create only style.css, missing index.php
    (theme_dir / "style.css").write_text("/* Theme Name: Test */")

    validator = ThemeValidator(strict=False)
    results = validator.validate(str(theme_dir))

    assert results["valid"] is False
    assert any("index.php" in error for error in results["errors"])


def test_theme_validator_warnings_in_strict_mode(tmp_path):
    """Test ThemeValidator treats warnings as errors in strict mode."""
    theme_dir = tmp_path / "test-theme"
    theme_dir.mkdir()

    # Create required files
    (theme_dir / "style.css").write_text("/* Theme Name: Test */")
    (theme_dir / "index.php").write_text("<?php // Test ?>")

    # Missing recommended files will generate warnings
    with patch("subprocess.run") as mock_run:
        # PHP available
        mock_run.return_value = Mock(returncode=0, stdout="PHP 8.0.0")

        validator_strict = ThemeValidator(strict=True)
        results_strict = validator_strict.validate(str(theme_dir))

        # In strict mode, warnings make validation fail
        if results_strict["warnings"]:
            assert results_strict["valid"] is False

        validator_non_strict = ThemeValidator(strict=False)
        results_non_strict = validator_non_strict.validate(str(theme_dir))

        # In non-strict mode, warnings don't fail validation
        if results_non_strict["warnings"] and not results_non_strict["errors"]:
            assert results_non_strict["valid"] is True


def test_validation_summary_table_output(tmp_path, capsys):
    """Test validation summary table is printed."""
    from wpgen.utils.validation_report import print_validation_summary_table

    results = {
        "files_checked": 10,
        "valid_files": 8,
        "files_with_errors": 2,
        "warnings": ["Warning 1", "Warning 2"],
        "errors": ["Error 1", "Error 2"],
        "valid": False,
    }

    print_validation_summary_table(results, strict=False)

    captured = capsys.readouterr()
    output = captured.out

    assert "Validation Summary" in output
    assert "10" in output  # files_checked
    assert "8" in output   # valid_files
    assert "2" in output   # errors
    assert "ERROR" in output or "✗" in output


def test_validation_summary_strict_mode(tmp_path, capsys):
    """Test validation summary shows strict mode warnings as errors."""
    from wpgen.utils.validation_report import print_validation_summary_table

    results = {
        "files_checked": 5,
        "valid_files": 5,
        "files_with_errors": 0,
        "warnings": ["PHP not available"],
        "errors": [],
        "valid": False,
    }

    print_validation_summary_table(results, strict=True)

    captured = capsys.readouterr()
    output = captured.out

    assert "ERROR" in output  # Warnings shown as errors in strict mode
    assert "Strict mode" in output or "strict" in output.lower()
