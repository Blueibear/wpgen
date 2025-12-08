"""Code validation utilities for generated theme files.

This module provides validation for generated code to catch syntax errors
and common issues before they cause WordPress to crash.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .logger import get_logger
from .php_validation import (
    validate_and_fix_php,
    clean_llm_output,
    PHPValidator,
)

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

    def validate_php_syntax(self, php_code: str) -> tuple[bool, str | None, bool]:
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

    def validate_file(self, file_path: Path) -> dict[str, Any]:
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

    def validate_directory(self, directory: str) -> dict[str, Any]:
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


def validate_php_syntax(php_code: str) -> tuple[bool, str | None]:
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


def remove_nonexistent_requires(php_code: str, theme_dir: Path | None = None) -> str:
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
    # Use the comprehensive cleaner from php_validation module
    code = clean_llm_output(code, file_type)

    # Additional PHP-specific validation
    if file_type == 'php':
        # Check for Python-like placeholders that weren't evaluated
        # We check for both bracket notation and dot notation that might be left over
        # Use regex to catch {theme_name}, {theme_name.replace...}, {requirements...}
        if re.search(r'\{theme_name[\.\}]|\{requirements', code):
            logger.error("CRITICAL: Found unevaluated Python expression in generated PHP code!")
            logger.error(f"Code snippet: {code[:200]}")
            raise ValueError("Generated code contains unevaluated Python expressions")

        # Check for markdown remnants
        if '```' in code:
            logger.warning("Found markdown code fences in PHP, removing")
            code = code.replace('```php', '').replace('```', '')

    return code.strip()


def validate_and_repair_php_file(
    php_code: str,
    file_type: str,
    filename: str,
    max_retries: int = 2,
    theme_dir: Path | None = None
) -> tuple[str, bool, list[str]]:
    """Validate and repair a PHP file with retry logic.

    For footer.php files, this includes:
    1. Footer-specific sanitization (backslash removal, duplicate cleanup)
    2. PHP syntax validation using php -l
    3. Structural repairs (wp_footer, closing tags, etc.)
    4. Fallback to template-based footer if all else fails

    Args:
        php_code: PHP code to validate
        file_type: Type of file (header, footer, functions, template)
        filename: Filename for logging
        max_retries: Maximum number of repair attempts
        theme_dir: Theme directory path (required for footer.php PHP syntax validation)

    Returns:
        Tuple of (final_code, is_valid, log_messages)
    """
    log_messages = []
    current_code = php_code

    # STEP 1: Footer-specific sanitization (before general validation)
    if file_type == 'footer' and filename == 'footer.php':
        logger.info(f"🔧 Running footer-specific sanitizer on {filename}")
        sanitized_code, cleanups = sanitize_footer_php(current_code)
        if cleanups:
            log_messages.append(f"🧹 SANITIZED {filename}:")
            for cleanup in cleanups:
                log_messages.append(f"  ✓ {cleanup}")
                logger.info(f"  Cleanup: {cleanup}")
            current_code = sanitized_code

    # STEP 2: General PHP validation and repair with retries
    for attempt in range(max_retries + 1):
        # Validate and attempt auto-fix
        fixed_code, is_valid, issues = validate_and_fix_php(
            current_code,
            file_type=file_type,
            filename=filename,
            auto_fix=True
        )

        if is_valid:
            if attempt > 0:
                log_messages.append(f"✓ REGENERATED: {filename} (fixed on attempt {attempt + 1})")
                logger.info(f"✓ Successfully repaired {filename} on attempt {attempt + 1}")
            else:
                log_messages.append(f"✓ VALID PHP: {filename}")
                logger.info(f"✓ {filename} passed validation")

            # STEP 3: Footer-specific validation and PHP syntax check
            if file_type == 'footer' and filename == 'footer.php':
                # Step 3a: Validate footer requirements (structure, no duplicates, etc.)
                logger.info(f"🔍 Validating footer.php requirements")
                requirements_valid, requirement_errors = validate_footer_requirements(fixed_code)

                if not requirements_valid:
                    log_messages.append(f"✗ FOOTER VALIDATION FAILED:")
                    for error in requirement_errors:
                        log_messages.append(f"  - {error}")
                        logger.error(f"  Footer requirement error: {error}")

                    # Continue to next retry or fallback
                    current_code = fixed_code
                    continue
                else:
                    log_messages.append(f"✓ FOOTER REQUIREMENTS: All checks passed")
                    logger.info(f"✓ Footer.php meets all structural requirements")

                # Step 3b: PHP syntax check using php -l
                if theme_dir:
                    logger.info(f"🔍 Running PHP syntax validation (php -l) on {filename}")
                    syntax_valid, syntax_error, syntax_issues = validate_footer_php_syntax(
                        fixed_code, theme_dir
                    )

                    if not syntax_valid:
                        log_messages.append(f"✗ PHP SYNTAX ERROR in {filename}:")
                        log_messages.extend([f"  - {issue}" for issue in syntax_issues])
                        logger.error(f"PHP syntax validation failed: {syntax_error}")

                        # Continue to next retry or fallback
                        current_code = fixed_code
                        continue
                    else:
                        if syntax_issues:  # PHP CLI not available
                            log_messages.append(f"⚠ {filename}: PHP CLI not available (skipped syntax check)")
                        else:
                            log_messages.append(f"✓ PHP SYNTAX VALID: {filename}")
                            logger.info(f"✓ PHP syntax validation passed for {filename}")

            return fixed_code, True, log_messages

        # Log the issues
        log_messages.append(f"✗ INVALID PHP: {filename} (attempt {attempt + 1}/{max_retries + 1})")
        for issue in issues:
            log_messages.append(f"  - {issue}")
            logger.error(f"  {issue}")

        # Update for next iteration
        current_code = fixed_code

    # If we get here, all attempts failed
    log_messages.append(f"✗ VALIDATION FAILED: {filename} after {max_retries + 1} attempts")
    logger.error(f"✗ Failed to repair {filename} after {max_retries + 1} attempts")

    return current_code, False, log_messages


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
 * Enqueue scripts and styles for front-end.
 *
 * CRITICAL: NO editor dependencies here (@wordpress/*, react, jetpack).
 * Editor scripts go in enqueue_block_editor_assets ONLY.
 */
function {safe_function_name}_scripts() {{
    // Enqueue base layout stylesheet (structural styles)
    wp_enqueue_style( 'theme-base-layout', get_template_directory_uri() . '/assets/css/style.css', array(), '1.0.0' );

    // Enqueue main theme stylesheet
    wp_enqueue_style( '{theme_name}-style', get_stylesheet_uri(), array( 'theme-base-layout' ), wp_get_theme()->get( 'Version' ) );

    // Enqueue wpgen-ui assets (front-end only, no editor deps)
    wp_enqueue_style( 'wpgen-ui', get_template_directory_uri() . '/assets/css/wpgen-ui.css', array(), '1.0.0' );
    wp_enqueue_script( 'wpgen-ui', get_template_directory_uri() . '/assets/js/wpgen-ui.js', array(), '1.0.0', true );
}}
add_action( 'wp_enqueue_scripts', '{safe_function_name}_scripts' );

/**
 * Enqueue block editor assets.
 *
 * IMPORTANT: Editor scripts (React, Gutenberg, Jetpack) should ONLY be enqueued here,
 * never in wp_enqueue_scripts. This prevents conflicts and duplicate registrations
 * that can break the Customizer and block editor.
 */
function {safe_function_name}_editor_assets() {{
    // Example: Uncomment to add custom editor scripts
    // wp_enqueue_script(
    //     '{theme_name}-editor',
    //     get_template_directory_uri() . '/assets/js/editor.js',
    //     array( 'wp-blocks', 'wp-element', 'wp-i18n', 'wp-components', 'wp-data', 'wp-edit-post' ),
    //     wp_get_theme()->get( 'Version' ),
    //     true
    // );
}}
add_action( 'enqueue_block_editor_assets', '{safe_function_name}_editor_assets' );

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
            # Check for HTML class attributes (not CSS selectors)
            if 'site-header' not in content:
                issues.append("header.php missing '.site-header' class - layout structure incomplete")
            if 'site-branding' not in content:
                issues.append("header.php missing '.site-branding' wrapper - logo may not be constrained")
            if 'the_custom_logo()' not in content:
                issues.append("header.php missing 'the_custom_logo()' call - custom logo support incomplete")
            if 'main-navigation' not in content:
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
            # Very relaxed validation: accept any <footer> tag with any attributes
            # Accept alternative closing structures (</div> wrappers, etc.) as long as DOM closes
            # This ensures maximum compatibility with local models and prevents false positives
            has_footer = '<footer' in content.lower()
            has_wp_footer = 'wp_footer()' in content
            has_closing_tags = ('</body>' in content.lower() and '</html>' in content.lower())

            # Only warn if critical WordPress hooks are missing
            if not has_wp_footer:
                issues.append("footer.php missing wp_footer() hook - WordPress scripts/styles may not load")

            # Only warn if HTML document is not properly closed
            if not has_closing_tags:
                issues.append("footer.php missing proper HTML closing tags (</body></html>)")

            # Footer tag is recommended but not required - just log info, don't fail validation
            if not has_footer:
                logger.info("footer.php does not use semantic <footer> tag (recommended but not required)")
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


def get_fallback_header_php(theme_name: str, requirements: dict = None) -> str:
    """Get strict structurally-guaranteed fallback header.php template.

    This header template GUARANTEES the following structure in exact order:
    1. <!DOCTYPE html>
    2. <html> with language_attributes()
    3. <head> with charset and viewport
    4. wp_head() hook
    5. <body> with body_class()
    6. wp_body_open() hook
    7. <header class="site-header">
    8. Logo and navigation
    9. Opens <main id="content"> (closed in footer.php)

    Args:
        theme_name: Theme name for text domain
        requirements: Optional theme requirements dict

    Returns:
        Guaranteed-safe header.php code
    """
    site_name = requirements.get('theme_display_name', 'My WordPress Site') if requirements else 'My WordPress Site'

    return f"""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
    <a class="skip-link screen-reader-text" href="#content"><?php esc_html_e( 'Skip to content', '{theme_name}' ); ?></a>

    <header class="site-header">
        <div class="header-inner container">
            <div class="site-branding">
                <?php
                if ( has_custom_logo() ) {{
                    the_custom_logo();
                }} else {{
                    ?>
                    <h1 class="site-title">
                        <a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home">
                            <?php bloginfo( 'name' ); ?>
                        </a>
                    </h1>
                    <?php
                    $description = get_bloginfo( 'description', 'display' );
                    if ( $description || is_customize_preview() ) {{
                        ?>
                        <p class="site-description"><?php echo esc_html( $description ); ?></p>
                        <?php
                    }}
                }}
                ?>
            </div><!-- .site-branding -->

            <nav class="main-navigation" aria-label="<?php esc_attr_e( 'Primary Navigation', '{theme_name}' ); ?>">
                <?php
                wp_nav_menu(
                    array(
                        'theme_location' => 'primary',
                        'menu_class'     => 'primary-menu',
                        'container'      => false,
                        'fallback_cb'    => false,
                    )
                );
                ?>
            </nav><!-- .main-navigation -->
        </div><!-- .header-inner -->
    </header><!-- .site-header -->

    <main id="content" class="site-main">
