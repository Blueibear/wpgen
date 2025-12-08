"""Test footer.php backslash sanitization and PHP validation.

This test file validates the fix for the recurring PHP validation error:
"PHP syntax error - unexpected token '\\'" in footer.php.

Tests cover:
1. remove_stray_backslashes() function enhancement
2. sanitize_footer_php() function for common LLM errors
3. Full validation pipeline for footer.php with problematic content
4. PHP -l validation of the cleaned output
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

from wpgen.utils.php_validation import remove_stray_backslashes, validate_and_fix_php
from wpgen.utils.code_validator import sanitize_footer_php


class TestBackslashSanitization:
    """Test backslash removal and sanitization functions."""

    def test_remove_escaped_single_quotes(self):
        """Test that \' is converted to ' in PHP code."""
        # Common LLM error: date(\'Y\')
        code_with_backslashes = "<?php echo date(\\'Y\\'); ?>"
        cleaned_code, removed = remove_stray_backslashes(code_with_backslashes)

        # Should remove 2 backslashes
        assert removed == 2
        # Should result in valid PHP
        assert cleaned_code == "<?php echo date('Y'); ?>"

    def test_remove_escaped_double_quotes(self):
        """Test that \" is converted to \" in PHP code."""
        code_with_backslashes = '<?php echo bloginfo(\\"name\\"); ?>'
        cleaned_code, removed = remove_stray_backslashes(code_with_backslashes)

        # Should remove 2 backslashes
        assert removed == 2
        # Should result in valid PHP
        assert cleaned_code == '<?php echo bloginfo("name"); ?>'

    def test_remove_multiple_backslash_patterns(self):
        """Test removal of various backslash patterns."""
        code_with_backslashes = """<?php
        echo date(\\'Y\\');
        bloginfo(\\'name\\');
        $var = "test\\<div\\>";
        ?>"""

        cleaned_code, removed = remove_stray_backslashes(code_with_backslashes)

        # Should remove all backslashes
        assert removed > 0
        # Should not contain \' or \" patterns
        assert "\\'" not in cleaned_code
        assert '\\"' not in cleaned_code
        # Should not contain \< or \> patterns
        assert "\\<" not in cleaned_code
        assert "\\>" not in cleaned_code

    def test_copyright_line_sanitization(self):
        """Test sanitization of common footer copyright line patterns."""
        # This is the exact pattern mentioned in the issue
        problematic_footer = """
        <footer class="site-footer">
            <div class="site-info">
                <p>&copy; <?php echo date(\\'Y\\'); ?> <?php bloginfo(\\'name\\'); ?>. All rights reserved.</p>
            </div>
        </footer>
        <?php wp_footer(); ?>
        </body>
        </html>
        """

        cleaned_code, removed = remove_stray_backslashes(problematic_footer)

        # Should clean the code
        assert removed >= 4  # At least 4 backslashes (2 in date, 2 in bloginfo)
        # Should result in valid PHP syntax
        assert "date('Y')" in cleaned_code
        assert "bloginfo('name')" in cleaned_code
        # Should not have escaped quotes
        assert "\\'" not in cleaned_code


class TestFooterSanitization:
    """Test footer-specific sanitization function."""

    def test_sanitize_footer_date_and_bloginfo(self):
        """Test that sanitize_footer_php normalizes date() and bloginfo() calls."""
        footer_with_escapes = """
        <footer>
            <p>&copy; <?php echo date(\\'Y\\'); ?> <?php bloginfo(\\'name\\'); ?></p>
        </footer>
        """

        cleaned_footer, cleanups = sanitize_footer_php(footer_with_escapes)

        # Should report cleanups
        assert len(cleanups) > 0
        # Should normalize to correct syntax
        assert "date('Y')" in cleaned_footer
        assert "bloginfo('name')" in cleaned_footer
        # Should not have backslashes
        assert "\\'" not in cleaned_footer

    def test_sanitize_footer_handles_duplicate_footers(self):
        """Test that multiple <footer> sections are deduplicated."""
        footer_with_duplicates = """
        <footer class="site-footer">
            <p>Footer 1</p>
        </footer>
        <footer class="site-footer">
            <p>Footer 2 (duplicate)</p>
        </footer>
        """

        cleaned_footer, cleanups = sanitize_footer_php(footer_with_duplicates)

        # Should report deduplication
        assert any("duplicate" in cleanup.lower() for cleanup in cleanups)
        # Should only have one <footer> tag
        assert cleaned_footer.count("<footer") == 1

    def test_sanitize_footer_ensures_closing_tags(self):
        """Test that missing </body> and </html> tags are added."""
        footer_without_closing_tags = """
        <footer class="site-footer">
            <p>&copy; 2024 My Site</p>
        </footer>
        <?php wp_footer(); ?>
        """

        cleaned_footer, cleanups = sanitize_footer_php(footer_without_closing_tags)

        # Should report additions
        assert len(cleanups) > 0
        # Should have closing tags
        assert "</body>" in cleaned_footer
        assert "</html>" in cleaned_footer


