"""
Test: Ensure generated front-page.php contains proper WordPress loop

Verifies that front-page.php (and other templates) contain:
- get_header() call
- get_footer() call
- have_posts() check
- the_content() call
- Proper WordPress loop structure
"""

import tempfile
import shutil
import re
from pathlib import Path
import pytest


def test_front_page_has_required_elements(tmp_path):
    """Generate a theme and verify front-page.php has required elements."""
    from wpgen.generators.wordpress_generator import WordPressGenerator
    from unittest.mock import MagicMock

    # Create a minimal theme configuration
    requirements = {
        "theme_name": "test-front-page-theme",
        "theme_display_name": "Test Front Page Theme",
        "description": "Test theme to verify front-page.php",
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

    theme_dir = None  # Initialize to prevent UnboundLocalError
    try:
        theme_path = generator.generate(requirements)
        theme_dir = Path(theme_path)

        # Check if front-page.php exists
        front_page_file = theme_dir / "front-page.php"

        # Note: front-page.php may not always be generated
        # If it doesn't exist, check index.php instead
        if not front_page_file.exists():
            front_page_file = theme_dir / "index.php"
            assert front_page_file.exists(), \
                "Neither front-page.php nor index.php exists"

        # Read the file
        content = front_page_file.read_text(encoding='utf-8', errors='ignore')

        # Check for required elements
        assert 'get_header()' in content or 'get_header(' in content, \
            f"{front_page_file.name} must call get_header()"

        assert 'get_footer()' in content or 'get_footer(' in content, \
            f"{front_page_file.name} must call get_footer()"

        assert 'have_posts()' in content or 'have_posts(' in content, \
            f"{front_page_file.name} must check have_posts()"

        # Check for at least one of these content output methods
        has_content_output = any([
            'the_content()' in content,
            'the_content(' in content,
            'get_the_content()' in content,
        ])
        assert has_content_output, \
            f"{front_page_file.name} must output content using the_content() or similar"

    finally:
        # Cleanup
        if theme_dir and theme_dir.exists():
            shutil.rmtree(theme_dir, ignore_errors=True)


def test_fallback_front_page_structure():
    """Test that the fallback front-page.php template has proper structure."""
    from wpgen.fallback_templates import get_rich_fallback_front_page

    # Get fallback template
    theme_name = "test-theme"
    front_page_content = get_rich_fallback_front_page(theme_name)

    # Verify it's not empty
    assert len(front_page_content) > 100, \
        "Fallback front-page.php should not be empty"

    # Check for required elements
    assert 'get_header()' in front_page_content or 'get_header(' in front_page_content, \
        "Fallback front-page.php must call get_header()"

    assert 'get_footer()' in front_page_content or 'get_footer(' in front_page_content, \
        "Fallback front-page.php must call get_footer()"

    assert 'have_posts()' in front_page_content or 'have_posts(' in front_page_content, \
        "Fallback front-page.php should check have_posts() or display static content"

    # Should start with <?php tag
    assert front_page_content.strip().startswith('<?php'), \
        "Fallback front-page.php should start with <?php"

    # Should not contain invalid PHP patterns
    assert '<?= ; ?>' not in front_page_content, \
        "Fallback front-page.php should not contain empty short echo"

    assert '<?php ; ?>' not in front_page_content, \
        "Fallback front-page.php should not contain empty PHP block"


def test_index_php_has_loop(tmp_path):
    """Verify that index.php has a proper WordPress loop."""
    from wpgen.generators.wordpress_generator import WordPressGenerator
    from unittest.mock import MagicMock

    # Create a minimal theme configuration
    requirements = {
        "theme_name": "test-index-loop-theme",
        "theme_display_name": "Test Index Loop Theme",
        "description": "Test theme to verify index.php loop",
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

    theme_dir = None  # Initialize to prevent UnboundLocalError
    try:
        theme_path = generator.generate(requirements)
        theme_dir = Path(theme_path)

        # Check index.php
        index_file = theme_dir / "index.php"
        assert index_file.exists(), "index.php must exist"

        # Read the file
        content = index_file.read_text(encoding='utf-8', errors='ignore')

        # Check for WordPress loop structure
        assert 'have_posts()' in content, \
            "index.php must check have_posts()"

        # Should have either while loop or alternative content display
        has_loop_structure = any([
            'while' in content and 'the_post()' in content,
            'the_content()' in content,
            'the_excerpt()' in content,
        ])
        assert has_loop_structure, \
            "index.php must have loop structure (while/the_post or content output)"

        # Check for get_header and get_footer
        assert 'get_header()' in content or 'get_header(' in content, \
            "index.php must call get_header()"

        assert 'get_footer()' in content or 'get_footer(' in content, \
            "index.php must call get_footer()"

    finally:
        # Cleanup
        if theme_dir and theme_dir.exists():
            shutil.rmtree(theme_dir, ignore_errors=True)


def test_no_parse_errors_in_front_page():
    """Verify fallback front-page.php has no common parse error patterns."""
    from wpgen.fallback_templates import get_rich_fallback_front_page
    from wpgen.utils.code_validator import check_invalid_php_patterns
    import tempfile

    # Get fallback template
    theme_name = "test-theme"
    front_page_content = get_rich_fallback_front_page(theme_name)

    # Write to temp file and check
    with tempfile.TemporaryDirectory() as tmpdir:
        theme_dir = Path(tmpdir)
        (theme_dir / "front-page.php").write_text(front_page_content)

        # Run invalid PHP patterns check
        results = check_invalid_php_patterns(theme_dir)

        # Should have no violations
        assert results['valid'], \
            f"Fallback front-page.php contains invalid PHP patterns:\n" + \
            "\n".join(results['errors'])

        assert len(results['violations']) == 0, \
            f"Found {len(results['violations'])} violation(s) in fallback front-page.php"
