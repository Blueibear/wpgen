"""
Magazine Blueprint for WPGen.

Defines structure and requirements for magazine and news themes.
"""

from typing import Any


class MagazineBlueprint:
    """Blueprint for magazine and news themes."""

    def __init__(self):
        """Initialize the magazine blueprint."""
        self.name = "magazine"
        self.display_name = "Magazine / News"
        self.description = "Modern magazine layout for news and publications"

    def get_required_templates(self) -> list[str]:
        """Get list of required template files."""
        return [
            'style.css',
            'index.php',
            'header.php',
            'footer.php',
            'functions.php',
            'home.php',
            'front-page.php',
            'page.php',
            'single.php',
            'archive.php',
            'category.php',
            'tag.php',
            'author.php',
            'search.php',
            'sidebar.php',
            '404.php',
        ]

    def get_template_structure(self) -> dict[str, str]:
        """Get template structure requirements."""
        return {
            'header.php': 'Top bar, logo, main navigation, category menu',
            'footer.php': 'Footer widgets, newsletter, social, copyright',
            'home.php': 'Featured story, category sections, trending sidebar',
            'single.php': 'Full article with featured image, author, sharing',
            'category.php': 'Category header, featured post, article grid',
        }

    def get_layout_defaults(self) -> dict[str, Any]:
        """Get default layout configuration."""
        return {
            'container_width': '1400px',
            'content_width': '900px',
            'sidebar_width': '350px',
            'sidebar_position': 'right',
            'header_layout': 'magazine',
            'footer_columns': 4,
        }

    def get_color_scheme(self) -> dict[str, str]:
        """Get default color scheme."""
        return {
            'primary': '#dc2626',
            'secondary': '#1e40af',
            'accent': '#0891b2',
            'background': '#ffffff',
            'surface': '#f3f4f6',
            'text': '#111827',
            'text_light': '#6b7280',
            'border': '#d1d5db',
        }

    def get_ux_elements(self) -> list[str]:
        """Get required UX elements."""
        return [
            'Large featured story hero',
            'Multi-column article grid',
            'Category navigation bar',
            'Trending/popular posts widget',
            'Author bio and articles',
            'Social sharing buttons',
            'Newsletter signup prominent',
            'Advertisement placeholder areas',
            'Infinite scroll or pagination',
            'Breadcrumb navigation',
            'Reading progress bar',
            'Related articles section',
            'Breaking news ticker (optional)',
        ]

    def get_homepage_sections(self) -> list[dict[str, str]]:
        """Get homepage section structure."""
        return [
            {'name': 'featured_story', 'description': 'Hero with main story', 'required': True},
            {'name': 'category_sections', 'description': 'Sections for each category', 'required': True},
            {'name': 'trending', 'description': 'Popular/trending articles', 'required': True},
            {'name': 'video', 'description': 'Video content section', 'required': False},
            {'name': 'newsletter', 'description': 'Email subscription', 'required': True},
        ]

    def get_full_requirements(self) -> dict[str, Any]:
        """Get all blueprint requirements."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'required_templates': self.get_required_templates(),
            'template_structure': self.get_template_structure(),
            'layout_defaults': self.get_layout_defaults(),
            'color_scheme': self.get_color_scheme(),
            'ux_elements': self.get_ux_elements(),
            'homepage_sections': self.get_homepage_sections(),
        }
