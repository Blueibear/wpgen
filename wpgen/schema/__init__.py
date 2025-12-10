"""Theme schema module for WPGen.

This module provides the JSON schema for WordPress theme specification.
The LLM outputs JSON following this schema, which is then rendered
through Jinja2 templates to produce valid PHP files.
"""

from .theme_schema import (
    ThemeSpecification,
    ColorScheme,
    Typography,
    LayoutConfig,
    HeroSection,
    NavigationItem,
    NavigationConfig,
    WidgetArea,
    Section,
    PageConfig,
    WooCommerceConfig,
    GutenbergBlock,
    FeaturesConfig,
    get_default_theme_spec,
    validate_theme_spec,
)

__all__ = [
    "ThemeSpecification",
    "ColorScheme",
    "Typography",
    "LayoutConfig",
    "HeroSection",
    "NavigationItem",
    "NavigationConfig",
    "WidgetArea",
    "Section",
    "PageConfig",
    "WooCommerceConfig",
    "GutenbergBlock",
    "FeaturesConfig",
    "get_default_theme_spec",
    "validate_theme_spec",
]