class TestFullValidationPipeline:
    """Test the complete validation pipeline with problematic footer content."""

    def test_validate_and_fix_footer_with_backslashes(self):
        """Test that validate_and_fix_php cleans footer with backslashes."""
        problematic_footer = """<!DOCTYPE html>
<html>
<body>
<footer class="site-footer">
    <div class="site-info container">
        <p class="copyright">
            &copy; <?php echo date(\\'Y\\'); ?> <?php bloginfo(\\'name\\'); ?>. All rights reserved.
        </p>
    </div>
</footer>
<?php wp_footer(); ?>
</body>
</html>"""

        # Run through validation pipeline with auto_fix=True
        fixed_code, is_valid, issues = validate_and_fix_php(
            problematic_footer,
            file_type='footer',
            filename='footer.php',
            auto_fix=True
        )

        # Should be valid after fixes
        assert is_valid, f"Validation failed with issues: {issues}"
        # Should report backslash removal
        assert any("backslash" in str(issue).lower() for issue in issues)
        # Should have correct syntax
        assert "date('Y')" in fixed_code
        assert "bloginfo('name')" in fixed_code
        # Should not have escaped quotes
        assert "\\'" not in fixed_code

    @pytest.mark.skipif(
        subprocess.run(['php', '--version'], capture_output=True).returncode != 0,
        reason="PHP CLI not available"
    )
    def test_php_cli_validates_cleaned_footer(self):
        """Test that PHP -l accepts the cleaned footer code."""
        # Start with problematic footer
        problematic_footer = """<!DOCTYPE html>
<html>
<body>
<footer class="site-footer">
    <p>&copy; <?php echo date(\\'Y\\'); ?> <?php bloginfo(\\'name\\'); ?>. All rights reserved.</p>
</footer>
<?php wp_footer(); ?>
</body>
</html>"""

        # Clean it
        fixed_code, is_valid, issues = validate_and_fix_php(
            problematic_footer,
            file_type='footer',
            filename='footer.php',
            auto_fix=True
        )

        # Should be valid
        assert is_valid

        # Verify with actual PHP -l
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(fixed_code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ['php', '-l', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Should pass PHP validation
            assert result.returncode == 0, f"PHP -l failed: {result.stderr}"
        finally:
            Path(temp_path).unlink()


class TestRegressionPrevention:
    """Test that the fixes prevent the specific error mentioned in the issue."""

    def test_no_unexpected_token_backslash_error(self):
        """Test that the exact error 'unexpected token \"\\\"' does not occur."""
        # This is the exact pattern that was causing the error
        footer_code = """
        <footer class="site-footer">
            <div class="site-info">
                <p>&copy; <?php echo date(\\'Y\\'); ?> <?php bloginfo(\\'name\\'); ?>. All rights reserved.</p>
            </div>
        </footer>
        <?php wp_footer(); ?>
        </body>
        </html>
        """

        # First sanitize with remove_stray_backslashes
        cleaned_code, _ = remove_stray_backslashes(footer_code)

        # Should not contain the problematic pattern
        assert "\\'" not in cleaned_code

        # If PHP is available, verify it validates
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
                f.write(cleaned_code)
                temp_path = f.name

            result = subprocess.run(
                ['php', '-l', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            Path(temp_path).unlink()

            # Should not have "unexpected token" error
            if result.returncode != 0:
                error_output = result.stderr + result.stdout
                assert 'unexpected token "\\"' not in error_output.lower()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # PHP not available, skip this check
            pytest.skip("PHP CLI not available")

    def test_remove_stray_backslashes_is_called_in_pipeline(self):
        """Verify that remove_stray_backslashes is actually invoked during validation."""
        code_with_backslashes = "<?php echo date(\\'Y\\'); ?>"

        # Validate with auto_fix
        fixed_code, is_valid, issues = validate_and_fix_php(
            code_with_backslashes,
            file_type='template',
            filename='test.php',
            auto_fix=True
        )

        # Should report backslash removal
        assert any("backslash" in str(issue).lower() for issue in issues), \
            f"Expected backslash removal to be reported in issues: {issues}"

        # Should be cleaned
        assert "\\'" not in fixed_code
