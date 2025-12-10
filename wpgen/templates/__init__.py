"""Template rendering module for WPGen.

This module provides the Jinja2-based template renderer that converts
JSON theme specifications into valid WordPress theme files.

The LLM outputs JSON, which is then rendered through these templates
to produce PHP, CSS, and JavaScript files with guaranteed valid syntax.
"""

from .renderer import (
    ThemeRenderer,
    render_theme,
    get_template_list,
)

__all__ = [
    "ThemeRenderer",
    "render_theme",
    "get_template_list",
]
