"""WPGen - WordPress Theme Generator.

A Python-based tool that generates WordPress themes from natural language descriptions.
"""

__version__ = "1.0.0"
__author__ = "WPGen"
__license__ = "MIT"

# Minimal imports to avoid import-time SDK hard dependencies
# Heavy SDK imports (openai, anthropic) are lazy-loaded when needed

# Re-export commonly used components for convenience
from .github.integration import GitHubIntegration
from .parsers.prompt_parser import PromptParser
from .generators.wordpress_generator import WordPressGenerator
from .utils.logger import get_logger, setup_logger
from .utils.config import get_llm_provider

__all__ = [
    "__version__",
    "GitHubIntegration",
    "PromptParser",
    "WordPressGenerator",
    "setup_logger",
    "get_logger",
    "get_llm_provider",
]
