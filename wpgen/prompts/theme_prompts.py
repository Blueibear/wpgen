"""LLM prompts for JSON-only theme specification output.

This module provides prompts that instruct the LLM to output ONLY valid JSON
following the ThemeSpecification schema. The LLM never outputs PHP, CSS, or
JavaScript code directly.

The JSON is then rendered through Jinja2 templates to produce valid WordPress
theme files, guaranteeing no syntax errors or hallucinated functions.
"""

import json
import re
from typing import Any

from ..design_inspiration import (
    get_ecommerce_best_practices,
    get_inspiration_context,
    get_modern_design_trends,
)
from ..schema import ThemeSpecification, get_default_theme_spec, validate_theme_spec
from ..utils.logger import get_logger

logger = get_logger(__name__)


# JSON Schema description for the LLM
SCHEMA_DESCRIPTION = """
## Theme Specification JSON Schema

You MUST output valid JSON following this exact schema:

```json
{
  "theme_name": "string (lowercase, hyphens only, e.g., 'my-awesome-theme')",
  "theme_display_name": "string (display name, e.g., 'My Awesome Theme')",
  "description": "string (theme description)",
  "version": "string (default: '1.0.0')",
  "author": "string (default: 'WPGen')",
  "author_uri": "string (author website URL)",
  "theme_uri": "string (theme website URL)",

  "colors": {
    "primary": "#hex (brand color)",
    "secondary": "#hex (secondary color)",
    "accent": "#hex (accent/highlight color)",
    "background": "#hex (page background)",
    "surface": "#hex (card/surface background)",
    "text_primary": "#hex (main text color)",
    "text_secondary": "#hex (secondary text)",
    "text_muted": "#hex (muted/subtle text)",
    "border": "#hex (border color)",
    "success": "#hex (success state)",
    "warning": "#hex (warning state)",
    "error": "#hex (error state)"
  },

  "typography": {
    "font_primary": "string (e.g., 'Inter', 'Roboto')",
    "font_headings": "string (headings font)",
    "font_mono": "string (monospace font)",
    "base_size": "string (e.g., '16px')",
    "scale_ratio": number (e.g., 1.25),
    "line_height_body": number (e.g., 1.6),
    "line_height_headings": number (e.g., 1.2)
  },

  "layout": {
    "container_width": "string (e.g., '1280px')",
    "content_width": "string (e.g., '720px')",
    "sidebar_width": "string (e.g., '300px')",
    "header_height": "string (e.g., '80px')",
    "header_style": "string: 'sticky' | 'fixed' | 'static'",
    "sidebar_position": "string: 'left' | 'right' | 'none'",
    "footer_columns": number (1-6)
  },

  "hero": {
    "enabled": boolean,
    "style": "string: 'image' | 'gradient' | 'video' | 'minimal'",
    "title": "string",
    "subtitle": "string",
    "cta_text": "string (button text)",
    "cta_url": "string (button URL)",
    "secondary_cta_text": "string (optional)",
    "secondary_cta_url": "string (optional)",
    "overlay_opacity": number (0-1),
    "min_height": "string (e.g., '600px')",
    "text_alignment": "string: 'left' | 'center' | 'right'"
  },

  "navigation": {
    "primary_menu": [
      {"label": "string", "url": "string", "children": []}
    ],
    "footer_menu": [
      {"label": "string", "url": "string"}
    ],
    "mobile_menu_style": "string: 'slide' | 'dropdown' | 'fullscreen'",
    "show_search": boolean
  },

  "widget_areas": [
    {"id": "string", "name": "string", "description": "string"}
  ],

  "features": {
    "woocommerce": {
      "enabled": boolean,
      "products_per_page": number,
      "products_columns": number,
      "show_cart_icon": boolean,
      "show_quick_view": boolean,
      "show_wishlist": boolean
    },
    "dark_mode": boolean,
    "preloader": boolean,
    "back_to_top": boolean,
    "smooth_scroll": boolean,
    "lazy_load_images": boolean,
    "custom_blocks": [
      {"name": "string", "title": "string", "description": "string", "category": "string", "icon": "string"}
    ],
    "social_links": ["facebook", "twitter", "instagram", ...]
  },

  "post_types": ["string array of custom post type slugs"],

  "tags": ["string array of WordPress theme tags"]
}
```

IMPORTANT RULES:
1. Output ONLY valid JSON - no explanations, no markdown code fences
2. All colors MUST be valid 6-digit hex codes (e.g., "#1a1a2e")
3. Theme name MUST be lowercase with hyphens only (no spaces, no special chars)
4. All boolean values must be true/false (not "true"/"false")
5. All numbers must be actual numbers (not strings)
"""


