"""WPGen - WordPress Theme Generator.

A Python-based tool that generates WordPress themes from natural language descriptions.
"""

__version__ = "1.0.0"
__author__ = "WPGen"
__license__ = "MIT"

from .llm import BaseLLMProvider, OpenAIProvider, AnthropicProvider
from .parsers import PromptParser
from .generators import WordPressGenerator
from .github import GitHubIntegration
from .wordpress import WordPressAPI, WordPressManager
from .utils import (
    setup_logger,
    get_logger,
    get_llm_provider,
    FileHandler,
    ImageAnalyzer,
    TextProcessor
)

__all__ = [
    "BaseLLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "PromptParser",
    "WordPressGenerator",
    "GitHubIntegration",
    "WordPressAPI",
    "WordPressManager",
    "setup_logger",
    "get_logger",
    "get_llm_provider",
    "FileHandler",
    "ImageAnalyzer",
    "TextProcessor",
]
