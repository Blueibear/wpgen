"""Comprehensive safety tests for generated WordPress themes.

This test suite generates a complete theme and validates all safety invariants:
1. No debug directives (WP_DEBUG, error_reporting, ini_set)
2. No invalid PHP patterns (<?= ; ?>, if (...);, etc.)
3. Required hooks present (wp_head, wp_body_open, wp_footer)
4. WordPress Loop properly implemented
5. No mixed-content (HTTP URLs)
6. All generated PHP files are syntactically valid

Run with: pytest tests/test_generated_php_safety.py -v
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wpgen.generators.wordpress_generator import WordPressGenerator

# Forbidden debug directives
FORBIDDEN_DEBUG = (
    "define('WP_DEBUG'",
    'define("WP_DEBUG"',
    "ini_set('display_errors'",
    'ini_set("display_errors"',
    "error_reporting(",
)

# Invalid PHP patterns
BAD_PHP = [
    re.compile(r"<\?=\s*;?\s*\?>"),  # <?= ; ?> or <?= ?>
    re.compile(r"<\?php\s*;+\s*\?>"),  # <?php ; ?>
    re.compile(r"\bif\s*\([^)]*\)\s*;"),  # if (...);
    re.compile(r"\bforeach\s*\([^)]*\)\s*;"),  # foreach (...);
    re.compile(r"\bfunction\s+\w+\s*\([^)]*\)\s*;"),  # function f();
]


@pytest.fixture
def generated_theme(tmp_path):
    """Generate a complete WordPress theme for testing."""
    requirements = {
        "theme_name": "test-safety-theme",
        "theme_display_name": "Test Safety Theme",
        "description": "A theme for comprehensive safety testing",
        "author": "Test",
        "version": "1.0.0",
        "features": {"responsive": True, "dark_mode": False, "woocommerce": False},
    }

    # Generate theme with mock LLM (use safe_mode for reliable generation)
    mock_llm = MagicMock()
    config = {
        "safe_mode": True,  # Use tested fallback templates
        "theme_prefix": "wpgen",
        "wp_version": "6.4",
        "author": "Test",
        "license": "GPL-2.0-or-later",
    }
    generator = WordPressGenerator(
        llm_provider=mock_llm, output_dir=str(tmp_path), config=config
    )

    theme_path = generator.generate(requirements)
    theme_dir = Path(theme_path)

    yield theme_dir

    # Cleanup
    if theme_dir.exists():
        shutil.rmtree(theme_dir, ignore_errors=True)


def test_no_debug_and_no_bad_php(generated_theme):
    """Test that no debug directives or bad PHP patterns exist in generated theme."""
    violations = []

    for php_file in generated_theme.rglob("*.php"):
        # Skip wp-config files (they're allowed to have WP_DEBUG)
        if php_file.name in ["wp-config-sample.php", "wp-config.php"]:
            continue

        content = php_file.read_text(encoding="utf-8", errors="ignore")
        relative_path = php_file.relative_to(generated_theme)

        # Check for forbidden debug directives
        for line_num, line in enumerate(content.splitlines(), 1):
            for token in FORBIDDEN_DEBUG:
                if token in line:
                    violations.append(
                        f"Debug directive in {relative_path}:{line_num}: {line.strip()[:80]}"
                    )

        # Check for invalid PHP patterns
        for pattern in BAD_PHP:
            match = pattern.search(content)
            if match:
                # Find line number
                line_num = content[: match.start()].count("\n") + 1
                start = content.rfind("\n", 0, match.start()) + 1
                end = content.find("\n", match.end())
                snippet = content[start : (len(content) if end == -1 else end)].strip()
                violations.append(
                    f"Invalid PHP in {relative_path}:{line_num}: {snippet[:80]}"
                )

    assert not violations, "Found safety violations:\n" + "\n".join(violations)


def test_hooks_and_loop(generated_theme):
    """Test that required WordPress hooks and loop are present."""
    # Check header.php
    header = generated_theme / "header.php"
    assert header.exists(), "header.php must exist"

    header_text = header.read_text(encoding="utf-8", errors="ignore")
    assert "wp_head()" in header_text, "header.php must contain wp_head()"
    assert "wp_body_open()" in header_text, "header.php must contain wp_body_open()"

    # Check footer.php
    footer = generated_theme / "footer.php"
    assert footer.exists(), "footer.php must exist"

    footer_text = footer.read_text(encoding="utf-8", errors="ignore")
    assert "wp_footer()" in footer_text, "footer.php must contain wp_footer()"

    # Check for WordPress loop in main templates
    front_page = generated_theme / "front-page.php"
    index_php = generated_theme / "index.php"

    # At least one should exist
    assert front_page.exists() or index_php.exists(), "Must have index.php or front-page.php"

    # Check whichever exists
    template = front_page if front_page.exists() else index_php
    template_text = template.read_text(encoding="utf-8", errors="ignore")

    # Should have WordPress loop functions
    assert "have_posts()" in template_text, f"{template.name} must use have_posts()"
    assert (
        "the_content()" in template_text or "the_excerpt()" in template_text
    ), f"{template.name} must use the_content() or the_excerpt()"


def test_no_mixed_content(generated_theme):
    """Test that generated theme has no insecure HTTP URLs."""
    violations = []

    # File extensions to check
    extensions = [".php", ".js", ".css", ".json", ".html"]

    for file_path in generated_theme.rglob("*"):
        if not file_path.is_file() or file_path.suffix not in extensions:
            continue

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        relative_path = file_path.relative_to(generated_theme)

        # Look for http:// URLs (excluding localhost and standard schemas)
        for line_num, line in enumerate(content.splitlines(), 1):
            if "http://" in line:
                # Allow localhost, 127.0.0.1, and standard schemas
                if any(
                    allowed in line
                    for allowed in [
                        "http://localhost",
                        "http://127.0.0.1",
                        "http://gmpg.org/xfn",
                        "http://www.w3.org",
                    ]
                ):
                    continue

                violations.append(
                    f"Insecure HTTP URL in {relative_path}:{line_num}: {line.strip()[:80]}"
                )

    assert not violations, "Found mixed-content violations:\n" + "\n".join(violations)


def test_php_syntax_validity(generated_theme):
    """Test that all generated PHP files are syntactically valid (if php is available)."""
    # Check if php command is available
    php_available = shutil.which("php") is not None

    if not php_available:
        pytest.skip("php command not available - skipping syntax validation")

    failures = []

    for php_file in generated_theme.rglob("*.php"):
        try:
            result = subprocess.run(
                ["php", "-l", str(php_file)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                relative_path = php_file.relative_to(generated_theme)
                failures.append(
                    f"{relative_path}:\n{result.stdout}\n{result.stderr}"
                )

        except Exception as e:
            relative_path = php_file.relative_to(generated_theme)
            failures.append(f"{relative_path}: {str(e)}")

    assert not failures, "PHP syntax errors found:\n\n" + "\n\n".join(failures)


def test_theme_structure(generated_theme):
    """Test that generated theme has the required WordPress file structure."""
    # Required files
    required_files = [
        "style.css",
        "functions.php",
        "index.php",
        "header.php",
        "footer.php",
    ]

    for filename in required_files:
        file_path = generated_theme / filename
        assert file_path.exists(), f"Required file missing: {filename}"
        assert file_path.stat().st_size > 0, f"Required file is empty: {filename}"

    # Check style.css has WordPress theme header
    style_css = generated_theme / "style.css"
    style_content = style_css.read_text()
    assert "Theme Name:" in style_content, "style.css must have 'Theme Name:' header"
    assert "Description:" in style_content, "style.css must have 'Description:' header"


def test_comprehensive_safety_scanner(generated_theme):
    """Test using the built-in comprehensive scanner."""
    from wpgen.utils.code_validator import scan_generated_theme

    # Run comprehensive scan
    results = scan_generated_theme(generated_theme, strict=True)

    # Collect all errors
    all_errors = results.get("all_errors", [])

    assert results["valid"], (
        f"Theme failed comprehensive safety scan:\n"
        + "\n".join(all_errors[:10])  # Show first 10 errors
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
