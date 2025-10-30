"""OpenAI LLM provider implementation.

Implements the LLM provider interface using OpenAI's API.
"""

import json
from typing import Dict, Any, Optional
from openai import OpenAI

from .base import BaseLLMProvider
from ..utils.logger import get_logger


logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI implementation of the LLM provider."""

    def __init__(self, api_key: str, config: Dict[str, Any]):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            config: OpenAI-specific configuration
        """
        super().__init__(api_key, config)
        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized OpenAI provider with model: {self.model}")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using OpenAI's API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            logger.debug(f"Sending request to OpenAI with {len(messages)} messages")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            result = response.choices[0].message.content
            logger.info("Successfully generated response from OpenAI")
            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def generate_code(
        self,
        description: str,
        file_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate code using OpenAI.

        Args:
            description: What the code should do
            file_type: Type of file (php, css, js, etc.)
            context: Additional context

        Returns:
            Generated code

        Raises:
            Exception: If generation fails
        """
        context = context or {}

        system_prompt = f"""You are an expert WordPress developer. Generate clean,
        well-documented, and production-ready {file_type.upper()} code. Follow WordPress
        coding standards and best practices. Only output the code without any explanations
        or markdown formatting."""

        prompt = f"""Generate {file_type.upper()} code for: {description}

Context:
{json.dumps(context, indent=2)}

Requirements:
- Follow WordPress coding standards
- Include inline documentation
- Make it production-ready
- Ensure compatibility with WordPress 6.4+
- Use modern best practices

Output only the code, no explanations."""

        try:
            code = self.generate(prompt, system_prompt)
            # Clean up any markdown code blocks if present
            code = code.replace("```php", "").replace("```css", "").replace("```javascript", "")
            code = code.replace("```", "").strip()
            logger.info(f"Generated {file_type} code successfully")
            return code

        except Exception as e:
            logger.error(f"Failed to generate {file_type} code: {str(e)}")
            raise

    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Analyze user prompt to extract WordPress theme requirements.

        Args:
            prompt: Natural language description

        Returns:
            Dictionary of extracted requirements

        Raises:
            Exception: If analysis fails
        """
        system_prompt = """You are an expert at analyzing WordPress website requirements.
        Extract key information from user descriptions and return a structured JSON object.
        Be specific and infer reasonable defaults when information is not explicit."""

        analysis_prompt = f"""Analyze this WordPress website description and extract the following information:

Description: "{prompt}"

Return a JSON object with these fields:
- theme_name: A short, kebab-case name for the theme (e.g., "dark-portfolio")
- theme_display_name: A human-readable name (e.g., "Dark Portfolio")
- description: A one-sentence theme description
- color_scheme: Primary color scheme (e.g., "dark", "light", "blue", "corporate")
- features: Array of features to implement (e.g., ["blog", "contact-form", "portfolio"])
- pages: Array of page templates needed (e.g., ["home", "about", "contact", "portfolio"])
- layout: Layout type (e.g., "full-width", "boxed", "sidebar")
- post_types: Custom post types needed (e.g., ["portfolio", "testimonials"])
- navigation: Navigation requirements (e.g., "header-menu", "footer-menu", "mobile-menu")
- integrations: External integrations (e.g., ["contact-form-7", "woocommerce"])

Return ONLY valid JSON, no other text."""

        try:
            response = self.generate(analysis_prompt, system_prompt)

            # Extract JSON from response (handle if wrapped in markdown)
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response

            result = json.loads(response)
            logger.info(f"Successfully analyzed prompt: {result.get('theme_name', 'unknown')}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {str(e)}")
            # Return a basic fallback structure
            return {
                "theme_name": "wpgen-theme",
                "theme_display_name": "WPGen Theme",
                "description": "A WordPress theme generated by WPGen",
                "color_scheme": "default",
                "features": ["blog"],
                "pages": ["home", "single", "archive"],
                "layout": "full-width",
                "post_types": [],
                "navigation": ["header-menu"],
                "integrations": []
            }
        except Exception as e:
            logger.error(f"Failed to analyze prompt: {str(e)}")
            raise
