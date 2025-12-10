"""Code generation modules for wpgen.

This module provides two generator implementations:

1. WordPressGenerator (Legacy):
   - Uses LLM to generate PHP code directly
   - Requires extensive validation and repair
   - Kept for backward compatibility

2. HybridWordPressGenerator (Recommended):
   - Uses JSON → Jinja → PHP architecture
   - LLM outputs only structured JSON
   - Jinja2 templates render valid PHP
   - Guarantees no syntax errors or hallucinated functions
"""

from .wordpress_generator import WordPressGenerator
from .hybrid_generator import HybridWordPressGenerator, create_hybrid_generator

__all__ = [
    "WordPressGenerator",
    "HybridWordPressGenerator",
    "create_hybrid_generator",
]
