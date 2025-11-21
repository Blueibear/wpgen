"""Tests for fallback template generation to prevent WordPress crashes."""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from wpgen.utils.code_validator import (
    clean_generated_code,
    get_fallback_functions_php,
    get_fallback_template,
    validate_theme_for_wordpress_safety,
)


class TestFallbackTemplates:
    """Test suite for fallback template generation."""

    def test_fallback_functions_php_generates_valid_syntax(self):
        """Test that fallback functions.php has valid PHP syntax."""
        php_code = get_fallback_functions_php("test-theme")

        # Verify no Python expressions remain in the output
        assert "{theme_name.replace" not in php_code, "Python expression not evaluated!"
        assert ".replace(" not in php_code, "Python code leaked into PHP!"

        # Verify function names use underscores (valid PHP)
        assert "function test_theme_setup()" in php_code
        assert "function test_theme_scripts()" in php_code
        assert "function test_theme_widgets_init()" in php_code

        # Verify action hooks match function names
        assert "'after_setup_theme', 'test_theme_setup'" in php_code
        assert "'wp_enqueue_scripts', 'test_theme_scripts'" in php_code
        assert "'widgets_init', 'test_theme_widgets_init'" in php_code

    def test_fallback_functions_php_with_hyphenated_theme_name(self):
        """Test that hyphenated theme names are converted to underscores."""
        php_code = get_fallback_functions_php("my-cool-theme")

        # Verify hyphens converted to underscores in function names
        assert "function my_cool_theme_setup()" in php_code
        assert "function my_cool_theme_scripts()" in php_code
        assert "function my_cool_theme_widgets_init()" in php_code

        # Verify no invalid PHP function names with hyphens
        assert "function my-cool-theme" not in php_code

    def test_fallback_functions_php_syntax_is_valid(self):
        """Test that generated PHP passes php -l syntax check."""
        php_code = get_fallback_functions_php("test-theme")

        # Write to temp file and validate with PHP
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(php_code)
            temp_path = f.name

        try:
            # Try to validate with php -l
            try:
                result = subprocess.run(
                    ["php", "-l", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    # PHP validation passed
                    assert True
                else:
                    pytest.fail(f"PHP syntax check failed: {result.stderr}")

            except FileNotFoundError:
                # PHP not available, skip validation
                pytest.skip("PHP binary not available for validation")
        finally:
            Path(temp_path).unlink()

    def test_fallback_functions_php_has_required_wordpress_hooks(self):
        """Test that fallback has essential WordPress hooks."""
        php_code = get_fallback_functions_php("test-theme")

        # Check for essential WordPress setup
        assert "add_theme_support( 'title-tag' )" in php_code
        assert "add_theme_support( 'post-thumbnails' )" in php_code
        assert "register_nav_menus" in php_code
        assert "register_sidebar" in php_code

        # Check for asset enqueuing
        assert "wp_enqueue_style" in php_code
        assert "wp_enqueue_script" in php_code

    def test_fallback_functions_php_has_wpgen_ui_assets(self):
        """Test that fallback enqueues wpgen-ui assets."""
        php_code = get_fallback_functions_php("test-theme")

        # Verify wpgen-ui CSS and JS are enqueued
        assert "wpgen-ui.css" in php_code
        assert "wpgen-ui.js" in php_code
        assert "wp_enqueue_style( 'wpgen-ui'" in php_code
        assert "wp_enqueue_script( 'wpgen-ui'" in php_code

    def test_fallback_functions_php_has_abspath_check(self):
        """Test that fallback has security check for direct access."""
        php_code = get_fallback_functions_php("test-theme")

        # Verify ABSPATH security check
        assert "if ( ! defined( 'ABSPATH' ) )" in php_code
        assert "exit;" in php_code

    def test_fallback_template_single_php(self):
        """Test that single.php fallback is valid."""
        php_code = get_fallback_template("single.php", "test-theme")

        assert php_code, "single.php template should not be empty"
        assert "<?php" in php_code
        assert "get_header()" in php_code
        assert "get_footer()" in php_code
        assert "have_posts()" in php_code
        assert "the_post()" in php_code

    def test_fallback_template_page_php(self):
        """Test that page.php fallback is valid."""
        php_code = get_fallback_template("page.php", "test-theme")

        assert php_code, "page.php template should not be empty"
        assert "<?php" in php_code
        assert "get_header()" in php_code
        assert "get_footer()" in php_code
        assert "the_content()" in php_code

    def test_fallback_template_archive_php(self):
        """Test that archive.php fallback is valid."""
        php_code = get_fallback_template("archive.php", "test-theme")

        assert php_code, "archive.php template should not be empty"
        assert "get_header()" in php_code
        assert "get_footer()" in php_code
        assert "the_archive_title" in php_code
        assert "the_posts_pagination" in php_code

    def test_fallback_template_404_php(self):
        """Test that 404.php fallback is valid."""
        php_code = get_fallback_template("404.php", "test-theme")

        assert php_code, "404.php template should not be empty"
        assert "get_header()" in php_code
        assert "get_footer()" in php_code
        assert "Page Not Found" in php_code

    def test_fallback_template_sidebar_php(self):
        """Test that sidebar.php fallback is valid."""
        php_code = get_fallback_template("sidebar.php", "test-theme")

        assert php_code, "sidebar.php template should not be empty"
        assert "is_active_sidebar" in php_code
        assert "dynamic_sidebar" in php_code
        assert "sidebar-1" in php_code

    def test_fallback_template_returns_empty_for_unknown(self):
        """Test that unknown templates return empty string."""
        php_code = get_fallback_template("unknown-template.php", "test-theme")
        assert php_code == ""

    def test_no_python_expressions_in_any_fallback(self):
        """Test that no fallback contains unevaluated Python expressions."""
        theme_name = "test-theme"

        # Test functions.php for Python-specific patterns
        functions_php = get_fallback_functions_php(theme_name)

        # Check for unevaluated Python expressions (not valid PHP)
        assert ".replace(" not in functions_php, "Python .replace() found in PHP"
        assert "{theme_name" not in functions_php, "Unevaluated {theme_name} variable"

        # Verify function names are valid (underscores, not hyphens)
        assert "function test_theme_" in functions_php, "Function names should use underscores"
        assert "function test-theme" not in functions_php, "Function names should not have hyphens"

        # Test all template files
        templates = ["single.php", "page.php", "archive.php", "search.php", "404.php", "sidebar.php"]
        for template_name in templates:
            template_code = get_fallback_template(template_name, theme_name)
            if template_code:
                # Check for Python-specific patterns that shouldn't be in PHP
                assert ".replace(" not in template_code, f"Python code in {template_name}"
                assert "{theme_name" not in template_code or "'{theme_name}'" in template_code, \
                    f"Unevaluated variable in {template_name}"


class TestWordPressSafetyValidation:
    """Test suite for comprehensive WordPress safety validation."""

    @pytest.fixture
    def safe_theme(self, tmp_path):
        """Create a safe, minimal WordPress theme."""
        theme_dir = tmp_path / "safe-theme"
        theme_dir.mkdir()

        # Create required files
        (theme_dir / "style.css").write_text("/* Theme Name: Test Theme */")
        (theme_dir / "index.php").write_text("<?php\nget_header();\nget_footer();")
        (theme_dir / "functions.php").write_text(get_fallback_functions_php("test-theme"))
        (theme_dir / "header.php").write_text("""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head><meta charset="<?php bloginfo( 'charset' ); ?>"><?php wp_head(); ?></head>
<body <?php body_class(); ?>>
<header class="site-header">
<div class="site-branding"><?php the_custom_logo(); ?></div>
<nav class="main-navigation"></nav>
</header>
<main id="content">""")
        (theme_dir / "footer.php").write_text("""</main>
<footer class="site-footer"></footer>
<?php wp_footer(); ?>
</body></html>""")

        # Create assets/css/style.css
        assets_css_dir = theme_dir / "assets" / "css"
        assets_css_dir.mkdir(parents=True)
        (assets_css_dir / "style.css").write_text("/* Base Layout */\n.site-header {}\n.site-branding img {}")

        return theme_dir

    @pytest.fixture
    def unsafe_theme_python_expr(self, tmp_path):
        """Create an unsafe theme with unevaluated Python expressions."""
        theme_dir = tmp_path / "unsafe-theme"
        theme_dir.mkdir()

        (theme_dir / "style.css").write_text("/* Theme Name: Test */")
        (theme_dir / "index.php").write_text("<?php\nget_header();\nget_footer();")
        # This is the bug that was causing crashes!
        (theme_dir / "functions.php").write_text(
            "<?php\nfunction {theme_name.replace('-', '_')}_setup() {\n}\n"
        )

        return theme_dir

    @pytest.fixture
    def unsafe_theme_markdown(self, tmp_path):
        """Create an unsafe theme with markdown code fences."""
        theme_dir = tmp_path / "unsafe-theme-md"
        theme_dir.mkdir()

        (theme_dir / "style.css").write_text("/* Theme Name: Test */")
        (theme_dir / "index.php").write_text("```php\n<?php\nget_header();\n```")

        return theme_dir

    def test_validate_safe_theme(self, safe_theme):
        """Test that a safe theme passes validation."""
        is_safe, issues = validate_theme_for_wordpress_safety(safe_theme)

        assert is_safe, f"Safe theme should pass validation. Issues: {issues}"
        assert len(issues) == 0

    def test_validate_unsafe_theme_python_expressions(self, unsafe_theme_python_expr):
        """Test that themes with Python expressions are caught."""
        is_safe, issues = validate_theme_for_wordpress_safety(unsafe_theme_python_expr)

        assert not is_safe, "Theme with Python expressions should fail validation"
        assert len(issues) > 0
        assert any("Python expression" in issue for issue in issues)

    def test_validate_unsafe_theme_markdown(self, unsafe_theme_markdown):
        """Test that themes with markdown are caught."""
        is_safe, issues = validate_theme_for_wordpress_safety(unsafe_theme_markdown)

        assert not is_safe, "Theme with markdown should fail validation"
        assert any("markdown" in issue.lower() for issue in issues)

    def test_validate_theme_missing_required_files(self, tmp_path):
        """Test that themes missing required files are caught."""
        theme_dir = tmp_path / "incomplete-theme"
        theme_dir.mkdir()

        # Only create style.css, missing index.php
        (theme_dir / "style.css").write_text("/* Theme Name: Test */")

        is_safe, issues = validate_theme_for_wordpress_safety(theme_dir)

        assert not is_safe
        assert any("index.php" in issue for issue in issues)

    def test_clean_generated_code_removes_markdown(self):
        """Test that clean_generated_code removes markdown fences."""
        code_with_markdown = "```php\n<?php\necho 'test';\n```"
        cleaned = clean_generated_code(code_with_markdown, "php")

        assert "```" not in cleaned
        assert "<?php" in cleaned
        assert "echo 'test';" in cleaned

    def test_clean_generated_code_detects_python_expressions(self):
        """Test that clean_generated_code detects unevaluated Python expressions."""
        code_with_python = "<?php\nfunction {theme_name.replace('-', '_')}_setup() {}"

        with pytest.raises(ValueError, match="unevaluated Python expressions"):
            clean_generated_code(code_with_python, "php")

    def test_clean_generated_code_removes_explanatory_text(self):
        """Test that explanatory text is removed."""
        code_with_text = "Here's the code for your theme:\n<?php\necho 'test';"
        cleaned = clean_generated_code(code_with_text, "php")

        assert "Here's" not in cleaned
        assert cleaned.startswith("<?php")

    def test_clean_generated_code_handles_doctype(self):
        """Test that <!DOCTYPE is preserved for header files."""
        code_with_doctype = "Some text\n<!DOCTYPE html>\n<html>"
        cleaned = clean_generated_code(code_with_doctype, "php")

        assert cleaned.startswith("<!DOCTYPE")
        assert "Some text" not in cleaned
