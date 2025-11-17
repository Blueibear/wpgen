"""Advanced PHP validation module for WordPress theme generation.

This module provides comprehensive PHP syntax validation, brace matching,
and structure verification to ensure generated themes never break WordPress.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)


# WordPress function whitelist - only allow real WordPress functions
WORDPRESS_CORE_FUNCTIONS = {
    # Template tags
    'wp_head', 'wp_footer', 'body_class', 'post_class', 'get_header', 'get_footer',
    'get_sidebar', 'get_template_part', 'bloginfo', 'get_bloginfo', 'wp_title',
    'the_title', 'the_content', 'the_excerpt', 'the_permalink', 'the_post_thumbnail',
    'the_ID', 'the_author', 'the_date', 'get_the_date', 'the_time', 'get_the_time',
    'the_category', 'the_tags', 'the_archive_title', 'the_archive_description',
    'get_the_author', 'get_the_category', 'get_the_tags', 'get_the_title',

    # Loop functions
    'have_posts', 'the_post', 'rewind_posts', 'wp_reset_postdata', 'wp_reset_query',

    # Conditional tags
    'is_home', 'is_front_page', 'is_single', 'is_page', 'is_archive', 'is_category',
    'is_tag', 'is_404', 'is_search', 'is_singular', 'is_post_type_archive',
    'is_active_sidebar', 'has_post_thumbnail', 'comments_open', 'get_comments_number',

    # Navigation
    'wp_nav_menu', 'the_posts_navigation', 'the_posts_pagination', 'get_search_form',
    'paginate_links', 'next_post_link', 'previous_post_link',

    # Comments
    'comments_template', 'comment_form', 'wp_list_comments',

    # Widgets
    'dynamic_sidebar', 'register_sidebar', 'is_active_sidebar',

    # Custom logo
    'the_custom_logo', 'get_custom_logo', 'has_custom_logo',

    # Theme support
    'add_theme_support', 'register_nav_menus',

    # Enqueue scripts/styles
    'wp_enqueue_style', 'wp_enqueue_script', 'get_stylesheet_uri',
    'get_template_directory_uri', 'get_template_directory', 'get_stylesheet_directory',
    'get_stylesheet_directory_uri',

    # Security/escaping
    'esc_html', 'esc_attr', 'esc_url', 'esc_js', 'esc_html__', 'esc_attr__',
    'esc_html_e', 'esc_attr_e', 'wp_kses_post', 'sanitize_text_field',

    # Translation
    '__', '_e', '_x', '_ex', '_n', '_nx',

    # WooCommerce (if enabled)
    'woocommerce_content', 'woocommerce_breadcrumb', 'woocommerce_output_content_wrapper',
    'woocommerce_output_content_wrapper_end', 'is_woocommerce', 'is_shop', 'is_product',
    'is_cart', 'is_checkout', 'is_account_page',

    # Other common functions
    'wp_get_theme', 'get_option', 'get_theme_mod', 'wp_parse_args',
    'absint', 'intval', 'floatval', 'boolval',
}


# Hallucinated functions to detect and remove
HALLUCINATED_FUNCTIONS = {
    'post_loop',  # Not a real WordPress function
    'render_post',  # Not standard
    'display_post',  # Not standard
    'show_content',  # Not standard
}


class PHPValidationError(Exception):
    """Exception raised when PHP validation fails."""
    pass


class PHPValidator:
    """Advanced PHP validator with brace matching, structure validation, and syntax checking."""

    def __init__(self, php_path: str = "php"):
        """Initialize PHP validator.

        Args:
            php_path: Path to PHP binary (default: "php")
        """
        self.php_path = php_path
        self.php_available = self._check_php_available()

    def _check_php_available(self) -> bool:
        """Check if PHP CLI is available.

        Returns:
            True if PHP is available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.php_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.debug(f"PHP is available: {result.stdout.splitlines()[0]}")
                return True
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning(f"PHP CLI not available at '{self.php_path}'")
            return False

    def validate_php_syntax(self, php_code: str, filename: str = "generated.php") -> Tuple[bool, Optional[str]]:
        """Validate PHP syntax using PHP CLI if available.

        Args:
            php_code: PHP code to validate
            filename: Filename for error reporting

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.php_available:
            logger.warning("PHP CLI not available, using Python-based validation")
            return self._python_based_validation(php_code, filename)

        # Use PHP -l for syntax checking
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
                f.write(php_code)
                temp_path = f.name

            result = subprocess.run(
                [self.php_path, "-l", temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            Path(temp_path).unlink()

            if result.returncode == 0:
                logger.debug(f"✓ PHP syntax validation passed: {filename}")
                return True, None
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"✗ PHP syntax error in {filename}: {error_msg}")
                return False, error_msg

        except Exception as e:
            logger.warning(f"PHP validation failed: {e}, falling back to Python validation")
            return self._python_based_validation(php_code, filename)

    def _python_based_validation(self, php_code: str, filename: str) -> Tuple[bool, Optional[str]]:
        """Python-based PHP validation when PHP CLI is unavailable.

        Args:
            php_code: PHP code to validate
            filename: Filename for error reporting

        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []

        # Check for proper PHP tags
        if not ('<?php' in php_code or '<?=' in php_code or '<!DOCTYPE' in php_code):
            errors.append(f"{filename}: Missing PHP opening tag (<?php)")

        # Check for brace matching
        brace_valid, brace_error = self.check_brace_matching(php_code, filename)
        if not brace_valid:
            errors.append(brace_error)

        # Check for PHP open/close tag matching
        tag_valid, tag_error = self.check_php_tags(php_code, filename)
        if not tag_valid:
            errors.append(tag_error)

        # Check for stray closing braces outside PHP blocks
        stray_valid, stray_error = self.check_stray_braces(php_code, filename)
        if not stray_valid:
            errors.append(stray_error)

        if errors:
            return False, "; ".join(errors)

        logger.debug(f"✓ Python-based validation passed: {filename}")
        return True, None

    def check_brace_matching(self, php_code: str, filename: str = "file.php") -> Tuple[bool, Optional[str]]:
        """Check if braces {} are balanced inside PHP blocks.

        Args:
            php_code: PHP code to check
            filename: Filename for error reporting

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Extract PHP blocks
        php_blocks = self._extract_php_blocks(php_code)

        for i, block in enumerate(php_blocks):
            # Count braces
            open_count = block.count('{')
            close_count = block.count('}')

            if open_count != close_count:
                return False, (
                    f"{filename}: Mismatched braces in PHP block {i+1} "
                    f"({open_count} opening, {close_count} closing)"
                )

        return True, None

    def check_php_tags(self, php_code: str, filename: str = "file.php") -> Tuple[bool, Optional[str]]:
        """Check if PHP tags are properly matched.

        Args:
            php_code: PHP code to check
            filename: Filename for error reporting

        Returns:
            Tuple of (is_valid, error_message)
        """
        # For template files with HTML, we don't need closing tags
        # Just check that opening tags are valid
        if '<!DOCTYPE' in php_code or '<html' in php_code:
            # This is an HTML template file, just check for valid opening tags
            php_opens = re.findall(r'<\?(?:php|=)', php_code)
            if not php_opens:
                # Pure HTML file (like header.php might be), that's ok
                return True, None
            return True, None

        # For pure PHP files, check tag matching
        php_opens = len(re.findall(r'<\?php', php_code))
        php_closes = php_code.count('?>')

        # It's ok to have more opens than closes (modern PHP doesn't require closing tags)
        if php_opens < php_closes:
            return False, f"{filename}: More PHP closing tags (?>) than opening tags (<?php)"

        return True, None

    def check_stray_braces(self, php_code: str, filename: str = "file.php") -> Tuple[bool, Optional[str]]:
        """Check for stray closing braces outside PHP blocks.

        Args:
            php_code: PHP code to check
            filename: Filename for error reporting

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove PHP blocks
        without_php = php_code
        for block in self._extract_php_blocks(php_code):
            without_php = without_php.replace(block, '', 1)

        # Check for braces in remaining HTML
        if '}' in without_php:
            return False, f"{filename}: Found stray closing brace '}}' outside PHP block"

        return True, None

    def _extract_php_blocks(self, php_code: str) -> List[str]:
        """Extract all PHP code blocks from a file.

        Args:
            php_code: PHP code

        Returns:
            List of PHP blocks
        """
        blocks = []

        # Find all <?php ... ?> blocks
        pattern = r'<\?php(.*?)(?:\?>|$)'
        matches = re.findall(pattern, php_code, re.DOTALL)
        blocks.extend(matches)

        # Find all <?= ... ?> blocks
        pattern = r'<\?=(.*?)(?:\?>|$)'
        matches = re.findall(pattern, php_code, re.DOTALL)
        blocks.extend(matches)

        return blocks

    def auto_fix_braces(self, php_code: str, filename: str = "file.php") -> Tuple[str, List[str]]:
        """Auto-fix brace mismatches in PHP code.

        Args:
            php_code: PHP code to fix
            filename: Filename for logging

        Returns:
            Tuple of (fixed_code, list_of_fixes_applied)
        """
        fixes = []

        # Extract PHP blocks and fix each one
        php_blocks = re.finditer(r'(<\?php.*?)(?=<\?php|$)', php_code, re.DOTALL)

        fixed_code = php_code
        for match in php_blocks:
            block = match.group(1)
            open_count = block.count('{')
            close_count = block.count('}')

            if open_count > close_count:
                # Add missing closing braces
                missing = open_count - close_count
                fixed_block = block + ('\n}' * missing)
                fixed_code = fixed_code.replace(block, fixed_block, 1)
                fixes.append(f"Added {missing} missing closing brace(s) in {filename}")
                logger.info(f"Auto-fixed: Added {missing} closing brace(s) in {filename}")

            elif close_count > open_count:
                # Remove extra closing braces
                extra = close_count - open_count
                # Remove from the end
                fixed_block = block
                for _ in range(extra):
                    fixed_block = fixed_block.rsplit('}', 1)[0]
                fixed_code = fixed_code.replace(block, fixed_block, 1)
                fixes.append(f"Removed {extra} extra closing brace(s) in {filename}")
                logger.info(f"Auto-fixed: Removed {extra} closing brace(s) in {filename}")

        return fixed_code, fixes

    def check_required_structure(self, php_code: str, file_type: str, filename: str = "file.php") -> Tuple[bool, List[str]]:
        """Check if PHP file has required WordPress structures.

        Args:
            php_code: PHP code to check
            file_type: Type of file (header, footer, functions, etc.)
            filename: Filename for error reporting

        Returns:
            Tuple of (is_valid, list_of_missing_elements)
        """
        missing = []

        if file_type == 'header':
            required = [
                ('<!DOCTYPE html>', 'DOCTYPE declaration'),
                ('<html', 'html tag'),
                ('<head>', 'head tag'),
                ('wp_head()', 'wp_head() hook'),
                ('<body', 'body tag'),
                ('site-header', '.site-header class or id'),
            ]

            for item, description in required:
                if item not in php_code:
                    missing.append(f"{filename}: Missing {description}")

        elif file_type == 'footer':
            required = [
                ('</main>', 'closing main tag (or similar content wrapper)'),
                ('<footer', 'footer tag'),
                ('wp_footer()', 'wp_footer() hook'),
                ('</body>', 'closing body tag'),
                ('</html>', 'closing html tag'),
            ]

            for item, description in required:
                if item not in php_code:
                    missing.append(f"{filename}: Missing {description}")

        elif file_type == 'functions':
            required = [
                ('<?php', 'PHP opening tag'),
                ('add_action', 'add_action() or add_filter() hooks'),
            ]

            # Check for at least one add_action or add_filter
            if 'add_action' not in php_code and 'add_filter' not in php_code:
                missing.append(f"{filename}: No WordPress hooks (add_action/add_filter)")

        if missing:
            return False, missing

        return True, []

    def validate_wordpress_functions(self, php_code: str, filename: str = "file.php") -> Tuple[List[str], List[str]]:
        """Check for hallucinated or invalid WordPress functions.

        Args:
            php_code: PHP code to check
            filename: Filename for error reporting

        Returns:
            Tuple of (list_of_hallucinated_functions, list_of_warnings)
        """
        hallucinated = []
        warnings = []

        # Find all function calls
        function_pattern = r'([a-z_][a-z0-9_]*)\s*\('
        functions = re.findall(function_pattern, php_code, re.IGNORECASE)

        for func in set(functions):
            # Check if it's a hallucinated function
            if func in HALLUCINATED_FUNCTIONS:
                hallucinated.append(func)
                logger.error(f"Found hallucinated function: {func}() in {filename}")

            # Check if it looks like a WordPress function but isn't in our whitelist
            elif func.startswith(('wp_', 'get_', 'the_', 'is_', 'has_', 'add_', 'register_')):
                if func not in WORDPRESS_CORE_FUNCTIONS:
                    warnings.append(f"Unknown WordPress-like function: {func}() in {filename}")

        return hallucinated, warnings

    def remove_hallucinated_functions(self, php_code: str, filename: str = "file.php") -> Tuple[str, List[str]]:
        """Remove hallucinated functions from PHP code.

        Args:
            php_code: PHP code to clean
            filename: Filename for logging

        Returns:
            Tuple of (cleaned_code, list_of_removals)
        """
        removals = []
        cleaned_code = php_code

        for func in HALLUCINATED_FUNCTIONS:
            pattern = rf'{func}\s*\([^)]*\)\s*;?'
            if re.search(pattern, cleaned_code):
                cleaned_code = re.sub(pattern, '// Removed hallucinated function', cleaned_code)
                removals.append(f"Removed {func}() from {filename}")
                logger.warning(f"Removed hallucinated function {func}() from {filename}")

        return cleaned_code, removals