SYSTEM_PROMPT = """You are a WordPress theme specification generator. Your ONLY job is to output valid JSON that describes a WordPress theme's design and structure.

CRITICAL RULES:
1. Output ONLY valid JSON - nothing else, no explanations, no markdown
2. NEVER output PHP, CSS, JavaScript, or HTML code
3. NEVER include code fences (```) in your response
4. The JSON must follow the exact schema provided
5. All hex colors must be valid 6-digit codes (e.g., "#1a1a2e")
6. Theme names must be lowercase with hyphens only

Your JSON will be processed by a template engine to generate the actual WordPress theme files. You are NOT generating code - you are generating a specification.

Think of yourself as a designer creating a design document, not a developer writing code."""


def get_theme_spec_system_prompt() -> str:
    """Get the system prompt for theme specification generation.

    Returns:
        System prompt string
    """
    return SYSTEM_PROMPT


def get_schema_description() -> str:
    """Get the JSON schema description for the LLM.

    Returns:
        Schema description string
    """
    return SCHEMA_DESCRIPTION


def get_theme_spec_prompt(
    user_prompt: str,
    design_profile: dict[str, Any] | None = None,
    woocommerce_enabled: bool = False,
    dark_mode_enabled: bool = False,
    image_analysis: str | None = None,
) -> str:
    """Generate the complete prompt for theme specification.

    Args:
        user_prompt: User's description of the theme they want
        design_profile: Optional design profile to apply
        woocommerce_enabled: Whether WooCommerce support is requested
        dark_mode_enabled: Whether dark mode is requested
        image_analysis: Optional analysis of uploaded design images

    Returns:
        Complete prompt string for the LLM
    """
    prompt_parts = [
        "Generate a WordPress theme specification based on the following request:",
        "",
        f"USER REQUEST: {user_prompt}",
        "",
    ]

    # Add image analysis if available
    if image_analysis:
        prompt_parts.extend([
            "DESIGN REFERENCE ANALYSIS:",
            image_analysis,
            "",
        ])

    # Add design profile if available
    if design_profile:
        prompt_parts.extend([
            "DESIGN SYSTEM TO FOLLOW:",
            f"- Profile: {design_profile.get('name', 'custom')}",
            f"- Description: {design_profile.get('description', '')}",
        ])

        if 'colors' in design_profile:
            colors = design_profile['colors']
            prompt_parts.append(f"- Colors: Primary={colors.get('primary', '#1a1a2e')}, "
                              f"Accent={colors.get('accent', '#e94560')}")

        if 'fonts' in design_profile:
            fonts = design_profile['fonts']
            prompt_parts.append(f"- Fonts: Primary={fonts.get('primary', 'Inter')}, "
                              f"Headings={fonts.get('headings', 'Inter')}")

        prompt_parts.append("")

    # Add feature flags
    feature_notes = []
    if woocommerce_enabled:
        feature_notes.append("- WooCommerce support is REQUIRED (set woocommerce.enabled to true)")
    if dark_mode_enabled:
        feature_notes.append("- Dark mode toggle is REQUIRED (set dark_mode to true)")

    if feature_notes:
        prompt_parts.extend([
            "REQUIRED FEATURES:",
            *feature_notes,
            "",
        ])

    guidance_blocks: list[str] = []

    if design_profile:
        inspiration_context = get_inspiration_context(design_profile.get("name", ""))
        if inspiration_context:
            guidance_blocks.append(inspiration_context)

    if design_profile or woocommerce_enabled:
        design_trends = get_modern_design_trends()
        if design_trends:
            guidance_blocks.append(design_trends)

    if woocommerce_enabled:
        ecommerce_best_practices = get_ecommerce_best_practices()
        if ecommerce_best_practices:
            guidance_blocks.append(ecommerce_best_practices)

    if guidance_blocks:
        prompt_parts.extend(guidance_blocks)
        prompt_parts.append("")

    # Add schema
    prompt_parts.extend([
        SCHEMA_DESCRIPTION,
        "",
        "Now generate the JSON theme specification. Output ONLY the JSON, nothing else.",
    ])

    return "\n".join(prompt_parts)


