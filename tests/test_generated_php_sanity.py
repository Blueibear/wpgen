"""
Test: Ensure generated themes have valid PHP (no parse errors)

Checks for invalid PHP patterns like:
- <?= ; ?> (empty short echo)
- <?php ; ?> (empty PHP block)
- if (...); { (semicolon before brace)
- foreach (...); { (semicolon before brace)
- function name(); (function declaration with semicolon)
"""

import tempfile
import shutil
import subprocess
from pathlib import Path
import pytest


def test_no_invalid_php_patterns_in_generated_theme(tmp_path):
    """Generate a theme and ensure no invalid PHP patterns exist."""
    from wpgen.generators.wordpress_generator import WordPressGenerator
    from wpgen.utils.code_validator import check_invalid_php_patterns
    from unittest.mock import MagicMock

    # Create a minimal theme configuration
    requirements = {
        "theme_name": "test-php-sanity-theme",
        "theme_display_name": "Test PHP Sanity Theme",
        "description": "Test theme to verify valid PHP",
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

        # Run the invalid PHP patterns check
        results = check_invalid_php_patterns(theme_dir)

        # Assert no violations
        assert results['valid'], \
            f"Theme contains invalid PHP patterns:\n" + \
            "\n".join(results['errors'])

        assert len(results['violations']) == 0, \
            f"Found {len(results['violations'])} violation(s): {results['violations']}"

    finally:
        # Cleanup
        if theme_dir.exists():
            shutil.rmtree(theme_dir, ignore_errors=True)


def test_invalid_php_pattern_detection():
    """Test that the checker correctly identifies invalid PHP patterns."""
    from wpgen.utils.code_validator import check_invalid_php_patterns

    # Create a temp directory with test PHP files
    with tempfile.TemporaryDirectory() as tmpdir:
        theme_dir = Path(tmpdir)

        # Create a file with invalid PHP patterns
        bad_php = """<?php
<?= ; ?>
<?php ; ?>
if ( true ); {
    echo 'bad';
}
foreach ( $items as $item ); {
    echo 'bad';
}
function bad_function(); {
    return true;
}
?>"""
        (theme_dir / "bad.php").write_text(bad_php)

        # Run check
        results = check_invalid_php_patterns(theme_dir)

        # Should find multiple violations
        assert not results['valid'], "Should have found violations"
        assert len(results['violations']) >= 5, \
            f"Expected at least 5 violations, found {len(results['violations'])}"

        # Check specific patterns are detected
        violation_patterns = [v['pattern'] for v in results['violations']]
        assert any('short echo' in p for p in violation_patterns), \
            "Should detect empty short echo"
        assert any('PHP block' in p for p in violation_patterns), \
            "Should detect empty PHP block"
        assert any('if' in p for p in violation_patterns), \
            "Should detect if with semicolon"
        assert any('foreach' in p for p in violation_patterns), \
            "Should detect foreach with semicolon"
        assert any('function' in p.lower() for p in violation_patterns), \
            "Should detect function with semicolon"


def test_php_lint_if_available(tmp_path):
    """If php command is available, run php -l on all generated files."""
    from wpgen.generators.wordpress_generator import WordPressGenerator
    from unittest.mock import MagicMock

    # Check if php is available
    php_available = shutil.which('php') is not None

    if not php_available:
        pytest.skip("php command not available - skipping lint test")

    # Create a minimal theme configuration
    requirements = {
        "theme_name": "test-php-lint-theme",
        "theme_display_name": "Test PHP Lint Theme",
        "description": "Test theme for PHP linting",
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

        # Find all PHP files
        php_files = list(theme_dir.rglob('*.php'))
        assert len(php_files) > 0, "Should have generated PHP files"

        # Run php -l on each file
        failed_files = []
        for php_file in php_files:
            try:
                result = subprocess.run(
                    ['php', '-l', str(php_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode != 0:
                    failed_files.append({
                        'file': php_file.name,
                        'output': result.stdout + result.stderr
                    })

            except Exception as e:
                failed_files.append({
                    'file': php_file.name,
                    'output': str(e)
                })

        # Assert no files failed
        if failed_files:
            error_msg = "PHP lint failed for the following files:\n"
            for failed in failed_files:
                error_msg += f"\n{failed['file']}:\n{failed['output']}\n"
            pytest.fail(error_msg)

    finally:
        # Cleanup
        if theme_dir.exists():
            shutil.rmtree(theme_dir, ignore_errors=True)


def test_good_php_patterns_not_flagged():
    """Test that valid PHP patterns are not incorrectly flagged."""
    from wpgen.utils.code_validator import check_invalid_php_patterns

    with tempfile.TemporaryDirectory() as tmpdir:
        theme_dir = Path(tmpdir)

        # Create a file with GOOD PHP patterns
        good_php = """<?php
// These are all valid and should NOT be flagged
if ( have_posts() ) {
    while ( have_posts() ) {
        the_post();
        the_content();
    }
}

foreach ( $items as $item ) {
    echo esc_html( $item );
}

function good_function() {
    return true;
}

<?php echo esc_html( $title ); ?>
?>"""
        (theme_dir / "good.php").write_text(good_php)

        # Run check
        results = check_invalid_php_patterns(theme_dir)

        # Should NOT find violations
        assert results['valid'], \
            f"Valid PHP should not be flagged. Found violations: {results['violations']}"
        assert len(results['violations']) == 0, \
            "Should not flag valid PHP patterns"
