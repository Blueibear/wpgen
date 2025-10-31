"""WordPress integration package for deployment and site management.

This package provides:
- WordPress REST API client for site operations
- LLM-powered natural language control of WordPress sites
- Theme deployment and activation
- Content management (pages, posts, media)
- Plugin management
"""

from .wordpress_api import WordPressAPI
from .wordpress_manager import WordPressManager

__all__ = ["WordPressAPI", "WordPressManager"]
