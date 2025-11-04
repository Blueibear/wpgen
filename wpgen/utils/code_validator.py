"""Code validation utilities for generated theme files.

This module provides validation for generated code to catch syntax errors
and common issues before they cause WordPress to crash.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional
from .logger import get_logger


logger = get_logger(__name__)


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
        # Remove any explanatory text before <?php
        if '<?php' in code:
            # Find first occurrence of <?php
            php_start = code.find('<?php')
            code = code[php_start:]

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
    return f"""<?php
/**
 * Theme functions and definitions
 *
 * @package {theme_name}
 */

if ( ! defined( 'ABSPATH' ) ) {{
    exit; // Exit if accessed directly
}}

/**
 * Sets up theme defaults and registers support for various WordPress features.
 */
function {theme_name.replace('-', '_')}_setup() {{
    // Add theme support
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'html5', array(
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
    ) );

    // Register navigation menus
    register_nav_menus( array(
        'primary' => __( 'Primary Menu', '{theme_name}' ),
    ) );
}}
add_action( 'after_setup_theme', '{theme_name.replace('-', '_')}_setup' );

/**
 * Enqueue scripts and styles.
 */
function {theme_name.replace('-', '_')}_scripts() {{
    // Enqueue styles
    wp_enqueue_style( '{theme_name}-style', get_stylesheet_uri(), array(), '1.0.0' );

    // Enqueue wpgen-ui assets
    wp_enqueue_style( 'wpgen-ui', get_template_directory_uri() . '/assets/css/wpgen-ui.css', array(), '1.0.0' );
    wp_enqueue_script( 'wpgen-ui', get_template_directory_uri() . '/assets/js/wpgen-ui.js', array(), '1.0.0', true );
}}
add_action( 'wp_enqueue_scripts', '{theme_name.replace('-', '_')}_scripts' );

/**
 * Register widget areas.
 */
function {theme_name.replace('-', '_')}_widgets_init() {{
    register_sidebar( array(
        'name'          => __( 'Sidebar', '{theme_name}' ),
        'id'            => 'sidebar-1',
        'description'   => __( 'Add widgets here.', '{theme_name}' ),
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h2 class="widget-title">',
        'after_title'   => '</h2>',
    ) );
}}
add_action( 'widgets_init', '{theme_name.replace('-', '_')}_widgets_init' );
"""
