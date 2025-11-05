"""Tests for wpgen/utils/code_validator.py CodeValidator class."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from wpgen.utils.code_validator import CodeValidator


class TestCodeValidator:
    """Test suite for CodeValidator class."""

    @pytest.fixture
    def mock_php_available(self):
        """Mock subprocess.run to simulate PHP being available."""
        with patch("wpgen.utils.code_validator.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="PHP 8.2.0\n")
            yield mock_run

    @pytest.fixture
    def mock_php_unavailable(self):
        """Mock subprocess.run to simulate PHP not being available."""
        with patch("wpgen.utils.code_validator.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("php not found")
            yield mock_run

    def test_init_default_parameters(self, mock_php_available):
        """Test CodeValidator initialization with default parameters."""
        validator = CodeValidator()
        assert validator.strict is False
        assert validator.php_path == "php"
        assert validator.php_available is True

    def test_init_strict_mode(self, mock_php_available):
        """Test CodeValidator initialization with strict mode enabled."""
        validator = CodeValidator(strict=True)
        assert validator.strict is True
        assert validator.php_available is True

    def test_init_custom_php_path(self, mock_php_available):
        """Test CodeValidator initialization with custom PHP path."""
        validator = CodeValidator(php_path="/usr/bin/php")
        assert validator.php_path == "/usr/bin/php"

    def test_check_php_available_success(self, mock_php_available):
        """Test _check_php_available when PHP is available."""
        validator = CodeValidator()
        assert validator.php_available is True
        mock_php_available.assert_called_once()

    def test_check_php_available_failure(self, mock_php_unavailable):
        """Test _check_php_available when PHP is not available."""
        validator = CodeValidator()
        assert validator.php_available is False

    def test_check_php_available_timeout(self):
        """Test _check_php_available when PHP command times out."""
        with patch("wpgen.utils.code_validator.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("php", 5)
            validator = CodeValidator()
            assert validator.php_available is False

    def test_validate_php_syntax_valid_code(self, mock_php_available):
        """Test validate_php_syntax with valid PHP code."""
        validator = CodeValidator()
        php_code = "<?php\necho 'Hello, World!';\n"

        # Mock the syntax check to succeed
        mock_php_available.return_value = Mock(returncode=0)

        is_valid, error_msg, is_warning = validator.validate_php_syntax(php_code)
        assert is_valid is True
        assert error_msg is None
        assert is_warning is False

    def test_validate_php_syntax_invalid_code(self, mock_php_available):
        """Test validate_php_syntax with invalid PHP code."""
        validator = CodeValidator()
        php_code = "<?php\necho 'Hello, World!'\n"  # Missing semicolon

        # First call is for __init__, second is for validate_php_syntax
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),
            Mock(returncode=1, stderr="Parse error: syntax error")
        ]

        validator = CodeValidator()
        is_valid, error_msg, is_warning = validator.validate_php_syntax(php_code)
        assert is_valid is False
        assert "Parse error" in error_msg
        assert is_warning is False

    def test_validate_php_syntax_php_unavailable_non_strict(self, mock_php_unavailable):
        """Test validate_php_syntax when PHP is unavailable in non-strict mode."""
        validator = CodeValidator(strict=False)
        php_code = "<?php\necho 'Hello, World!';\n"

        is_valid, error_msg, is_warning = validator.validate_php_syntax(php_code)
        assert is_valid is True  # Should pass in non-strict mode
        assert "PHP binary not found" in error_msg
        assert is_warning is True

    def test_validate_php_syntax_php_unavailable_strict(self, mock_php_unavailable):
        """Test validate_php_syntax when PHP is unavailable in strict mode."""
        validator = CodeValidator(strict=True)
        php_code = "<?php\necho 'Hello, World!';\n"

        is_valid, error_msg, is_warning = validator.validate_php_syntax(php_code)
        assert is_valid is False  # Should fail in strict mode
        assert "PHP binary not found" in error_msg
        assert is_warning is True

    def test_validate_file_php_file_valid(self, mock_php_available, tmp_path):
        """Test validate_file with a valid PHP file."""
        validator = CodeValidator()

        # Create a temporary PHP file
        php_file = tmp_path / "test.php"
        php_file.write_text("<?php\necho 'Hello, World!';\n")

        # Mock the syntax check to succeed
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=0)  # validate_php_syntax
        ]

        validator = CodeValidator()
        result = validator.validate_file(php_file)

        assert result["valid"] is True
        assert result["file"] == str(php_file)
        assert len(result["errors"]) == 0

    def test_validate_file_php_file_invalid(self, mock_php_available, tmp_path):
        """Test validate_file with an invalid PHP file."""
        validator = CodeValidator()

        # Create a temporary PHP file with syntax error
        php_file = tmp_path / "test.php"
        php_file.write_text("<?php\necho 'Hello, World!'\n")  # Missing semicolon

        # Mock the syntax check to fail
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=1, stderr="Parse error: syntax error")  # validate_php_syntax
        ]

        validator = CodeValidator()
        result = validator.validate_file(php_file)

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_file_non_php_file(self, mock_php_available, tmp_path):
        """Test validate_file with a non-PHP file (should skip validation)."""
        validator = CodeValidator()

        # Create a temporary non-PHP file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is a text file")

        result = validator.validate_file(txt_file)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0

    def test_validate_file_file_not_readable(self, mock_php_available, tmp_path):
        """Test validate_file with a file that cannot be read."""
        validator = CodeValidator()

        # Create a file and then delete it to simulate read failure
        php_file = tmp_path / "test.php"

        result = validator.validate_file(php_file)

        assert result["valid"] is False
        assert any("Failed to read file" in error for error in result["errors"])

    def test_validate_directory_valid_php_files(self, mock_php_available, tmp_path):
        """Test validate_directory with valid PHP files."""
        # Create a directory with valid PHP files
        (tmp_path / "file1.php").write_text("<?php\necho 'File 1';\n")
        (tmp_path / "file2.php").write_text("<?php\necho 'File 2';\n")

        # Mock all syntax checks to succeed
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=0),  # file1.php
            Mock(returncode=0),  # file2.php
        ]

        validator = CodeValidator()
        result = validator.validate_directory(str(tmp_path))

        assert result["valid"] is True
        assert result["files_checked"] == 2
        assert result["files_with_errors"] == 0

    def test_validate_directory_with_errors(self, mock_php_available, tmp_path):
        """Test validate_directory with some invalid PHP files."""
        # Create files - one valid, one invalid
        (tmp_path / "valid.php").write_text("<?php\necho 'Valid';\n")
        (tmp_path / "invalid.php").write_text("<?php\necho 'Invalid'\n")  # Missing semicolon

        # Mock syntax checks
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=1, stderr="Parse error"),  # invalid.php
            Mock(returncode=0),  # valid.php
        ]

        validator = CodeValidator()
        result = validator.validate_directory(str(tmp_path))

        assert result["valid"] is False
        assert result["files_checked"] == 2
        assert result["files_with_errors"] > 0

    def test_validate_directory_nonexistent(self, mock_php_available):
        """Test validate_directory with a nonexistent directory."""
        validator = CodeValidator()
        result = validator.validate_directory("/nonexistent/path")

        assert result["valid"] is False
        assert any("does not exist" in error for error in result["errors"])

    def test_validate_directory_strict_mode_warnings(self, mock_php_unavailable, tmp_path):
        """Test validate_directory in strict mode with warnings."""
        # Create a valid PHP file
        (tmp_path / "test.php").write_text("<?php\necho 'Test';\n")

        # In strict mode with PHP unavailable, should fail
        validator = CodeValidator(strict=True)
        result = validator.validate_directory(str(tmp_path))

        assert result["valid"] is False
