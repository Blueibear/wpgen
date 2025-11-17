"""Image analysis utilities for WPGen.

This module provides comprehensive image analysis capabilities including:
- Vision-based image analysis using Claude/GPT-4 Vision
- Image captioning and description generation
- Layout and design pattern detection
- OCR fallback for text extraction from images
- Color palette extraction
"""

import base64
import io
from typing import Any

from PIL import Image

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ImageAnalyzer:
    """Analyze images for design insights and content extraction."""

    def __init__(self, llm_provider=None):
        """Initialize image analyzer.

        Args:
            llm_provider: Optional LLM provider with vision capabilities
        """
        self.llm_provider = llm_provider
        logger.info("Initialized ImageAnalyzer")

    def analyze_design_mockup(
        self, image_data: dict[str, Any], use_llm: bool = True
    ) -> dict[str, Any]:
        """Analyze a design mockup image for layout and styling insights.

        Args:
            image_data: Dictionary with 'data' (base64), 'mime_type', 'name'
            use_llm: Whether to use LLM vision for analysis

        Returns:
            Dictionary containing:
                - caption: str - Brief description of the image
                - layout_hints: list[str] - Detected layout patterns
                - color_notes: str - Color scheme observations
                - typography_notes: str - Typography observations
                - components: list[str] - Detected UI components
                - overall_style: str - Overall design style
        """
        logger.info(f"Analyzing design mockup: {image_data.get('name', 'unknown')}")

        analysis = {
            "caption": "",
            "layout_hints": [],
            "color_notes": "",
            "typography_notes": "",
            "components": [],
            "overall_style": "",
            "technical_details": {},
        }

        # Basic image analysis (dimensions, format)
        try:
            analysis["technical_details"] = self._get_image_metadata(image_data)
        except Exception as e:
            logger.warning(f"Could not extract image metadata: {str(e)}")

        # LLM-based vision analysis
        if use_llm and self.llm_provider:
            try:
                llm_analysis = self._analyze_with_vision(image_data)
                analysis.update(llm_analysis)
            except Exception as e:
                logger.error(f"LLM vision analysis failed: {str(e)}")
                # Continue with other analysis methods

        # Fallback: Basic color analysis
        if not analysis.get("color_notes"):
            try:
                color_info = self._extract_color_palette(image_data)
                analysis["color_notes"] = color_info
            except Exception as e:
                logger.warning(f"Color extraction failed: {str(e)}")

        # OCR fallback for text in images
        try:
            ocr_text = self._extract_text_ocr(image_data)
            if ocr_text:
                analysis["ocr_text"] = ocr_text
                logger.info(f"Extracted {len(ocr_text)} characters via OCR")
        except Exception as e:
            logger.debug(f"OCR extraction failed: {str(e)}")

        return analysis

    def _analyze_with_vision(self, image_data: dict[str, Any]) -> dict[str, Any]:
        """Use LLM vision capabilities to analyze the image.

        Args:
            image_data: Image data dictionary

        Returns:
            Analysis results from vision model
        """
        if not self.llm_provider:
            return {}

        logger.info("Using LLM vision for detailed image analysis")

        # Construct vision prompt
        vision_prompt = """Analyze this UI/design mockup image and provide detailed insights.

Please analyze the following aspects:

1. **Overall Layout**: Describe the page structure, grid system, and content organization
2. **Color Scheme**: Identify primary, secondary, and accent colors (provide hex codes if possible)
3. **Typography**: Describe font choices, heading styles, text hierarchy
4. **UI Components**: List visible components (navigation, buttons, cards, forms, etc.)
5. **Design Style**: Describe the overall aesthetic (modern, minimal, corporate, playful, etc.)
6. **Layout Patterns**: Identify any specific patterns (hero section, sidebar, grid, masonry, etc.)

Provide your analysis in this exact JSON format:
{
  "caption": "Brief one-sentence description of the page",
  "layout_hints": ["layout pattern 1", "layout pattern 2"],
  "color_notes": "Description of color scheme with hex codes if visible",
  "typography_notes": "Description of typography style",
  "components": ["component1", "component2"],
  "overall_style": "Design style description"
}

Return ONLY the JSON, no other text."""

        try:
            # Use the LLM's vision capability
            if hasattr(self.llm_provider, "analyze_image"):
                result = self.llm_provider.analyze_image(
                    image_data=image_data, prompt=vision_prompt
                )
            else:
                # Fallback: use the multi-modal analyze
                result = self.llm_provider.analyze_prompt_multimodal(
                    prompt="Analyze this design mockup image for WordPress theme creation.",
                    images=[image_data],
                    additional_context=vision_prompt,
                )

            # Parse the result
            if isinstance(result, dict):
                return result
            elif isinstance(result, str):
                import json

                # Try to extract JSON from the response
                result = result.strip()
                if result.startswith("```"):
                    lines = result.split("\n")
                    result = "\n".join(lines[1:-1]) if len(lines) > 2 else result
                    result = result.replace("```json", "").replace("```", "")
                return json.loads(result)

        except Exception as e:
            logger.error(f"Vision analysis failed: {str(e)}")
            return {}

    def _get_image_metadata(self, image_data: dict[str, Any]) -> dict[str, Any]:
        """Extract basic metadata from image.

        Args:
            image_data: Image data dictionary

        Returns:
            Dictionary with width, height, format, size
        """
        # Decode base64 image
        image_bytes = base64.b64decode(image_data["data"])
        img = Image.open(io.BytesIO(image_bytes))

        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "size_bytes": len(image_bytes),
        }

    def _extract_color_palette(self, image_data: dict[str, Any], max_colors: int = 5) -> str:
        """Extract dominant colors from image.

        Args:
            image_data: Image data dictionary
            max_colors: Maximum number of colors to extract

        Returns:
            String describing the color palette
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data["data"])
            img = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize for faster processing
            img.thumbnail((100, 100))

            # Get colors using PIL (basic approach)
            colors = img.getcolors(img.width * img.height)
            if colors:
                # Sort by frequency
                colors.sort(reverse=True, key=lambda x: x[0])

                # Convert top colors to hex
                hex_colors = []
                for count, color in colors[:max_colors]:
                    if isinstance(color, tuple) and len(color) >= 3:
                        hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
                        hex_colors.append(hex_color)

                if hex_colors:
                    return f"Dominant colors detected: {', '.join(hex_colors)}"

        except Exception as e:
            logger.debug(f"Color extraction error: {str(e)}")

        return "Color analysis not available"

    def _extract_text_ocr(self, image_data: dict[str, Any]) -> str | None:
        """Extract text from image using OCR (Tesseract fallback).

        Args:
            image_data: Image data dictionary

        Returns:
            Extracted text or None if OCR not available
        """
        try:
            import pytesseract
            from PIL import Image

            # Decode base64 image
            image_bytes = base64.b64decode(image_data["data"])
            img = Image.open(io.BytesIO(image_bytes))

            # Perform OCR
            text = pytesseract.image_to_string(img)

            # Clean up extracted text
            text = text.strip()

            if len(text) > 10:  # Only return if meaningful text found
                return text

        except ImportError:
            logger.debug("pytesseract not installed, skipping OCR")
        except Exception as e:
            logger.debug(f"OCR extraction failed: {str(e)}")

        return None

    def generate_image_summary(self, analyses: list[dict[str, Any]]) -> str:
        """Generate a comprehensive summary from multiple image analyses.

        Args:
            analyses: List of analysis dictionaries

        Returns:
            Formatted summary text
        """
        if not analyses:
            return ""

        summary_parts = ["=== IMAGE ANALYSIS SUMMARY ===\n"]

        for idx, analysis in enumerate(analyses, 1):
            summary_parts.append(f"\n--- Image {idx} ---")

            if analysis.get("caption"):
                summary_parts.append(f"Description: {analysis['caption']}")

            if analysis.get("overall_style"):
                summary_parts.append(f"Style: {analysis['overall_style']}")

            if analysis.get("layout_hints"):
                summary_parts.append(f"Layout: {', '.join(analysis['layout_hints'])}")

            if analysis.get("color_notes"):
                summary_parts.append(f"Colors: {analysis['color_notes']}")

            if analysis.get("typography_notes"):
                summary_parts.append(f"Typography: {analysis['typography_notes']}")

            if analysis.get("components"):
                summary_parts.append(f"Components: {', '.join(analysis['components'])}")

            if analysis.get("ocr_text"):
                # Include first 200 chars of OCR text
                ocr_preview = analysis["ocr_text"][:200]
                if len(analysis["ocr_text"]) > 200:
                    ocr_preview += "..."
                summary_parts.append(f"Text found: {ocr_preview}")

        summary_parts.append("\n" + "=" * 40)

        return "\n".join(summary_parts)

    def batch_analyze_images(
        self, images: list[dict[str, Any]], use_llm: bool = True
    ) -> list[dict[str, Any]]:
        """Analyze multiple images in batch.

        Args:
            images: List of image data dictionaries
            use_llm: Whether to use LLM vision

        Returns:
            List of analysis results
        """
        logger.info(f"Batch analyzing {len(images)} images")

        analyses = []
        for idx, image_data in enumerate(images):
            logger.info(f"Analyzing image {idx + 1}/{len(images)}")
            try:
                analysis = self.analyze_design_mockup(image_data, use_llm=use_llm)
                analysis["image_index"] = idx
                analysis["image_name"] = image_data.get("name", f"image_{idx}")
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze image {idx}: {str(e)}")
                # Add placeholder
                analyses.append(
                    {
                        "image_index": idx,
                        "image_name": image_data.get("name", f"image_{idx}"),
                        "caption": "Analysis failed",
                        "error": str(e),
                    }
                )

        return analyses