"""


def get_fallback_footer_php(theme_name: str) -> str:
    """Get strict structurally-guaranteed fallback footer.php template.

    This footer template GUARANTEES the following structure in exact order:
    1. Closes </main> (opened in header.php)
    2. <footer class="site-footer"> with working WordPress footer code
    3. Footer widgets with visible fallback content
    4. wp_footer() hook
    5. Closes </body>
    6. Closes </html>

    This template is used when:
    - LLM generation fails
    - PHP syntax validation fails
    - Generated footer has malformed syntax

    Args:
        theme_name: Theme name for text domain

    Returns:
        Guaranteed-safe footer.php code with working WordPress features
    """
    return f"""<?php
/**
 * Footer Template - Fallback Safe Version
 *
 * @package {theme_name}
 */
?>
</main><!-- #content .site-main -->

<footer class="site-footer">
    <div class="footer-widgets container">
        <?php if ( is_active_sidebar( 'footer-1' ) ) : ?>
            <div class="footer-widget-area footer-widget-1">
                <?php dynamic_sidebar( 'footer-1' ); ?>
            </div>
        <?php else : ?>
            <div class="footer-widget-area footer-widget-1">
                <h3 class="widget-title">About</h3>
                <p><?php bloginfo( 'description' ); ?></p>
            </div>
        <?php endif; ?>
    </div>

    <div class="footer-bottom">
        <p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?></p>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
