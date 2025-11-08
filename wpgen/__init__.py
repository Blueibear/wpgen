"""WPGen - WordPress Theme Generator.

A Python-based tool that generates WordPress themes from natural language descriptions.
"""

__version__ = "1.0.0"
__author__ = "WPGen"
__license__ = "MIT"

# Minimal imports to avoid import-time SDK hard dependencies
# Heavy SDK imports (openai, anthropic) are lazy-loaded when needed

# Export commonly used classes and functions for convenience
from .generators.wordpress_generator import WordPressGenerator
from .github.integration import GitHubIntegration
from .parsers.prompt_parser import PromptParser
from .utils.config import get_llm_provider
from .utils.logger import setup_logger

__all__ = [
    "__version__",
    "WordPressGenerator",
    "GitHubIntegration",
    "PromptParser",
    "get_llm_provider",
    "setup_logger",
]
