"""Configuration utilities for WPGen.

Provides helper functions for loading configuration and initializing components.
"""

import os
from typing import Dict, Any

from ..llm import OpenAIProvider, AnthropicProvider, BaseLLMProvider


def get_llm_provider(config: Dict[str, Any]) -> BaseLLMProvider:
    """Initialize and return the configured LLM provider.

    Args:
        config: Configuration dictionary

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider is not configured correctly or API key is missing
    """
    provider_name = config.get("llm", {}).get("provider", "openai")

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI provider"
            )
        provider_config = config.get("llm", {}).get("openai", {})
        return OpenAIProvider(api_key, provider_config)

    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required for Anthropic provider"
            )
        provider_config = config.get("llm", {}).get("anthropic", {})
        return AnthropicProvider(api_key, provider_config)

    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
