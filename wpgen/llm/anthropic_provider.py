"""Anthropic (Claude) LLM provider implementation.

Implements the LLM provider interface using Anthropic's Claude API.
"""

import json
from typing import Any

from ..utils.logger import get_logger
from .base import BaseLLMProvider

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic (Claude) implementation of the LLM provider."""

    def __init__(self, api_key: str, config: dict[str, Any]):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            config: Anthropic-specific configuration
        """
        super().__init__(api_key, config)
        # Lazy import to avoid import-time hard dependency
        from anthropic import Anthropic

        self.client = Anthropic(api_key=api_key)
        logger.info(f"Initialized Anthropic provider with model: {self.model}")

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text using Anthropic's Claude API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        try:
            logger.debug("Sending request to Anthropic Claude")

            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)

            result = response.content[0].text
            logger.info("Successfully generated response from Anthropic")
            return result

        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise

    def generate_code(
        self,
        description: str,
        file_type: str,
        context: dict[str, Any | None] = None,
        images: list[dict[str, Any | None]] = None,
    ) -> str:
        """Generate code using Anthropic Claude with optional visual references.

        Args:
            description: What the code should do
            file_type: Type of file (php, css, js, etc.)
            context: Additional context
            images: Optional design mockups/screenshots for vision-based generation

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

        # Build prompt text
        prompt_text = f"""Generate {file_type.upper()} code for: {description}

Context:
{json.dumps(context, indent=2)}

Requirements:
- Follow WordPress coding standards
- Include inline documentation
- Make it production-ready
- Ensure compatibility with WordPress 6.4+
- Use modern best practices
- Implement security best practices (sanitization, escaping, nonces)"""

        # Add image guidance if images provided
        if images and len(images) > 0:
            prompt_text += f"""
