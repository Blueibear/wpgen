"""WordPress Template Hierarchy Validator.

This module enforces WordPress template naming conventions and prevents
invalid template files that cause Customizer white-screens and hierarchy failures.

Reference: https://developer.wordpress.org/themes/basics/template-hierarchy/
"""

import re
from pathlib import Path
from typing import Set
from .logger import get_logger

logger = get_logger(__name__)


class TemplateHierarchyValidator:
    """Validator for WordPress template hierarchy and naming conventions."""

    # Core WordPress template files (always lowercase, .php extension)
    CORE_TEMPLATES = {
        'index.php',
        'front-page.php',
        'home.php',
        'single.php',
        'page.php',
        'archive.php',
        'category.php',
        'tag.php',
        'taxonomy.php',
        'author.php',
        'date.php',
        'search.php',
        '404.php',
    }

    # Theme structure files (always lowercase, .php extension)
    STRUCTURE_FILES = {
        'functions.php',
        'header.php',
        'footer.php',
        'sidebar.php',
        'comments.php',
    }

    # WooCommerce template files (only when WooCommerce is enabled)
    WOOCOMMERCE_TEMPLATES = {
        'woocommerce.php',
        'archive-product.php',
        'single-product.php',
        'taxonomy-product_cat.php',
        'taxonomy-product_tag.php',
    }

    # Valid page template pattern: page-{slug}.php
    PAGE_TEMPLATE_PATTERN = re.compile(r'^page-[a-z0-9]+(-[a-z0-9]+)*\.php$')

    # Valid custom taxonomy template pattern: taxonomy-{taxonomy}(-{term})?.php
    TAXONOMY_TEMPLATE_PATTERN = re.compile(r'^taxonomy-[a-z0-9_]+(-[a-z0-9_-]+)?\.php$')

    # Valid custom post type template patterns
    CUSTOM_POST_TYPE_PATTERNS = [
        re.compile(r'^single-[a-z0-9_-]+\.php$'),  # single-{posttype}.php
        re.compile(r'^archive-[a-z0-9_-]+\.php$'),  # archive-{posttype}.php (not product)
    ]

    # Forbidden template names (common mistakes that break WordPress)
    FORBIDDEN_NAMES = {
        'Home.php',
        'Account.php',
        'Cart.php',
        'Product.php',
        'Category.php',
        'About.php',
        'Contact.php',
        'Service.php',
        'Services.php',
        'Portfolio.php',
        'Blog.php',
        'Shop.php',
    }

    # Files that must always be CSS
    CSS_ONLY_FILES = {
        'style.css',
        'editor-style.css',
    }

    def __init__(self):
        """Initialize the template hierarchy validator."""
        self._all_valid_core = self.CORE_TEMPLATES | self.STRUCTURE_FILES

    def is_valid_template_name(self, filename: str, woocommerce_enabled: bool = False) -> tuple[bool, str]:
        """Check if a template filename is valid according to WordPress hierarchy.

        Args:
            filename: Template filename to validate
            woocommerce_enabled: Whether WooCommerce support is enabled

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "Filename is empty"

        # Check for forbidden capitalized names
        if filename in self.FORBIDDEN_NAMES:
            lowercase_name = filename.lower()
            return False, f"Invalid capitalized template name '{filename}'. Use '{lowercase_name}' or 'page-{lowercase_name[:-4]}.php' instead"

        # Check for uppercase letters in PHP templates
        if filename.endswith('.php') and filename != filename.lower():
            return False, f"Template names must be lowercase: '{filename}' should be '{filename.lower()}'"

        # Allow CSS files
        if filename in self.CSS_ONLY_FILES:
            return True, ""

        # Check core templates
        if filename in self._all_valid_core:
            return True, ""

        # Check WooCommerce templates
        if woocommerce_enabled and filename in self.WOOCOMMERCE_TEMPLATES:
            return True, ""

        # Check page templates (page-{slug}.php)
        if self.PAGE_TEMPLATE_PATTERN.match(filename):
            return True, ""

        # Check taxonomy templates
        if self.TAXONOMY_TEMPLATE_PATTERN.match(filename):
            return True, ""

        # Check custom post type templates
        for pattern in self.CUSTOM_POST_TYPE_PATTERNS:
            if pattern.match(filename):
                # Ensure it's not a WooCommerce template without WooCommerce enabled
                if 'product' in filename and not woocommerce_enabled:
                    return False, f"WooCommerce template '{filename}' requires WooCommerce support to be enabled"
                return True, ""

        # Check template-parts (in subdirectories)
        if '/' in filename:
            parts = filename.split('/')
            if parts[0] == 'template-parts' and parts[-1].endswith('.php'):
                return True, ""

        # Not a recognized WordPress template
        return False, f"Unrecognized WordPress template: '{filename}'. Must follow WordPress template hierarchy naming conventions."

    def normalize_page_name(self, page_name: str) -> str:
        """Normalize a page name to WordPress-safe format.

        Args:
            page_name: Page name (may be capitalized or contain spaces)

        Returns:
            Normalized page name (lowercase, kebab-case)

        Examples:
            normalize_page_name("About") -> "about"
            normalize_page_name("Contact Us") -> "contact-us"
            normalize_page_name("FAQ") -> "faq"
            normalize_page_name("Product_Catalog") -> "product-catalog"
        """
        if not page_name:
            return ""

        # Convert to lowercase
        normalized = page_name.lower()

        # Replace underscores and spaces with hyphens
        normalized = re.sub(r'[_\s]+', '-', normalized)

        # Remove any characters that aren't alphanumeric or hyphens
        normalized = re.sub(r'[^a-z0-9-]+', '', normalized)

        # Remove consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)

        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')

        return normalized

    def get_page_template_filename(self, page_name: str) -> str:
        """Get the proper WordPress page template filename for a custom page.

        Args:
            page_name: Page name (may be capitalized)

        Returns:
            Proper WordPress page template filename (page-{slug}.php)

        Examples:
            get_page_template_filename("About") -> "page-about.php"
            get_page_template_filename("Contact Us") -> "page-contact-us.php"
        """
        normalized = self.normalize_page_name(page_name)
        if not normalized:
            raise ValueError(f"Invalid page name: '{page_name}'")

        return f"page-{normalized}.php"

    def validate_theme_templates(self, theme_dir: Path, woocommerce_enabled: bool = False) -> list[str]:
        """Validate all template files in a theme directory.

        Args:
            theme_dir: Path to theme directory
            woocommerce_enabled: Whether WooCommerce support is enabled

        Returns:
            List of error messages (empty if all valid)
        """
        errors = []

        if not theme_dir.exists():
            return [f"Theme directory does not exist: {theme_dir}"]

        # Check for required files
        index_php = theme_dir / "index.php"
        style_css = theme_dir / "style.css"

        if not index_php.exists():
            errors.append("Required file missing: index.php")

        if not style_css.exists():
            errors.append("Required file missing: style.css")

        # Validate all PHP and CSS files
        for php_file in theme_dir.rglob("*.php"):
            relative_path = php_file.relative_to(theme_dir)
            filename = str(relative_path)

            is_valid, error_msg = self.is_valid_template_name(filename, woocommerce_enabled)
            if not is_valid:
                errors.append(error_msg)

        for css_file in theme_dir.rglob("*.css"):
            relative_path = css_file.relative_to(theme_dir)
            # Only validate root-level CSS files
            if relative_path.parent == Path('.'):
                filename = str(relative_path)
                if filename not in self.CSS_ONLY_FILES and not filename.startswith('assets/'):
                    logger.warning(f"Unexpected CSS file in theme root: {filename}")

        return errors

    def suggest_valid_template_name(self, invalid_name: str) -> str:
        """Suggest a valid WordPress template name for an invalid one.

        Args:
            invalid_name: Invalid template name

        Returns:
            Suggested valid template name
        """
        # Remove extension
        name_without_ext = invalid_name
        if name_without_ext.endswith('.php'):
            name_without_ext = name_without_ext[:-4]

        # Normalize the name
        normalized = self.normalize_page_name(name_without_ext)

        # Check if it's a core template name
        if f"{normalized}.php" in self._all_valid_core:
            return f"{normalized}.php"

        # Otherwise, suggest page template format
        return f"page-{normalized}.php"


# Convenience functions
def validate_template_name(filename: str, woocommerce_enabled: bool = False) -> tuple[bool, str]:
    """Validate a WordPress template filename.

    Args:
        filename: Template filename
        woocommerce_enabled: Whether WooCommerce is enabled

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = TemplateHierarchyValidator()
    return validator.is_valid_template_name(filename, woocommerce_enabled)


def normalize_page_name(page_name: str) -> str:
    """Normalize a page name to WordPress-safe format.

    Args:
        page_name: Page name (may be capitalized)

    Returns:
        Normalized page name (lowercase, kebab-case)
    """
    validator = TemplateHierarchyValidator()
    return validator.normalize_page_name(page_name)


def get_page_template_filename(page_name: str) -> str:
    """Get proper WordPress page template filename.

    Args:
        page_name: Page name

    Returns:
        Page template filename (page-{slug}.php)
    """
    validator = TemplateHierarchyValidator()
    return validator.get_page_template_filename(page_name)
