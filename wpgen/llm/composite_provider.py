"""Composite LLM provider for dual-model local setups.

Supports separate brains (text-only) and vision models, routing automatically
based on whether images are present in the request.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .base import BaseLLMProvider

logger = get_logger(__name__)


@dataclass
class CompositeLLMProvider(BaseLLMProvider):
    """Dual-model provider that routes between brains and vision models.

    Uses brains model for text-only requests, vision model when images are present.
    Both models are accessed via OpenAI-compatible APIs.
    """

    def __init__(
        self,
        brains_client,
        brains_model: str,
        vision_client=None,
        vision_model: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 2048,
        timeout: int = 60,
    ):
        """Initialize composite provider with brains and optional vision clients.

        Args:
            brains_client: OpenAI client for text-only reasoning
            brains_model: Model name for brains client
            vision_client: Optional OpenAI client for vision tasks
            vision_model: Optional model name for vision client
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        # Initialize base class (requires api_key and config)
        config = {
            "model": brains_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        super().__init__("local", config)

        self.brains_client = brains_client
        self.brains_model = brains_model
        self.vision_client = vision_client
        self.vision_model = vision_model
        self.timeout = timeout

        logger.info(
            f"Initialized CompositeLLMProvider: brains={brains_model}, "
            f"vision={vision_model or 'disabled'}"
        )

    def _route_client(self, images: Optional[List[Dict[str, Any]]] = None):
        """Determine which client and model to use based on images.

        Args:
            images: Optional list of image data

        Returns:
            Tuple of (client, model_name)

        Raises:
            RuntimeError: If vision model required but not configured
        """
        has_images = bool(images)

        if has_images:
            if not self.vision_client or not self.vision_model:
                raise RuntimeError(
                    "A vision model is required to process images. "
                    "Please configure llm.vision_model and llm.vision_base_url in config.yaml, "
                    "or remove image uploads from your request."
                )
            logger.debug(f"Routing to vision model: {self.vision_model}")
            return self.vision_client, self.vision_model
        else:
            logger.debug(f"Routing to brains model: {self.brains_model}")
            return self.brains_client, self.brains_model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using brains model (text-only).

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        client, model = self._route_client(images=None)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise

    def generate_code(
        self,
        description: str,
        file_type: str,
        context: Optional[Dict[str, Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate code using appropriate model (vision if images, else brains).

        Args:
            description: What the code should do
            file_type: Type of file (php, css, js, etc.)
            context: Additional context
            images: Optional design mockups for vision-based generation

        Returns:
            Generated code
        """
        context = context or {}
        client, model = self._route_client(images)

        system_prompt = (
            "You are an expert WordPress developer. Generate clean, "
            f"well-documented, and production-ready {file_type.upper()} code. Follow WordPress "
            "coding standards and best practices. Only output the code without any explanations "
            "or markdown formatting."
        )

        # Build prompt text
        prompt_text = f"""Generate {file_type.upper()} code for: {description}

Context:
{context}

Requirements:
- Follow WordPress coding standards
- Include inline documentation
- Make it production-ready
- Ensure compatibility with WordPress 6.4+
- Use modern best practices"""

        if images and len(images) > 0:
            prompt_text += (
                f"\n- Match the visual design from the {len(images)} reference "
                "image(s) provided"
                "\n- Extract colors, typography, spacing, and layout patterns from "
                "the design mockups"
                "\n- Ensure the generated code accurately reflects the visual style "
                "shown in the images"
            )

        prompt_text += "\n\nOutput only the code, no explanations."

        try:
            # Use vision-enabled generation if images provided
            if images and len(images) > 0:
                logger.debug(f"Generating {file_type} code with {len(images)} visual reference(s)")

                # Build multi-modal content with images
                content = [{"type": "text", "text": prompt_text}]

                # Add all images
                for image in images:
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{image.get('mime_type', 'image/jpeg')};"
                                f"base64,{image['data']}"
                            )
                        },
                    })

                response = client.chat.completions.create(
                    model=model,
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
        """Analyze user prompt to extract requirements (brains model).

        Args:
            prompt: Natural language description

        Returns:
            Dictionary of extracted requirements
        """
        # Use brains model for text analysis
        client, model = self._route_client(images=None)

        system_prompt = """You are an expert at analyzing WordPress website requirements.
        Extract key information from user descriptions and return a structured JSON object.
        Be specific and infer reasonable defaults when information is not explicit."""

        analysis_prompt = (
            "Analyze this WordPress website description and extract the following information:\n\n"
            f'Description: "{prompt}"\n\n'
            "Return a JSON object with these fields:\n"
            "- theme_name: A short, kebab-case name\n"
            "- theme_display_name: A human-readable name\n"
            "- description: A one-sentence theme description\n"
            "- color_scheme: Primary color scheme\n"
            "- features: Array of features to implement\n"
            "- pages: Array of page templates needed\n"
            "- layout: Layout type\n"
            "- post_types: Custom post types needed\n"
            "- navigation: Navigation requirements\n"
            "- integrations: External integrations\n\n"
            "Return ONLY valid JSON, no other text."
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": analysis_prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            result_text = response.choices[0].message.content

            # Extract JSON from response
            import json
            try:
                result = self._extract_json(result_text)
            except (json.JSONDecodeError, ValueError):
                logger.error("Failed to extract JSON from response")
                result = self._get_fallback_requirements()

            # Ensure theme_display_name exists
            if "theme_display_name" not in result and "theme_name" in result:
                result["theme_display_name"] = result["theme_name"].replace("-", " ").title()

            logger.info(f"Successfully analyzed prompt: {result.get('theme_name', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Failed to analyze prompt: {str(e)}")
            return self._get_fallback_requirements()

    def analyze_prompt_multimodal(
        self,
        prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze prompt with multi-modal inputs (uses vision model if images present).

        Args:
            prompt: Natural language description
            images: List of image data dicts
            additional_context: Additional text context

        Returns:
            Dictionary containing extracted requirements
        """
        client, model = self._route_client(images)

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

        # Add images if provided
        if images and len(images) > 0:
            text_content += (
                f"\n\nDesign reference images ({len(images)} provided): "
                "Analyze these images for style, layout, color scheme, and design patterns.\n"
            )

            content.append({"type": "text", "text": text_content})

            for image in images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image.get('mime_type', 'image/jpeg')};base64,{image['data']}"
                    },
                })

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
            logger.debug(f"Sending multi-modal request (images: {len(images) if images else 0})")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            result_text = response.choices[0].message.content

            # Extract JSON
            import json
            try:
                result = self._extract_json(result_text)
            except (json.JSONDecodeError, ValueError):
                logger.error("Failed to extract JSON from multi-modal response")
                result = self._get_fallback_requirements()

            # Ensure theme_display_name exists
            if "theme_display_name" not in result and "theme_name" in result:
                result["theme_display_name"] = result["theme_name"].replace("-", " ").title()

            logger.info(
                f"Successfully analyzed multi-modal prompt: "
                f"{result.get('theme_name', 'unknown')}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to analyze multi-modal prompt: {str(e)}")
            return self._get_fallback_requirements()

    def analyze_image(self, image_data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Analyze a single image with vision model.

        Args:
            image_data: Dictionary with 'data' (base64), 'mime_type', 'name'
            prompt: Question or instruction for analyzing the image

        Returns:
            Analysis results
        """
        client, model = self._route_client(images=[image_data])

        try:
            logger.debug(f"Analyzing image '{image_data.get('name', 'unknown')}' with vision model")

            # Build multi-modal content
            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{image_data.get('mime_type', 'image/jpeg')};"
                            f"base64,{image_data['data']}"
                        )
                    },
                },
            ]

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            result = response.choices[0].message.content
            logger.info("Successfully analyzed image with vision model")

            return {
                "analysis": result,
                "image_name": image_data.get("name", "unknown"),
                "provider": "composite",
            }

        except Exception as e:
            logger.error(f"Failed to analyze image: {str(e)}")
            raise

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text.

        Args:
            text: Response text from LLM

        Returns:
            Parsed JSON dictionary
        """
        import json

        text = text.strip()

        # Try direct parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try removing markdown code blocks
        if "```" in text:
            parts = text.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Inside code block
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
        start = text.find("{")
        if start != -1:
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

        raise json.JSONDecodeError("No valid JSON found in response", text, 0)

    def _get_fallback_requirements(self) -> Dict[str, Any]:
        """Get fallback requirements structure."""
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
