"""Test that generated themes don't contain insecure HTTP URLs (mixed-content)."""

import tempfile
from pathlib import Path

import pytest

from wpgen.utils.code_validator import scan_mixed_content, get_fallback_functions_php


def test_scan_mixed_content_utility():
    """Test that the scan_mixed_content utility function works correctly."""
    # Create a temporary theme directory with test files
    with tempfile.TemporaryDirectory() as tmp_dir:
        theme_dir = Path(tmp_dir) / "test-theme"
        theme_dir.mkdir()

        # Create a file with insecure HTTP URL
        insecure_file = theme_dir / "insecure.php"
        insecure_file.write_text(
            '<?php\n'
            'echo "Visit http://example.com";\n'
            '?>'
        )

        # Create a file with secure HTTPS URL
        secure_file = theme_dir / "secure.php"
        secure_file.write_text(
            '<?php\n'
            'echo "Visit https://example.com";\n'
            '?>'
        )

        # Scan for mixed content
        results = scan_mixed_content(theme_dir, enforce_https=True)

        # Should find the insecure URL
        assert not results['valid'], "Should detect insecure HTTP URL"
        assert len(results['http_urls']) == 1, "Should find exactly one HTTP URL"
        assert results['http_urls'][0]['file'] == 'insecure.php'
        assert 'http://example.com' in results['http_urls'][0]['url']


def test_scan_allows_localhost():
    """Test that scan_mixed_content allows localhost URLs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        theme_dir = Path(tmp_dir) / "test-theme"
        theme_dir.mkdir()

        # Create a file with localhost URL (allowed for development)
        localhost_file = theme_dir / "dev.php"
        localhost_file.write_text(
            '<?php\n'
            'echo "Dev server: http://localhost:3000";\n'
            '?>'
        )

        # Scan for mixed content
        results = scan_mixed_content(theme_dir, enforce_https=True)

        # Should NOT flag localhost URLs
        assert results['valid'], "Should allow localhost URLs"
        assert len(results['http_urls']) == 0, "Localhost should not be flagged"


def test_scan_allows_standard_schemas():
    """Test that scan_mixed_content allows standard HTTP schemas (W3C, XFN, etc.)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        theme_dir = Path(tmp_dir) / "test-theme"
        theme_dir.mkdir()

        # Create header with standard schemas
        header_file = theme_dir / "header.php"
        header_file.write_text(
            '<!DOCTYPE html>\n'
            '<html>\n'
            '<head>\n'
            '  <link rel="profile" href="http://gmpg.org/xfn/11">\n'
            '</head>\n'
            '</html>'
        )

        # Scan for mixed content
        results = scan_mixed_content(theme_dir, enforce_https=True)

        # Should NOT flag standard schemas
        assert results['valid'], "Should allow standard HTTP schemas"
        assert len(results['http_urls']) == 0, "Standard schemas should not be flagged"


def test_fallback_templates_have_no_mixed_content():
    """Test that our fallback templates don't have mixed-content issues."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        theme_dir = Path(tmp_dir) / "test-theme"
        theme_dir.mkdir()

        # Write fallback functions.php
        functions_content = get_fallback_functions_php("test-theme")
        (theme_dir / "functions.php").write_text(functions_content)

        # Scan for mixed content
        results = scan_mixed_content(theme_dir, enforce_https=True)

        # Should pass (no insecure HTTP URLs)
        if not results['valid']:
            print("\nFound mixed-content issues:")
            for item in results['http_urls']:
                print(f"  {item['file']}:{item['line']} → {item['url']}")

        assert results['valid'], "Fallback templates should not have mixed-content issues"


def test_mixed_content_scanner_checks_multiple_extensions():
    """Test that scanner checks PHP, JS, CSS, JSON files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        theme_dir = Path(tmp_dir) / "test-theme"
        theme_dir.mkdir()

        # Create files with different extensions, all with HTTP URLs
        test_files = {
            'test.php': '<?php echo "http://insecure.com"; ?>',
            'test.js': 'const url = "http://insecure.com";',
            'test.css': '/* background: url(http://insecure.com/bg.png); */',
            'test.json': '{"url": "http://insecure.com"}',
        }

        for filename, content in test_files.items():
            (theme_dir / filename).write_text(content)

        # Scan for mixed content
        results = scan_mixed_content(theme_dir, enforce_https=True)

        # Should find HTTP URLs in all file types
        assert not results['valid'], "Should detect HTTP URLs in multiple file types"
        # We should find at least 3 (CSS comment might be skipped depending on regex)
        assert len(results['http_urls']) >= 3, f"Should find HTTP URLs in multiple files, found {len(results['http_urls'])}"


def test_scan_provides_helpful_error_messages():
    """Test that scan results include helpful context for fixing issues."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        theme_dir = Path(tmp_dir) / "test-theme"
        theme_dir.mkdir()

        # Create a file with insecure HTTP URL
        (theme_dir / "bad.php").write_text('<?php echo "http://example.com"; ?>')

        # Scan for mixed content
        results = scan_mixed_content(theme_dir, enforce_https=True)

        # Should provide helpful error messages
        assert len(results['errors']) > 0, "Should provide error messages"
        error_text = '\n'.join(results['errors'])

        # Check for helpful guidance
        assert 'http://' in error_text.lower() or 'insecure' in error_text.lower()
        assert 'bad.php' in error_text, "Should mention the problematic file"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
