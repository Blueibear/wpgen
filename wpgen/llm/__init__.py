"""LLM provider abstraction layer for wpgen."""

# Import base class directly (no dependencies)
from .base import BaseLLMProvider


def __getattr__(name):
    """Lazy imports to avoid import-time dependencies on SDK packages.

    This allows importing the mock provider without requiring openai/anthropic SDKs.
    """
    if name == "AnthropicProvider":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider
    elif name == "OpenAIProvider":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider
    elif name == "CompositeLLMProvider":
        from .composite_provider import CompositeLLMProvider

        return CompositeLLMProvider
    elif name == "MockLLMProvider":
        from .mock_provider import MockLLMProvider

        return MockLLMProvider
    elif name == "get_provider_class":
        from .factory import get_provider_class

        return get_provider_class
    elif name == "list_providers":
        from .factory import list_providers

        return list_providers
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseLLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "CompositeLLMProvider",
    "MockLLMProvider",
    "get_provider_class",
    "list_providers",
]
