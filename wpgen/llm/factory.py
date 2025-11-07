"""LLM provider factory for wpgen.

Provides a registry and factory function for LLM provider classes.
For actual provider instantiation with configuration, use wpgen.utils.config.get_llm_provider.
"""

from typing import Dict, Type

from .anthropic_provider import AnthropicProvider
from .base import BaseLLMProvider
from .composite_provider import CompositeLLMProvider
from .openai_provider import OpenAIProvider

# Provider registry mapping provider names to classes
_PROVIDER_MAP: Dict[str, Type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "local-lmstudio": CompositeLLMProvider,
    "local-ollama": CompositeLLMProvider,
}


def get_provider_class(name: str) -> Type[BaseLLMProvider]:
    """Get LLM provider class by name.

    Args:
        name: Provider name (openai, anthropic, local-lmstudio, local-ollama)

    Returns:
        Provider class

    Raises:
        ValueError: If provider name is not supported
    """
    try:
        return _PROVIDER_MAP[name]
    except KeyError as e:
        supported = ", ".join(_PROVIDER_MAP.keys())
        raise ValueError(
            f"Unsupported LLM provider: {name!r}. "
            f"Supported providers: {supported}"
        ) from e


def list_providers() -> list[str]:
    """Get list of supported provider names.

    Returns:
        List of provider names
    """
    return list(_PROVIDER_MAP.keys())


__all__ = ["get_provider_class", "list_providers", "_PROVIDER_MAP"]
