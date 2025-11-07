"""Mock LLM provider for testing.

Provides deterministic responses for CI/testing without requiring API keys.
"""

from typing import Any, Dict, List, Optional

from .base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that returns deterministic responses for testing."""

    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """Initialize mock provider.

        Args:
            responses: Optional dict mapping prompt keywords to responses
        """
        self.responses = responses or {}
        self.call_count = 0
        self.last_prompt = None

    def generate(
        self,
        prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate a mocked response based on prompt keywords.

        Args:
            prompt: The prompt text
            images: Optional list of images (ignored in mock)
            max_tokens: Maximum tokens (ignored in mock)
            temperature: Temperature setting (ignored in mock)
            **kwargs: Additional arguments (ignored in mock)

        Returns:
            Deterministic response based on prompt content
        """
        self.call_count += 1
        self.last_prompt = prompt

        prompt_lower = prompt.lower()

        # Check for custom responses
        for keyword, response in self.responses.items():
            if keyword.lower() in prompt_lower:
                return response

        # Default responses based on common patterns
        if "parse" in prompt_lower or "requirements" in prompt_lower:
            return self._mock_parse_response()
        elif "generate" in prompt_lower or "create" in prompt_lower:
            return self._mock_generate_response()
        elif "analyze" in prompt_lower or "describe" in prompt_lower:
            return self._mock_analyze_response()
        else:
            return "Mock LLM response"

    def _mock_parse_response(self) -> str:
        """Return a mock theme requirements response."""
        return """
        {
            "theme_name": "test-theme",
            "theme_display_name": "Test Theme",
            "description": "A minimal test theme for automated testing",
            "features": ["responsive", "accessibility", "custom-colors"],
            "color_scheme": {
                "primary": "#007cba",
                "secondary": "#23282d",
                "accent": "#00a0d2"
            },
            "layout": "standard",
            "pages": ["home", "about", "contact"]
        }
        """

    def _mock_generate_response(self) -> str:
        """Return mock PHP/CSS code."""
        return """
        <?php
        // Mock generated code
        function test_theme_setup() {
            add_theme_support('title-tag');
            add_theme_support('post-thumbnails');
        }
        add_action('after_setup_theme', 'test_theme_setup');
        ?>
        """

    def _mock_analyze_response(self) -> str:
        """Return mock analysis response."""
        return """
        Analysis: This is a mock analysis of the provided content.
        The design appears to be clean and modern with good use of whitespace.
        """

    def get_model_name(self) -> str:
        """Get the model name."""
        return "mock-llm-v1"

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "mock"

    def count_tokens(self, text: str) -> int:
        """Estimate token count (mock implementation)."""
        return len(text.split())

    def reset(self):
        """Reset mock state for testing."""
        self.call_count = 0
        self.last_prompt = None
