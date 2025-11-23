"""Test that generated templates include the WordPress Loop."""

from wpgen.fallback_templates import get_rich_fallback_index
from wpgen.utils.code_validator import get_fallback_template


def test_index_has_wordpress_loop():
    """Test that index.php contains the WordPress Loop."""
    index_content = get_rich_fallback_index("test-theme")

    # Check for Loop structure
    assert "have_posts()" in index_content, "index.php must call have_posts()"
    assert "the_post()" in index_content, "index.php must call the_post()"
    assert "get_header()" in index_content, "index.php must call get_header()"
    assert "get_footer()" in index_content, "index.php must call get_footer()"


def test_index_has_fallback_content():
    """Test that index.php has fallback content for empty sites."""
    index_content = get_rich_fallback_index("test-theme")

    # Check for else clause with fallback content
    assert "else" in index_content, "index.php should have else clause for empty sites"
    # Should have some visible fallback content
    content_lower = index_content.lower()
    has_fallback = ("no" in content_lower and "content" in content_lower) or \
                   "nothing" in content_lower or \
                   "not found" in content_lower

    assert has_fallback, "index.php should have fallback content for Customizer preview"


def test_single_has_wordpress_loop():
    """Test that single.php contains the WordPress Loop."""
    single_content = get_fallback_template("single.php", "test-theme")

    if single_content:  # Only test if template exists
        assert "have_posts()" in single_content, "single.php must call have_posts()"
        assert "the_post()" in single_content, "single.php must call the_post()"
        assert "the_content()" in single_content, "single.php must call the_content()"


def test_page_has_wordpress_loop():
    """Test that page.php contains the WordPress Loop."""
    page_content = get_fallback_template("page.php", "test-theme")

    if page_content:  # Only test if template exists
        assert "have_posts()" in page_content, "page.php must call have_posts()"
        assert "the_post()" in page_content, "page.php must call the_post()"
        assert "the_content()" in page_content, "page.php must call the_content()"


def test_archive_has_wordpress_loop():
    """Test that archive.php contains the WordPress Loop."""
    archive_content = get_fallback_template("archive.php", "test-theme")

    if archive_content:  # Only test if template exists
        assert "have_posts()" in archive_content, "archive.php must call have_posts()"
        assert "the_post()" in archive_content, "archive.php must call the_post()"


def test_templates_dont_use_invalid_functions():
    """Test that templates don't use undefined functions like post_loop()."""
    templates = [
        ("index.php", get_rich_fallback_index("test-theme")),
        ("single.php", get_fallback_template("single.php", "test-theme")),
        ("page.php", get_fallback_template("page.php", "test-theme")),
        ("archive.php", get_fallback_template("archive.php", "test-theme")),
    ]

    for name, content in templates:
        if content:  # Only test if template exists
            assert "post_loop()" not in content, \
                f"{name} should not use undefined post_loop() function"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
