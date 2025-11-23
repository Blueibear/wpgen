"""Test generated theme structure includes required WordPress hooks."""

import tempfile
from pathlib import Path

import pytest

from wpgen.utils.code_validator import (
    get_fallback_header_php,
    get_fallback_footer_php,
    get_fallback_functions_php,
)


def test_header_has_required_hooks():
    """Test that generated header.php contains all required WordPress hooks."""
    header_content = get_fallback_header_php("test-theme")

    # Check for required hooks and attributes
    assert "<?php wp_head(); ?>" in header_content, "Missing wp_head() hook"
    assert "<?php wp_body_open(); ?>" in header_content, "Missing wp_body_open() hook"
    assert "<?php language_attributes(); ?>" in header_content, "Missing language_attributes()"
    assert "<?php body_class(); ?>" in header_content, "Missing body_class()"

    # Check for proper HTML structure
    assert "<!DOCTYPE html>" in header_content, "Missing DOCTYPE declaration"
    assert "<html" in header_content, "Missing <html> tag"
    assert "<head>" in header_content, "Missing <head> tag"
    assert "<body" in header_content, "Missing <body> tag"

    # Check for viewport meta tag (mobile-friendly)
    assert 'name="viewport"' in header_content, "Missing viewport meta tag"


def test_footer_has_required_hooks():
    """Test that generated footer.php contains all required WordPress hooks."""
    footer_content = get_fallback_footer_php("test-theme")

    # Check for required hook
    assert "<?php wp_footer(); ?>" in footer_content, "Missing wp_footer() hook"

    # Check for closing tags
    assert "</body>" in footer_content, "Missing </body> closing tag"
    assert "</html>" in footer_content, "Missing </html> closing tag"


def test_functions_has_proper_structure():
    """Test that generated functions.php has proper structure."""
    functions_content = get_fallback_functions_php("test-theme")

    # Check for setup function
    assert "function test_theme_setup()" in functions_content, "Missing theme setup function"
    assert "add_action( 'after_setup_theme', 'test_theme_setup' )" in functions_content

    # Check for enqueue function
    assert "function test_theme_scripts()" in functions_content, "Missing enqueue function"
    assert "add_action( 'wp_enqueue_scripts', 'test_theme_scripts' )" in functions_content

    # Check for editor assets function (new requirement)
    assert "function test_theme_editor_assets()" in functions_content, "Missing editor assets function"
    assert "add_action( 'enqueue_block_editor_assets', 'test_theme_editor_assets' )" in functions_content

    # Check for theme support
    assert "add_theme_support( 'title-tag' )" in functions_content
    assert "add_theme_support( 'post-thumbnails' )" in functions_content


def test_header_footer_are_paired():
    """Test that header opens tags that footer closes."""
    header_content = get_fallback_header_php("test-theme")
    footer_content = get_fallback_footer_php("test-theme")

    # Header should open main tag
    assert '<main' in header_content, "Header should open <main> tag"

    # Footer should close main tag
    assert '</main>' in footer_content, "Footer should close </main> tag"


def test_functions_uses_safe_urls():
    """Test that functions.php uses WordPress URL helpers instead of hardcoded URLs."""
    functions_content = get_fallback_functions_php("test-theme")

    # Check that it uses WordPress helpers
    assert "get_template_directory_uri()" in functions_content, "Should use get_template_directory_uri()"
    assert "get_stylesheet_uri()" in functions_content, "Should use get_stylesheet_uri()"

    # Check that it doesn't have hardcoded http:// URLs (except in comments)
    lines = functions_content.split('\n')
    code_lines = [line for line in lines if not line.strip().startswith('//') and not line.strip().startswith('*')]
    code_content = '\n'.join(code_lines)

    # Should not have http:// in actual code (only https:// is acceptable or WordPress helpers)
    assert 'http://' not in code_content, "Should not have hardcoded http:// URLs in code"


def test_enqueue_separation_documented():
    """Test that functions.php documents the separation between front-end and editor enqueues."""
    functions_content = get_fallback_functions_php("test-theme")

    # Check that editor assets function has documentation about the separation
    assert "enqueue_block_editor_assets" in functions_content, "Should reference editor hook"
    assert ("Editor scripts" in functions_content or
            "editor assets" in functions_content or
            "block editor" in functions_content), "Should document editor assets"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
