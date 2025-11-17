"""
Blog Blueprint for WPGen.

Defines structure and requirements for blog and content-focused themes.
"""

from typing import Any


class BlogBlueprint:
    """Blueprint for blog and content-focused themes."""

    def __init__(self):
        """Initialize the blog blueprint."""
        self.name = "blog"
        self.display_name = "Blog / Content"
        self.description = "Professional blog theme for writers and content creators"

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
            'header.php': 'Site branding, navigation, opening <main>',
            'footer.php': 'Closing </main>, footer widgets, copyright',
            'single.php': 'Post content, author bio, navigation, comments',
            'home.php': 'Blog index with featured posts',
            'category.php': 'Category archive with description',
            'author.php': 'Author archive with bio',
        }

    def get_layout_defaults(self) -> dict[str, Any]:
        """Get default layout configuration."""
        return {
            'container_width': '1200px',
            'content_width': '800px',
            'sidebar_width': '350px',
            'sidebar_position': 'right',
            'header_layout': 'centered',
            'footer_columns': 3,
        }

    def get_color_scheme(self) -> dict[str, str]:
        """Get default color scheme."""
        return {
            'primary': '#1e40af',
            'secondary': '#7c3aed',
            'accent': '#ec4899',
            'background': '#ffffff',
            'surface': '#f9fafb',
            'text': '#111827',
            'text_light': '#6b7280',
            'border': '#e5e7eb',
        }

    def get_ux_elements(self) -> list[str]:
        """Get required UX elements."""
        return [
            'Featured posts section on homepage',
            'Post grid/list with thumbnails',
            'Author bio box',
            'Social sharing buttons',
            'Related posts section',
            'Category and tag navigation',
            'Search bar in header or sidebar',
            'Post navigation (prev/next)',
            'Comment section',
            'Newsletter signup form',
            'Breadcrumb navigation',
            'Reading time indicator',
            'Table of contents for long posts',
        ]

    def get_homepage_sections(self) -> list[dict[str, str]]:
        """Get homepage section structure."""
        return [
            {'name': 'hero', 'description': 'Featured post or welcome message', 'required': True},
            {'name': 'featured_posts', 'description': 'Highlighted recent posts', 'required': True},
            {'name': 'categories', 'description': 'Category grid or list', 'required': True},
            {'name': 'about', 'description': 'Brief author/site introduction', 'required': False},
            {'name': 'newsletter', 'description': 'Email signup form', 'required': True},
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
