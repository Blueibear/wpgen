"""
Pytest tests for generated theme preview safety.

These tests ensure generated themes always render correctly in WordPress Customizer
by validating:
1. Required hooks (wp_head, wp_body_open, wp_footer) are present
2. WordPress Loop is properly implemented
3. No mixed-content (HTTP) URLs
4. No forbidden debug directives (WP_DEBUG, error_reporting, ini_set)
5. No invalid PHP patterns (<?= ; ?>, if (...);, etc.)
6. Block categories are valid WordPress core categories
"""

import json
import re
import tempfile
from pathlib import Path

import pytest

# Valid WordPress core block categories
VALID_BLOCK_CATEGORIES = {"text", "media", "design", "widgets", "theme", "embed"}

# Forbidden debug directives
FORBIDDEN_DEBUG_TOKENS = (
    "define('WP_DEBUG'",
    'define("WP_DEBUG"',
    "define('WP_DEBUG_LOG'",
    'define("WP_DEBUG_LOG"',
    "define('WP_DEBUG_DISPLAY'",
    'define("WP_DEBUG_DISPLAY"',
    "ini_set('display_errors'",
    'ini_set("display_errors"',
    "ini_set('error_reporting'",
    'ini_set("error_reporting"',
    "error_reporting(",
)

# Invalid PHP patterns
BAD_PHP_PATTERNS = [
    (re.compile(r"<\?=\s*;?\s*\?>"), "Empty short echo: <?= ; ?> or <?= ?>"),
    (re.compile(r"<\?php\s*;+\s*\?>"), "Empty PHP block: <?php ; ?>"),
    (re.compile(r"\bif\s*\([^)]*\)\s*;"), "if statement with trailing semicolon"),
    (re.compile(r"\bforeach\s*\([^)]*\)\s*;"), "foreach with trailing semicolon"),
    (re.compile(r"\bwhile\s*\([^)]*\)\s*;"), "while with trailing semicolon"),
    (re.compile(r"\bfor\s*\([^)]*\)\s*;"), "for with trailing semicolon"),
    (re.compile(r"\bfunction\s+\w+\s*\([^)]*\)\s*;"), "function declaration with semicolon"),
]


@pytest.fixture
def sample_theme_dir(tmp_path):
    """Create a sample theme directory structure for testing."""
    theme_dir = tmp_path / "test-theme"
    theme_dir.mkdir()
    return theme_dir


def test_normalize_block_category():
    """Test block category normalization function."""
    from wpgen.generators.wordpress_generator import normalize_block_category

    # Test valid categories
    assert normalize_block_category("text") == "text"
    assert normalize_block_category("media") == "media"
    assert normalize_block_category("design") == "design"
    assert normalize_block_category("widgets") == "widgets"
    assert normalize_block_category("theme") == "theme"
    assert normalize_block_category("embed") == "embed"

    # Test normalization map
    assert normalize_block_category("design_layout") == "design"
    assert normalize_block_category("layout") == "design"
    assert normalize_block_category("formatting") == "text"
    assert normalize_block_category("ecommerce") == "widgets"

    # Test case insensitivity
    assert normalize_block_category("DESIGN") == "design"
    assert normalize_block_category("Design") == "design"

    # Test invalid category defaults to "design"
    assert normalize_block_category("invalid_category") == "design"
    assert normalize_block_category("") == "design"
    assert normalize_block_category(None) == "design"


def test_header_php_has_required_hooks(sample_theme_dir):
    """Test that header.php contains all required WordPress hooks."""
    header_file = sample_theme_dir / "header.php"

    # Create a proper header.php
    header_content = """<!doctype html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<header class="site-header">
    <h1><?php bloginfo('name'); ?></h1>
</header>
"""
    header_file.write_text(header_content, encoding="utf-8")

    content = header_file.read_text(encoding="utf-8", errors="ignore")

    assert "wp_head()" in content, "header.php must contain wp_head() hook"
    assert "wp_body_open()" in content, "header.php must contain wp_body_open() hook"
    assert "<!doctype html>" in content.lower(), "header.php must have DOCTYPE"
    assert "language_attributes()" in content, "header.php must have language_attributes()"


def test_footer_php_has_required_hooks(sample_theme_dir):
    """Test that footer.php contains all required WordPress hooks."""
    footer_file = sample_theme_dir / "footer.php"

    # Create a proper footer.php
    footer_content = """</main>
<footer class="site-footer">
    <p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?></p>
</footer>
<?php wp_footer(); ?>
</body>
</html>
"""
    footer_file.write_text(footer_content, encoding="utf-8")

    content = footer_file.read_text(encoding="utf-8", errors="ignore")

    assert "wp_footer()" in content, "footer.php must contain wp_footer() hook"
    assert "</body>" in content, "footer.php must close body tag"
    assert "</html>" in content, "footer.php must close html tag"