"""


def get_fallback_template(template_name: str, theme_name: str) -> str:
    """Get fallback template for various WordPress template files.

    Args:
        template_name: Name of the template (e.g., 'single', 'page', 'archive')
        theme_name: Theme name for text domain

    Returns:
        Fallback template code
    """
    # Return strict structural templates for header/footer
    if template_name == 'header.php':
        return get_fallback_header_php(theme_name)
    elif template_name == 'footer.php':
        return get_fallback_footer_php(theme_name)

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


def final_pass_sanitizer(php_code: str, filename: str = "file.php") -> tuple[str, list[str]]:
    """FINAL PASS sanitizer that removes ALL illegal backslashes and malformed escapes.

    This runs AFTER the file is written to disk, as the last line of defense against
    malformed syntax. It's more aggressive than the initial sanitizer.

    This function:
    1. Removes illegal backslashes (preserving only valid PHP escapes)
    2. Fixes common LLM escape errors (\', \", \<, \ )
    3. Repairs malformed PHP blocks (mismatched <?php and ?>)
    4. Logs all removals for debugging

    Valid escapes that are preserved: \n, \r, \t, \\, \', \", \$

    Args:
        php_code: PHP code to sanitize
        filename: Filename for logging

    Returns:
        Tuple of (sanitized_code, list_of_cleanups_with_line_numbers)
    """
    cleanups = []
    original_code = php_code
    lines = php_code.split('\n')

    # STEP 1: Fix common escape errors
    # Replace \' with ' (LLM often escapes quotes unnecessarily)
    before = php_code
    php_code = php_code.replace(r"\'", "'")
    if php_code != before:
        # Count how many times we replaced
        count = before.count(r"\'")
        cleanups.append(f"[SANITIZER] Replaced {count} instances of \\' with ' (unnecessary escapes)")

    # Replace \" with " (LLM often escapes quotes unnecessarily)
    before = php_code
    php_code = php_code.replace(r'\"', '"')
    if php_code != before:
        count = before.count(r'\"')
        cleanups.append(f"[SANITIZER] Replaced {count} instances of \\\" with \" (unnecessary escapes)")

    # STEP 2: Remove backslashes before HTML tags
    before = php_code
    php_code = re.sub(r'\\<', '<', php_code)
    php_code = re.sub(r'\\>', '>', php_code)
    if php_code != before:
        cleanups.append(f"[SANITIZER] Removed backslashes before HTML tags (\\< and \\>)")

    # STEP 3: Remove backslashes before spaces
    before = php_code
    php_code = re.sub(r'\\ ', ' ', php_code)
    if php_code != before:
        cleanups.append(f"[SANITIZER] Removed backslashes before spaces (\\ )")

    # STEP 4: Remove unpaired/illegal backslashes
    # This regex keeps only valid PHP escapes: \n, \r, \t, \\, \', \", \$
    # Everything else is removed
    before = php_code
    # Match backslash NOT followed by valid escape characters
    php_code = re.sub(r'\\(?![nrt"\'\\$])', '', php_code)
    if php_code != before:
        removed_count = len(before) - len(php_code)
        cleanups.append(f"[SANITIZER] Removed {removed_count} illegal backslash(es) (preserving \\n, \\r, \\t, \\\\, \\', \\\", \\$)")

    # STEP 5: Remove backslashes before letters (except valid escapes)
    # This catches things like \a, \b, \c, etc. that aren't valid PHP escapes
    before = php_code
    # Remove \ before letters that aren't part of valid escapes
    # Valid: \n, \r, \t (already preserved above)
    # Invalid: \a, \b, \c, \d, etc.
    php_code = re.sub(r'\\([a-mo-qs-zA-MO-QS-Z])', r'\1', php_code)
    if php_code != before:
        cleanups.append(f"[SANITIZER] Removed backslashes before non-escape letters (\\a, \\b, etc.)")

    # STEP 6: Repair malformed PHP blocks
    php_open_count = php_code.count('<?php')
    php_close_count = php_code.count('?>')

    if php_open_count != php_close_count:
        if php_open_count > php_close_count:
            # More opens than closes - add missing closes
            missing = php_open_count - php_close_count
            php_code += '\n?>' * missing
            cleanups.append(f"[SANITIZER] Added {missing} missing ?> tag(s) to balance PHP blocks")
        else:
            # More closes than opens - add missing opens at the start
            missing = php_close_count - php_open_count
            php_code = '<?php\n' * missing + php_code
            cleanups.append(f"[SANITIZER] Added {missing} missing <?php tag(s) to balance PHP blocks")

    # STEP 7: Log line-by-line changes for detailed debugging
    if cleanups and len(lines) == len(php_code.split('\n')):
        new_lines = php_code.split('\n')
        changed_lines = []
        for i, (old_line, new_line) in enumerate(zip(lines, new_lines), start=1):
            if old_line != new_line:
                # Find what changed
                if '\\' in old_line and old_line != new_line:
                    changed_lines.append(i)

        if changed_lines and len(changed_lines) <= 10:  # Only log if reasonable number
            cleanups.append(f"[SANITIZER] Modified lines: {', '.join(map(str, changed_lines))}")

    return php_code, cleanups


def repair_php_blocks(php_code: str) -> tuple[str, list[str]]:
    """Detect and repair malformed PHP blocks (mismatched <?php and ?>).

    Args:
        php_code: PHP code to repair

    Returns:
        Tuple of (repaired_code, list_of_repairs)
    """
    repairs = []

    # Count PHP tags
    php_open_count = php_code.count('<?php')
    php_close_count = php_code.count('?>')

    if php_open_count != php_close_count:
        if php_open_count > php_close_count:
            # More opens than closes - add missing closes
            missing = php_open_count - php_close_count
            php_code += '\n?>' * missing
            repairs.append(f"Added {missing} missing ?> tag(s)")
        else:
            # More closes than opens - add missing opens
            missing = php_close_count - php_open_count
            # Try to add at the beginning if it doesn't already start with <?php
            if not php_code.strip().startswith('<?php'):
                php_code = '<?php\n' + php_code
                missing -= 1

            # If still missing, add more at the start
            if missing > 0:
                php_code = '<?php\n' * missing + php_code
                repairs.append(f"Added {missing} missing <?php tag(s)")

    return php_code, repairs


def get_minimal_fallback(filename: str, theme_name: str = "theme") -> str:
    """Get minimal non-breaking fallback template for any PHP file.

    These fallbacks are guaranteed to pass PHP syntax validation and never break WordPress.
    They are used when LLM generation fails AND sanitization cannot fix the code.

    Args:
        filename: Name of the PHP file (e.g., 'footer.php', 'header.php')
        theme_name: Theme name for text domain

    Returns:
        Minimal working PHP code for the file
    """
    if filename == 'footer.php':
        return """</main>

<footer class="site-footer">
    <div class="footer-container">
        <?php if ( is_active_sidebar( 'footer-1' ) ) dynamic_sidebar( 'footer-1' ); ?>
        <p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?></p>
    </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
"""

    elif filename == 'header.php':
        return f"""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<header class="site-header">
    <div class="container">
        <div class="site-branding">
            <?php if ( has_custom_logo() ) : ?>
                <?php the_custom_logo(); ?>
            <?php else : ?>
                <h1 class="site-title"><a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php bloginfo( 'name' ); ?></a></h1>
            <?php endif; ?>
        </div>

        <nav class="main-navigation">
            <?php
            wp_nav_menu( array(
                'theme_location' => 'primary',
                'menu_class'     => 'primary-menu',
                'fallback_cb'    => false,
            ) );
            ?>
        </nav>
    </div>
</header>

<main id="content" class="site-main">
"""

    elif filename == 'index.php':
        return f"""<?php get_header(); ?>

<div class="content-area">
    <?php if ( have_posts() ) : ?>
        <?php while ( have_posts() ) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                <header class="entry-header">
                    <h2 class="entry-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                </header>
                <div class="entry-content">
                    <?php the_excerpt(); ?>
                </div>
            </article>
        <?php endwhile; ?>
        <?php the_posts_pagination(); ?>
    <?php else : ?>
        <p>No posts found.</p>
    <?php endif; ?>
</div>

<?php get_footer(); ?>
"""

    elif filename == 'single.php':
        return f"""<?php get_header(); ?>

<div class="content-area">
    <?php while ( have_posts() ) : the_post(); ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
            <header class="entry-header">
                <h1 class="entry-title"><?php the_title(); ?></h1>
            </header>
            <div class="entry-content">
                <?php the_content(); ?>
            </div>
        </article>
    <?php endwhile; ?>
</div>

<?php get_footer(); ?>
"""

    elif filename == 'page.php':
        return f"""<?php get_header(); ?>

<div class="content-area">
    <?php while ( have_posts() ) : the_post(); ?>
        <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
            <header class="entry-header">
                <h1 class="entry-title"><?php the_title(); ?></h1>
            </header>
            <div class="entry-content">
                <?php the_content(); ?>
            </div>
        </article>
    <?php endwhile; ?>
</div>

<?php get_footer(); ?>
"""

    elif filename == 'sidebar.php':
        return f"""<aside class="sidebar">
    <?php if ( is_active_sidebar( 'sidebar-1' ) ) : ?>
        <?php dynamic_sidebar( 'sidebar-1' ); ?>
    <?php endif; ?>
</aside>
"""

    elif filename == 'functions.php':
        safe_name = theme_name.replace('-', '_')
        return f"""<?php
if ( ! defined( 'ABSPATH' ) ) exit;

function {safe_name}_setup() {{
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    register_nav_menus( array(
        'primary' => __( 'Primary Menu', '{theme_name}' ),
    ) );
}}
add_action( 'after_setup_theme', '{safe_name}_setup' );

function {safe_name}_scripts() {{
    wp_enqueue_style( '{theme_name}-style', get_stylesheet_uri() );
}}
add_action( 'wp_enqueue_scripts', '{safe_name}_scripts' );

function {safe_name}_widgets_init() {{
    register_sidebar( array(
        'name'          => __( 'Sidebar', '{theme_name}' ),
        'id'            => 'sidebar-1',
        'before_widget' => '<section class="widget">',
        'after_widget'  => '</section>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ) );
    register_sidebar( array(
        'name'          => __( 'Footer', '{theme_name}' ),
        'id'            => 'footer-1',
        'before_widget' => '<section class="widget">',
        'after_widget'  => '</section>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ) );
}}
add_action( 'widgets_init', '{safe_name}_widgets_init' );
"""

    else:
        # Generic fallback for unknown files
        return f"""<?php
// Minimal fallback for {filename}
"""


def sanitize_footer_php(php_code: str) -> tuple[str, list[str]]:
    """Sanitize footer.php to remove malformed syntax and fix common LLM errors.

    This function performs aggressive cleaning to prevent syntax errors:
    1. Removes ALL stray backslashes except valid PHP escapes
    2. Converts \' to ' and \" to "
    3. Normalizes common WordPress function calls (date, bloginfo, etc.)
    4. Removes \ before HTML tags or whitespace
    5. Removes duplicated <footer> sections (keeps only first)
    6. Ensures exactly one closing </body> and </html>

    Args:
        php_code: Footer PHP code to sanitize

    Returns:
        Tuple of (sanitized_code, list_of_cleanups_performed)
    """
    cleanups = []
    original_code = php_code

    # Step 0: Footer-specific WordPress function sanitization
    # Fix common LLM errors in copyright lines
    before = php_code
    # Normalize date() calls: date(\'Y\') -> date('Y')
    php_code = re.sub(r"date\(\\*'Y'\\*\)", "date('Y')", php_code)
    php_code = re.sub(r'date\(\\*"Y"\\*\)', "date('Y')", php_code)
    # Normalize bloginfo() calls: bloginfo(\'name\') -> bloginfo('name')
    php_code = re.sub(r"bloginfo\(\\*'name'\\*\)", "bloginfo('name')", php_code)
    php_code = re.sub(r'bloginfo\(\\*"name"\\*\)', "bloginfo('name')", php_code)
    # Also handle other common bloginfo parameters
    php_code = re.sub(r"bloginfo\(\\*'description'\\*\)", "bloginfo('description')", php_code)
    php_code = re.sub(r"bloginfo\(\\*'url'\\*\)", "bloginfo('url')", php_code)
    if php_code != before:
        cleanups.append("Normalized WordPress function calls (date, bloginfo) to remove backslash escaping")

    # Step 1: Remove backslashes before quotes (convert \' to ' and \" to ")
    # But preserve valid PHP escape sequences in strings
    before = php_code
    # Replace \' with ' (except in strings with proper context)
    php_code = re.sub(r"\\\'", "'", php_code)
    # Replace \" with " (except in strings with proper context)
    php_code = re.sub(r'\\"', '"', php_code)
    if php_code != before:
        cleanups.append("Converted escaped quotes (\' and \") to regular quotes")

    # Step 2: Remove backslashes before HTML tags
    before = php_code
    php_code = re.sub(r'\\<', '<', php_code)  # \< to <
    php_code = re.sub(r'\\>', '>', php_code)  # \> to >
    if php_code != before:
        cleanups.append("Removed backslashes before HTML tags")

    # Step 3: Remove backslashes before whitespace
    before = php_code
    php_code = re.sub(r'\\ +', ' ', php_code)  # "\ " to " "
    php_code = re.sub(r'\\\t', '\t', php_code)  # "\t" to tab
    php_code = re.sub(r'\\\n', '\n', php_code)  # "\n" to newline
    if php_code != before:
        cleanups.append("Removed backslashes before whitespace")

    # Step 4: Remove other stray backslashes (aggressive cleaning)
    before = php_code
    # Remove backslashes before common punctuation (but preserve in strings)
    php_code = re.sub(r'\\,', ',', php_code)
    php_code = re.sub(r'\\;', ';', php_code)
    php_code = re.sub(r'\\\(', '(', php_code)
    php_code = re.sub(r'\\\)', ')', php_code)
    php_code = re.sub(r'\\\{', '{', php_code)
    php_code = re.sub(r'\\\}', '}', php_code)
    php_code = re.sub(r'\\\[', '[', php_code)
    php_code = re.sub(r'\\\]', ']', php_code)
    if php_code != before:
        cleanups.append("Removed stray backslashes before punctuation")

    # Step 5: Remove duplicated <footer> sections (keep only the first)
    footer_matches = list(re.finditer(r'<footer[^>]*>', php_code, re.IGNORECASE))
    if len(footer_matches) > 1:
        # Find all complete footer sections
        footer_sections = []
        for i, match in enumerate(footer_matches):
            start = match.start()
            # Find the corresponding </footer>
            remaining = php_code[match.end():]
            close_match = re.search(r'</footer>', remaining, re.IGNORECASE)
            if close_match:
                end = match.end() + close_match.end()
                footer_sections.append((start, end))

        # Keep only the first footer, remove the rest
        if len(footer_sections) > 1:
            # Work backwards to maintain string indices
            for start, end in reversed(footer_sections[1:]):
                php_code = php_code[:start] + php_code[end:]
            cleanups.append(f"Removed {len(footer_sections) - 1} duplicate <footer> section(s), kept first one")

    # Step 6: Ensure exactly one </body> tag
    body_close_count = len(re.findall(r'</body>', php_code, re.IGNORECASE))
    if body_close_count > 1:
        # Keep only the last </body>
        php_code = re.sub(r'</body>', '', php_code, count=body_close_count - 1, flags=re.IGNORECASE)
        cleanups.append(f"Removed {body_close_count - 1} duplicate </body> tag(s), kept one")
    elif body_close_count == 0:
        # Add missing </body>
        php_code = php_code.rstrip() + "\n</body>"
        cleanups.append("Added missing </body> tag")

    # Step 7: Ensure exactly one </html> tag
    html_close_count = len(re.findall(r'</html>', php_code, re.IGNORECASE))
    if html_close_count > 1:
        # Keep only the last </html>
        php_code = re.sub(r'</html>', '', php_code, count=html_close_count - 1, flags=re.IGNORECASE)
        cleanups.append(f"Removed {html_close_count - 1} duplicate </html> tag(s), kept one")
    elif html_close_count == 0:
        # Add missing </html>
        php_code = php_code.rstrip() + "\n</html>"
        cleanups.append("Added missing </html> tag")

    return php_code, cleanups


def validate_footer_php_syntax(php_code: str, theme_dir: Path) -> tuple[bool, str, list[str]]:
    """Validate footer.php syntax using PHP CLI (php -l).

    This performs actual PHP syntax validation by writing the code to a temp file
    and running 'php -l' on it.

    Args:
        php_code: Footer PHP code to validate
        theme_dir: Theme directory (for temp file creation)

    Returns:
        Tuple of (is_valid, error_message, list_of_issues)
    """
    issues = []

    # Create a temporary file with the PHP code
    import tempfile
    import os

    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.php',
            delete=False,
            encoding='utf-8',
            dir=theme_dir if theme_dir.exists() else None
        ) as tmp:
            tmp.write(php_code)
            tmp_path = tmp.name

        # Run php -l on the file
        try:
            result = subprocess.run(
                ['php', '-l', tmp_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Syntax is valid
                return True, "", []
            else:
                # Syntax error found
                error_msg = result.stderr.strip() or result.stdout.strip()
                issues.append(f"PHP syntax error: {error_msg}")
                return False, error_msg, issues

        except subprocess.TimeoutExpired:
            issues.append("PHP validation timed out")
            return False, "Validation timeout", issues
        except FileNotFoundError:
            # php command not found
            logger.warning("PHP CLI not available for syntax validation")
            issues.append("PHP CLI not available (skipping syntax check)")
            return True, "", issues  # Assume valid if we can't check
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Error during PHP syntax validation: {str(e)}")
        issues.append(f"Validation error: {str(e)}")
        return False, str(e), issues


def validate_footer_requirements(php_code: str) -> tuple[bool, list[str]]:
    """Validate footer.php meets strict requirements before accepting it.

    This enforces the requirements:
    1. No more than one <footer> tag
    2. No stray backslashes inside PHP blocks
    3. Exactly one </body> tag
    4. Exactly one </html> tag

    Args:
        php_code: Footer PHP code to validate

    Returns:
        Tuple of (is_valid, list_of_validation_errors)
    """
    errors = []

    # Check 1: No more than one <footer> tag
    footer_count = len(re.findall(r'<footer[^>]*>', php_code, re.IGNORECASE))
    if footer_count > 1:
        errors.append(f"Multiple <footer> tags found ({footer_count}), expected exactly 1")

    # Check 2: No stray backslashes in PHP blocks
    # Extract PHP blocks
    php_blocks = re.findall(r'<\?php(.*?)\?>', php_code, re.DOTALL)
    for i, block in enumerate(php_blocks):
        # Look for suspicious backslashes (not in strings)
        # This is a simple heuristic - remove strings first
        block_no_strings = re.sub(r"'[^']*'", '', block)
        block_no_strings = re.sub(r'"[^"]*"', '', block_no_strings)

        # Check for backslashes before common characters
        if re.search(r'\\[<>\s,;(){}]', block_no_strings):
            errors.append(f"Stray backslashes found in PHP block {i+1}")

    # Check 3: Exactly one </body> tag
    body_close_count = len(re.findall(r'</body>', php_code, re.IGNORECASE))
    if body_close_count == 0:
        errors.append("Missing </body> tag")
    elif body_close_count > 1:
        errors.append(f"Multiple </body> tags found ({body_close_count}), expected exactly 1")

    # Check 4: Exactly one </html> tag
    html_close_count = len(re.findall(r'</html>', php_code, re.IGNORECASE))
    if html_close_count == 0:
        errors.append("Missing </html> tag")
    elif html_close_count > 1:
        errors.append(f"Multiple </html> tags found ({html_close_count}), expected exactly 1")

    is_valid = len(errors) == 0
    return is_valid, errors


def repair_footer_php(php_code: str) -> tuple[str, list[str]]:
    """Automatically repair footer.php to ensure it has required structure.

    This function ensures footer.php will never cause WordPress to display a blank
    screen or break the Customizer preview.

    Args:
        php_code: Footer PHP code to repair

    Returns:
        Tuple of (repaired_code, list_of_repairs_made)
    """
    repairs = []
    content_lower = php_code.lower()

    # Safe default footer that prevents layout collapse
    safe_footer = """
<footer class="site-footer">
    <div class="footer-inner container">
        <div class="footer-widgets">
            <?php if ( is_active_sidebar( 'footer-1' ) ) : ?>
                <div class="footer-widget-area">
                    <?php dynamic_sidebar( 'footer-1' ); ?>
                </div>
            <?php else : ?>
                <div class="footer-widget-area">
                    <h3 class="widget-title">About</h3>
                    <p>Welcome to <?php bloginfo( 'name' ); ?>.</p>
                </div>
            <?php endif; ?>
        </div>
        <div class="site-info">
            <p>&copy; <?php echo date( 'Y' ); ?> <?php bloginfo( 'name' ); ?>. All rights reserved.</p>
        </div>
    </div>
</footer>
"""

    # 1. Ensure wp_footer() hook exists
    if 'wp_footer()' not in php_code:
        # Find the position before </body> or at the end
        if '</body>' in content_lower:
            # Insert before </body>
            php_code = re.sub(
                r'(</body>)',
                r'<?php wp_footer(); ?>\n\1',
                php_code,
                flags=re.IGNORECASE
            )
            repairs.append("Added missing wp_footer() hook before </body>")
        else:
            # Append at end with closing tags
            php_code = php_code.rstrip() + "\n<?php wp_footer(); ?>\n</body>\n</html>\n"
            repairs.append("Added missing wp_footer() hook and closing tags")

    # 2. Ensure closing </body> and </html> tags exist
    if '</body>' not in content_lower:
        php_code = php_code.rstrip() + "\n</body>\n</html>\n"
        repairs.append("Added missing </body></html> closing tags")
    elif '</html>' not in content_lower:
        php_code = php_code.rstrip() + "\n</html>\n"
        repairs.append("Added missing </html> closing tag")

    # 3. If no <footer> tag at all, insert safe default footer
    if '<footer' not in content_lower:
        # Try to insert before wp_footer() or </body>
        if 'wp_footer()' in php_code:
            php_code = re.sub(
                r'(<\?php\s+wp_footer\(\);?\s*\?>)',
                safe_footer + r'\n\1',
                php_code,
                flags=re.IGNORECASE
            )
            repairs.append("Inserted safe default <footer> block (was missing)")
        elif '</body>' in content_lower:
            php_code = re.sub(
                r'(</body>)',
                safe_footer + r'\n\1',
                php_code,
                flags=re.IGNORECASE
            )
            repairs.append("Inserted safe default <footer> block before </body>")
        else:
            # Append before the end
            php_code = php_code.rstrip() + "\n" + safe_footer + "\n"
            repairs.append("Appended safe default <footer> block")

    # 4. If content area (</main>, </div class="content">, etc.) is not closed,
    # try to add a closing tag before footer
    # Look for opening <main but no closing </main>
    has_main_open = '<main' in content_lower
    has_main_close = '</main>' in content_lower

    if has_main_open and not has_main_close:
        # Insert </main> before <footer>
        if '<footer' in content_lower:
            php_code = re.sub(
                r'(<footer)',
                r'</main><!-- .site-main -->\n\n\1',
                php_code,
                count=1,
                flags=re.IGNORECASE
            )
            repairs.append("Added missing </main> closing tag before footer")

    # 5. Ensure there's at least some visible content in footer
    # Check if footer has any visible text or widgets
    if '<footer' in content_lower:
        # Extract footer content
        footer_match = re.search(
            r'<footer[^>]*>(.*?)</footer>',
            php_code,
            flags=re.IGNORECASE | re.DOTALL
        )
        if footer_match:
            footer_content = footer_match.group(1)
            # Remove PHP code and check if there's any HTML content
            footer_content_no_php = re.sub(r'<\?php.*?\?>', '', footer_content, flags=re.DOTALL)
            # Check for any meaningful HTML tags or text
            has_content = (
                'dynamic_sidebar' in footer_content or
                '<div' in footer_content_no_php or
                '<p' in footer_content_no_php or
                len(footer_content_no_php.strip()) > 20
            )
            if not has_content:
                # Footer is empty, replace it with safe footer
                php_code = re.sub(
                    r'<footer[^>]*>.*?</footer>',
                    safe_footer,
                    php_code,
                    count=1,
                    flags=re.IGNORECASE | re.DOTALL
                )
                repairs.append("Replaced empty footer with safe default content")

    return php_code, repairs


def validate_and_fix_template_structure(theme_dir: Path) -> dict[str, Any]:
    """
    Validate and auto-correct template structure issues to prevent white screens.

    This enforces:
    - header.php must contain <header>, site-branding, nav, and opening <main id="content">
    - footer.php must contain closing </main> and <footer>
    - index.php must include a loop and get_footer()
    - No unmatched braces, missing tags, or broken PHP blocks

    Args:
        theme_dir: Path to theme directory

    Returns:
        Dictionary with validation results and repairs made
    """
    logger.info("Validating and fixing template structure")
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'repairs': [],
    }

    # Define required structure for each template
    template_requirements = {
        'header.php': {
            'must_contain': ['<header', 'wp_head()', '<main'],
            'must_not_contain': ['</main>'],  # Should NOT close main
            'should_contain': ['wp_nav_menu', 'bloginfo'],
            'php_required': True,
        },
        'footer.php': {
            'must_contain': ['</main>', '<footer', 'wp_footer()'],
            'must_not_contain': [],
            'should_contain': ['</body>', '</html>'],
            'php_required': True,
        },
        'index.php': {
            'must_contain': ['get_header()', 'get_footer()', 'have_posts'],
            'must_not_contain': [],
            'should_contain': ['the_post()', 'the_content'],
            'php_required': True,
        },
        'functions.php': {
            'must_contain': ['<?php'],
            'must_not_contain': [],
            'should_contain': ['function', 'add_action', 'add_theme_support'],
            'php_required': True,
        },
    }

    # Validate and fix each template
    for template_name, requirements in template_requirements.items():
        template_path = theme_dir / template_name

        if not template_path.exists():
            results['warnings'].append(f"Template not found: {template_name}")
            continue

        try:
            with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original_content = content
            content_lower = content.lower()
            repairs_made = []

            # Check for required elements
            for required in requirements['must_contain']:
                if required.lower() not in content_lower:
                    content, repair_msg = _add_missing_element(
                        content, template_name, required
                    )
                    if repair_msg:
                        repairs_made.append(repair_msg)
                        results['repairs'].append(f"{template_name}: {repair_msg}")

            # Check for prohibited elements
            for prohibited in requirements['must_not_contain']:
                if prohibited.lower() in content_lower:
                    content, repair_msg = _remove_element(
                        content, template_name, prohibited
                    )
                    if repair_msg:
                        repairs_made.append(repair_msg)
                        results['repairs'].append(f"{template_name}: {repair_msg}")

            # Validate PHP syntax
            is_valid, error_msg = validate_php_syntax(content)
            if not is_valid:
                logger.warning(f"PHP syntax error in {template_name}: {error_msg}")
                # Try to fix
                content, php_repairs = repair_wordpress_code(content, template_name)
                repairs_made.extend(php_repairs)
                for repair in php_repairs:
                    results['repairs'].append(f"{template_name}: {repair}")

                # Validate again
                is_valid, error_msg = validate_php_syntax(content)
                if not is_valid:
                    results['errors'].append(f"{template_name}: {error_msg}")
                    results['valid'] = False

            # Check for unmatched braces/tags
            brace_issues = _check_balanced_braces(content)
            if brace_issues:
                for issue in brace_issues:
                    results['errors'].append(f"{template_name}: {issue}")
                results['valid'] = False

            # Write repaired content if changed
            if content != original_content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Auto-repaired {template_name} ({len(repairs_made)} fixes)")

        except Exception as e:
            logger.error(f"Error validating {template_name}: {e}")
            results['errors'].append(f"{template_name}: Validation error - {str(e)}")
            results['valid'] = False

    return results


def _add_missing_element(content: str, template_name: str, element: str) -> tuple[str, str]:
    """Add a missing required element to a template."""
    repair_msg = ""

    if template_name == 'header.php':
        if element == '<header':
            # Add header tag after body
            if '<body' in content.lower():
                content = re.sub(
                    r'(<body[^>]*>)',
                    r'\1\n<header class="site-header">\n    <!-- Header content -->\n</header>\n',
                    content,
                    count=1,
                    flags=re.IGNORECASE
                )
                repair_msg = "Added missing <header> tag"

        elif element == 'wp_head()':
            # Add wp_head() before </head>
            if '</head>' in content.lower():
                content = re.sub(
                    r'(</head>)',
                    r'<?php wp_head(); ?>\n\1',
                    content,
                    count=1,
                    flags=re.IGNORECASE
                )
                repair_msg = "Added missing wp_head() call"

        elif element == '<main':
            # Add opening main tag at the end
            if '</header>' in content.lower():
                content = re.sub(
                    r'(</header>)',
                    r'\1\n<main id="content" class="site-main">\n',
                    content,
                    count=1,
                    flags=re.IGNORECASE
                )
            else:
                content += '\n<main id="content" class="site-main">\n'
            repair_msg = "Added opening <main id=\"content\"> tag"

    elif template_name == 'footer.php':
        if element == '</main>':
            # Add closing main tag at the beginning
            content = '</main><!-- .site-main -->\n\n' + content
            repair_msg = "Added closing </main> tag"

        elif element == '<footer':
            # Add footer tag
            if 'wp_footer()' in content:
                content = re.sub(
                    r'(<\?php\s+wp_footer\(\);?\s*\?>)',
                    r'<footer class="site-footer">\n    <div class="footer-content">\n        <p>&copy; <?php echo date(\'Y\'); ?> <?php bloginfo(\'name\'); ?></p>\n    </div>\n</footer>\n\n\1',
                    content,
                    count=1
                )
            else:
                content = '<footer class="site-footer">\n    <div class="footer-content">\n        <p>&copy; <?php echo date(\'Y\'); ?> <?php bloginfo(\'name\'); ?></p>\n    </div>\n</footer>\n' + content
            repair_msg = "Added <footer> tag"

        elif element == 'wp_footer()':
            # Add wp_footer() before </body>
            if '</body>' in content.lower():
                content = re.sub(
                    r'(</body>)',
                    r'<?php wp_footer(); ?>\n\1',
                    content,
                    count=1,
                    flags=re.IGNORECASE
                )
            else:
                content += '\n<?php wp_footer(); ?>\n</body>\n</html>\n'
            repair_msg = "Added wp_footer() call"

    elif template_name == 'index.php':
        if element == 'get_header()':
            # Add get_header() at the beginning
            if not content.startswith('<?php'):
                content = '<?php get_header(); ?>\n\n' + content
            else:
                content = re.sub(
                    r'(<\?php)',
                    r'\1 get_header(); ?>',
                    content,
                    count=1
                )
            repair_msg = "Added get_header() call"

        elif element == 'get_footer()':
            # Add get_footer() at the end
            if '?>' in content:
                content = re.sub(
                    r'(\?>)(?!.*\?>)',
                    r'<?php get_footer(); \1',
                    content,
                    flags=re.DOTALL
                )
            else:
                content += '\n<?php get_footer(); ?>\n'
            repair_msg = "Added get_footer() call"

        elif element == 'have_posts':
            # Add basic WordPress loop
            loop_code = """
if ( have_posts() ) :
    while ( have_posts() ) :
        the_post();
        the_content();
    endwhile;
endif;
"""
            # Insert after get_header if present
            if 'get_header()' in content:
                content = re.sub(
                    r'(get_header\(\);?\s*\?>)',
                    r'\1\n\n<?php\n' + loop_code + '\n?>',
                    content,
                    count=1
                )
            else:
                content += '\n<?php\n' + loop_code + '\n?>\n'
            repair_msg = "Added WordPress loop"

    return content, repair_msg


def _remove_element(content: str, template_name: str, element: str) -> tuple[str, str]:
    """Remove a prohibited element from a template."""
    repair_msg = ""

    if template_name == 'header.php' and element == '</main>':
        # Remove closing main tag from header
        content = re.sub(
            r'</main[^>]*>',
            '',
            content,
            flags=re.IGNORECASE
        )
        repair_msg = "Removed incorrect </main> tag (should be in footer.php)"

    return content, repair_msg


def _check_balanced_braces(content: str) -> list[str]:
    """Check for unmatched braces and tags."""
    issues = []

    # Remove PHP strings and comments to avoid false positives
    cleaned = re.sub(r"'[^']*'", '', content)
    cleaned = re.sub(r'"[^"]*"', '', cleaned)
    cleaned = re.sub(r'//.*?$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)

    # Check PHP braces
    php_open = cleaned.count('{')
    php_close = cleaned.count('}')
    if php_open != php_close:
        issues.append(f"Unmatched braces: {php_open} opening, {php_close} closing")

    # Check PHP tags
    php_tag_open = len(re.findall(r'<\?php', cleaned, re.IGNORECASE))
    php_tag_close = cleaned.count('?>')
    if php_tag_open != php_tag_close:
        issues.append(f"Unmatched PHP tags: {php_tag_open} <?php, {php_tag_close} ?>")

    return issues


def sanitize_theme_filename(filename: str) -> tuple[str, list[str]]:
    """Sanitize theme filenames to prevent duplicates and invalid extensions.

    Fixes common LLM-generated filename errors:
    - page-header.php.php → header.php
    - page-style.css.php → style.css
    - page-index.php.php → index.php
    - footer.php.css → footer.php
    - header.html.php → header.php

    Args:
        filename: Original filename

    Returns:
        Tuple of (sanitized_filename, list_of_changes_made)
    """
    changes = []
    original = filename

    # Strip any leading "page-" prefix that LLMs sometimes add
    if filename.startswith('page-'):
        filename = filename[5:]  # Remove "page-"
        changes.append(f"Removed 'page-' prefix")

    # Remove duplicate extensions (.php.php, .css.css, etc.)
    while True:
        # Check for double .php
        if filename.endswith('.php.php'):
            filename = filename[:-4]  # Remove one .php
            changes.append("Removed duplicate .php extension")
        # Check for .css.php (wrong extension)
        elif filename.endswith('.css.php'):
            filename = filename[:-4]  # Remove .php, keep .css
            changes.append("Removed incorrect .php extension from CSS file")
        # Check for .html.php (wrong extension)
        elif filename.endswith('.html.php'):
            filename = filename[:-5]  # Remove .html
            changes.append("Removed .html extension from PHP file")
        # Check for .js.php (wrong extension)
        elif filename.endswith('.js.php'):
            filename = filename[:-4]  # Remove .php, keep .js
            changes.append("Removed incorrect .php extension from JS file")
        # Check for any other double extension
        elif re.search(r'\.\w+\.\w+$', filename):
            # Keep only the last extension
            parts = filename.rsplit('.', 2)
            if len(parts) >= 3:
                filename = parts[0] + '.' + parts[2]
                changes.append(f"Removed duplicate extension .{parts[1]}")
        else:
            break

    # Ensure PHP template files have .php extension only
    php_templates = [
        'header', 'footer', 'index', 'functions', 'single', 'page',
        'archive', 'search', '404', 'sidebar', 'front-page',
        'home', 'category', 'tag', 'author', 'date', 'attachment'
    ]

    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
    if base_name in php_templates:
        if not filename.endswith('.php'):
            filename = base_name + '.php'
            changes.append(f"Corrected extension to .php for template file")

    # Ensure style.css is exactly that
    if 'style' in filename.lower() and filename != 'style.css':
        if not filename.startswith('_') and not filename.startswith('.'):
            filename = 'style.css'
            changes.append("Normalized to 'style.css'")

    # Prevent common hallucinated filenames
    invalid_patterns = {
        r'^template-.*\.php$': None,  # template-header.php → header.php
        r'^wp-.*\.php$': None,  # wp-header.php → header.php
        r'^theme-.*\.php$': None,  # theme-header.php → header.php
    }

    for pattern, replacement in invalid_patterns.items():
        if re.match(pattern, filename):
            # Extract the core name (e.g., "header" from "template-header.php")
            match = re.search(r'-([\w-]+)\.php$', filename)
            if match:
                core_name = match.group(1)
                if core_name in php_templates:
                    filename = f"{core_name}.php"
                    changes.append(f"Removed invalid prefix from filename")

    if changes:
        logger.info(f"Sanitized filename: '{original}' → '{filename}'")
        for change in changes:
            logger.debug(f"  - {change}")

    return filename, changes


def validate_theme_filenames(theme_dir: Path) -> dict[str, Any]:
    """Validate and sanitize all filenames in a theme directory.

    Args:
        theme_dir: Path to theme directory

    Returns:
        Dictionary with validation results and renames performed
    """
    results = {
        'valid': True,
        'renames': [],
        'errors': [],
    }

    theme_dir = Path(theme_dir)

    if not theme_dir.exists():
        results['valid'] = False
        results['errors'].append(f"Theme directory does not exist: {theme_dir}")
        return results

    # Check all files in theme directory (non-recursive for now, just top-level templates)
    for file_path in theme_dir.iterdir():
        if file_path.is_file():
            original_name = file_path.name
            sanitized_name, changes = sanitize_theme_filename(original_name)

            if changes:
                # Rename the file
                new_path = theme_dir / sanitized_name

                # Check if target already exists
                if new_path.exists() and new_path != file_path:
                    logger.warning(f"Cannot rename {original_name} to {sanitized_name}: target already exists")
                    results['errors'].append(f"Rename conflict: {original_name} → {sanitized_name} (target exists)")
                    results['valid'] = False
                else:
                    try:
                        file_path.rename(new_path)
                        results['renames'].append(f"{original_name} → {sanitized_name}")
                        logger.info(f"Renamed file: {original_name} → {sanitized_name}")
                    except Exception as e:
                        logger.error(f"Failed to rename {original_name}: {e}")
                        results['errors'].append(f"Failed to rename {original_name}: {str(e)}")
                        results['valid'] = False

    return results


def scan_mixed_content(theme_dir: Path, enforce_https: bool = True) -> dict[str, Any]:
    """Scan generated theme files for mixed-content (http://) URLs.

    This scanner helps ensure themes don't have insecure HTTP URLs that would
    cause mixed-content warnings on HTTPS sites.

    Args:
        theme_dir: Path to theme directory to scan
        enforce_https: If True, fail generation when http:// URLs are found (default: True)

    Returns:
        Dictionary with scan results:
        {
            'valid': bool,
            'http_urls': list of dicts with {'file': str, 'line': int, 'url': str},
            'errors': list of error messages
        }
    """
    results = {
        'valid': True,
        'http_urls': [],
        'errors': [],
    }

    theme_dir = Path(theme_dir)

    if not theme_dir.exists():
        results['valid'] = False
        results['errors'].append(f"Theme directory does not exist: {theme_dir}")
        return results

    # Allowed HTTP patterns that are safe (localhost, local development)
    allowed_patterns = [
        r'http://localhost',
        r'http://127\.0\.0\.1',
        r'http://\[::1\]',
        r'http://.*\.local',
        r'http://schemas\.wp\.org',  # WordPress JSON schemas
        r'http://www\.w3\.org',      # W3C standards (DTDs, etc.)
        r'http://gmpg\.org/xfn',     # XFN profile (legacy but standard)
    ]

    # File extensions to scan
    extensions = ['.php', '.js', '.css', '.json', '.html', '.htm']

    # Recursively scan all files
    for file_path in theme_dir.rglob('*'):
        if not file_path.is_file():
            continue

        if file_path.suffix not in extensions:
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # Find all http:// URLs
                http_urls = re.findall(r'http://[^\s\'"<>]+', line)

                for url in http_urls:
                    # Check if URL matches any allowed pattern
                    is_allowed = any(re.match(pattern, url) for pattern in allowed_patterns)

                    if not is_allowed:
                        relative_path = file_path.relative_to(theme_dir)
                        results['http_urls'].append({
                            'file': str(relative_path),
                            'line': line_num,
                            'url': url,
                            'context': line.strip()[:100]  # First 100 chars for context
                        })

        except Exception as e:
            logger.warning(f"Error scanning {file_path}: {e}")
            continue

    # If enforce_https is True and we found insecure URLs, mark as invalid
    if enforce_https and results['http_urls']:
        results['valid'] = False
        error_msg = f"Found {len(results['http_urls'])} insecure HTTP URL(s) in theme:"
        results['errors'].append(error_msg)

        for item in results['http_urls']:
            results['errors'].append(f"  {item['file']}:{item['line']} → {item['url']}")

        results['errors'].append("\nTo fix: Use https:// or WordPress helpers like get_template_directory_uri()")

    return results


def check_forbidden_config_directives(theme_dir: Path) -> dict[str, Any]:
    """Scan generated theme files for forbidden WordPress config directives.

    Themes should NEVER define WP_DEBUG, error_reporting, or ini_set directives
    as these should only appear in wp-config.php, not in theme files.

    Args:
        theme_dir: Path to theme directory to scan

    Returns:
        Dictionary with scan results:
        {
            'valid': bool,
            'violations': list of dicts with {'file': str, 'line': int, 'pattern': str, 'context': str},
            'errors': list of error messages
        }
    """
    results = {
        'valid': True,
        'violations': [],
        'errors': [],
    }

    theme_dir = Path(theme_dir)

    if not theme_dir.exists():
        results['valid'] = False
        results['errors'].append(f"Theme directory does not exist: {theme_dir}")
        return results

    # Forbidden patterns that should never appear in theme files
    forbidden_patterns = [
        (r"define\s*\(\s*['\"]WP_DEBUG['\"]", "define('WP_DEBUG', ...)"),
        (r"define\s*\(\s*['\"]WP_DEBUG_LOG['\"]", "define('WP_DEBUG_LOG', ...)"),
        (r"define\s*\(\s*['\"]WP_DEBUG_DISPLAY['\"]", "define('WP_DEBUG_DISPLAY', ...)"),
        (r"ini_set\s*\(\s*['\"]display_errors['\"]", "ini_set('display_errors', ...)"),
        (r"ini_set\s*\(\s*['\"]error_reporting['\"]", "ini_set('error_reporting', ...)"),
        (r"\berror_reporting\s*\(", "error_reporting(...)"),
    ]

    # File extensions to scan (PHP files only)
    extensions = ['.php']

    # Recursively scan all PHP files
    for file_path in theme_dir.rglob('*'):
        if not file_path.is_file():
            continue

        if file_path.suffix not in extensions:
            continue

        # Skip wp-config-sample.php (legitimate place for WP_DEBUG)
        if file_path.name == 'wp-config-sample.php' or file_path.name == 'wp-config.php':
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern_regex, pattern_name in forbidden_patterns:
                    if re.search(pattern_regex, line, re.IGNORECASE):
                        relative_path = file_path.relative_to(theme_dir)
                        results['violations'].append({
                            'file': str(relative_path),
                            'line': line_num,
                            'pattern': pattern_name,
                            'context': line.strip()[:150]  # First 150 chars for context
                        })

        except Exception as e:
            logger.warning(f"Error scanning {file_path}: {e}")
            continue

    # Mark as invalid if violations found
    if results['violations']:
        results['valid'] = False
        error_msg = f"Found {len(results['violations'])} forbidden config directive(s) in theme files:"
        results['errors'].append(error_msg)

        for violation in results['violations']:
            results['errors'].append(
                f"  {violation['file']}:{violation['line']} → {violation['pattern']}"
            )
            results['errors'].append(f"    Context: {violation['context']}")

        results['errors'].append(
            "\nThemes must NOT define WP_DEBUG, error_reporting, or ini_set directives."
        )
        results['errors'].append("These belong in wp-config.php, not theme files.")

    return results


def check_invalid_php_patterns(theme_dir: Path) -> dict[str, Any]:
    """Scan generated theme files for invalid PHP patterns that cause parse errors.

    Detects patterns like:
    - <?= ; ?> (empty short echo)
    - <?php ; ?> (empty PHP block)
    - if (...); { (semicolon before brace)
    - foreach (...); { (semicolon before brace)
    - function name(); (function declaration with semicolon instead of brace)

    Args:
        theme_dir: Path to theme directory to scan

    Returns:
        Dictionary with scan results:
        {
            'valid': bool,
            'violations': list of dicts with {'file': str, 'line': int, 'pattern': str, 'context': str},
            'errors': list of error messages
        }
    """
    results = {
        'valid': True,
        'violations': [],
        'errors': [],
    }

    theme_dir = Path(theme_dir)

    if not theme_dir.exists():
        results['valid'] = False
        results['errors'].append(f"Theme directory does not exist: {theme_dir}")
        return results

    # Invalid PHP patterns to detect
    # Each pattern includes regex and description
    invalid_patterns = [
        (r"<\?=\s*;?\s*\?>", "Empty short echo: <?= ; ?> or <?= ?>"),
        (r"<\?php\s*;+\s*\?>", "Empty PHP block with semicolon: <?php ; ?>"),
        (r"\bif\s*\([^)]*\)\s*;", "if statement with trailing semicolon: if (...);"),
        (r"\bforeach\s*\([^)]*\)\s*;", "foreach with trailing semicolon: foreach (...);"),
        (r"\bwhile\s*\([^)]*\)\s*;", "while with trailing semicolon: while (...);"),
        (r"\bfor\s*\([^)]*\)\s*;", "for with trailing semicolon: for (...);"),
        (r"\bfunction\s+\w+\s*\([^)]*\)\s*;", "Function declaration with semicolon: function name();"),
    ]

    # File extensions to scan (PHP files only)
    extensions = ['.php']

    # Recursively scan all PHP files
    for file_path in theme_dir.rglob('*'):
        if not file_path.is_file():
            continue

        if file_path.suffix not in extensions:
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern_regex, pattern_name in invalid_patterns:
                    match = re.search(pattern_regex, line)
                    if match:
                        relative_path = file_path.relative_to(theme_dir)

                        # Extract the matched text for better error messages
                        matched_text = match.group(0)

                        results['violations'].append({
                            'file': str(relative_path),
                            'line': line_num,
                            'pattern': pattern_name,
                            'matched': matched_text,
                            'context': line.strip()[:150]  # First 150 chars for context
                        })

        except Exception as e:
            logger.warning(f"Error scanning {file_path}: {e}")
            continue

    # Mark as invalid if violations found
    if results['violations']:
        results['valid'] = False
        error_msg = f"Found {len(results['violations'])} invalid PHP pattern(s) in theme files:"
        results['errors'].append(error_msg)

        for violation in results['violations']:
            results['errors'].append(
                f"  {violation['file']}:{violation['line']} → {violation['pattern']}"
            )
            results['errors'].append(f"    Matched: '{violation['matched']}'")
            results['errors'].append(f"    Context: {violation['context']}")

        results['errors'].append("\nSuggested fixes:")
        results['errors'].append("  - Remove empty PHP blocks: <?= ; ?> → (remove entirely)")
        results['errors'].append("  - Remove semicolons before braces: if (...); { → if (...) {")
        results['errors'].append("  - Use braces for functions: function name(); → function name() {")

    return results


def check_block_categories(theme_dir: Path) -> dict[str, Any]:
    """Scan block.json files for invalid WordPress block categories.

    Valid categories are: text, media, design, widgets, theme, embed

    Args:
        theme_dir: Path to theme directory to scan

    Returns:
        Dictionary with scan results:
        {
            'valid': bool,
            'violations': list of dicts with {'file': str, 'category': str},
            'errors': list of error messages
        }
    """
    results = {
        'valid': True,
        'violations': [],
        'errors': [],
    }

    theme_dir = Path(theme_dir)

    if not theme_dir.exists():
        results['valid'] = False
        results['errors'].append(f"Theme directory does not exist: {theme_dir}")
        return results

    # Valid WordPress core block categories
    valid_categories = {"text", "media", "design", "widgets", "theme", "embed"}

    # Find all block.json files
    for file_path in theme_dir.rglob('block.json'):
        try:
            import json
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                block_data = json.load(f)

            category = block_data.get('category', '')
            if category and category not in valid_categories:
                relative_path = file_path.relative_to(theme_dir)
                results['valid'] = False
                results['violations'].append({
                    'file': str(relative_path),
                    'category': category
                })
                results['errors'].append(
                    f"Invalid block category '{category}' in {relative_path}. "
                    f"Must be one of: {', '.join(sorted(valid_categories))}"
                )
        except Exception as e:
            # If we can't parse the JSON, skip it (will be caught by other validators)
            logger.debug(f"Could not parse {file_path}: {e}")
            continue

    return results


def scan_generated_theme(theme_dir: Path, strict: bool = True) -> dict[str, Any]:
    """Comprehensive post-render scan of generated theme to catch forbidden patterns.

    This is the master scanner that runs all checks:
    1. Forbidden config directives (WP_DEBUG, error_reporting, ini_set)
    2. Invalid PHP patterns (<?= ; ?>, if (...);, etc.)
    3. Block category validation
    4. Mixed content (optional, based on strict flag)

    Args:
        theme_dir: Path to generated theme directory
        strict: If True, fail on any violations (default: True)

    Returns:
        Dictionary with combined scan results:
        {
            'valid': bool (True if all checks pass),
            'config_check': dict (results from check_forbidden_config_directives),
            'php_check': dict (results from check_invalid_php_patterns),
            'block_check': dict (results from check_block_categories),
            'mixed_content_check': dict (results from scan_mixed_content, if strict),
            'all_errors': list of all error messages combined
        }
    """
    logger.info(f"Running post-render scan on theme directory: {theme_dir}")

    # Run all checks
    config_check = check_forbidden_config_directives(theme_dir)
    php_check = check_invalid_php_patterns(theme_dir)
    block_check = check_block_categories(theme_dir)

    # Collect all errors
    all_errors = []
    all_errors.extend(config_check['errors'])
    all_errors.extend(php_check['errors'])
    all_errors.extend(block_check['errors'])

    # Determine overall validity
    is_valid = config_check['valid'] and php_check['valid'] and block_check['valid']

    results = {
        'valid': is_valid,
        'config_check': config_check,
        'php_check': php_check,
        'block_check': block_check,
        'all_errors': all_errors,
    }

    # If strict mode, also check mixed content
    if strict:
        mixed_content_check = scan_mixed_content(theme_dir, enforce_https=True)
        results['mixed_content_check'] = mixed_content_check
        all_errors.extend(mixed_content_check['errors'])
        is_valid = is_valid and mixed_content_check['valid']
        results['valid'] = is_valid
        results['all_errors'] = all_errors

    # Log summary
    if is_valid:
        logger.info("✓ Theme passed all post-render checks")
    else:
        logger.error(f"✗ Theme failed post-render checks with {len(all_errors)} error(s)")
        for error in all_errors:
            logger.error(f"  {error}")

    return results
