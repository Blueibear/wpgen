"""Hybrid WordPress theme generator using JSON → Jinja → PHP architecture.

This generator completely eliminates LLM-generated PHP code. Instead:
1. The LLM outputs ONLY structured JSON describing the theme
2. The JSON is validated against a strict schema
3. Safe Jinja2 templates render the JSON into valid PHP files

This guarantees:
- No broken PHP syntax
- No invalid template structure
- No hallucinated functions
- No invalid filenames
- No Unicode corruption
- No WordPress preview white-screen
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ..llm.base import BaseLLMProvider
from ..prompts import (
    get_theme_spec_prompt,
    get_theme_spec_system_prompt,
    parse_llm_json_response,
)
from ..schema import ThemeSpecification, get_default_theme_spec, validate_theme_spec
from ..templates import ThemeRenderer
from ..utils.logger import get_logger

logger = get_logger(__name__)


class HybridWordPressGenerator:
    """Hybrid generator that uses JSON specifications and Jinja2 templates.

    This generator:
    1. Asks the LLM for a JSON theme specification (not PHP code)
    2. Validates the JSON against a strict schema
    3. Renders safe Jinja2 templates with the specification
    4. Produces guaranteed-valid WordPress theme files
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        output_dir: str = "output",
        config: dict[str, Any] | None = None,
    ):
        """Initialize the hybrid generator.

        Args:
            llm_provider: LLM provider for generating JSON specifications
            output_dir: Base output directory for generated themes
            config: Optional configuration dictionary
        """
        self.llm_provider = llm_provider
        self.output_dir = Path(str(output_dir).replace('\\', '/'))
        self.config = config or {}
        self.safe_mode = self.config.get("safe_mode", False)

        # Initialize template renderer
        self.renderer = ThemeRenderer(self.output_dir)

        # Store design images for vision-based generation
        self.design_images: list[dict[str, Any]] | None = None

        logger.info(f"Initialized HybridWordPressGenerator with output dir: {output_dir}")

        if self.safe_mode:
            logger.warning("Safe mode enabled - will use defaults if LLM fails")

    def generate(
        self,
        requirements: dict[str, Any],
        images: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate a complete WordPress theme from requirements.

        This method:
        1. Converts requirements to an LLM prompt
        2. Gets JSON specification from LLM
        3. Validates and parses the JSON
        4. Renders Jinja2 templates with the specification
        5. Returns path to the generated theme

        Args:
            requirements: Theme requirements (from prompt parser or GUI)
            images: Optional list of design mockup images

        Returns:
            Path to the generated theme directory

        Raises:
            ValueError: If generation fails
        """
        self.design_images = images

        # Extract information from requirements
        user_prompt = requirements.get("original_prompt", requirements.get("description", ""))
        theme_name = requirements.get("theme_name", "wpgen-theme")
        design_profile = requirements.get("design_profile")

        # Check for feature flags
        woocommerce_enabled = "woocommerce" in str(requirements.get("features", [])).lower()
        dark_mode_enabled = "dark" in str(requirements.get("features", [])).lower()

        logger.info(f"Starting hybrid theme generation: {theme_name}")

        # Step 1: Analyze images if provided
        image_analysis = None
        if images and self.llm_provider:
            logger.info(f"Analyzing {len(images)} design reference images...")
            image_analysis = self._analyze_design_images(images)

        # Step 2: Generate JSON specification from LLM
        logger.info("Requesting JSON theme specification from LLM...")
        spec = self._get_theme_specification(
            user_prompt=user_prompt,
            design_profile=design_profile,
            woocommerce_enabled=woocommerce_enabled,
            dark_mode_enabled=dark_mode_enabled,
            image_analysis=image_analysis,
            fallback_name=theme_name,
        )

        # Step 3: Override with explicit requirements if provided
        spec = self._apply_requirements_overrides(spec, requirements)

        # Step 4: Render theme using Jinja2 templates
        logger.info(f"Rendering theme: {spec.theme_display_name}")
        theme_dir = self.renderer.render(spec, images)

        # Step 5: Post-generation validation
        self._validate_generated_theme(theme_dir)

        logger.info(f"Successfully generated theme: {theme_dir}")
        return theme_dir

    def _analyze_design_images(self, images: list[dict[str, Any]]) -> str | None:
        """Analyze design images to extract visual information.

        Args:
            images: List of image data dictionaries

        Returns:
            Text analysis of the images or None
        """
        try:
            prompt = """Analyze these design mockup images and describe:
1. Color scheme (identify hex colors if visible)
2. Typography style (modern, classic, bold, minimal)
3. Layout structure (header style, hero section, content areas)
4. Visual style (minimalist, corporate, creative, ecommerce)
5. Key UI components visible (buttons, cards, navigation)

Be specific and concise. Focus on extractable design decisions."""

            response = self.llm_provider.generate_code(
                prompt,
                language="text",
                context={},
                images=images,
            )

            return response.strip() if response else None

        except Exception as e:
            logger.warning(f"Image analysis failed: {e}")
            return None

    def _get_theme_specification(
        self,
        user_prompt: str,
        design_profile: dict[str, Any] | None,
        woocommerce_enabled: bool,
        dark_mode_enabled: bool,
        image_analysis: str | None,
        fallback_name: str,
    ) -> ThemeSpecification:
        """Get theme specification from LLM.

        Args:
            user_prompt: User's description of desired theme
            design_profile: Optional design profile to apply
            woocommerce_enabled: Whether WooCommerce is requested
            dark_mode_enabled: Whether dark mode is requested
            image_analysis: Optional image analysis text
            fallback_name: Fallback theme name if parsing fails

        Returns:
            Validated ThemeSpecification
        """
        # Build the prompt
        prompt = get_theme_spec_prompt(
            user_prompt=user_prompt,
            design_profile=design_profile,
            woocommerce_enabled=woocommerce_enabled,
            dark_mode_enabled=dark_mode_enabled,
            image_analysis=image_analysis,
        )

        system_prompt = get_theme_spec_system_prompt()

        # Call LLM
        try:
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )

            logger.debug(f"LLM response length: {len(response) if response else 0}")

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            if self.safe_mode:
                logger.warning("Safe mode: Using default specification")
                spec = get_default_theme_spec()
                spec.theme_name = fallback_name
                return spec
            raise ValueError(f"LLM generation failed: {e}")

        # Parse and validate JSON response
        success, spec, errors = parse_llm_json_response(
            response,
            fallback_to_defaults=self.safe_mode,
        )

        if errors:
            for error in errors:
                logger.warning(f"JSON parsing: {error}")

        if not success or spec is None:
            if self.safe_mode:
                logger.warning("Safe mode: Using default specification")
                spec = get_default_theme_spec()
                spec.theme_name = fallback_name
            else:
                raise ValueError(f"Failed to parse theme specification: {errors}")

        return spec

    def _apply_requirements_overrides(
        self,
        spec: ThemeSpecification,
        requirements: dict[str, Any],
    ) -> ThemeSpecification:
        """Apply explicit requirement overrides to specification.

        Args:
            spec: Base specification from LLM
            requirements: Requirements dictionary with overrides

        Returns:
            Modified specification
        """
        # Override theme name if specified
        if requirements.get("theme_name"):
            spec.theme_name = requirements["theme_name"]

        if requirements.get("theme_display_name"):
            spec.theme_display_name = requirements["theme_display_name"]

        if requirements.get("description"):
            spec.description = requirements["description"]

        # Apply design profile colors if available
        design_profile = requirements.get("design_profile")
        if design_profile and isinstance(design_profile, dict):
            if "colors" in design_profile:
                for key, value in design_profile["colors"].items():
                    if hasattr(spec.colors, key):
                        setattr(spec.colors, key, value)

            if "fonts" in design_profile:
                fonts = design_profile["fonts"]
                if "primary" in fonts:
                    spec.typography.font_primary = fonts["primary"]
                if "headings" in fonts:
                    spec.typography.font_headings = fonts["headings"]

        # Apply feature flags
        features = requirements.get("features", [])
        if isinstance(features, list):
            features_str = " ".join(str(f).lower() for f in features)
            if "woocommerce" in features_str or "ecommerce" in features_str:
                spec.features.woocommerce.enabled = True
            if "dark" in features_str:
                spec.features.dark_mode = True

        return spec

    def _validate_generated_theme(self, theme_dir: str) -> None:
        """Validate the generated theme.

        Args:
            theme_dir: Path to generated theme directory

        Raises:
            ValueError: If validation fails
        """
        theme_path = Path(theme_dir)

        # Check required files exist
        required_files = [
            "style.css",
            "index.php",
            "header.php",
            "footer.php",
            "functions.php",
        ]

        missing = []
        for filename in required_files:
            if not (theme_path / filename).exists():
                missing.append(filename)

        if missing:
            raise ValueError(f"Generated theme missing required files: {', '.join(missing)}")

        # Verify style.css has valid header
        style_css = theme_path / "style.css"
        content = style_css.read_text(encoding="utf-8")

        if "Theme Name:" not in content:
            raise ValueError("style.css missing Theme Name header")

        # Check for empty files
        for php_file in theme_path.glob("*.php"):
            file_content = php_file.read_text(encoding="utf-8")
            if len(file_content.strip()) < 50:
                logger.warning(f"Warning: {php_file.name} appears to be minimal")

        logger.info("Theme validation passed")


def create_hybrid_generator(
    llm_provider: BaseLLMProvider,
    output_dir: str = "output",
    config: dict[str, Any] | None = None,
) -> HybridWordPressGenerator:
    """Factory function to create a hybrid generator.

    Args:
        llm_provider: LLM provider for JSON generation
        output_dir: Output directory for themes
        config: Optional configuration

    Returns:
        Configured HybridWordPressGenerator instance
    """
    return HybridWordPressGenerator(
        llm_provider=llm_provider,
        output_dir=output_dir,
        config=config,
    )
