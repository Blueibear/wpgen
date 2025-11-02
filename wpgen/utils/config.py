"""Configuration utilities for WPGen.

Provides helper functions for loading configuration and initializing components.
"""

import os
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm import BaseLLMProvider


def get_llm_provider(config: Dict[str, Any]) -> "BaseLLMProvider":
    """Initialize and return the configured LLM provider.

    Args:
        config: Configuration dictionary

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider is not configured correctly or API key is missing
    """
    # Import here to avoid circular imports
    from ..llm import OpenAIProvider, AnthropicProvider

    provider_name = config.get("llm", {}).get("provider", "openai")

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")
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

    elif provider_name in {"local-lmstudio", "local-ollama"}:
        # Local providers use OpenAI-compatible API with custom base_url
        # Import OpenAI SDK for local server connection
        from openai import OpenAI

        # Get provider-specific config or fallback to top-level llm config
        provider_config = config.get("llm", {}).get(provider_name, {})
        llm_config = config.get("llm", {})

        # Determine base_url: provider-specific > top-level > default
        base_url = provider_config.get("base_url") or llm_config.get("base_url")
        if not base_url:
            # Set defaults based on provider
            base_url = (
                "http://localhost:1234/v1" if provider_name == "local-lmstudio"
                else "http://localhost:11434/v1"
            )

        # Get model name with sensible defaults
        model = provider_config.get("model") or llm_config.get("model")
        if not model:
            # Default models for each local provider
            model = (
                "Meta-Llama-3.1-8B-Instruct" if provider_name == "local-lmstudio"
                else "llama3.1:8b-instruct"
            )

        # Get other parameters with defaults
        temperature = float(provider_config.get("temperature", llm_config.get("temperature", 0.4)))
        max_tokens = int(provider_config.get("max_tokens", llm_config.get("max_tokens", 2048)))
        timeout = int(provider_config.get("timeout", llm_config.get("timeout", 60)))

        # Create OpenAI client with custom base_url
        # Local servers typically don't require real API keys
        client = OpenAI(
            base_url=base_url,
            api_key="local",  # Placeholder - most local servers don't validate this
            timeout=timeout,
        )

        # Build config dict for OpenAIProvider
        openai_config = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Create OpenAIProvider with custom client
        # We use a dummy API key since the client is already configured
        provider = OpenAIProvider("local", openai_config)
        # Override the client with our custom one
        provider.client = client

        return provider

    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
