"""Filename sanitizer for WordPress theme generation.

This module prevents filename corruption bugs like file.php.php, page-style.css.php, etc.
It ensures all filenames are valid and properly formatted.
"""

import re
from pathlib import Path
from .logger import get_logger

logger = get_logger(__name__)


class FilenameSanitizer:
    """Sanitizer for WordPress theme filenames."""

    # Valid file extensions for WordPress themes
    VALID_EXTENSIONS = {
        '.php',
        '.css',
        '.js',
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.svg',
        '.woff',
        '.woff2',
        '.ttf',
        '.eot',
        '.md',
        '.txt',
    }

    # Files that MUST be .php
    PHP_ONLY_FILES = {
        'functions',
        'header',
        'footer',
        'index',
        'front-page',
        'page',
        'single',
        'archive',
        'search',
        '404',
        'sidebar',
        'comments',
    }

    # Files that MUST be .css
    CSS_ONLY_FILES = {
        'style',
        'editor-style',
    }

    def __init__(self):
        """Initialize the filename sanitizer."""
        pass

    def sanitize(self, filename: str, default_ext: str = '.php') -> str:
        """Sanitize a filename to prevent corruption.

        Rules:
        1. Strip all trailing extensions
        2. Add back ONLY the correct extension
        3. Never double-append extensions
        4. Ensure proper WordPress naming conventions

        Args:
            filename: Original filename (may have incorrect extensions)
            default_ext: Default extension to use if none specified

        Returns:
            Sanitized filename

        Examples:
            sanitize('page.php.php') -> 'page.php'
            sanitize('style.css.php') -> 'style.css'
            sanitize('functions.php.css') -> 'functions.php'
            sanitize('header') -> 'header.php'
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        original = filename
        path = Path(filename)

        # Get the base name without any extensions
        name_parts = path.name.split('.')
        base_name = name_parts[0]

        # Determine the correct extension
        correct_ext = self._determine_correct_extension(base_name, default_ext)

        # Build the sanitized filename
        sanitized = f"{base_name}{correct_ext}"

        if sanitized != original:
            logger.info(f"Sanitized filename: '{original}' -> '{sanitized}'")

        return sanitized

    def _determine_correct_extension(self, base_name: str, default_ext: str) -> str:
        """Determine the correct file extension for a given base name.

        Args:
            base_name: Base filename without extension
            default_ext: Default extension to use

        Returns:
            Correct file extension (including the dot)
        """
        # Remove any WordPress subdirectory prefixes for checking
        check_name = base_name
        if '/' in check_name:
            check_name = check_name.split('/')[-1]

        # Check if it's a PHP-only file
        for php_file in self.PHP_ONLY_FILES:
            if check_name.startswith(php_file):
                return '.php'

        # Check if it's a CSS-only file
        for css_file in self.CSS_ONLY_FILES:
            if check_name.startswith(css_file):
                return '.css'

        # Check for WooCommerce template files (always .php)
        if 'woocommerce' in check_name or 'product' in check_name:
            return '.php'

        # Check for template parts (always .php)
        if 'template' in check_name or 'content' in check_name or 'part' in check_name:
            return '.php'

        # Default to provided extension
        if default_ext not in self.VALID_EXTENSIONS:
            logger.warning(f"Invalid default extension '{default_ext}', using '.php'")
            return '.php'

        return default_ext

    def validate(self, filename: str) -> tuple[bool, str]:
        """Validate a filename for common issues.

        Args:
            filename: Filename to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []

        if not filename:
            errors.append("Filename is empty")
            return False, "; ".join(errors)

        # Check for double extensions
        if filename.count('.') > 1:
            parts = filename.split('.')
            if len(parts) >= 3:
                # Check if last two are both extensions
                if f".{parts[-2]}" in self.VALID_EXTENSIONS and f".{parts[-1]}" in self.VALID_EXTENSIONS:
                    errors.append(f"Double extension detected: {parts[-2]}.{parts[-1]}")

        # Check for invalid characters
        if re.search(r'[<>:"|?*]', filename):
            errors.append("Filename contains invalid characters")

        # Check for spaces (should use hyphens)
        if ' ' in filename:
            errors.append("Filename contains spaces (use hyphens instead)")

        # Check extension validity
        ext = Path(filename).suffix
        if ext and ext not in self.VALID_EXTENSIONS:
            errors.append(f"Invalid file extension: {ext}")

        # Check for incorrect extension combinations
        name_parts = filename.split('.')
        if len(name_parts) >= 2:
            base = name_parts[0]
            ext = '.' + name_parts[-1]

            # Check if PHP-only file has wrong extension
            if base in self.PHP_ONLY_FILES and ext != '.php':
                errors.append(f"File '{base}' must have .php extension, not {ext}")

            # Check if CSS-only file has wrong extension
            if base in self.CSS_ONLY_FILES and ext != '.css':
                errors.append(f"File '{base}' must have .css extension, not {ext}")

        if errors:
            return False, "; ".join(errors)

        return True, ""

    def sanitize_path(self, filepath: str, default_ext: str = '.php') -> str:
        """Sanitize a full file path (including directories).

        Args:
            filepath: Full file path
            default_ext: Default extension for the filename

        Returns:
            Sanitized file path
        """
        path = Path(filepath)

        # Sanitize just the filename
        sanitized_name = self.sanitize(path.name, default_ext)

        # Rebuild the path
        if path.parent and str(path.parent) != '.':
            return str(path.parent / sanitized_name)
        else:
            return sanitized_name


# Convenience functions for direct use
def sanitize_filename(filename: str, default_ext: str = '.php') -> str:
    """Sanitize a filename to prevent corruption.

    Convenience function that creates a FilenameSanitizer instance.

    Args:
        filename: Original filename
        default_ext: Default extension to use

    Returns:
        Sanitized filename
    """
    sanitizer = FilenameSanitizer()
    return sanitizer.sanitize(filename, default_ext)


def validate_filename(filename: str) -> tuple[bool, str]:
    """Validate a filename for common issues.

    Convenience function that creates a FilenameSanitizer instance.

    Args:
        filename: Filename to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    sanitizer = FilenameSanitizer()
    return sanitizer.validate(filename)