- Match the visual design from the {len(images)} reference image(s) provided
- Extract colors, typography, spacing, and layout patterns from the design mockups
- Ensure the generated code accurately reflects the visual style shown in the images"""

        prompt_text += "\n\nOutput only the code, no explanations."

        try:
            # Use vision-enabled generation if images provided
            if images and len(images) > 0:
                logger.debug(f"Generating {file_type} code with {len(images)} visual reference(s)")

                # Build multi-modal content with images
                content = []

                # Add all images first for Claude to analyze
                for idx, image in enumerate(images):
                    content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image.get("mime_type", "image/jpeg"),
                                "data": image["data"],
                            },
                        }
                    )

                # Add the text prompt after images
                content.append({"type": "text", "text": prompt_text})

                # Call Claude vision API
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": content}],
                )

                code = response.content[0].text
                logger.info(f"Generated {file_type} code with vision successfully")
            else:
                # Text-only generation
                code = self.generate(prompt_text, system_prompt)
                logger.info(f"Generated {file_type} code successfully")

            # Clean up any markdown code blocks if present
            code = code.replace("```php", "").replace("```css", "").replace("```javascript", "")
            code = code.replace("```", "").strip()

            return code

        except Exception as e:
            logger.error(f"Failed to generate {file_type} code: {str(e)}")
            raise

    def analyze_prompt(self, prompt: str) -> dict[str, Any]:
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

        analysis_prompt = (
            "Analyze this WordPress website description and extract the following information:\n\n"
            f'Description: "{prompt}"\n\n'
            "Return a JSON object with these fields:\n"
            "- theme_name: A short, kebab-case name for the theme "
            '(e.g., "dark-portfolio")\n'
            "- theme_display_name: A human-readable name "
            '(e.g., "Dark Portfolio")\n'
            "- description: A one-sentence theme description\n"
            "- color_scheme: Primary color scheme "
            '(e.g., "dark", "light", "blue", "corporate")\n'
            "- features: Array of features to implement "
            '(e.g., ["blog", "contact-form", "portfolio"])\n'
            "- pages: Array of page templates needed "
            '(e.g., ["home", "about", "contact", "portfolio"])\n'
            '- layout: Layout type (e.g., "full-width", "boxed", "sidebar")\n'
            "- post_types: Custom post types needed "
            '(e.g., ["portfolio", "testimonials"])\n'
            "- navigation: Navigation requirements "
            '(e.g., "header-menu", "footer-menu", "mobile-menu")\n'
            "- integrations: External integrations "
            '(e.g., ["contact-form-7", "woocommerce"])\n\n'
            "Return ONLY valid JSON, no other text."
        )

        try:
            response = self.generate(analysis_prompt, system_prompt)

            # Extract JSON from response (handle if wrapped in markdown)
            try:
                result = self._extract_json(response)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to extract JSON from response: {str(e)}")
                logger.error(f"Response text: {response[:500]}")
                # Return fallback structure
                result = {
                    "theme_name": "wpgen-theme",
                    "theme_display_name": "WPGen Theme",
                    "description": "A WordPress theme generated by WPGen",
                    "color_scheme": "default",
                    "features": ["blog"],
                    "pages": ["home", "single", "archive"],
                    "layout": "full-width",
                    "post_types": [],
                    "navigation": ["header-menu"],
                    "integrations": [],
                }

            # Ensure theme_display_name exists
            if "theme_display_name" not in result and "theme_name" in result:
                result["theme_display_name"] = result["theme_name"].replace("-", " ").title()

            logger.info(f"Successfully analyzed prompt: {result.get('theme_name', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Failed to analyze prompt: {str(e)}")
            # Return fallback structure even on complete failure
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
                "integrations": [],
            }

    def analyze_prompt_multimodal(
        self,
        prompt: str,
        images: list[dict[str, Any | None]] = None,
        additional_context: str | None = None,
    ) -> dict[str, Any]:
        """Analyze user prompt with multi-modal inputs (images, additional text).

        Args:
            prompt: Natural language description of the website
            images: List of image data dicts with 'data' (base64) and 'mime_type'
            additional_context: Additional text context from uploaded files

        Returns:
            Dictionary containing extracted requirements

        Raises:
            Exception: If analysis fails
        """
        system_prompt = """You are an expert at analyzing WordPress website requirements.
        Extract key information from user descriptions, design references, and additional context.
        Return a structured JSON object. Be specific and infer reasonable defaults."""

        # Build multi-modal content
        content = []

        # Add text prompt
        text_content = (
            "Analyze this WordPress website description and extract the following information:\n\n"
            f'Description: "{prompt}"\n\n'
        )

        if additional_context:
            text_content += f"\n\nAdditional Context from uploaded files:\n{additional_context}\n"

        # Add images if provided (Claude supports vision)
        if images and len(images) > 0:
            text_content += (
                f"\n\nDesign reference images ({len(images)} provided): "
                "Analyze these images for style, layout, color scheme, and design patterns.\n"
            )

            for idx, image in enumerate(images):
                content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image.get("mime_type", "image/jpeg"),
                            "data": image["data"],
                        },
                    }
                )

        text_content += """
Return a JSON object with these fields:
- theme_name: A short, kebab-case name for the theme
- theme_display_name: A human-readable name
- description: A one-sentence theme description
- color_scheme: Primary color scheme inferred from description or images
- features: Array of features to implement
- pages: Array of page templates needed
- layout: Layout type (analyze from images if provided)
- post_types: Custom post types needed
- navigation: Navigation requirements
- integrations: External integrations
- design_notes: Additional design observations from images (if provided)