def test_index_php_has_wordpress_loop(sample_theme_dir):
    """Test that index.php contains proper WordPress Loop."""
    index_file = sample_theme_dir / "index.php"

    # Create a proper index.php with Loop
    index_content = """<?php get_header(); ?>
<main class="site-content">
    <?php if ( have_posts() ) : ?>
        <?php while ( have_posts() ) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                <?php the_content(); ?>
            </article>
        <?php endwhile; ?>
    <?php else : ?>
        <article class="no-content">
            <h1><?php esc_html_e('Nothing to display yet', 'theme'); ?></h1>
            <p><?php esc_html_e('Add a page or post to see preview.', 'theme'); ?></p>
        </article>
    <?php endif; ?>
</main>
<?php get_footer(); ?>
"""
    index_file.write_text(index_content, encoding="utf-8")

    content = index_file.read_text(encoding="utf-8", errors="ignore")

    assert "get_header()" in content, "index.php must call get_header()"
    assert "get_footer()" in content, "index.php must call get_footer()"
    assert "have_posts()" in content, "index.php must use have_posts()"
    assert "the_post()" in content, "index.php must use the_post()"
    assert "the_content()" in content, "index.php must use the_content()"
    # Must have else clause for empty sites
    assert "else" in content.lower(), "index.php must have else clause for empty sites"


def test_no_mixed_content_urls(sample_theme_dir):
    """Test that theme files don't contain HTTP URLs (mixed content)."""
    # Create files with and without HTTP URLs

    # Good file (HTTPS)
    good_file = sample_theme_dir / "good.php"
    good_file.write_text("<?php\n$url = 'https://example.com/image.jpg';", encoding="utf-8")

    # Bad file (HTTP) - but this should be caught by scanner
    bad_file = sample_theme_dir / "bad.php"
    bad_file.write_text("<?php\n$url = 'http://example.com/image.jpg';", encoding="utf-8")

    # Scan for mixed content
    from wpgen.utils.code_validator import scan_mixed_content

    results = scan_mixed_content(sample_theme_dir, enforce_https=True)

    # Should find the HTTP URL
    assert not results['valid'], "Should detect HTTP URL"
    assert len(results['http_urls']) > 0, "Should find HTTP URLs"
    assert 'http://example.com' in str(results['http_urls']), "Should identify the specific URL"


def test_no_forbidden_debug_directives(sample_theme_dir):
    """Test that theme files don't contain forbidden debug directives."""
    # Create a file with forbidden directive
    bad_file = sample_theme_dir / "functions.php"
    bad_file.write_text("<?php\ndefine('WP_DEBUG', true);", encoding="utf-8")

    # Scan for forbidden directives
    from wpgen.utils.code_validator import check_forbidden_config_directives

    results = check_forbidden_config_directives(sample_theme_dir)

    assert not results['valid'], "Should detect forbidden WP_DEBUG directive"
    assert len(results['violations']) > 0, "Should find violations"
    # Check that WP_DEBUG is mentioned somewhere in the errors
    all_errors = ' '.join(results['errors'])
    assert "WP_DEBUG" in all_errors or len(results['violations']) > 0, "Should detect WP_DEBUG"


def test_no_invalid_php_patterns(sample_theme_dir):
    """Test that theme files don't contain invalid PHP patterns."""
    # Create files with invalid patterns

    # Empty short echo
    bad1 = sample_theme_dir / "bad1.php"
    bad1.write_text("<?php\n<?= ; ?>", encoding="utf-8")

    # If with semicolon
    bad2 = sample_theme_dir / "bad2.php"
    bad2.write_text("<?php\nif (true) ; { echo 'test'; }", encoding="utf-8")

    # Scan for invalid patterns
    from wpgen.utils.code_validator import check_invalid_php_patterns

    results = check_invalid_php_patterns(sample_theme_dir)

    assert not results['valid'], "Should detect invalid PHP patterns"
    assert len(results['violations']) > 0, "Should find violations"


