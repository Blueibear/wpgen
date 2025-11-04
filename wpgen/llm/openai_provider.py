"""OpenAI LLM provider implementation.

Implements the LLM provider interface using OpenAI's API.
"""

import json
from typing import Dict, Any, Optional, List

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
        # Lazy import to avoid import-time hard dependency
        from openai import OpenAI

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
        context: Optional[Dict[str, Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate code using OpenAI with optional visual references.

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

        system_prompt = (
            "You are an expert WordPress developer. Generate clean,\n"
            f"well-documented, and production-ready {file_type.upper()} code. Follow WordPress\n"
            "coding standards and best practices. Only output the code without any explanations\n"
            "or markdown formatting."
        )

        # Build prompt text
        prompt_text = f"""Generate {file_type.upper()} code for: {description}

Context:
{json.dumps(context, indent=2)}

Requirements:
- Follow WordPress coding standards
- Include inline documentation
- Make it production-ready
- Ensure compatibility with WordPress 6.4+
- Use modern best practices"""

        # Add image guidance if images provided
        if images and len(images) > 0:
            prompt_text += (
                f"\n- Match the visual design from the {len(images)} reference image(s) provided"
                "\n- Extract colors, typography, spacing,"
                " and layout patterns from the design mockups"
                "\n- Ensure the generated code accurately reflects the visual style"
                " shown in the images"
            )

        prompt_text += "\n\nOutput only the code, no explanations."

        try:
            # Use vision-enabled generation if images provided
            if images and len(images) > 0:
                logger.debug(f"Generating {file_type} code with {len(images)} visual reference(s)")

                # Build multi-modal content with images
                content = [{"type": "text", "text": prompt_text}]

                # Add all images for GPT-4 Vision to analyze
                for idx, image in enumerate(images):
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:{image.get('mime_type', 'image/jpeg')};base64,"
                                    f"{image['data']}"
                                )
                            },
                        }
                    )

                # Use vision-capable model
                vision_model = "gpt-4o"

                # Call OpenAI vision API
                response = self.client.chat.completions.create(
                    model=vision_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content},
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )

                code = response.choices[0].message.content
                logger.info(f"Generated {file_type} code with vision successfully")
            else:
                # Text-only generation
                code = self.generate(prompt_text, system_prompt)
                logger.info(f"Generated {file_type} code successfully")

            # Clean up markdown and explanatory text
            from ..utils.code_validator import clean_generated_code
            code = clean_generated_code(code, file_type)

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
        images: Optional[List[Dict[str, Any]]] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
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

        # Add images if provided (GPT-4 Vision supports images)
        if images and len(images) > 0:
            text_content += (
                f"\n\nDesign reference images ({len(images)} provided): "
                "Analyze these images for style, layout, color scheme, and design patterns.\n"
            )

            content.append({"type": "text", "text": text_content})

            for idx, image in enumerate(images):
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{image.get('mime_type', 'image/jpeg')};base64,"
                                f"{image['data']}"
                            )
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

        if not content:
            content.append({"type": "text", "text": text_content})

        try:
            logger.debug(
                f"Sending multi-modal request to OpenAI (images: {len(images) if images else 0})"
            )

            # Use vision model if images are provided
            model = "gpt-4o" if images else self.model

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            result_text = response.choices[0].message.content

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

    def analyze_image(self, image_data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Analyze a single image with GPT-4 Vision capabilities.

        Args:
            image_data: Dictionary with 'data' (base64), 'mime_type', 'name'
            prompt: Question or instruction for analyzing the image

        Returns:
            Analysis results containing the LLM's response

        Raises:
            Exception: If vision analysis fails
        """
        try:
            logger.debug(f"Analyzing image '{image_data.get('name', 'unknown')}' with GPT-4 Vision")

            # Build multi-modal content with image and prompt
            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{image_data.get('mime_type', 'image/jpeg')};base64,"
                            f"{image_data['data']}"
                        )
                    },
                },
            ]

            # Use vision-capable model
            vision_model = "gpt-4o"

            # Call OpenAI vision API
            response = self.client.chat.completions.create(
                model=vision_model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            result = response.choices[0].message.content
            logger.info("Successfully analyzed image with GPT-4 Vision")

            return {
                "analysis": result,
                "image_name": image_data.get("name", "unknown"),
                "provider": "openai",
            }

        except Exception as e:
            logger.error(f"Failed to analyze image with GPT-4 Vision: {str(e)}")
            raise

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text.

        Handles various formats:
        - Plain JSON
        - JSON wrapped in markdown code blocks (```json, ```)
        - JSON with extra text before/after

        Args:
            text: Response text from LLM

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If no valid JSON found
        """
        text = text.strip()

        # Try direct parsing first
        try:
            return json.loads(text)
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
                    if lines[0].strip().lower() in ["json", ""]:
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
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            pass
                        break

        # If all else fails, raise the original error
        raise json.JSONDecodeError("No valid JSON found in response", text, 0)