Return ONLY valid JSON, no other text."""

        content.insert(0, {"type": "text", "text": text_content})

        try:
            logger.debug(
                f"Sending multi-modal request to Anthropic (images: {len(images) if images else 0})"
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": content}],
            )

            result_text = response.content[0].text

            # Extract JSON from response
            try:
                result = self._extract_json(result_text)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to extract JSON from multi-modal response: {str(e)}")
                logger.error(f"Response text: {result_text[:500]}")
                # Return fallback structure
                result = {
                    "theme_name": "wpgen-theme",
                    "theme_display_name": "WPGen Theme",
                    "description": "A WordPress theme generated by WPGen",
                    "color_scheme": "default",
                    "features": ["blog"],
                    "pages": ["home", "single", "archive"],
                    "layout": "full-width",
                    "post_types": [],
                    "navigation": ["header-menu"],
                    "integrations": [],
                }

            # Ensure theme_display_name exists
            if "theme_display_name" not in result and "theme_name" in result:
                result["theme_display_name"] = result["theme_name"].replace("-", " ").title()

            logger.info(
                f"Successfully analyzed multi-modal prompt: {result.get('theme_name', 'unknown')}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to analyze multi-modal prompt: {str(e)}")
            # Return fallback structure even on complete failure
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
                "integrations": [],
            }

    def analyze_image(self, image_data: dict[str, Any], prompt: str) -> dict[str, Any]:
        """Analyze a single image with Claude's vision capabilities.

        Args:
            image_data: Dictionary with 'data' (base64), 'mime_type', 'name'
            prompt: Question or instruction for analyzing the image

        Returns:
            Analysis results containing the LLM's response

        Raises:
            Exception: If vision analysis fails
        """
        try:
            logger.debug(
                f"Analyzing image '{image_data.get('name', 'unknown')}' with Claude vision"
            )

            # Build multi-modal content with image and prompt
            content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_data.get("mime_type", "image/jpeg"),
                        "data": image_data["data"],
                    },
                },
                {"type": "text", "text": prompt},
            ]

            # Call Claude vision API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": content}],
            )

            result = response.content[0].text
            logger.info("Successfully analyzed image with Claude vision")

            return {
                "analysis": result,
                "image_name": image_data.get("name", "unknown"),
                "provider": "anthropic",
            }

        except Exception as e:
            logger.error(f"Failed to analyze image with Claude vision: {str(e)}")
            raise

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response text.

        Handles various formats:
        - Plain JSON
        - JSON wrapped in markdown code blocks (```json, ```)
        - JSON with extra text before/after
        - JSON with comments (// or /* */)
        - Multiple JSON objects (returns first valid one)

        Args:
            text: Response text from LLM

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If no valid JSON found
        """
        import re

        text = text.strip()

        # Try direct parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Remove common comment patterns before parsing
        # Remove single-line comments
        text_no_comments = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
        # Remove multi-line comments
        text_no_comments = re.sub(r'/\*.*?\*/', '', text_no_comments, flags=re.DOTALL)

        # Try parsing without comments
        try:
            return json.loads(text_no_comments.strip())
        except json.JSONDecodeError:
            pass

        # Try removing markdown code blocks
        if "```" in text:
            # Find content between code blocks
            parts = text.split("```")
            for i, part in enumerate(parts):
                # Skip the outer parts and language identifiers
                if i % 2 == 1:  # Inside code block
                    # Remove language identifier if present
                    lines = part.strip().split("\n", 1)
                    if lines[0].strip().lower() in ["json", "javascript", "js", ""]:
                        json_text = lines[1] if len(lines) > 1 else lines[0]
                    else:
                        json_text = part

                    try:
                        return json.loads(json_text.strip())
                    except json.JSONDecodeError:
                        continue

        # Try to find JSON object in text
        # Look for content between { and }
        start = text.find("{")
        if start != -1:
            # Find matching closing brace
            depth = 0
            in_string = False
            escape_next = False

            for i in range(start, len(text)):
                char = text[i]

                # Handle string escaping
                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                # Toggle string mode on unescaped quotes
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                # Only count braces outside of strings
                if not in_string:
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                candidate = text[start : i + 1]
                                # Remove comments from candidate
                                candidate = re.sub(r'//.*?$', '', candidate, flags=re.MULTILINE)
                                candidate = re.sub(r'/\*.*?\*/', '', candidate, flags=re.DOTALL)
                                return json.loads(candidate)
                            except json.JSONDecodeError:
                                # Try to find next JSON object
                                start = text.find("{", i + 1)
                                if start == -1:
                                    break
                                i = start - 1
                                depth = 0
                                continue

        # If all else fails, raise the original error
        raise json.JSONDecodeError("No valid JSON found in response", text, 0)
