"""LLM Prompt templates for JSON-only theme specification.

This module provides prompts that instruct the LLM to output ONLY JSON
following the ThemeSpecification schema. No PHP, CSS, or JavaScript
is generated directly by the LLM.
"""

from .theme_prompts import (
    get_theme_spec_prompt,
    get_theme_spec_system_prompt,
    get_schema_description,
    parse_llm_json_response,
)

__all__ = [
    "get_theme_spec_prompt",
    "get_theme_spec_system_prompt",
    "get_schema_description",
    "parse_llm_json_response",
]
