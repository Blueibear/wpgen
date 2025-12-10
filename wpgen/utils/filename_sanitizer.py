"""Filename sanitizer for WordPress theme generation.

This module prevents filename corruption bugs like file.php.php, page-style.css.php, etc.
It ensures all filenames are valid and properly formatted.

Key features:
- Lowercase filenames only
- Valid WordPress template names only
- No spaces, Unicode icons, or emojis
- No injection of user strings into filenames
- Double extension prevention
"""

import re
import unicodedata
from pathlib import Path
from .logger import get_logger

logger = get_logger(__name__)


# Unicode categories to strip (invisible/control characters, emojis, symbols)
STRIP_UNICODE_CATEGORIES = {
    'Cc',  # Control characters
    'Cf',  # Format characters (including BOM, zero-width chars)
    'Co',  # Private use
    'Cs',  # Surrogate
    'Mn',  # Non-spacing marks
    'So',  # Other symbols (emojis, etc.)
}


def strip_unicode_special_chars(text: str) -> str:
    """Strip invisible Unicode characters, emojis, and special symbols from text.

    Args:
        text: Input text that may contain special characters

    Returns:
        Cleaned text with only safe ASCII and basic Unicode letters
    """
    if not text:
        return ""

    result = []
    for char in text:
        category = unicodedata.category(char)
        # Keep only letters, numbers, common punctuation, and spaces
        if category not in STRIP_UNICODE_CATEGORIES:
            # Also filter out most non-ASCII characters except basic letters
            if ord(char) < 128 or category.startswith('L'):
                result.append(char)

    return ''.join(result)


class FilenameSanitizer:
    """Sanitizer for WordPress theme filenames."""

    # Valid file extensions for WordPress themes
    VALID_EXTENSIONS = {
        '.php',
        '.css',
        '.js',
        '.json',
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.svg',
        '.webp',
        '.ico',
        '.woff',
        '.woff2',
        '.ttf',
        '.eot',
        '.md',
        '.txt',
        '.html',
        '.htm',
        '.pot',
        '.mo',
        '.po',
    }

    # Files that MUST be .php - comprehensive WordPress template list
    PHP_ONLY_FILES = {
        # Core templates
        'functions',
        'header',
        'footer',
        'index',
        'front-page',
        'home',
        'page',
        'single',
        'singular',
        'archive',
        'search',
        '404',
        'sidebar',
        'comments',
        # Archive templates
        'author',
        'category',
        'tag',
        'taxonomy',
        'date',
        # Post type templates
        'single-post',
        'single-page',
        'single-attachment',
        'attachment',
        'image',
        'video',
        'audio',
        # WooCommerce templates
        'woocommerce',
        'single-product',
        'archive-product',
        # Other templates
        'searchform',
        'content',
        'content-none',
        'content-page',
        'content-single',
        'content-search',
        'loop',
        'template-parts',
    }

    # Files that MUST be .css
    CSS_ONLY_FILES = {
        'style',
        'editor-style',
        'rtl',
        'print',
    }

    # Files that MUST be .js
    JS_ONLY_FILES = {
        'theme',
        'navigation',
        'customizer',
        'admin',
    }

    def __init__(self):
        """Initialize the filename sanitizer."""
        pass

    def sanitize(self, filename: str, default_ext: str = '.php') -> str:
        """Sanitize a filename to prevent corruption.

        Rules:
        1. Strip Unicode special chars, emojis, invisible characters
        2. Convert to lowercase
        3. Replace spaces/underscores with hyphens
        4. Strip all trailing extensions
        5. Add back ONLY the correct extension
        6. Never double-append extensions
        7. Ensure proper WordPress naming conventions

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
            sanitize('My Page 🚀.php') -> 'my-page.php'
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        original = filename

        # Step 1: Strip Unicode special characters (emojis, invisible chars)
        filename = strip_unicode_special_chars(filename)

        # Step 2: Convert to lowercase
        filename = filename.lower()

        # Step 3: Get base name and handle path separators
        path = Path(filename)
        name_with_ext = path.name

        # Step 4: Get the base name without any extensions
        name_parts = name_with_ext.split('.')
        base_name = name_parts[0]

        # Step 5: Replace spaces and underscores with hyphens
        base_name = re.sub(r'[\s_]+', '-', base_name)

        # Step 6: Remove any remaining invalid characters
        base_name = re.sub(r'[^a-z0-9-]', '', base_name)

        # Step 7: Remove multiple consecutive hyphens
        base_name = re.sub(r'-+', '-', base_name)

        # Step 8: Remove leading/trailing hyphens
        base_name = base_name.strip('-')

        # Step 9: Ensure we have a valid base name
        if not base_name:
            base_name = "file"

        # Step 10: Determine the correct extension
        correct_ext = self._determine_correct_extension(base_name, default_ext)

        # Step 11: Build the sanitized filename
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
            if check_name == php_file or check_name.startswith(f"{php_file}-"):
                return '.php'

        # Check if it's a CSS-only file
        for css_file in self.CSS_ONLY_FILES:
            if check_name == css_file or check_name.startswith(f"{css_file}-"):
                return '.css'

        # Check if it's a JS-only file (in assets context)
        for js_file in self.JS_ONLY_FILES:
            if check_name == js_file or check_name.startswith(f"{js_file}-"):
                return '.js'

        # Check for WooCommerce template files (always .php)
        if 'woocommerce' in check_name or 'product' in check_name:
            return '.php'

        # Check for template parts (always .php)
        if 'template' in check_name or 'content' in check_name or 'part' in check_name:
            return '.php'

        # Check for common patterns
        if check_name.endswith('-template') or check_name.startswith('template-'):
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
