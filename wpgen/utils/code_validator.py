"""Code validation utilities for generated theme files.

This module provides validation for generated code to catch syntax errors
and common issues before they cause WordPress to crash.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .logger import get_logger

logger = get_logger(__name__)


# Plugin compatibility layer configuration
# Dictionary of known plugin constants and functions that themes should define as fallbacks
PLUGIN_COMPATIBILITY_CONSTANTS = {
    'RESPONSIVE_THEME_DIR': {
        'value': 'get_template_directory()',
        'description': 'Responsive theme directory path (for Responsive Add-Ons plugin)',
    },
    'RESPONSIVE_THEME_URL': {
        'value': 'get_template_directory_uri()',
        'description': 'Responsive theme URL (for Responsive Add-Ons plugin)',
    },
}

PLUGIN_COMPATIBILITY_FUNCTIONS = {
    'responsive_theme_dir': {
        'return': 'get_template_directory()',
        'description': 'Returns theme directory (for Responsive Add-Ons plugin)',
    },
}


def generate_plugin_compatibility_layer(theme_name: str) -> tuple[str, list[str]]:
    """Generate plugin compatibility layer code to prevent fatal errors.

    This creates safe fallback constants and functions for plugins that assume
    a specific theme environment (e.g., Responsive Add-Ons expecting RESPONSIVE_THEME_DIR).

    Args:
        theme_name: Theme name for logging

    Returns:
        Tuple of (compatibility_code, list_of_injected_items)
    """
    injected_items = []
    code_lines = []

    code_lines.append("<?php")
    code_lines.append("/**")
    code_lines.append(" * Auto-generated Plugin Compatibility Layer")
    code_lines.append(" *")
    code_lines.append(" * This block defines safe fallback constants and functions to prevent")
    code_lines.append(" * fatal PHP errors when plugins depend on theme-specific definitions.")
    code_lines.append(" *")
    code_lines.append(f" * @package {theme_name}")
    code_lines.append(" */")
    code_lines.append("")

    # Add constants
    if PLUGIN_COMPATIBILITY_CONSTANTS:
        code_lines.append("// Plugin compatibility constants")
        for const_name, const_config in PLUGIN_COMPATIBILITY_CONSTANTS.items():
            code_lines.append(f"if ( ! defined( '{const_name}' ) ) {{")
            code_lines.append(f"    define( '{const_name}', {const_config['value']} );")
            code_lines.append("}")
            injected_items.append(const_name)
        code_lines.append("")

    # Add functions
    if PLUGIN_COMPATIBILITY_FUNCTIONS:
        code_lines.append("// Plugin compatibility functions")
        for func_name, func_config in PLUGIN_COMPATIBILITY_FUNCTIONS.items():
            code_lines.append(f"if ( ! function_exists( '{func_name}' ) ) {{")
            code_lines.append(f"    function {func_name}() {{")
            code_lines.append(f"        return {func_config['return']};")
            code_lines.append("    }")
            code_lines.append("}")
            injected_items.append(f"{func_name}()")
        code_lines.append("")

    # Add comment listing injected items
    if injected_items:
        code_lines.append(f"// Injected compatibility layer: {', '.join(injected_items)}")
        code_lines.append("")

    compatibility_code = '\n'.join(code_lines)

    logger.info(f"Generated plugin compatibility layer with {len(injected_items)} items")
    return compatibility_code, injected_items


class CodeValidator:
    """Code validator with strict mode support."""

    def __init__(self, strict: bool = False, php_path: str = "php"):
        """Initialize code validator.

        Args:
            strict: If True, fail on warnings. If False, only fail on errors.
            php_path: Path to PHP binary (default: "php")
        """
        self.strict = strict
        self.php_path = php_path
        self.php_available = self._check_php_available()

    def _check_php_available(self) -> bool:
        """Check if PHP is available on the system.

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
            logger.warning(f"PHP command failed with code {result.returncode}")
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"PHP is not available: {e}")
            return False

    def validate_php_syntax(self, php_code: str) -> Tuple[bool, Optional[str], bool]:
        """Validate PHP code syntax.

        Args:
            php_code: PHP code to validate

        Returns:
            Tuple of (is_valid, error_message, is_warning)
            - is_valid: True if validation passed or was skipped
            - error_message: Error/warning message if any
            - is_warning: True if this is a warning (PHP not available), False for actual error
        """
        if not self.php_available:
            warning_msg = f"PHP binary not found at '{self.php_path}' - skipping syntax validation"
            if self.strict:
                logger.error(f"STRICT MODE: {warning_msg}")
                return False, warning_msg, True
            else:
                logger.warning(warning_msg)
                return True, warning_msg, True

        # Create temporary file with PHP code
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
                f.write(php_code)
                temp_path = f.name

            # Run php -l to check syntax
            result = subprocess.run(
                [self.php_path, "-l", temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Clean up temp file
            Path(temp_path).unlink()

            if result.returncode == 0:
                logger.debug("PHP syntax validation passed")
                return True, None, False
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"PHP syntax validation failed: {error_msg}")
                return False, error_msg, False

        except Exception as e:
            warning_msg = f"Could not validate PHP syntax: {str(e)}"
            if self.strict:
                logger.error(f"STRICT MODE: {warning_msg}")
                return False, warning_msg, True
            else:
                logger.warning(warning_msg)
                return True, warning_msg, True

    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single file.

        Args:
            file_path: Path to file to validate

        Returns:
            Dictionary with validation results
        """
        result = {
            "file": str(file_path),
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        if file_path.suffix == '.php':
            try:
                php_code = file_path.read_text(encoding='utf-8')
                is_valid, message, is_warning = self.validate_php_syntax(php_code)

                if not is_valid:
                    if is_warning:
                        result["warnings"].append(message)
                        if self.strict:
                            result["valid"] = False
                    else:
                        result["errors"].append(message)
                        result["valid"] = False
                elif message and is_warning:
                    result["warnings"].append(message)

            except Exception as e:
                error_msg = f"Failed to read file: {e}"
                result["errors"].append(error_msg)
                result["valid"] = False

        return result

    def validate_directory(self, directory: str) -> Dict[str, Any]:
        """Validate all PHP files in a directory.

        Args:
            directory: Path to directory to validate

        Returns:
            Dictionary with aggregated validation results
        """
        dir_path = Path(directory)
        results = {
            "valid": True,
            "files_checked": 0,
            "files_with_errors": 0,
            "files_with_warnings": 0,
            "errors": [],
            "warnings": [],
            "details": [],
        }

        if not dir_path.exists():
            results["valid"] = False
            results["errors"].append(f"Directory does not exist: {directory}")
            return results

        # Find all PHP files
        php_files = list(dir_path.rglob("*.php"))
        results["files_checked"] = len(php_files)

        for php_file in php_files:
            file_result = self.validate_file(php_file)
            results["details"].append(file_result)

            if not file_result["valid"]:
                results["files_with_errors"] += 1
                results["valid"] = False
                for error in file_result["errors"]:
                    results["errors"].append(f"{php_file.name}: {error}")

            if file_result["warnings"]:
                results["files_with_warnings"] += 1
                for warning in file_result["warnings"]:
                    results["warnings"].append(f"{php_file.name}: {warning}")

        # In strict mode, warnings make the overall result invalid
        if self.strict and results["warnings"]:
            results["valid"] = False

        return results


def validate_php_syntax(php_code: str) -> Tuple[bool, Optional[str]]:
    """Validate PHP code syntax using php -l command.

    Args:
        php_code: PHP code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if PHP is available
    try:
        result = subprocess.run(
            ["php", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            logger.warning("PHP command not available, skipping syntax validation")
            return True, None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("PHP command not available, skipping syntax validation")
        return True, None

    # Create temporary file with PHP code
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.php', delete=False) as f:
            f.write(php_code)
            temp_path = f.name

        # Run php -l to check syntax
        result = subprocess.run(
            ["php", "-l", temp_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Clean up temp file
        Path(temp_path).unlink()

        if result.returncode == 0:
            logger.debug("PHP syntax validation passed")
            return True, None
        else:
            error_msg = result.stderr or result.stdout
            logger.error(f"PHP syntax validation failed: {error_msg}")
            return False, error_msg

    except Exception as e:
        logger.warning(f"Could not validate PHP syntax: {str(e)}")
        return True, None  # Don't block on validation errors


def remove_nonexistent_requires(php_code: str, theme_dir: Optional[Path] = None) -> str:
    """Remove or comment out require/include statements for files that don't exist.

    Args:
        php_code: PHP code to check
        theme_dir: Optional theme directory path to check file existence

    Returns:
        Modified PHP code with non-existent requires removed/commented
    """
    if not theme_dir:
        # Can't validate without theme directory
        return php_code

    lines = php_code.split('\n')
    modified_lines = []
    changes_made = False

    for line in lines:
        # Check for require/include statements
        if re.search(r'\b(require|include|require_once|include_once)\s*\(?\s*get_template_directory', line):
            # Extract the file path
            match = re.search(r"['\"]([^'\"]+\.php)['\"]", line)
            if match:
                file_path = match.group(1)
                # Remove leading slash if present
                file_path = file_path.lstrip('/')
                full_path = theme_dir / file_path

                if not full_path.exists():
                    # Comment out the line
                    modified_lines.append(f"// REMOVED: File does not exist - {line.strip()}")
                    logger.warning(f"Removed require for non-existent file: {file_path}")
                    changes_made = True
                    continue

        modified_lines.append(line)

    if changes_made:
        logger.info("Removed require/include statements for non-existent files")

    return '\n'.join(modified_lines)


def clean_generated_code(code: str, file_type: str) -> str:
    """Clean generated code by removing markdown and explanatory text.

    Args:
        code: Generated code string
        file_type: Type of file (php, css, js)

    Returns:
        Cleaned code
    """
    # Remove markdown code blocks
    code = code.strip()

    # Remove code fence markers with language
    code = re.sub(r'^```(?:php|css|javascript|js|html)?\s*\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n```\s*$', '', code)

    # Remove remaining code fences
    code = code.replace('```', '')

    # For PHP files, ensure proper opening tag
    if file_type == 'php':
        # Remove any explanatory text before <?php or <!DOCTYPE
        if '<?php' in code:
            # Find first occurrence of <?php
            php_start = code.find('<?php')
            code = code[php_start:]
        elif '<!DOCTYPE' in code:
            # HTML template with <!DOCTYPE (like header.php)
            doctype_start = code.find('<!DOCTYPE')
            code = code[doctype_start:]

        # Check for Python-like placeholders that weren't evaluated
        if '{theme_name.' in code or '.replace(' in code:
            logger.error("CRITICAL: Found unevaluated Python expression in generated PHP code!")
            logger.error(f"Code snippet: {code[:200]}")
            raise ValueError("Generated code contains unevaluated Python expressions")

        # Check for markdown remnants
        if '```' in code:
            logger.warning("Found markdown code fences in PHP, removing")
            code = code.replace('```php', '').replace('```', '')

        # Remove any text after the last PHP closing tag (if it exists)
        if '?>' in code:
            # Find last occurrence of ?>
            php_end = code.rfind('?>')
            # Check if there's only whitespace after
            after_close = code[php_end + 2:].strip()
            if after_close and not after_close.startswith('<?'):
                # There's non-whitespace content after ?>, keep it
                pass
            else:
                code = code[:php_end + 2]

    # Remove common AI explanatory phrases at the start
    explanatory_patterns = [
        r'^(?:Here\'s|Here is|This is|Below is|I\'ve created|I have created).*?:\s*\n+',
        r'^(?:Sure|Certainly|Of course)[,!].*?\n+',
    ]
    for pattern in explanatory_patterns:
        code = re.sub(pattern, '', code, flags=re.IGNORECASE)

    return code.strip()


def get_fallback_functions_php(theme_name: str) -> str:
    """Get fallback functions.php template.

    Args:
        theme_name: Theme name for text domain

    Returns:
        Fallback functions.php code
    """
    # Convert theme name to valid PHP function name (replace hyphens with underscores)
    safe_function_name = theme_name.replace('-', '_')

    # Generate compatibility layer
    compatibility_layer, injected_items = generate_plugin_compatibility_layer(theme_name)

    return f"""{compatibility_layer}

if ( ! defined( 'ABSPATH' ) ) {{
    exit; // Exit if accessed directly
}}

/**
 * Sets up theme defaults and registers support for various WordPress features.
 */
function {safe_function_name}_setup() {{
    // Add theme support
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'automatic-feed-links' );
    add_theme_support( 'html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
    ) );

    // Add custom logo support
    add_theme_support( 'custom-logo', array(
        'height'      => 80,
        'width'       => 240,
        'flex-height' => true,
        'flex-width'  => true,
    ) );

    // Register navigation menus
    register_nav_menus( array(
        'primary' => __( 'Primary Menu', '{theme_name}' ),
    ) );
}}
add_action( 'after_setup_theme', '{safe_function_name}_setup' );

/**
 * Enqueue scripts and styles.
 */
function {safe_function_name}_scripts() {{
    // Enqueue base layout stylesheet (structural styles)
    wp_enqueue_style( 'theme-base-layout', get_template_directory_uri() . '/assets/css/style.css', array(), '1.0.0' );

    // Enqueue main theme stylesheet
    wp_enqueue_style( '{theme_name}-style', get_stylesheet_uri(), array( 'theme-base-layout' ), wp_get_theme()->get( 'Version' ) );

    // Enqueue wpgen-ui assets
    wp_enqueue_style( 'wpgen-ui', get_template_directory_uri() . '/assets/css/wpgen-ui.css', array(), '1.0.0' );
    wp_enqueue_script( 'wpgen-ui', get_template_directory_uri() . '/assets/js/wpgen-ui.js', array(), '1.0.0', true );
}}
add_action( 'wp_enqueue_scripts', '{safe_function_name}_scripts' );

/**
 * Register widget areas.
 */
function {safe_function_name}_widgets_init() {{
    register_sidebar( array(
        'name'          => __( 'Sidebar', '{theme_name}' ),
        'id'            => 'sidebar-1',
        'description'   => __( 'Add widgets here.', '{theme_name}' ),
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h2 class="widget-title">',
        'after_title'   => '</h2>',
    ) );

    // Register footer widget areas
    register_sidebar( array(
        'name'          => __( 'Footer 1', '{theme_name}' ),
        'id'            => 'footer-1',
        'description'   => __( 'Footer widget area 1', '{theme_name}' ),
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ) );

    register_sidebar( array(
        'name'          => __( 'Footer 2', '{theme_name}' ),
        'id'            => 'footer-2',
        'description'   => __( 'Footer widget area 2', '{theme_name}' ),
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ) );
}}
add_action( 'widgets_init', '{safe_function_name}_widgets_init' );

/**
 * Display post meta data (date and author).
 */
function {safe_function_name}_get_the_meta_data() {{
    echo '<div class="entry-meta">';
    echo '<span class="posted-on">' . esc_html( get_the_date() ) . '</span>';
    echo '<span class="byline"> by ' . esc_html( get_the_author() ) . '</span>';
    echo '</div>';
}}

/**
 * Display the post thumbnail with fallback.
 *
 * @param string $size Thumbnail size. Default 'large'.
 */
function {safe_function_name}_get_the_image( $size = 'large' ) {{
    if ( has_post_thumbnail() ) {{
        the_post_thumbnail( $size );
    }} else {{
        // Optional: Display a placeholder image
        echo '<img src="' . esc_url( get_template_directory_uri() . '/assets/images/placeholder.png' ) . '" alt="' . esc_attr( get_the_title() ) . '" class="placeholder-image" />';
    }}
}}

/**
 * Display pagination with fallback for WP-PageNavi plugin.
 */
function {safe_function_name}_pagination() {{
    if ( function_exists( 'wp_pagenavi' ) ) {{
        wp_pagenavi();
    }} else {{
        the_posts_navigation();
    }}
}}

/**
 * Display posts pagination with fallback.
 */
function {safe_function_name}_posts_pagination() {{
    if ( function_exists( 'wp_pagenavi' ) ) {{
        wp_pagenavi();
    }} else {{
        the_posts_pagination( array(
            'mid_size'  => 2,
            'prev_text' => __( '&laquo; Previous', '{theme_name}' ),
            'next_text' => __( 'Next &raquo;', '{theme_name}' ),
        ) );
    }}
}}
"""


def check_plugin_compatibility(php_code: str, theme_name: str) -> list[str]:
    """Check for plugin-related constants/functions that may be missing.

    Args:
        php_code: PHP code to check
        theme_name: Theme name for logging

    Returns:
        List of warnings about potentially missing plugin constants
    """
    warnings = []

    # Check for references to known plugin constants that should be in compatibility layer
    for const_name in PLUGIN_COMPATIBILITY_CONSTANTS.keys():
        # Look for constant usage (not definition)
        if const_name in php_code:
            # Check if it's being defined (not just used)
            if f"define( '{const_name}'" not in php_code and f"defined( '{const_name}'" not in php_code:
                warnings.append(
                    f"References constant {const_name} but doesn't define it. "
                    f"Ensure plugin compatibility layer is present."
                )

    return warnings


def validate_layout_structure(theme_dir: Path) -> list[str]:
    """Validate theme has proper layout structure and styling.

    Args:
        theme_dir: Path to theme directory

    Returns:
        List of layout validation issues
    """
    issues = []
    theme_dir = Path(theme_dir)

    # Check for header.php with proper structure
    header_file = theme_dir / "header.php"
    if header_file.exists():
        try:
            content = header_file.read_text(encoding='utf-8')
            if '.site-header' not in content:
                issues.append("header.php missing '.site-header' class - layout structure incomplete")
            if '.site-branding' not in content:
                issues.append("header.php missing '.site-branding' wrapper - logo may not be constrained")
            if 'the_custom_logo()' not in content:
                issues.append("header.php missing 'the_custom_logo()' call - custom logo support incomplete")
            if '.main-navigation' not in content:
                issues.append("header.php missing '.main-navigation' class - navigation structure incomplete")
        except Exception as e:
            logger.warning(f"Could not validate header.php structure: {e}")
    else:
        issues.append("Missing header.php - theme will not display properly")

    # Check for footer.php with proper structure
    footer_file = theme_dir / "footer.php"
    if footer_file.exists():
        try:
            content = footer_file.read_text(encoding='utf-8')
            if '.site-footer' not in content:
                issues.append("footer.php missing '.site-footer' class - layout structure incomplete")
        except Exception as e:
            logger.warning(f"Could not validate footer.php structure: {e}")
    else:
        issues.append("Missing footer.php - theme will not display properly")

    # Check for base layout CSS
    base_css = theme_dir / "assets" / "css" / "style.css"
    if not base_css.exists():
        issues.append("Missing assets/css/style.css - base layout styles not present")
    else:
        try:
            content = base_css.read_text(encoding='utf-8')
            # Check for essential layout rules
            if '.site-header' not in content:
                issues.append("Base layout CSS missing '.site-header' styles")
            if '.site-branding img' not in content and '.custom-logo-link img' not in content:
                issues.append("Base layout CSS missing logo constraint styles - logos may be full-width")
        except Exception as e:
            logger.warning(f"Could not validate base layout CSS: {e}")

    # Check functions.php for proper stylesheet enqueue
    functions_file = theme_dir / "functions.php"
    if functions_file.exists():
        try:
            content = functions_file.read_text(encoding='utf-8')
            if 'theme-base-layout' not in content and 'assets/css/style.css' not in content:
                issues.append("functions.php not enqueuing base layout CSS - styles will not load")
        except Exception as e:
            logger.warning(f"Could not validate functions.php enqueue: {e}")

    return issues


def validate_theme_for_wordpress_safety(theme_dir: Path) -> tuple[bool, list[str]]:
    """Perform comprehensive validation to prevent WordPress crashes.

    Args:
        theme_dir: Path to theme directory

    Returns:
        Tuple of (is_safe, list_of_issues)
    """
    issues = []
    warnings = []
    theme_dir = Path(theme_dir)

    # Check required files exist
    required_files = ["style.css", "index.php"]
    for required_file in required_files:
        if not (theme_dir / required_file).exists():
            issues.append(f"Missing required file: {required_file}")

    # Validate layout structure
    layout_issues = validate_layout_structure(theme_dir)
    if layout_issues:
        issues.extend(layout_issues)

    # Validate all PHP files
    php_files = list(theme_dir.rglob("*.php"))
    templates_with_header = []
    templates_with_footer = []

    for php_file in php_files:
        try:
            content = php_file.read_text(encoding='utf-8')

            # Check for plugin compatibility issues (only in functions.php)
            if php_file.name == 'functions.php':
                compat_warnings = check_plugin_compatibility(content, theme_dir.name)
                for warning in compat_warnings:
                    logger.warning(f"Plugin compatibility: {warning}")
                    warnings.append(f"{php_file.name}: {warning}")

            # Check for Python expressions that weren't evaluated
            if '{theme_name.' in content or '{requirements[' in content:
                issues.append(f"{php_file.name}: Contains unevaluated Python expression")
                logger.error(f"Found Python expression in {php_file}: {content[:100]}")

            # Check for markdown code fences
            if '```' in content:
                issues.append(f"{php_file.name}: Contains markdown code fences")

            # Check for explanatory text
            first_line = content.split('\n')[0].strip()
            if first_line and not first_line.startswith('<?php') and not first_line.startswith('<!DOCTYPE'):
                if any(phrase in first_line.lower() for phrase in ["here's", "here is", "below is", "this is"]):
                    issues.append(f"{php_file.name}: Contains explanatory text before code")

            # Check for invalid/undefined WordPress functions
            if 'post_loop(' in content:
                issues.append(f"{php_file.name}: Uses undefined function 'post_loop()' - should use 'have_posts()' and 'the_post()'")

            # Check for get_template_part calls and verify referenced files exist
            template_part_pattern = r"get_template_part\s*\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?\s*\)"
            for match in re.finditer(template_part_pattern, content):
                slug = match.group(1)
                name = match.group(2) if match.group(2) else None

                # Check if template-parts directory exists
                template_parts_dir = theme_dir / 'template-parts'
                if name:
                    # Check for {slug}-{name}.php
                    expected_file = theme_dir / f"{slug}-{name}.php"
                    if not expected_file.exists():
                        # Also check in template-parts directory
                        alt_file = template_parts_dir / f"{slug.replace('template-parts/', '')}-{name}.php"
                        if not alt_file.exists():
                            issues.append(f"{php_file.name}: References template part '{slug}-{name}.php' which doesn't exist")
                else:
                    # Check for {slug}.php
                    expected_file = theme_dir / f"{slug}.php"
                    if not expected_file.exists():
                        # Also check in template-parts directory
                        alt_file = template_parts_dir / f"{slug.replace('template-parts/', '')}.php"
                        if not alt_file.exists():
                            issues.append(f"{php_file.name}: References template part '{slug}.php' which doesn't exist")

            # Track templates with get_header() and get_footer()
            if 'get_header(' in content and php_file.name not in ['header.php', 'functions.php']:
                templates_with_header.append(php_file.name)
            if 'get_footer(' in content and php_file.name not in ['footer.php', 'functions.php']:
                templates_with_footer.append(php_file.name)

            # Check for unchecked wp_pagenavi() calls
            # Check each occurrence, not just the first
            if 'wp_pagenavi(' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'wp_pagenavi(' in line:
                        # Check previous 3 lines for function_exists check
                        context_start = max(0, i - 3)
                        prev_lines = lines[context_start:i]

                        has_check = any('function_exists' in pline and 'wp_pagenavi' in pline
                                       for pline in prev_lines)

                        if not has_check:
                            issues.append(f"{php_file.name}: Line {i+1} calls wp_pagenavi() without function_exists() check - will crash if plugin not installed")
                            break  # Only report first occurrence to avoid spam

            # Basic PHP syntax check if PHP is available
            is_valid, error_msg = validate_php_syntax(content)
            if not is_valid and error_msg:
                issues.append(f"{php_file.name}: PHP syntax error - {error_msg[:100]}")

        except Exception as e:
            issues.append(f"{php_file.name}: Could not read/validate - {str(e)}")

    # Check for templates with get_header() but missing get_footer()
    templates_missing_footer = set(templates_with_header) - set(templates_with_footer)
    for template in templates_missing_footer:
        issues.append(f"{template}: Calls get_header() but missing get_footer() - incomplete template")

    # Log warnings (these don't fail validation, but are useful info)
    if warnings:
        logger.info(f"Theme validation warnings ({len(warnings)} total):")
        for warning in warnings:
            logger.info(f"  ⚠ {warning}")

    is_safe = len(issues) == 0
    return is_safe, issues


def get_fallback_template(template_name: str, theme_name: str) -> str:
    """Get fallback template for various WordPress template files.

    Args:
        template_name: Name of the template (e.g., 'single', 'page', 'archive')
        theme_name: Theme name for text domain

    Returns:
        Fallback template code
    """
    templates = {
        'single.php': """<?php
/**
 * Single post template
 */
get_header();

if ( have_posts() ) :
    while ( have_posts() ) : the_post();
        ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
            <header class="entry-header">
                <h1 class="entry-title"><?php the_title(); ?></h1>
                <div class="entry-meta">
                    <span class="posted-on"><?php echo get_the_date(); ?></span>
                    <span class="byline"> by <?php the_author(); ?></span>
                </div>
            </header>
            <div class="entry-content">
                <?php the_content(); ?>
            </div>
        </article>
        <?php
        if ( comments_open() || get_comments_number() ) :
            comments_template();
        endif;
    endwhile;
endif;

get_footer();
""",
        'page.php': """<?php
/**
 * Page template
 */
get_header();

if ( have_posts() ) :
    while ( have_posts() ) : the_post();
        ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
            <header class="entry-header">
                <h1 class="entry-title"><?php the_title(); ?></h1>
            </header>
            <div class="entry-content">
                <?php the_content(); ?>
            </div>
        </article>
        <?php
    endwhile;
endif;

get_footer();
""",
        'archive.php': """<?php
/**
 * Archive template
 */
get_header();
?>

<header class="page-header">
    <?php
    the_archive_title( '<h1 class="page-title">', '</h1>' );
    the_archive_description( '<div class="archive-description">', '</div>' );
    ?>
</header>

<?php
if ( have_posts() ) :
    while ( have_posts() ) : the_post();
        ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
            <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
            <div class="entry-summary">
                <?php the_excerpt(); ?>
            </div>
        </article>
        <?php
    endwhile;
    the_posts_pagination();
else :
    ?>
    <p><?php esc_html_e( 'No posts found.', '{theme_name}' ); ?></p>
    <?php
endif;

get_footer();
""",
        'search.php': """<?php
/**
 * Search results template
 */
get_header();
?>

<header class="page-header">
    <h1 class="page-title">
        <?php printf( esc_html__( 'Search Results for: %s', '{theme_name}' ), '<span>' . get_search_query() . '</span>' ); ?>
    </h1>
</header>

<?php
if ( have_posts() ) :
    while ( have_posts() ) : the_post();
        ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
            <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
            <div class="entry-summary">
                <?php the_excerpt(); ?>
            </div>
        </article>
        <?php
    endwhile;
    the_posts_pagination();
else :
    ?>
    <p><?php esc_html_e( 'Nothing found. Try a different search?', '{theme_name}' ); ?></p>
    <?php get_search_form(); ?>
    <?php
endif;

get_footer();
""",
        '404.php': """<?php
/**
 * 404 error page template
 */
get_header();
?>

<header class="page-header">
    <h1 class="page-title"><?php esc_html_e( 'Page Not Found', '{theme_name}' ); ?></h1>
</header>

<div class="page-content">
    <p><?php esc_html_e( 'The page you are looking for does not exist.', '{theme_name}' ); ?></p>
    <?php get_search_form(); ?>
</div>

<?php
get_footer();
""",
        'sidebar.php': """<?php
/**
 * Sidebar template
 */
if ( ! is_active_sidebar( 'sidebar-1' ) ) {
    return;
}
?>

<aside id="secondary" class="widget-area">
    <?php dynamic_sidebar( 'sidebar-1' ); ?>
</aside>
"""
    }

    return templates.get(template_name, "")


def repair_wordpress_code(php_code: str, theme_name: str) -> tuple[str, list[str]]:
    """Automatically repair common WordPress code issues.

    Args:
        php_code: PHP code to repair
        theme_name: Theme name for generating proper function names

    Returns:
        Tuple of (repaired_code, list_of_repairs_made)
    """
    repairs = []
    original_code = php_code

    # 1. Fix wp_pagenavi() calls without function_exists() wrapper
    # Pattern: Find wp_pagenavi() not already wrapped in function_exists
    lines = php_code.split('\n')
    repaired_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line contains wp_pagenavi()
        if 'wp_pagenavi(' in line and '<?php' not in line:
            # Check if previous few lines contain function_exists check for this call
            context_start = max(0, i - 3)
            context_lines = lines[context_start:i]

            # Check if already wrapped: look for "function_exists" AND "wp_pagenavi" in preceding lines
            already_wrapped = False
            for prev_line in context_lines:
                if 'function_exists' in prev_line and 'wp_pagenavi' in prev_line:
                    already_wrapped = True
                    break

            if not already_wrapped:
                # Get indentation
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent

                # Replace with wrapped version
                repaired_lines.append(f"{indent_str}if ( function_exists( 'wp_pagenavi' ) ) {{")
                repaired_lines.append(line)
                repaired_lines.append(f"{indent_str}}} else {{")
                repaired_lines.append(f"{indent_str}    the_posts_pagination();")
                repaired_lines.append(f"{indent_str}}}")

                repairs.append("Wrapped wp_pagenavi() call with function_exists() check")
                i += 1
                continue

        repaired_lines.append(line)
        i += 1

    php_code = '\n'.join(repaired_lines)

    # 2. Replace post_loop() with proper WordPress loop
    if 'post_loop(' in php_code:
        php_code = re.sub(
            r'post_loop\(\s*\)',
            'the_post()',
            php_code
        )
        repairs.append("Replaced post_loop() with the_post()")

    # 3. Ensure theme helper functions exist if referenced
    safe_function_name = theme_name.replace('-', '_')

    # Check if helper functions are called but not defined
    helpers_needed = []
    if f'{safe_function_name}_get_the_meta_data(' in php_code and \
       f'function {safe_function_name}_get_the_meta_data(' not in php_code:
        helpers_needed.append('get_the_meta_data')

    if f'{safe_function_name}_get_the_image(' in php_code and \
       f'function {safe_function_name}_get_the_image(' not in php_code:
        helpers_needed.append('get_the_image')

    if f'{safe_function_name}_pagination(' in php_code and \
       f'function {safe_function_name}_pagination(' not in php_code:
        helpers_needed.append('pagination')

    if helpers_needed:
        # Add missing helper functions at the end
        helper_code = "\n\n// Auto-generated helper functions\n"

        if 'get_the_meta_data' in helpers_needed:
            helper_code += f"""
/**
 * Display post meta data (date and author).
 */
function {safe_function_name}_get_the_meta_data() {{
    echo '<div class="entry-meta">';
    echo '<span class="posted-on">' . esc_html( get_the_date() ) . '</span>';
    echo '<span class="byline"> by ' . esc_html( get_the_author() ) . '</span>';
    echo '</div>';
}}
"""

        if 'get_the_image' in helpers_needed:
            helper_code += f"""
/**
 * Display the post thumbnail with fallback.
 */
function {safe_function_name}_get_the_image( $size = 'large' ) {{
    if ( has_post_thumbnail() ) {{
        the_post_thumbnail( $size );
    }} else {{
        echo '<img src="' . esc_url( get_template_directory_uri() . '/assets/images/placeholder.png' ) . '" alt="' . esc_attr( get_the_title() ) . '" class="placeholder-image" />';
    }}
}}
"""

        if 'pagination' in helpers_needed:
            helper_code += f"""
/**
 * Display pagination with fallback.
 */
function {safe_function_name}_pagination() {{
    if ( function_exists( 'wp_pagenavi' ) ) {{
        wp_pagenavi();
    }} else {{
        the_posts_pagination();
    }}
}}
"""

        php_code = php_code.rstrip() + helper_code
        repairs.append(f"Added missing helper functions: {', '.join(helpers_needed)}")

    return php_code, repairs