def parse_llm_json_response(
    response: str,
    fallback_to_defaults: bool = True
) -> tuple[bool, ThemeSpecification | None, list[str]]:
    """Parse LLM response and extract JSON theme specification.

    This function handles various edge cases:
    - Response wrapped in code fences
    - Response with explanatory text before/after JSON
    - Invalid JSON that needs correction
    - Missing required fields

    Args:
        response: Raw LLM response string
        fallback_to_defaults: Whether to use defaults for missing fields

    Returns:
        Tuple of (success, specification, errors)
    """
    errors = []

    # Clean the response
    cleaned = _clean_json_response(response)

    if not cleaned:
        errors.append("No JSON found in response")
        if fallback_to_defaults:
            logger.warning("Using default theme specification")
            return True, get_default_theme_spec(), errors
        return False, None, errors

    # Try to parse JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error: {e}")

        # Try to fix common JSON issues
        fixed = _try_fix_json(cleaned)
        if fixed:
            try:
                data = json.loads(fixed)
                errors.append("Fixed JSON syntax issues")
            except json.JSONDecodeError:
                if fallback_to_defaults:
                    logger.warning("JSON parsing failed, using defaults")
                    return True, get_default_theme_spec(), errors
                return False, None, errors
        else:
            if fallback_to_defaults:
                logger.warning("JSON parsing failed, using defaults")
                return True, get_default_theme_spec(), errors
            return False, None, errors

    # Validate against schema
    is_valid, validation_errors, spec = validate_theme_spec(data)

    if validation_errors:
        errors.extend(validation_errors)

    if not is_valid:
        if fallback_to_defaults:
            logger.warning("Schema validation failed, using defaults")
            return True, get_default_theme_spec(), errors
        return False, None, errors

    return True, spec, errors


def _clean_json_response(response: str) -> str | None:
    """Clean LLM response to extract JSON.

    Args:
        response: Raw response string

    Returns:
        Cleaned JSON string or None
    """
    if not response:
        return None

    text = response.strip()

    # Remove markdown code fences
    # Handle ```json ... ``` or ``` ... ```
    code_fence_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    match = re.search(code_fence_pattern, text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # Try to find JSON object
    # Look for { ... } pattern
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = list(re.finditer(json_pattern, text, re.DOTALL))

    if matches:
        # Find the largest match (most complete JSON)
        largest = max(matches, key=lambda m: len(m.group(0)))
        text = largest.group(0)
    elif '{' in text and '}' in text:
        # Extract from first { to last }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start < end:
            text = text[start:end]
    else:
        return None

    return text.strip()


def _try_fix_json(json_str: str) -> str | None:
    """Try to fix common JSON issues.

    Args:
        json_str: JSON string with potential issues

    Returns:
        Fixed JSON string or None
    """
    if not json_str:
        return None

    fixed = json_str

    # Fix trailing commas
    fixed = re.sub(r',\s*}', '}', fixed)
    fixed = re.sub(r',\s*]', ']', fixed)

    # Fix single quotes to double quotes (but be careful with content)
    # Only replace quotes around keys
    fixed = re.sub(r"'(\w+)':", r'"\1":', fixed)

    # Fix missing quotes around string values
    # This is risky so we do it conservatively
    fixed = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}\]])', r': "\1"\2', fixed)

    # Fix boolean values
    fixed = re.sub(r'\bTrue\b', 'true', fixed)
    fixed = re.sub(r'\bFalse\b', 'false', fixed)
    fixed = re.sub(r'\bNone\b', 'null', fixed)

    return fixed


def extract_theme_requirements_from_json(spec: ThemeSpecification) -> dict[str, Any]:
    """Extract requirements dictionary from theme specification.

    This converts the new JSON-based spec to the format expected by
    existing code that uses requirements dictionaries.

    Args:
        spec: Theme specification

    Returns:
        Requirements dictionary compatible with existing code
    """
    return {
        "theme_name": spec.theme_name,
        "theme_display_name": spec.theme_display_name,
        "description": spec.description,
        "color_scheme": spec.colors.primary,
        "layout": "sidebar-right" if spec.layout.sidebar_position == "right" else "full-width",
        "features": spec.tags,
        "navigation": ["primary", "footer"],
        "post_types": spec.post_types,
        "integrations": [],
        "design_profile": {
            "name": "custom",
            "colors": spec.colors.model_dump(),
            "fonts": {
                "primary": spec.typography.font_primary,
                "headings": spec.typography.font_headings,
            },
        },
    }
