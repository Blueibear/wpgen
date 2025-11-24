"""
Test: Ensure generated themes never redefine WP_DEBUG or related directives

Themes should NEVER define:
- WP_DEBUG, WP_DEBUG_LOG, WP_DEBUG_DISPLAY
- error_reporting()
- ini_set('display_errors', ...)
- ini_set('error_reporting', ...)

These belong in wp-config.php, not theme files.
"""

import tempfile
import shutil
from pathlib import Path
import pytest


def test_no_wp_debug_in_generated_theme(tmp_path):
    """Generate a theme and ensure no WP_DEBUG redefinitions exist."""
    from wpgen.generators.wordpress_generator import WordPressGenerator
    from wpgen.utils.code_validator import check_forbidden_config_directives
    from unittest.mock import MagicMock

    # Create a minimal theme configuration
    requirements = {
        "theme_name": "test-no-debug-theme",
        "theme_display_name": "Test No Debug Theme",
        "description": "Test theme to verify no WP_DEBUG",
        "author": "Test",
        "version": "1.0.0",
        "features": {
            "responsive": True,
            "dark_mode": False,
            "woocommerce": False
        }
    }

    # Generate theme in temp directory with mock LLM
    mock_llm = MagicMock()
    generator = WordPressGenerator(llm_provider=mock_llm, output_dir=str(tmp_path))

    try:
        theme_path = generator.generate(requirements)
        theme_dir = Path(theme_path)

        # Run the forbidden config directives check
        results = check_forbidden_config_directives(theme_dir)

        # Assert no violations
        assert results['valid'], \
            f"Theme contains forbidden config directives:\n" + \
            "\n".join(results['errors'])

        assert len(results['violations']) == 0, \
            f"Found {len(results['violations'])} violation(s): {results['violations']}"

    finally:
        # Cleanup
        if theme_dir.exists():
            shutil.rmtree(theme_dir, ignore_errors=True)


def test_specific_forbidden_patterns():
    """Test that the checker correctly identifies forbidden patterns."""
    from wpgen.utils.code_validator import check_forbidden_config_directives

    # Create a temp directory with test PHP files
    with tempfile.TemporaryDirectory() as tmpdir:
        theme_dir = Path(tmpdir)

        # Create a functions.php with forbidden patterns
        bad_functions = """<?php
// This is BAD - should be caught
define( 'WP_DEBUG', true );
error_reporting( E_ALL );
ini_set( 'display_errors', 1 );
"""
        (theme_dir / "functions.php").write_text(bad_functions)

        # Run check
        results = check_forbidden_config_directives(theme_dir)

        # Should find 3 violations
        assert not results['valid'], "Should have found violations"
        assert len(results['violations']) >= 3, \
            f"Expected at least 3 violations, found {len(results['violations'])}"

        # Check specific patterns are detected
        violation_patterns = [v['pattern'] for v in results['violations']]
        assert any('WP_DEBUG' in p for p in violation_patterns), \
            "Should detect WP_DEBUG"
        assert any('error_reporting' in p for p in violation_patterns), \
            "Should detect error_reporting"
        assert any('display_errors' in p for p in violation_patterns), \
            "Should detect ini_set display_errors"


def test_wp_config_sample_is_allowed():
    """Test that wp-config-sample.php is allowed to have WP_DEBUG."""
    from wpgen.utils.code_validator import check_forbidden_config_directives

    with tempfile.TemporaryDirectory() as tmpdir:
        theme_dir = Path(tmpdir)

        # wp-config-sample.php SHOULD be allowed to have WP_DEBUG
        wp_config_sample = """<?php
define( 'WP_DEBUG', false );
define( 'WP_DEBUG_LOG', false );
"""
        (theme_dir / "wp-config-sample.php").write_text(wp_config_sample)

        # Run check
        results = check_forbidden_config_directives(theme_dir)

        # Should NOT find violations (wp-config-sample.php is exempt)
        assert results['valid'], \
            "wp-config-sample.php should be exempt from WP_DEBUG checks"
        assert len(results['violations']) == 0, \
            "Should not flag wp-config-sample.php"
