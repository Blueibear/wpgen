"""
Portfolio Blueprint for WPGen.

Defines structure and requirements for portfolio and showcase themes.
"""

from typing import Any


class PortfolioBlueprint:
    """Blueprint for portfolio and showcase themes."""

    def __init__(self):
        """Initialize the portfolio blueprint."""
        self.name = "portfolio"
        self.display_name = "Portfolio / Showcase"
        self.description = "Professional portfolio for creatives and agencies"

    def get_required_templates(self) -> list[str]:
        """Get list of required template files."""
        return [
            'style.css',
            'index.php',
            'header.php',
            'footer.php',
            'functions.php',
            'front-page.php',
            'page.php',
            'single.php',
            'archive.php',
            'search.php',
            '404.php',
            'page-portfolio.php',
            'single-portfolio.php',
        ]

    def get_template_structure(self) -> dict[str, str]:
        """Get template structure requirements."""
        return {
            'header.php': 'Minimal header with logo and navigation',
            'footer.php': 'Contact info, social links, copyright',
            'front-page.php': 'Hero, portfolio grid, services, about, contact',
            'single-portfolio.php': 'Project showcase with gallery and details',
            'page-portfolio.php': 'Full portfolio grid with filtering',
        }

    def get_layout_defaults(self) -> dict[str, Any]:
        """Get default layout configuration."""
        return {
            'container_width': '1400px',
            'content_width': '100%',
            'grid_columns': 3,
            'grid_gap': '40px',
            'sidebar_position': 'none',
            'header_layout': 'minimal',
            'footer_columns': 1,
        }

    def get_color_scheme(self) -> dict[str, str]:
        """Get default color scheme."""
        return {
            'primary': '#0f172a',
            'secondary': '#64748b',
            'accent': '#f59e0b',
            'background': '#ffffff',
            'surface': '#f8fafc',
            'text': '#1e293b',
            'text_light': '#94a3b8',
            'border': '#e2e8f0',
        }

    def get_ux_elements(self) -> list[str]:
        """Get required UX elements."""
        return [
            'Full-width hero with portfolio highlights',
            'Portfolio grid with hover effects',
            'Project filtering by category',
            'Lightbox/modal for project images',
            'Case study layout for detailed projects',
            'Skills and services section',
            'Client logo grid',
            'Testimonials carousel',
            'Contact form',
            'About section with profile image',
            'Social media links',
            'Smooth scroll navigation',
        ]

    def get_homepage_sections(self) -> list[dict[str, str]]:
        """Get homepage section structure."""
        return [
            {'name': 'hero', 'description': 'Bold introduction with tagline', 'required': True},
            {'name': 'portfolio', 'description': 'Featured projects grid', 'required': True},
            {'name': 'services', 'description': 'Services or skills offered', 'required': True},
            {'name': 'about', 'description': 'Brief bio and credentials', 'required': True},
            {'name': 'testimonials', 'description': 'Client testimonials', 'required': False},
            {'name': 'contact', 'description': 'Contact form and info', 'required': True},
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
