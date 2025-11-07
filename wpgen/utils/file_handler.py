"""File handler utilities for processing uploaded files.

Handles image processing, text extraction from various file formats,
and preparing files for LLM multi-modal context with security hardening.
"""

import base64
import mimetypes
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Handle file uploads and process them for LLM context with security hardening."""

    # Whitelisted file extensions
    SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    SUPPORTED_TEXT_FORMATS = [".txt", ".md", ".markdown"]
    SUPPORTED_DOC_FORMATS = [".pdf"]

    # Security limits (configurable via env vars)
    DEFAULT_MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25MB default
    DEFAULT_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    DEFAULT_MAX_TEXT_SIZE = 1 * 1024 * 1024  # 1MB
    DEFAULT_MAX_PDF_PAGES = 50  # Maximum PDF pages to process

    def __init__(
        self,
        max_upload_size: Optional[int] = None,
        max_image_size: Optional[int] = None,
        max_text_size: Optional[int] = None,
        max_pdf_pages: Optional[int] = None,
        temp_workspace: Optional[Path] = None,
    ):
        """Initialize file handler with security limits.

        Args:
            max_upload_size: Maximum upload size in bytes (default: 25MB)
            max_image_size: Maximum image size in bytes (default: 5MB)
            max_text_size: Maximum text file size in bytes (default: 1MB)
            max_pdf_pages: Maximum PDF pages to process (default: 50)
            temp_workspace: Temporary workspace directory (created if None)
        """
        # Load from env or use defaults
        self.max_upload_size = max_upload_size or int(
            os.getenv("WPGEN_MAX_UPLOAD_SIZE", self.DEFAULT_MAX_UPLOAD_SIZE)
        )
        self.max_image_size = max_image_size or int(
            os.getenv("WPGEN_MAX_IMAGE_SIZE", self.DEFAULT_MAX_IMAGE_SIZE)
        )
        self.max_text_size = max_text_size or int(
            os.getenv("WPGEN_MAX_TEXT_SIZE", self.DEFAULT_MAX_TEXT_SIZE)
        )
        self.max_pdf_pages = max_pdf_pages or int(
            os.getenv("WPGEN_MAX_PDF_PAGES", self.DEFAULT_MAX_PDF_PAGES)
        )

        # Create secure temp workspace
        if temp_workspace:
            self.temp_workspace = Path(temp_workspace)
            self.temp_workspace.mkdir(parents=True, exist_ok=True)
            self._owns_workspace = False
        else:
            self.temp_workspace = Path(tempfile.mkdtemp(prefix="wpgen-upload-"))
            self._owns_workspace = True

        logger.info(
            f"Initialized FileHandler with workspace: {self.temp_workspace} "
            f"(max_upload: {self.max_upload_size // 1024 // 1024}MB)"
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp workspace."""
        self.cleanup()

    def cleanup(self):
        """Clean up temporary workspace."""
        if self._owns_workspace and self.temp_workspace.exists():
            try:
                shutil.rmtree(self.temp_workspace)
                logger.info(f"Cleaned up temp workspace: {self.temp_workspace}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp workspace: {e}")

    def process_uploads(
        self, image_files: Optional[List[str]] = None, text_files: Optional[List[str]] = None
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
        result = {"images": [], "text_content": "", "file_descriptions": []}

        # Process images
        if image_files:
            for image_path in image_files:
                try:
                    image_data = self.process_image(image_path)
                    if image_data:
                        result["images"].append(image_data)
                        result["file_descriptions"].append(f"Image: {Path(image_path).name}")
                except Exception as e:
                    logger.error(f"Failed to process image {image_path}: {str(e)}")

        # Process text files
        if text_files:
            for text_path in text_files:
                try:
                    content = self.process_text_file(text_path)
                    if content:
                        result[
                            "text_content"
                        ] += f"\n\n--- Content from {Path(text_path).name} ---\n{content}"
                        result["file_descriptions"].append(f"Document: {Path(text_path).name}")
                except Exception as e:
                    logger.error(f"Failed to process text file {text_path}: {str(e)}")

        logger.info(
            f"Processed {len(result['images'])} images and "
            f"{len(result['file_descriptions']) - len(result['images'])} text files"
        )

        return result

    def _secure_copy_to_workspace(self, file_path: str) -> Optional[Path]:
        """Securely copy file to temp workspace with path validation.

        Args:
            file_path: Original file path

        Returns:
            Path to copied file in workspace, or None if failed
        """
        try:
            src = Path(file_path).resolve()
            if not src.exists():
                logger.warning(f"Source file not found: {file_path}")
                return None

            # Prevent path traversal attacks
            safe_name = Path(src.name).name  # Strip any directory components
            dest = (self.temp_workspace / safe_name).resolve()

            # Ensure destination is within workspace
            if not str(dest).startswith(str(self.temp_workspace.resolve())):
                logger.error(f"Path traversal attempt detected: {file_path}")
                return None

            # Copy file
            shutil.copy2(src, dest)
            return dest

        except Exception as e:
            logger.error(f"Failed to copy file to workspace: {e}")
            return None

    def process_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Process a single image file with EXIF orientation fix.

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
        if file_size > self.max_image_size:
            logger.warning(
                f"Image file too large: {file_size} bytes (max {self.max_image_size})"
            )
            return None

        try:
            # Try to apply EXIF orientation fix if Pillow is available
            image_data = None
            try:
                from PIL import Image, ImageOps

                # Open and auto-orient image
                with Image.open(path) as img:
                    # Apply EXIF orientation
                    img = ImageOps.exif_transpose(img)

                    # Convert to RGB if necessary
                    if img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGB")

                    # Save to temp workspace
                    temp_path = self.temp_workspace / f"processed_{path.name}"
                    img.save(temp_path, format=img.format or "JPEG")

                    # Read back as base64
                    with open(temp_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")

                    logger.info(f"Applied EXIF orientation fix to {path.name}")

            except ImportError:
                logger.debug("Pillow not available, skipping EXIF orientation fix")
                # Fallback: read raw file
                with open(path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")

            except Exception as pil_error:
                logger.warning(f"Image processing error, using raw file: {pil_error}")
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
                "name": path.name,
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
        if file_size > self.max_text_size:
            logger.warning(
                f"Text file too large: {file_size} bytes (max {self.max_text_size})"
            )
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
        """Extract text from a PDF file with page limit.

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
                    num_pages = len(reader.pages)

                    # Enforce page limit
                    if num_pages > self.max_pdf_pages:
                        logger.warning(
                            f"PDF has {num_pages} pages, limiting to {self.max_pdf_pages}"
                        )
                        num_pages = self.max_pdf_pages

                    text = ""
                    for i in range(num_pages):
                        page_text = reader.pages[i].extract_text()
                        text += page_text + "\n"

                    logger.info(f"Extracted text from {num_pages} pages of {pdf_path.name}")
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
            self.SUPPORTED_IMAGE_FORMATS + self.SUPPORTED_TEXT_FORMATS + self.SUPPORTED_DOC_FORMATS
        )

        if suffix not in all_supported:
            return False, f"Unsupported file format: {suffix}"

        # Check file size
        file_size = path.stat().st_size

        # Check overall upload size limit
        if file_size > self.max_upload_size:
            return False, f"File too large (max {self.max_upload_size // 1024 // 1024}MB)"

        if suffix in self.SUPPORTED_IMAGE_FORMATS:
            if file_size > self.max_image_size:
                return False, f"Image too large (max {self.max_image_size // 1024 // 1024}MB)"
        else:
            if file_size > self.max_text_size:
                return False, f"File too large (max {self.max_text_size // 1024 // 1024}MB)"

        return True, ""

    def create_zip(self, directory: str) -> Optional[str]:
        """Create a ZIP archive of a directory.

        Args:
            directory: Path to directory to zip

        Returns:
            Path to created ZIP file, or None if failed
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                logger.error(f"Directory not found: {directory}")
                return None

            zip_path = self.temp_workspace / f"{dir_path.name}.zip"

            import zipfile

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(dir_path)
                        zipf.write(file_path, arcname)

            logger.info(f"Created ZIP archive: {zip_path}")
            return str(zip_path)

        except Exception as e:
            logger.error(f"Failed to create ZIP: {e}")
            return None
