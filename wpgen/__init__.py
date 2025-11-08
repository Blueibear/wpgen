"""WPGen - WordPress Theme Generator.

A Python-based tool that generates WordPress themes from natural language descriptions.
"""

__version__ = "1.0.0"
__author__ = "WPGen"
__license__ = "MIT"


def __getattr__(name):
    """Lazy imports to avoid import-time dependencies.

    This allows importing wpgen without requiring all dependencies to be installed,
    which is especially useful for CI/testing with mock providers.
    """
    if name == "WordPressGenerator":
        from .generators.wordpress_generator import WordPressGenerator

        return WordPressGenerator
    elif name == "GitHubIntegration":
        from .github.integration import GitHubIntegration

        return GitHubIntegration
    elif name == "PromptParser":
        from .parsers.prompt_parser import PromptParser

        return PromptParser
    elif name == "get_llm_provider":
        from .utils.config import get_llm_provider

        return get_llm_provider
    elif name == "setup_logger":
        from .utils.logger import setup_logger

        return setup_logger
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "__version__",
    "WordPressGenerator",
    "GitHubIntegration",
    "PromptParser",
    "get_llm_provider",
    "setup_logger",
]
