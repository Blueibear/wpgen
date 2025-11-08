"""Mock LLM provider for testing.

Provides deterministic responses for CI/testing without requiring API keys.
"""

from typing import Any, Dict, List, Optional

from .base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that returns deterministic responses for testing."""

    def __init__(self, *_, **kwargs):
        """Initialize mock provider accepting any args to bypass base class requirements."""
        # Bypass base class __init__ which requires api_key
        # Set minimal attributes expected by base class
        self.api_key = "mock-key"
        self.config = {}
        self.model = "mock-model"
        self.max_tokens = 4096
        self.temperature = 0.7

        # Mock-specific attributes
        self.responses = kwargs.get('responses', {})
        self.call_count = 0
        self.last_prompt = None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a mocked response based on prompt keywords.

        Args:
            prompt: The prompt text
            system_prompt: Optional system prompt (ignored in mock)
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
        if "parse" in prompt_lower or "requirements" in prompt_lower or "analyze" in prompt_lower:
            return self._mock_parse_response()
        elif "generate" in prompt_lower or "create" in prompt_lower:
            return self._mock_generate_response()
        else:
            return "Mock LLM response"

    def generate_code(
        self,
        description: str,
        file_type: str,
        context: Optional[Dict[str, Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate mock code for WordPress theme files.

        Args:
            description: Description of what the code should do
            file_type: Type of file to generate (e.g., 'php', 'css', 'js')
            context: Additional context for code generation
            images: Optional list of images (ignored in mock)

        Returns:
            Mock code appropriate for the file type
        """
        self.call_count += 1

        if file_type == "css":
            return self._mock_css_code()
        elif file_type == "php":
            return self._mock_php_code()
        elif file_type == "js":
            return self._mock_js_code()
        else:
            return f"/* Mock {file_type} code */\n"

    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Analyze user prompt to extract requirements.

        Args:
            prompt: Natural language description of the website

        Returns:
            Dictionary containing extracted requirements for deterministic testing
        """
        import json

        # Use generate method to get response (which respects custom responses)
        response = self.generate(prompt)

        # Try to parse as JSON
        try:
            # Remove leading/trailing whitespace and newlines
            response = response.strip()
            return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            # If not valid JSON, return default structure
            return {
                "theme_name": "wpgen-test-theme",
                "theme_display_name": "WPGen Test Theme",
                "description": "Deterministic analysis for CI",
                "features": ["blog", "responsive"],
                "color_scheme": "#007cba",
                "layout": "standard",
                "pages": ["home", "about", "contact"],
                "post_types": [],
                "navigation": ["header-menu"],
                "integrations": [],
            }

    def _mock_parse_response(self) -> str:
        """Return a mock theme requirements response."""
        return """
        {
            "theme_name": "test-theme",
            "theme_display_name": "Test Theme",
            "description": "A minimal test theme for automated testing",
            "features": ["responsive", "accessibility", "custom-colors"],
            "color_scheme": "#007cba",
            "layout": "standard",
            "pages": ["home", "about", "contact"]
        }
        """

    def _mock_generate_response(self) -> str:
        """Return mock PHP/CSS code."""
        return self._mock_php_code()

    def _mock_css_code(self) -> str:
        """Return mock CSS code."""
        return """
/*
Theme Name: WPGen Test Theme
Author: WPGen
Version: 0.0.0
Description: Minimal theme for CI
*/

body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
}
"""

    def _mock_php_code(self) -> str:
        """Return mock PHP code."""
        return """<?php
// Mock generated code
function test_theme_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
}
add_action('after_setup_theme', 'test_theme_setup');
?>"""

    def _mock_js_code(self) -> str:
        """Return mock JavaScript code."""
        return """// Mock JavaScript code
(function() {
    'use strict';
    console.log('Mock theme JS loaded');
})();
"""

    def reset(self):
        """Reset mock state for testing."""
        self.call_count = 0
        self.last_prompt = None
