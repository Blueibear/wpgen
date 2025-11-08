"""Prompt parser for analyzing and structuring user requirements.

This module takes natural language descriptions and converts them into
structured theme requirements using LLM providers.
"""

from typing import Any, Dict, List, Optional

from ..llm.base import BaseLLMProvider
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PromptParser:
    """Parser for converting natural language prompts to structured requirements."""

    def __init__(self, llm_provider: BaseLLMProvider):
        """Initialize the prompt parser.

        Args:
            llm_provider: LLM provider instance to use for parsing
        """
        self.llm_provider = llm_provider
        logger.info("Initialized PromptParser")

    def parse(self, prompt: str) -> Dict[str, Any]:
        """Parse a natural language prompt into structured requirements.

        Args:
            prompt: Natural language description of the WordPress site

        Returns:
            Dictionary containing structured requirements including:
                - theme_name: str
                - theme_display_name: str
                - description: str
                - color_scheme: str
                - features: List[str]
                - pages: List[str]
                - layout: str
                - post_types: List[str]
                - navigation: List[str]
                - integrations: List[str]

        Raises:
            ValueError: If prompt is empty or invalid
            Exception: If parsing fails
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        logger.info(f"Parsing prompt: {prompt[:100]}...")

        try:
            # Use the LLM provider to analyze the prompt
            requirements = self.llm_provider.analyze_prompt(prompt)

            # Validate and normalize the requirements
            requirements = self._validate_requirements(requirements)

            logger.info(f"Successfully parsed prompt into theme: {requirements['theme_name']}")
            return requirements

        except Exception as e:
            logger.error(f"Failed to parse prompt: {str(e)}")
            # Return fallback structure instead of raising
            logger.warning("Using fallback theme structure due to parsing failure")
            return {
                "theme_name": "wpgen-theme",
                "theme_display_name": "WPGen Theme",
                "description": f"A WordPress theme based on: {prompt[:100]}...",
                "color_scheme": "default",
                "features": ["blog"],
                "pages": ["index", "single", "archive"],
                "layout": "full-width",
                "post_types": [],
                "navigation": ["header-menu"],
                "integrations": [],
            }

    def parse_multimodal(
        self,
        prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Parse a prompt with multi-modal inputs (images, additional text).

        Args:
            prompt: Natural language description of the WordPress site
            images: List of image data dicts with 'data' (base64) and 'mime_type'
            additional_context: Additional text context from uploaded files

        Returns:
            Dictionary containing structured requirements

        Raises:
            ValueError: If prompt is empty or invalid
            Exception: If parsing fails
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        logger.info(
            f"Parsing multi-modal prompt: {prompt[:100]}... "
            f"(images: {len(images) if images else 0}, "
            f"context: {len(additional_context) if additional_context else 0} chars)"
        )

        try:
            # Use the LLM provider's multi-modal analyze method
            requirements = self.llm_provider.analyze_prompt_multimodal(
                prompt, images=images, additional_context=additional_context
            )

            # Validate and normalize the requirements
            requirements = self._validate_requirements(requirements)

            logger.info(
                f"Successfully parsed multi-modal prompt into theme: {requirements['theme_name']}"
            )
            return requirements

        except Exception as e:
            logger.error(f"Failed to parse multi-modal prompt: {str(e)}")
            # Return fallback structure instead of raising
            logger.warning("Using fallback theme structure due to parsing failure")
            return {
                "theme_name": "wpgen-theme",
                "theme_display_name": "WPGen Theme",
                "description": f"A WordPress theme based on: {prompt[:100]}...",
                "color_scheme": "default",
                "features": ["blog"],
                "pages": ["index", "single", "archive"],
                "layout": "full-width",
                "post_types": [],
                "navigation": ["header-menu"],
                "integrations": [],
            }

    def _validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize parsed requirements.

        Args:
            requirements: Raw requirements dictionary from LLM

        Returns:
            Validated and normalized requirements

        Raises:
            ValueError: If requirements are invalid
        """
        # Ensure requirements is a dictionary
        if not isinstance(requirements, dict):
            logger.error(f"Requirements is not a dictionary: {type(requirements)}")
            requirements = {}

        # Add missing required fields with defaults
        if "theme_name" not in requirements:
            logger.warning("Missing theme_name, using default")
            requirements["theme_name"] = "wpgen-theme"

        if "theme_display_name" not in requirements:
            logger.warning("Missing theme_display_name, generating from theme_name")
            requirements["theme_display_name"] = (
                requirements["theme_name"].replace("-", " ").title()
            )

        if "description" not in requirements:
            logger.warning("Missing description, using default")
            requirements["description"] = "A WordPress theme generated by WPGen"

        # Normalize theme_name (kebab-case, lowercase, no special chars)
        theme_name = str(requirements["theme_name"]).lower()
        theme_name = "".join(c if c.isalnum() or c == "-" else "-" for c in theme_name)
        theme_name = "-".join(filter(None, theme_name.split("-")))  # Remove consecutive dashes
        if not theme_name:  # If theme_name becomes empty after normalization
            theme_name = "wpgen-theme"
        requirements["theme_name"] = theme_name

        # Ensure arrays are actually arrays with string elements
        array_fields = ["features", "pages", "post_types", "navigation", "integrations"]
        for field in array_fields:
            if field not in requirements:
                requirements[field] = []
            elif not isinstance(requirements[field], list):
                # Convert single value to list
                requirements[field] = [str(requirements[field])]
            else:
                # Ensure all items in the list are strings
                requirements[field] = [
                    str(item) if not isinstance(item, str) else item
                    for item in requirements[field]
                ]

        # Ensure scalar string fields are actually strings (not dicts or other types)
        string_fields = ["color_scheme", "layout", "description", "theme_display_name"]
        for field in string_fields:
            if field in requirements and not isinstance(requirements[field], str):
                # Convert dict or other types to string representation
                if isinstance(requirements[field], dict):
                    # For dicts, try to extract a reasonable string value
                    if field == "color_scheme" and "primary" in requirements[field]:
                        requirements[field] = str(requirements[field]["primary"])
                    elif "value" in requirements[field]:
                        requirements[field] = str(requirements[field]["value"])
                    else:
                        # Use first value if dict
                        values = list(requirements[field].values())
                        requirements[field] = str(values[0]) if values else "default"
                else:
                    requirements[field] = str(requirements[field])
                logger.warning(
                    f"Converted {field} from {type(requirements[field]).__name__} "
                    "to string"
                )

        # Set defaults for optional fields
        if "color_scheme" not in requirements:
            requirements["color_scheme"] = "default"

        if "layout" not in requirements:
            requirements["layout"] = "full-width"

        # Ensure minimum required pages exist
        if not requirements["pages"]:  # If pages list is empty
            requirements["pages"] = ["index", "single", "archive"]
        else:
            required_pages = ["index", "single", "archive"]
            for page in required_pages:
                if page not in requirements["pages"]:
                    requirements["pages"].append(page)

        logger.debug(f"Validated requirements: {requirements}")
        return requirements

    def extract_features(self, requirements: Dict[str, Any]) -> Dict[str, bool]:
        """Extract and categorize features from requirements.

        Args:
            requirements: Parsed requirements dictionary

        Returns:
            Dictionary mapping feature names to boolean flags
        """
        features = {
            "blog": False,
            "portfolio": False,
            "contact_form": False,
            "gallery": False,
            "ecommerce": False,
            "custom_post_types": False,
            "widgets": True,  # Always include widgets
            "customizer": True,  # Always include customizer
        }

        # Check features list
        for feature in requirements.get("features", []):
            feature_lower = feature.lower()
            if "blog" in feature_lower:
                features["blog"] = True
            if "portfolio" in feature_lower:
                features["portfolio"] = True
            if "contact" in feature_lower or "form" in feature_lower:
                features["contact_form"] = True
            if "gallery" in feature_lower or "photo" in feature_lower:
                features["gallery"] = True
            if (
                "shop" in feature_lower
                or "ecommerce" in feature_lower
                or "woocommerce" in feature_lower
            ):
                features["ecommerce"] = True

        # Check custom post types
        if requirements.get("post_types"):
            features["custom_post_types"] = True

        # Check integrations
        integrations = requirements.get("integrations", [])
        for integration in integrations:
            integration_lower = integration.lower()
            if "woocommerce" in integration_lower:
                features["ecommerce"] = True
            if "contact" in integration_lower:
                features["contact_form"] = True

        return features
