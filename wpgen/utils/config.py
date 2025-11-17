"""Configuration utilities for WPGen.

Provides helper functions for loading configuration and initializing components.
"""

import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..llm import BaseLLMProvider


def get_llm_provider(config: dict[str, Any]) -> "BaseLLMProvider":
    """Initialize and return the configured LLM provider.

    Args:
        config: Configuration dictionary

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider is not configured correctly or API key is missing
    """
    # Import here to avoid circular imports
    from ..llm import AnthropicProvider, OpenAIProvider

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
        # Local providers use dual-model setup (brains + vision) via OpenAI-compatible API
        # Import dependencies
        from openai import OpenAI

        from ..llm import CompositeLLMProvider

        # Get provider-specific config
        provider_config = config.get("llm", {}).get(provider_name, {})
        llm_config = config.get("llm", {})

        # Default base URLs based on provider type
        default_base_url = (
            "http://localhost:1234/v1" if provider_name == "local-lmstudio"
            else "http://localhost:11434/v1"
        )

        # --- Brains model configuration (text-only reasoning) ---
        brains_model = provider_config.get("brains_model") or llm_config.get("brains_model")
        if not brains_model:
            # Default brains models
            brains_model = (
                "Meta-Llama-3.1-8B-Instruct" if provider_name == "local-lmstudio"
                else "llama3.1:8b-instruct"
            )

        brains_base_url = (
            provider_config.get("brains_base_url") or
            llm_config.get("brains_base_url") or
            default_base_url
        )

        # --- Vision model configuration (image analysis) ---
        vision_model = provider_config.get("vision_model") or llm_config.get("vision_model")
        vision_base_url = (
            provider_config.get("vision_base_url") or
            llm_config.get("vision_base_url") or
            brains_base_url  # Default to same server as brains
        )

        # --- Global parameters ---
        temperature = float(provider_config.get("temperature", llm_config.get("temperature", 0.4)))
        max_tokens = int(provider_config.get("max_tokens", llm_config.get("max_tokens", 2048)))
        timeout = int(provider_config.get("timeout", llm_config.get("timeout", 60)))

        # Create OpenAI clients for brains and vision
        # Local servers typically don't require real API keys
        brains_client = OpenAI(
            base_url=brains_base_url,
            api_key="local",
            timeout=timeout,
        )

        # Vision client only if vision_model is configured
        vision_client = None
        if vision_model:
            vision_client = OpenAI(
                base_url=vision_base_url,
                api_key="local",
                timeout=timeout,
            )

        # Return composite provider with dual-model routing
        return CompositeLLMProvider(
            brains_client=brains_client,
            brains_model=brains_model,
            vision_client=vision_client,
            vision_model=vision_model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
