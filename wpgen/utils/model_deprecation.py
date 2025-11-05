"""Model deprecation warnings and recommendations."""

import re
from typing import Optional, Tuple
from .logger import get_logger

logger = get_logger(__name__)

# Deprecated/preview model patterns and their stable replacements
DEPRECATED_MODELS = {
    # OpenAI
    "gpt-4-turbo-preview": "gpt-4-turbo",
    "gpt-4-1106-preview": "gpt-4-turbo",
    "gpt-4-0125-preview": "gpt-4-turbo",
    "gpt-4-vision-preview": "gpt-4-turbo",
    "gpt-3.5-turbo-1106": "gpt-3.5-turbo",
    "gpt-3.5-turbo-0125": "gpt-3.5-turbo",

    # Anthropic
    "claude-3-opus-20240229": "claude-3-5-sonnet-20241022",  # Suggest newer model
    "claude-3-sonnet-20240229": "claude-3-5-sonnet-20241022",
    "claude-2.1": "claude-3-5-sonnet-20241022",
    "claude-2.0": "claude-3-5-sonnet-20241022",
}

# Patterns that indicate a preview/deprecated model
DEPRECATED_PATTERNS = [
    (re.compile(r'-preview$', re.IGNORECASE), "This appears to be a preview model"),
    (re.compile(r'-\d{4}(?:-\d{2}){0,2}$'), "This appears to be a dated snapshot model"),
    (re.compile(r'turbo-\d{4}$'), "This appears to be an older turbo model"),
]


def check_model_deprecation(model_name: str, provider: str = "unknown") -> Tuple[bool, Optional[str], Optional[str]]:
    """Check if a model name appears deprecated and suggest replacement.

    Args:
        model_name: Model name to check
        provider: Provider name (openai, anthropic, etc.)

    Returns:
        Tuple of (is_deprecated, warning_message, suggested_replacement)
    """
    if not model_name:
        return False, None, None

    # Check exact matches first
    if model_name in DEPRECATED_MODELS:
        suggested = DEPRECATED_MODELS[model_name]
        warning = (
            f"Model '{model_name}' may be deprecated or is a preview version. "
            f"Consider using '{suggested}' instead."
        )
        return True, warning, suggested

    # Check patterns
    for pattern, reason in DEPRECATED_PATTERNS:
        if pattern.search(model_name):
            # Try to suggest a stable equivalent
            suggested = _suggest_stable_model(model_name, provider)
            warning = (
                f"Model '{model_name}' may be deprecated. {reason}. "
            )
            if suggested:
                warning += f"Consider using '{suggested}' instead."
            else:
                warning += "Please check your provider's documentation for stable model names."
            return True, warning, suggested

    return False, None, None


def _suggest_stable_model(model_name: str, provider: str) -> Optional[str]:
    """Suggest a stable model based on the deprecated model name.

    Args:
        model_name: Deprecated model name
        provider: Provider name

    Returns:
        Suggested stable model name or None
    """
    provider_lower = provider.lower()

    # OpenAI suggestions
    if provider_lower == "openai":
        if "gpt-4" in model_name:
            if "vision" in model_name:
                return "gpt-4o"  # GPT-4o has vision
            return "gpt-4-turbo"
        elif "gpt-3.5" in model_name:
            return "gpt-3.5-turbo"

    # Anthropic suggestions
    elif provider_lower == "anthropic":
        if "claude-3" in model_name or "claude-2" in model_name:
            return "claude-3-5-sonnet-20241022"

    return None


def log_model_deprecation_warning(model_name: str, provider: str = "unknown") -> None:
    """Check for model deprecation and log warning if needed.

    Args:
        model_name: Model name to check
        provider: Provider name
    """
    is_deprecated, warning, suggested = check_model_deprecation(model_name, provider)

    if is_deprecated and warning:
        logger.warning(f"⚠️  {warning}")
        if suggested:
            logger.info(f"💡 Suggested model: {suggested}")
            logger.info(f"   You can override the model using the WPGEN_{provider.upper()}_MODEL environment variable")
