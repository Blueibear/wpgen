"""Text processing utilities for WPGen.

This module provides text extraction and processing capabilities for
various file formats including markdown, plain text, and PDFs.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class TextProcessor:
    """Process and extract text from various file formats."""

    def __init__(self):
        """Initialize text processor."""
        logger.info("Initialized TextProcessor")

    def process_text_file(self, file_path: str) -> Dict[str, Any]:
        """Process a text file and extract structured content.

        Args:
            file_path: Path to the text file

        Returns:
            Dictionary containing:
                - content: str - Full text content
                - summary: str - Brief summary
                - sections: List[Dict] - Detected sections
                - metadata: Dict - File metadata
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return self._empty_result()

        logger.info(f"Processing text file: {path.name}")

        result = {
            "content": "",
            "summary": "",
            "sections": [],
            "metadata": {
                "filename": path.name,
                "extension": path.suffix,
                "size": path.stat().st_size,
            },
        }

        try:
            # Extract content based on file type
            if path.suffix.lower() == ".pdf":
                result["content"] = self._extract_from_pdf(path)
            elif path.suffix.lower() in [".md", ".markdown"]:
                result["content"] = self._extract_from_markdown(path)
                result["sections"] = self._parse_markdown_sections(result["content"])
            else:
                result["content"] = self._extract_from_text(path)

            # Generate summary
            result["summary"] = self._generate_summary(result["content"])

            logger.info(f"Extracted {len(result['content'])} characters from {path.name}")

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")
            result["error"] = str(e)

        return result

    def _extract_from_pdf(self, path: Path) -> str:
        """Extract text from PDF file.

        Args:
            path: Path to PDF file

        Returns:
            Extracted text content
        """
        try:
            import PyPDF2

            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []

                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

                content = "\n\n".join(text_parts)
                return content.strip()

        except ImportError:
            logger.warning("PyPDF2 not installed, cannot extract PDF text")
            return f"[PDF file: {path.name} - PyPDF2 required for text extraction]"
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            return f"[PDF file: {path.name} - extraction failed: {str(e)}]"

    def _extract_from_markdown(self, path: Path) -> str:
        """Extract text from Markdown file.

        Args:
            path: Path to markdown file

        Returns:
            Markdown content
        """
        try:
            content = path.read_text(encoding="utf-8")
            return content
        except Exception as e:
            logger.error(f"Markdown extraction error: {str(e)}")
            return ""

    def _extract_from_text(self, path: Path) -> str:
        """Extract text from plain text file.

        Args:
            path: Path to text file

        Returns:
            Text content
        """
        try:
            content = path.read_text(encoding="utf-8")
            return content
        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            return ""

    def _parse_markdown_sections(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Parse markdown content into sections.

        Args:
            markdown_content: Markdown text

        Returns:
            List of section dictionaries with title and content
        """
        sections = []

        # Split by headers (# Header)
        lines = markdown_content.split("\n")
        current_section = None

        for line in lines:
            # Check if line is a header
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if header_match:
                # Save previous section
                if current_section:
                    sections.append(current_section)

                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                current_section = {"level": level, "title": title, "content": []}
            elif current_section:
                current_section["content"].append(line)

        # Add last section
        if current_section:
            current_section["content"] = "\n".join(current_section["content"]).strip()
            sections.append(current_section)

        return sections

    def _generate_summary(self, content: str, max_length: int = 300) -> str:
        """Generate a brief summary of text content.

        Args:
            content: Full text content
            max_length: Maximum summary length

        Returns:
            Summary text
        """
        if not content:
            return ""

        # Clean and normalize
        content = re.sub(r"\s+", " ", content).strip()

        # Take first paragraph or first max_length characters
        paragraphs = content.split("\n\n")
        if paragraphs and len(paragraphs[0]) < max_length:
            return paragraphs[0]

        # Truncate at sentence boundary
        if len(content) <= max_length:
            return content

        truncated = content[:max_length]
        last_period = truncated.rfind(".")
        if last_period > max_length // 2:
            return truncated[: last_period + 1]

        return truncated + "..."

    def batch_process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple text files in batch.

        Args:
            file_paths: List of file paths

        Returns:
            Dictionary containing:
                - files: List of processed file results
                - combined_content: str - All content combined
                - total_size: int - Total characters
        """
        logger.info(f"Batch processing {len(file_paths)} text files")

        results = {"files": [], "combined_content": "", "total_size": 0}

        content_parts = []

        for file_path in file_paths:
            processed = self.process_text_file(file_path)
            results["files"].append(processed)

            if processed.get("content"):
                # Add file separator
                file_header = f"\n\n{'='*60}\nFILE: {processed['metadata']['filename']}\n{'='*60}\n"
                content_parts.append(file_header + processed["content"])
                results["total_size"] += len(processed["content"])

        results["combined_content"] = "\n".join(content_parts)

        logger.info(
            f"Batch processed {len(file_paths)} files, total {results['total_size']} characters"
        )

        return results

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure.

        Returns:
            Empty result dictionary
        """
        return {"content": "", "summary": "", "sections": [], "metadata": {}}

    def create_structured_context(
        self,
        user_prompt: str,
        image_summaries: Optional[str] = None,
        text_content: Optional[str] = None,
        file_descriptions: Optional[List[str]] = None,
    ) -> str:
        """Create a well-structured context for LLM from all inputs.

        Args:
            user_prompt: User's natural language description
            image_summaries: Summarized image analysis
            text_content: Combined text from uploaded files
            file_descriptions: List of file descriptions

        Returns:
            Formatted context string
        """
        sections = []

        # Header
        sections.append("=" * 80)
        sections.append("WORDPRESS THEME GENERATION REQUEST")
        sections.append("=" * 80)

        # User's prompt description
        sections.append("\n### USER DESCRIPTION")
        sections.append("-" * 40)
        sections.append(user_prompt)

        # Image analysis
        if image_summaries:
            sections.append("\n### VISUAL DESIGN REFERENCES")
            sections.append("-" * 40)
            sections.append(image_summaries)

        # Uploaded text content
        if text_content:
            sections.append("\n### CONTENT FROM UPLOADED FILES")
            sections.append("-" * 40)
            sections.append(text_content)

        # File list
        if file_descriptions:
            sections.append("\n### UPLOADED FILES")
            sections.append("-" * 40)
            for desc in file_descriptions:
                sections.append(f"  • {desc}")

        # Footer
        sections.append("\n" + "=" * 80)
        sections.append("END OF CONTEXT")
        sections.append("=" * 80 + "\n")

        return "\n".join(sections)

    def extract_key_requirements(self, text: str) -> Dict[str, List[str]]:
        """Extract key requirements from text using pattern matching.

        Args:
            text: Text content to analyze

        Returns:
            Dictionary of extracted requirements
        """
        requirements = {"features": [], "pages": [], "colors": [], "fonts": []}

        # Feature keywords
        feature_patterns = [
            r"\b(blog|portfolio|gallery|contact\s*form|testimonials|pricing)\b",
            r"\b(e-?commerce|shop|cart|checkout)\b",
            r"\b(newsletter|subscription|email)\b",
        ]

        # Page keywords
        page_patterns = [
            r"\b(home|about|contact|services|products)\s*(page)?\b",
            r"\b(landing\s*page|splash\s*page)\b",
        ]

        # Color keywords
        color_patterns = [
            r"\b(dark|light|bright|muted)\s*(theme|color|scheme)?\b",
            r"#[0-9a-fA-F]{3,6}\b",  # Hex colors
            r"\b(blue|red|green|orange|purple|pink|black|white|gray|grey)\b",
        ]

        text_lower = text.lower()

        # Extract features
        for pattern in feature_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            requirements["features"].extend(matches)

        # Extract pages
        for pattern in page_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if isinstance(matches[0], tuple):
                requirements["pages"].extend([m[0] for m in matches])
            else:
                requirements["pages"].extend(matches)

        # Extract colors
        for pattern in color_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            requirements["colors"].extend(matches)

        # Remove duplicates and clean
        for key in requirements:
            requirements[key] = list(set([str(item).strip() for item in requirements[key] if item]))

        return requirements