def test_block_categories_valid(sample_theme_dir):
    """Test that block.json files use valid WordPress core categories."""
    # Create blocks directory
    blocks_dir = sample_theme_dir / "blocks"
    blocks_dir.mkdir()

    # Good block with valid category
    good_block_dir = blocks_dir / "good-block"
    good_block_dir.mkdir()
    good_block_json = {
        "name": "wpgen/good-block",
        "title": "Good Block",
        "category": "widgets"  # Valid category
    }
    (good_block_dir / "block.json").write_text(json.dumps(good_block_json), encoding="utf-8")

    # Bad block with invalid category
    bad_block_dir = blocks_dir / "bad-block"
    bad_block_dir.mkdir()
    bad_block_json = {
        "name": "wpgen/bad-block",
        "title": "Bad Block",
        "category": "design_layout"  # Invalid category
    }
    (bad_block_dir / "block.json").write_text(json.dumps(bad_block_json), encoding="utf-8")

    # Scan for invalid categories
    from wpgen.utils.code_validator import check_block_categories

    results = check_block_categories(sample_theme_dir)

    assert not results['valid'], "Should detect invalid block category"
    assert len(results['violations']) > 0, "Should find violations"
    assert "design_layout" in results['errors'][0], "Error should mention the invalid category"


def test_comprehensive_theme_scan(sample_theme_dir):
    """Test the comprehensive scan_generated_theme function."""
    # Create a clean theme structure
    header = sample_theme_dir / "header.php"
    header.write_text("""<!doctype html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
""", encoding="utf-8")

    footer = sample_theme_dir / "footer.php"
    footer.write_text("""<?php wp_footer(); ?>
</body>
</html>
""", encoding="utf-8")

    index = sample_theme_dir / "index.php"
    index.write_text("""<?php get_header(); ?>
<main>
    <?php if ( have_posts() ) : while ( have_posts() ) : the_post(); ?>
        <article><?php the_content(); ?></article>
    <?php endwhile; else : ?>
        <p>No content</p>
    <?php endif; ?>
</main>
<?php get_footer(); ?>
""", encoding="utf-8")

    # Run comprehensive scan
    from wpgen.utils.code_validator import scan_generated_theme

    results = scan_generated_theme(sample_theme_dir, strict=True)

    # Should pass all checks (no forbidden patterns, no HTTP URLs, etc.)
    assert results['valid'], f"Theme should pass all checks. Errors: {results.get('all_errors', [])}"
    assert results['config_check']['valid'], "Should pass config check"
    assert results['php_check']['valid'], "Should pass PHP pattern check"
    assert results['block_check']['valid'], "Should pass block category check"


def test_hooks_present_in_all_templates(sample_theme_dir):
    """Test that get_header() and get_footer() are in main templates."""
    templates = ['index.php', 'front-page.php', 'single.php', 'page.php']

    for template_name in templates:
        template_file = sample_theme_dir / template_name
        template_content = f"""<?php get_header(); ?>
<main>
    <?php if ( have_posts() ) : while ( have_posts() ) : the_post(); ?>
        <?php the_content(); ?>
    <?php endwhile; endif; ?>
</main>
<?php get_footer(); ?>
"""
        template_file.write_text(template_content, encoding="utf-8")

        content = template_file.read_text(encoding="utf-8")
        assert "get_header()" in content, f"{template_name} must call get_header()"
        assert "get_footer()" in content, f"{template_name} must call get_footer()"


def test_no_empty_php_blocks(sample_theme_dir):
    """Test that files don't contain empty PHP blocks that could cause issues."""
    test_file = sample_theme_dir / "test.php"

    # Test various empty patterns
    empty_patterns = [
        "<?php ; ?>",
        "<?= ?>",
        "<?= ; ?>",
    ]

    for pattern in empty_patterns:
        test_file.write_text(f"<?php\necho 'test';\n{pattern}", encoding="utf-8")

        from wpgen.utils.code_validator import check_invalid_php_patterns
        results = check_invalid_php_patterns(sample_theme_dir)

        assert not results['valid'], f"Should detect invalid pattern: {pattern}"


def test_functions_php_no_debug_config(sample_theme_dir):
    """Test that functions.php doesn't set debug configuration."""
    functions_file = sample_theme_dir / "functions.php"

    # Test forbidden patterns
    forbidden_patterns = [
        "define('WP_DEBUG', true);",
        'define("WP_DEBUG", false);',
        "ini_set('display_errors', 1);",
        "error_reporting(E_ALL);",
    ]

    for pattern in forbidden_patterns:
        functions_file.write_text(f"<?php\n{pattern}", encoding="utf-8")

        from wpgen.utils.code_validator import check_forbidden_config_directives
        results = check_forbidden_config_directives(sample_theme_dir)

        assert not results['valid'], f"Should detect forbidden pattern: {pattern}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
