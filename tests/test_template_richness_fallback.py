"""Ensure generated templates fall back to rich variants when too minimal."""

from unittest.mock import MagicMock

from wpgen.fallback_templates import get_rich_fallback_archive, get_rich_fallback_front_page
from wpgen.generators.wordpress_generator import WordPressGenerator


def _base_requirements() -> dict:
    return {
        "theme_name": "richness-test-theme",
        "theme_display_name": "Richness Test Theme",
        "description": "Test theme for richness fallback behavior",
        "author": "Test",
        "version": "1.0.0",
        "features": {
            "responsive": True,
            "dark_mode": False,
            "woocommerce": False,
        },
    }


def test_front_page_falls_back_when_rich_sections_missing(tmp_path, caplog):
    """Front page should use the rich fallback when hero/grid/CTA are absent."""

    minimal_loop = (
        "<?php get_header(); ?>\n"
        "<?php if ( have_posts() ) : while ( have_posts() ) : the_post(); ?>\n"
        "<?php the_content(); ?>\n"
        "<?php endwhile; endif; ?>\n"
        "<?php get_footer(); ?>"
    )

    mock_llm = MagicMock()
    mock_llm.generate_code.return_value = minimal_loop

    generator = WordPressGenerator(llm_provider=mock_llm, output_dir=str(tmp_path))

    caplog.set_level("WARNING")
    theme_dir = tmp_path / _base_requirements()["theme_name"]
    theme_dir.mkdir()

    generator._generate_templates(theme_dir, _base_requirements())

    front_page_content = (theme_dir / "front-page.php").read_text(encoding="utf-8")
    fallback_content = get_rich_fallback_front_page("richness-test-theme")

    assert "hero-section" in front_page_content
    assert "products-section" in front_page_content
    assert front_page_content.count("hero-section") == fallback_content.count("hero-section")
    assert any("missing required sections" in message for message in caplog.messages)


def test_archive_falls_back_when_grid_missing(tmp_path, caplog):
    """Archive template should default to the rich fallback when grid/pagination are absent."""

    bare_archive = (
        "<?php get_header(); ?>\n"
        "<?php if ( have_posts() ) : while ( have_posts() ) : the_post(); ?>\n"
        "<article><h1><?php the_title(); ?></h1></article>\n"
        "<?php endwhile; endif; ?>\n"
        "<?php get_footer(); ?>"
    )

    mock_llm = MagicMock()
    mock_llm.generate_code.return_value = bare_archive

    generator = WordPressGenerator(llm_provider=mock_llm, output_dir=str(tmp_path))

    caplog.set_level("WARNING")
    theme_dir = tmp_path / _base_requirements()["theme_name"]
    theme_dir.mkdir()

    generator._generate_templates(theme_dir, _base_requirements())

    archive_content = (theme_dir / "archive.php").read_text(encoding="utf-8")
    fallback_content = get_rich_fallback_archive("richness-test-theme")

    assert "archive-grid" in archive_content
    assert "the_posts_pagination" in archive_content or "the_posts_navigation" in archive_content
    assert archive_content.count("archive-grid") == fallback_content.count("archive-grid")
    assert any("missing rich layout elements" in message for message in caplog.messages)