def validate_and_fix_php(
    php_code: str,
    file_type: str = 'template',
    filename: str = 'file.php',
    auto_fix: bool = True
) -> Tuple[str, bool, List[str]]:
    """Comprehensive PHP validation and auto-fixing.

    Args:
        php_code: PHP code to validate/fix
        file_type: Type of file (header, footer, functions, template)
        filename: Filename for error reporting
        auto_fix: Whether to automatically fix issues

    Returns:
        Tuple of (fixed_code, is_valid, list_of_issues_or_fixes)
    """
    validator = PHPValidator()
    issues = []
    fixed_code = php_code

    # 1. Remove hallucinated functions
    if auto_fix:
        fixed_code, removals = validator.remove_hallucinated_functions(fixed_code, filename)
        issues.extend(removals)
    else:
        hallucinated, _ = validator.validate_wordpress_functions(fixed_code, filename)
        if hallucinated:
            issues.append(f"Contains hallucinated functions: {', '.join(hallucinated)}")

    # 2. Auto-fix brace mismatches
    if auto_fix:
        fixed_code, brace_fixes = validator.auto_fix_braces(fixed_code, filename)
        issues.extend(brace_fixes)
    else:
        brace_valid, brace_error = validator.check_brace_matching(fixed_code, filename)
        if not brace_valid:
            issues.append(brace_error)

    # 3. Validate syntax
    syntax_valid, syntax_error = validator.validate_php_syntax(fixed_code, filename)
    if not syntax_valid:
        issues.append(f"PHP syntax error: {syntax_error}")
        return fixed_code, False, issues

    # 4. Check required structures
    if file_type in ['header', 'footer', 'functions']:
        struct_valid, struct_missing = validator.check_required_structure(fixed_code, file_type, filename)
        if not struct_valid:
            issues.extend(struct_missing)
            return fixed_code, False, issues

    # 5. Validate WordPress functions
    hallucinated, warnings = validator.validate_wordpress_functions(fixed_code, filename)
    if hallucinated and not auto_fix:
        issues.append(f"Contains hallucinated functions: {', '.join(hallucinated)}")
        return fixed_code, False, issues

    # Log warnings but don't fail
    for warning in warnings:
        logger.warning(warning)

    # If we get here, validation passed
    is_valid = len(issues) == 0 or all('Removed' in i or 'Added' in i for i in issues)

    if is_valid:
        logger.info(f"✓ VALID PHP: {filename}")
    else:
        logger.error(f"✗ INVALID PHP: {filename}")
        for issue in issues:
            logger.error(f"  - {issue}")

    return fixed_code, is_valid, issues


