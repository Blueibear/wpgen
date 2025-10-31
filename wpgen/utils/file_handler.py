"""File handler utilities for processing uploaded files.

Handles image processing, text extraction from various file formats,
and preparing files for LLM multi-modal context.
"""

import base64
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import mimetypes

from ..utils.logger import get_logger


logger = get_logger(__name__)


class FileHandler:
    """Handle file uploads and process them for LLM context."""

    SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    SUPPORTED_TEXT_FORMATS = [".txt", ".md", ".markdown"]
    SUPPORTED_DOC_FORMATS = [".pdf"]

    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_TEXT_SIZE = 1 * 1024 * 1024   # 1MB

    def __init__(self):
        """Initialize file handler."""
        logger.info("Initialized FileHandler")

    def process_uploads(
        self,
        image_files: Optional[List[str]] = None,
        text_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Process all uploaded files and prepare them for LLM context.

        Args:
            image_files: List of image file paths
            text_files: List of text/document file paths

        Returns:
            Dictionary containing processed files and extracted content:
            {
                "images": [{"path": str, "data": str, "mime_type": str}, ...],
                "text_content": str,
                "file_descriptions": [str, ...]
            }
        """
        result = {
            "images": [],
            "text_content": "",
            "file_descriptions": []
        }

        # Process images
        if image_files:
            for image_path in image_files:
                try:
                    image_data = self.process_image(image_path)
                    if image_data:
                        result["images"].append(image_data)
                        result["file_descriptions"].append(
                            f"Image: {Path(image_path).name}"
                        )
                except Exception as e:
                    logger.error(f"Failed to process image {image_path}: {str(e)}")

        # Process text files
        if text_files:
            for text_path in text_files:
                try:
                    content = self.process_text_file(text_path)
                    if content:
                        result["text_content"] += f"\n\n--- Content from {Path(text_path).name} ---\n{content}"
                        result["file_descriptions"].append(
                            f"Document: {Path(text_path).name}"
                        )
                except Exception as e:
                    logger.error(f"Failed to process text file {text_path}: {str(e)}")

        logger.info(
            f"Processed {len(result['images'])} images and "
            f"{len(result['file_descriptions']) - len(result['images'])} text files"
        )

        return result

    def process_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Process a single image file.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary with image data:
            {
                "path": str,
                "data": str (base64),
                "mime_type": str,
                "size": int
            }
        """
        path = Path(image_path)

        if not path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return None

        if path.suffix.lower() not in self.SUPPORTED_IMAGE_FORMATS:
            logger.warning(f"Unsupported image format: {path.suffix}")
            return None

        file_size = path.stat().st_size
        if file_size > self.MAX_IMAGE_SIZE:
            logger.warning(f"Image file too large: {file_size} bytes (max {self.MAX_IMAGE_SIZE})")
            return None

        try:
            with open(path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            mime_type, _ = mimetypes.guess_type(str(path))
            if not mime_type:
                mime_type = "image/jpeg"  # Default

            logger.info(f"Processed image: {path.name} ({file_size} bytes)")

            return {
                "path": str(path),
                "data": image_data,
                "mime_type": mime_type,
                "size": file_size,
                "name": path.name
            }

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return None

    def process_text_file(self, file_path: str) -> Optional[str]:
        """Process a text file and extract its content.

        Args:
            file_path: Path to the text file

        Returns:
            Extracted text content
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"Text file not found: {file_path}")
            return None

        file_size = path.stat().st_size
        if file_size > self.MAX_TEXT_SIZE:
            logger.warning(f"Text file too large: {file_size} bytes (max {self.MAX_TEXT_SIZE})")
            return None

        try:
            # Handle text and markdown files
            if path.suffix.lower() in self.SUPPORTED_TEXT_FORMATS:
                content = path.read_text(encoding="utf-8")
                logger.info(f"Extracted text from {path.name} ({len(content)} chars)")
                return content

            # Handle PDF files (basic extraction)
            elif path.suffix.lower() in self.SUPPORTED_DOC_FORMATS:
                content = self._extract_pdf_text(path)
                if content:
                    logger.info(f"Extracted text from PDF {path.name} ({len(content)} chars)")
                return content

            else:
                logger.warning(f"Unsupported text file format: {path.suffix}")
                return None

        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            return None

    def _extract_pdf_text(self, pdf_path: Path) -> Optional[str]:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text content
        """
        try:
            # Try using PyPDF2 if available
            try:
                import PyPDF2

                with open(pdf_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return text.strip()

            except ImportError:
                logger.warning("PyPDF2 not installed, cannot extract PDF text")
                return f"[PDF file: {pdf_path.name} - install PyPDF2 to extract text]"

        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return f"[PDF file: {pdf_path.name} - error extracting text]"

    def validate_upload(self, file_path: str) -> Tuple[bool, str]:
        """Validate an uploaded file.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path:
            return False, "No file provided"

        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        suffix = path.suffix.lower()

        # Check if it's a supported format
        all_supported = (
            self.SUPPORTED_IMAGE_FORMATS +
            self.SUPPORTED_TEXT_FORMATS +
            self.SUPPORTED_DOC_FORMATS
        )

        if suffix not in all_supported:
            return False, f"Unsupported file format: {suffix}"

        # Check file size
        file_size = path.stat().st_size

        if suffix in self.SUPPORTED_IMAGE_FORMATS:
            if file_size > self.MAX_IMAGE_SIZE:
                return False, f"Image too large (max {self.MAX_IMAGE_SIZE // 1024 // 1024}MB)"
        else:
            if file_size > self.MAX_TEXT_SIZE:
                return False, f"File too large (max {self.MAX_TEXT_SIZE // 1024 // 1024}MB)"

        return True, ""
