"""Tests for wpgen/utils/theme_validator.py ThemeValidator class."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from wpgen.utils.theme_validator import ThemeValidator


class TestThemeValidator:
    """Test suite for ThemeValidator class."""

    @pytest.fixture
    def mock_php_available(self):
        """Mock subprocess.run to simulate PHP being available."""
        with patch("wpgen.utils.theme_validator.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="PHP 8.2.0\n")
            yield mock_run

    @pytest.fixture
    def mock_php_unavailable(self):
        """Mock subprocess.run to simulate PHP not being available."""
        with patch("wpgen.utils.theme_validator.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("php not found")
            yield mock_run

    @pytest.fixture
    def basic_theme(self, tmp_path):
        """Create a basic WordPress theme structure."""
        theme_dir = tmp_path / "test-theme"
        theme_dir.mkdir()

        # Create required files
        (theme_dir / "style.css").write_text("/* Theme Name: Test Theme */")
        (theme_dir / "index.php").write_text("<?php\nget_header();\nget_footer();\n")

        # Create recommended files
        (theme_dir / "functions.php").write_text("<?php\n// Theme functions\n")
        (theme_dir / "header.php").write_text("<?php\n// Header\n")
        (theme_dir / "footer.php").write_text("<?php\n// Footer\n")

        return theme_dir

    def test_init_default_parameters(self, mock_php_available):
        """Test ThemeValidator initialization with default parameters."""
        validator = ThemeValidator()
        assert validator.strict is False
        assert validator.php_path == "php"
        assert validator.php_available is True

    def test_init_strict_mode(self, mock_php_available):
        """Test ThemeValidator initialization with strict mode enabled."""
        validator = ThemeValidator(strict=True)
        assert validator.strict is True

    def test_init_custom_php_path(self, mock_php_available):
        """Test ThemeValidator initialization with custom PHP path."""
        validator = ThemeValidator(php_path="/usr/bin/php")
        assert validator.php_path == "/usr/bin/php"

    def test_check_php_available_success(self, mock_php_available):
        """Test _check_php_available when PHP is available."""
        validator = ThemeValidator()
        assert validator.php_available is True

    def test_check_php_available_failure(self, mock_php_unavailable):
        """Test _check_php_available when PHP is not available."""
        validator = ThemeValidator()
        assert validator.php_available is False

    def test_check_php_available_timeout(self):
        """Test _check_php_available when PHP command times out."""
        with patch("wpgen.utils.theme_validator.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("php", 5)
            validator = ThemeValidator()
            assert validator.php_available is False

    def test_validate_theme_not_found(self, mock_php_available):
        """Test validate with nonexistent theme directory."""
        validator = ThemeValidator()
        result = validator.validate("/nonexistent/theme")

        assert result["valid"] is False
        assert "not found" in result["error"]

    def test_validate_not_a_directory(self, mock_php_available, tmp_path):
        """Test validate with a file instead of directory."""
        validator = ThemeValidator()
        test_file = tmp_path / "test.txt"
        test_file.write_text("not a directory")

        result = validator.validate(str(test_file))

        assert result["valid"] is False
        assert "Not a directory" in result["error"]

    def test_validate_missing_required_files(self, mock_php_available, tmp_path):
        """Test validate with missing required files."""
        theme_dir = tmp_path / "incomplete-theme"
        theme_dir.mkdir()

        # Only create style.css, missing index.php
        (theme_dir / "style.css").write_text("/* Theme Name: Test */")

        validator = ThemeValidator()
        result = validator.validate(str(theme_dir))

        assert result["valid"] is False
        assert any("index.php" in error for error in result["errors"])

    def test_validate_missing_recommended_files(self, mock_php_available, tmp_path):
        """Test validate with missing recommended files."""
        theme_dir = tmp_path / "minimal-theme"
        theme_dir.mkdir()

        # Create only required files
        (theme_dir / "style.css").write_text("/* Theme Name: Test */")
        (theme_dir / "index.php").write_text("<?php\n// Index\n")

        # Mock PHP syntax validation to succeed
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=0),  # index.php validation
        ]

        validator = ThemeValidator()
        result = validator.validate(str(theme_dir))

        # Should be valid but have warnings
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("functions.php" in warning for warning in result["warnings"])

    def test_validate_php_unavailable_non_strict(self, mock_php_unavailable, tmp_path):
        """Test validate when PHP is unavailable in non-strict mode."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()
        (theme_dir / "style.css").write_text("/* Theme Name: Test */")
        (theme_dir / "index.php").write_text("<?php\n// Index\n")

        validator = ThemeValidator(strict=False)
        result = validator.validate(str(theme_dir))

        # Should have warnings about PHP not available but still be valid
        assert len(result["warnings"]) > 0
        assert any("PHP binary not found" in warning for warning in result["warnings"])

    def test_validate_php_unavailable_strict(self, mock_php_unavailable, tmp_path):
        """Test validate when PHP is unavailable in strict mode."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()
        (theme_dir / "style.css").write_text("/* Theme Name: Test */")
        (theme_dir / "index.php").write_text("<?php\n// Index\n")

        validator = ThemeValidator(strict=True)
        result = validator.validate(str(theme_dir))

        # Should fail in strict mode
        assert result["valid"] is False
        assert any("PHP binary not found" in error for error in result["errors"])

    def test_validate_valid_theme(self, mock_php_available, basic_theme):
        """Test validate with a complete valid theme."""
        # Mock all PHP validations to succeed
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=0),  # functions.php
            Mock(returncode=0),  # footer.php
            Mock(returncode=0),  # header.php
            Mock(returncode=0),  # index.php
        ]

        validator = ThemeValidator()
        result = validator.validate(str(basic_theme))

        assert result["valid"] is True
        assert result["theme_name"] == "test-theme"
        assert result["php_files"] > 0
        assert result["invalid_files"] == 0

    def test_validate_theme_with_syntax_errors(self, mock_php_available, tmp_path):
        """Test validate with PHP syntax errors in theme files."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()

        (theme_dir / "style.css").write_text("/* Theme Name: Test */")
        (theme_dir / "index.php").write_text("<?php\necho 'test'\n")  # Missing semicolon

        # Mock PHP validation to fail
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=1, stderr="Parse error: syntax error"),  # index.php
        ]

        validator = ThemeValidator()
        result = validator.validate(str(theme_dir))

        assert result["valid"] is False
        assert result["invalid_files"] > 0
        assert any("syntax error" in error for error in result["errors"])

    def test_validate_php_file_missing_opening_tag(self, mock_php_available, tmp_path):
        """Test _validate_php_file with missing PHP opening tag."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()

        php_file = theme_dir / "test.php"
        php_file.write_text("echo 'Hello';")  # Missing <?php

        # Mock PHP validation to succeed (file is syntactically valid, just missing tag)
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=0),  # syntax check
        ]

        validator = ThemeValidator()
        result = validator._validate_php_file(php_file, theme_dir)

        assert len(result["warnings"]) > 0
        assert any("Missing <?php opening tag" in warning for warning in result["warnings"])

    def test_validate_php_file_with_markdown_blocks(self, mock_php_available, tmp_path):
        """Test _validate_php_file with markdown code blocks."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()

        php_file = theme_dir / "test.php"
        php_file.write_text("```php\n<?php echo 'test'; ?>\n```")

        validator = ThemeValidator()
        result = validator._validate_php_file(php_file, theme_dir)

        assert len(result["errors"]) > 0
        assert any("markdown code blocks" in error for error in result["errors"])

    def test_validate_php_file_with_explanatory_text(self, mock_php_available, tmp_path):
        """Test _validate_php_file with explanatory text before code."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()

        php_file = theme_dir / "test.php"
        php_file.write_text("Here's the code for your theme:\n<?php echo 'test'; ?>")

        validator = ThemeValidator()
        result = validator._validate_php_file(php_file, theme_dir)

        assert len(result["errors"]) > 0
        assert any("explanatory text" in error for error in result["errors"])

    def test_validate_php_file_cannot_read(self, mock_php_available, tmp_path):
        """Test _validate_php_file when file cannot be read."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()

        # Create a file reference that doesn't exist
        php_file = theme_dir / "nonexistent.php"

        validator = ThemeValidator()
        result = validator._validate_php_file(php_file, theme_dir)

        assert len(result["errors"]) > 0
        assert any("Cannot read file" in error for error in result["errors"])

    def test_validate_php_syntax_file_valid(self, mock_php_available, tmp_path):
        """Test _validate_php_syntax_file with valid PHP file."""
        php_file = tmp_path / "valid.php"
        php_file.write_text("<?php echo 'test'; ?>")

        # Mock PHP syntax validation to succeed
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=0),  # syntax validation
        ]

        validator = ThemeValidator()
        is_valid, error_msg = validator._validate_php_syntax_file(str(php_file))

        assert is_valid is True
        assert error_msg == ""

    def test_validate_php_syntax_file_invalid(self, mock_php_available, tmp_path):
        """Test _validate_php_syntax_file with invalid PHP file."""
        php_file = tmp_path / "invalid.php"
        php_file.write_text("<?php echo 'test'")  # Missing semicolon and closing tag

        # Mock PHP syntax validation to fail
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=1, stderr="Parse error: syntax error, unexpected end of file in /path/to/file"),
        ]

        validator = ThemeValidator()
        is_valid, error_msg = validator._validate_php_syntax_file(str(php_file))

        assert is_valid is False
        assert "syntax error" in error_msg

    def test_validate_php_syntax_file_php_unavailable(self, mock_php_unavailable, tmp_path):
        """Test _validate_php_syntax_file when PHP is unavailable."""
        php_file = tmp_path / "test.php"
        php_file.write_text("<?php echo 'test'; ?>")

        validator = ThemeValidator()
        is_valid, error_msg = validator._validate_php_syntax_file(str(php_file))

        # Should return True with message when PHP is unavailable
        assert is_valid is True
        assert "PHP command not available" in error_msg

    def test_validate_strict_mode_warnings_fail(self, mock_php_available, tmp_path):
        """Test validate in strict mode where warnings cause failure."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()

        # Create required files
        (theme_dir / "style.css").write_text("/* Theme Name: Test */")
        (theme_dir / "index.php").write_text("<?php\n// Index\n")

        # Missing recommended files will create warnings
        # Mock PHP validation to succeed
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=0),  # index.php
        ]

        validator = ThemeValidator(strict=True)
        result = validator.validate(str(theme_dir))

        # In strict mode, warnings should make it invalid
        assert result["valid"] is False
        assert len(result["warnings"]) > 0

    def test_validate_counts_files_correctly(self, mock_php_available, basic_theme):
        """Test that validate correctly counts total files and PHP files."""
        # Add some non-PHP files
        (basic_theme / "readme.txt").write_text("README")
        (basic_theme / "screenshot.png").write_bytes(b"fake image")

        # Mock PHP validations
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
        ] + [Mock(returncode=0)] * 10  # Enough for all PHP files

        validator = ThemeValidator()
        result = validator.validate(str(basic_theme))

        # Should count only PHP files
        assert result["php_files"] == 4  # index, functions, header, footer
        assert result["total_files"] == 4

    def test_validate_php_file_with_doctype(self, mock_php_available, tmp_path):
        """Test _validate_php_file with DOCTYPE (valid for header.php)."""
        theme_dir = tmp_path / "theme"
        theme_dir.mkdir()

        php_file = theme_dir / "header.php"
        php_file.write_text("<!DOCTYPE html>\n<html>\n<?php wp_head(); ?>\n</html>")

        # Mock PHP validation to succeed
        mock_php_available.side_effect = [
            Mock(returncode=0, stdout="PHP 8.2.0\n"),  # __init__
            Mock(returncode=0),  # syntax check
        ]

        validator = ThemeValidator()
        result = validator._validate_php_file(php_file, theme_dir)

        # Should not complain about missing <?php tag for DOCTYPE files
        assert len(result["errors"]) == 0