def clean_llm_output(code: str, file_type: str = 'php') -> str:
    """Clean LLM output to extract only raw code.

    Args:
        code: Generated code from LLM
        file_type: Type of file (php, css, js)

    Returns:
        Cleaned code
    """
    # Remove markdown code fences
    code = code.strip()

    # Remove code fence markers with language
    code = re.sub(r'^```(?:php|css|javascript|js|html)?\s*\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n```\s*$', '', code)

    # Remove remaining code fences
    code = code.replace('```', '')

    # For PHP files, ensure proper opening
    if file_type == 'php':
        # Remove explanatory text before code
        if '<?php' in code:
            php_start = code.find('<?php')
            code = code[php_start:]
        elif '<!DOCTYPE' in code:
            doctype_start = code.find('<!DOCTYPE')
            code = code[doctype_start:]

    # Remove common AI explanatory phrases
    explanatory_patterns = [
        r'^(?:Here\'s|Here is|This is|Below is|I\'ve created|I have created).*?:\s*\n+',
        r'^(?:Sure|Certainly|Of course)[,!].*?\n+',
        r'^(?:This code|This file|This template).*?\n+',
    ]

    for pattern in explanatory_patterns:
        code = re.sub(pattern, '', code, flags=re.IGNORECASE)

    return code.strip()
