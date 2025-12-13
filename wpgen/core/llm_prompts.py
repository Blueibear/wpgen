"""LLM Prompts Module for WPGen.

This module provides standardized, carefully crafted prompts for LLM code generation.
All prompts are designed to:
- Minimize hallucinations
- Enforce WordPress best practices
- Prevent common errors (barewords, stray backslashes, duplicate tags)
- Generate clean, valid code without markdown or explanations

Every prompt explicitly constrains the LLM to prevent known failure modes.
"""

from typing import Dict, Any, Optional


def get_base_system_prompt() -> str:
    """Get base system prompt for all WordPress theme generation.

    This prompt establishes the fundamental rules that apply to all
    generated code regardless of file type.

    Returns:
        Base system prompt string
    """
    return """You are a WordPress theme code generator. You generate ONLY valid, working PHP, HTML, CSS, and JavaScript code for WordPress themes.

CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:

1. OUTPUT RULES:
   - Output ONLY raw code - no explanations, no markdown, no comments outside code
   - Do NOT wrap code in ```php or ``` code fences
   - Do NOT start with phrases like "Here's the code:" or "Sure, I'll create..."
   - Start immediately with <?php (for PHP files) or the appropriate opening tag

2. PHP RULES:
   - Use ONLY real WordPress functions - no hallucinated functions
   - Always quote string values in arrays: 'key' => 'value', NOT 'key' => value
   - Never use stray backslashes: use date('Y') NOT date(\\'Y\\')
   - Never define WP_DEBUG, error_reporting, or ini_set in theme files
   - Always escape output: esc_html(), esc_attr(), esc_url()

3. STRUCTURE RULES:
   - Never duplicate closing tags (</body>, </html> appear only once)
   - Always balance opening and closing tags
   - Never put wp_head() anywhere except header.php
   - Never put wp_footer() anywhere except footer.php

4. WORDPRESS TEMPLATE HIERARCHY:
   - header.php: Contains <!DOCTYPE>, <html>, <head>, wp_head(), opening <body>
   - footer.php: Contains wp_footer(), closing </body>, closing </html>
   - All other templates: Use get_header() and get_footer(), contain <main>...</main>

5. BANNED PATTERNS:
   - Do NOT use: post_loop(), render_post(), display_product(), is_on_sale()
   - These functions DO NOT exist in WordPress
   - Use ONLY documented WordPress functions

Your generated code will be validated. Invalid code will be automatically replaced with fallback templates."""


def get_header_prompt(theme_name: str, theme_slug: str, requirements: Dict[str, Any]) -> str:
    """Get prompt for generating header.php.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        requirements: Theme requirements dictionary

    Returns:
        Complete prompt for header.php generation
    """
    sticky = "sticky" if requirements.get('sticky_header', False) else ""
    show_search = requirements.get('show_search', True)

    return f"""Generate header.php for WordPress theme "{theme_name}".

REQUIRED ELEMENTS (all must be present):
1. <!DOCTYPE html>
2. <html <?php language_attributes(); ?>>
3. <head> with charset, viewport, wp_head()
4. <body <?php body_class(); ?>>
5. <?php wp_body_open(); ?>
6. Site header with navigation

STRUCTURE:
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<div id="page" class="site">
    <header class="site-header {sticky}">
        [site branding with logo/title]
        [navigation menu]
        {"[search form]" if show_search else ""}
    </header>

REQUIREMENTS:
- Use bloginfo() for site name/description
- Use has_custom_logo() and the_custom_logo() for logo
- Use wp_nav_menu() with theme_location 'primary'
- Add menu toggle button for mobile
{"- Include search form" if show_search else ""}
- Text domain: {theme_slug}

Do NOT close </body> or </html> - that's footer.php's job.
Output ONLY the code, starting with <!DOCTYPE html>"""


def get_footer_prompt(theme_name: str, theme_slug: str, requirements: Dict[str, Any]) -> str:
    """Get prompt for generating footer.php.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        requirements: Theme requirements dictionary

    Returns:
        Complete prompt for footer.php generation
    """
    footer_columns = requirements.get('footer_columns', 3)

    return f"""Generate footer.php for WordPress theme "{theme_name}".

REQUIRED ELEMENTS (all must be present):
1. Footer widget areas
2. Copyright/site info section
3. <?php wp_footer(); ?> BEFORE </body>
4. Closing </div> for #page
5. Closing </body>
6. Closing </html>

STRUCTURE:
    <footer class="site-footer">
        [widget areas - {footer_columns} columns]
        [copyright and site info]
    </footer>
</div><!-- #page -->
<?php wp_footer(); ?>
</body>
</html>

REQUIREMENTS:
- Use dynamic_sidebar() for footer-1, footer-2, footer-3 widget areas
- Use is_active_sidebar() to check before displaying widget areas
- Display copyright with current year using gmdate('Y')
- Text domain: {theme_slug}
- wp_footer() must be BEFORE </body>

FORBIDDEN:
- Do NOT include <!DOCTYPE>, <html>, <head>, or wp_head() - that's header.php
- Do NOT duplicate </body> or </html> tags - use each exactly ONCE

Output ONLY the code."""


def get_functions_prompt(theme_name: str, theme_slug: str, requirements: Dict[str, Any]) -> str:
    """Get prompt for generating functions.php.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        requirements: Theme requirements dictionary

    Returns:
        Complete prompt for functions.php generation
    """
    woocommerce = requirements.get('woocommerce_support', False)

    return f"""Generate functions.php for WordPress theme "{theme_name}".

REQUIRED ELEMENTS:
1. Theme setup function hooked to 'after_setup_theme'
2. Widget registration function hooked to 'widgets_init'
3. Scripts/styles enqueue function hooked to 'wp_enqueue_scripts'

THEME SETUP MUST INCLUDE:
- load_theme_textdomain( '{theme_slug}' )
- add_theme_support( 'title-tag' )
- add_theme_support( 'post-thumbnails' )
- add_theme_support( 'html5', [...] )
- add_theme_support( 'custom-logo' )
- register_nav_menus() for 'primary' and 'footer'
{"- add_theme_support( 'woocommerce' )" if woocommerce else ""}

WIDGET AREAS TO REGISTER:
- sidebar-1 (main sidebar)
- footer-1, footer-2, footer-3 (footer columns)

ENQUEUE:
- Main stylesheet using get_stylesheet_uri()
- Navigation script from /js/navigation.js
- comment-reply script on singular posts if comments open

CRITICAL RULES:
- NEVER define WP_DEBUG, WP_DEBUG_LOG, or WP_DEBUG_DISPLAY
- NEVER use ini_set() or error_reporting()
- NEVER use eval(), exec(), or shell commands
- Use add_action() and add_filter() hooks properly
- All functions must have {theme_slug}_ prefix

Output ONLY PHP code starting with <?php
Do NOT include closing ?> tag (WordPress standard for functions.php)"""


def get_index_prompt(theme_name: str, theme_slug: str, requirements: Dict[str, Any]) -> str:
    """Get prompt for generating index.php.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        requirements: Theme requirements dictionary

    Returns:
        Complete prompt for index.php generation
    """
    return f"""Generate index.php for WordPress theme "{theme_name}".

REQUIRED STRUCTURE:
<?php
get_header();
?>
<main id="primary" class="site-main">
    <?php if ( have_posts() ) : ?>
        [header with page title]
        <?php while ( have_posts() ) : the_post(); ?>
            <?php get_template_part( 'template-parts/content', get_post_type() ); ?>
        <?php endwhile; ?>
        <?php the_posts_pagination(); ?>
    <?php else : ?>
        <?php get_template_part( 'template-parts/content', 'none' ); ?>
    <?php endif; ?>
</main>
<?php get_footer(); ?>

REQUIREMENTS:
- Call get_header() at start
- Call get_footer() at end
- Use have_posts() and the_post() in loop
- Use get_template_part() for content display
- Use the_posts_pagination() for navigation
- Include fallback for no posts (content-none)
- Text domain: {theme_slug}

FORBIDDEN:
- Do NOT include <!DOCTYPE>, <html>, <head>, </body>, </html>
- Do NOT use wp_head() or wp_footer() - only in header.php/footer.php
- Do NOT use hallucinated functions like post_loop() or render_post()

Output ONLY the code."""


def get_template_part_prompt(
    part_name: str,
    theme_slug: str,
    requirements: Dict[str, Any]
) -> str:
    """Get prompt for generating template part (content.php, content-none.php, etc).

    Args:
        part_name: Template part name (e.g., 'content', 'content-none')
        theme_slug: Theme text domain slug
        requirements: Theme requirements dictionary

    Returns:
        Complete prompt for template part generation
    """
    if part_name == 'content-none':
        return f"""Generate template-parts/content-none.php for when no content is found.

STRUCTURE:
<section class="no-results not-found">
    <header class="page-header">
        <h1><?php esc_html_e( 'Nothing Found', '{theme_slug}' ); ?></h1>
    </header>
    <div class="page-content">
        [Different messages based on context: is_home(), is_search(), etc.]
        [Include search form for search pages]
    </div>
</section>

REQUIREMENTS:
- Check context with is_home(), is_search()
- Provide helpful messages for users
- Include get_search_form() for search pages
- Use esc_html_e() for translatable strings
- Text domain: {theme_slug}

Output ONLY the code."""

    else:
        return f"""Generate template-parts/content.php for displaying post content.

STRUCTURE:
<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
    <header class="entry-header">
        <?php the_title(); ?>
        [post meta: date, author]
    </header>
    [post thumbnail if has_post_thumbnail()]
    <div class="entry-content">
        <?php the_content() or the_excerpt() based on context ?>
    </div>
    <footer class="entry-footer">
        [read more link or categories/tags]
    </footer>
</article>

REQUIREMENTS:
- Use the_ID(), post_class(), the_title(), the_content(), the_excerpt()
- Check is_singular() to decide full content vs excerpt
- Display post thumbnail with has_post_thumbnail() and the_post_thumbnail()
- Show post date with get_the_date()
- Use esc_html() for all output
- Text domain: {theme_slug}

Output ONLY the code."""


def get_style_css_prompt(theme_name: str, requirements: Dict[str, Any]) -> str:
    """Get prompt for generating CSS styles.

    Args:
        theme_name: Theme display name
        requirements: Theme requirements dictionary

    Returns:
        Complete prompt for CSS generation
    """
    primary_color = requirements.get('primary_color', '#2563eb')
    font_family = requirements.get('font_family', 'system-ui, -apple-system, sans-serif')

    return f"""Generate CSS styles for WordPress theme "{theme_name}".

The style.css header is already included. Generate ONLY the CSS rules.

PRIMARY COLOR: {primary_color}
FONT FAMILY: {font_family}

REQUIRED STYLES:
1. CSS Reset/normalization
2. Typography (body, headings, links)
3. Layout (.site, .site-header, .site-main, .site-footer)
4. Navigation (.main-navigation, .menu-toggle)
5. Content (.entry-content, .entry-header, .entry-footer)
6. Widgets (.widget, .widget-title)
7. Responsive design (mobile-first approach)

STRUCTURE:
/* CSS Reset */
*, *::before, *::after {{ box-sizing: border-box; }}

/* Typography */
body {{ font-family: {font_family}; }}

/* Layout */
.site {{ max-width: 1200px; margin: 0 auto; }}

/* Navigation */
.main-navigation {{ ... }}

/* Content */
.entry-content {{ ... }}

/* Responsive */
@media (max-width: 768px) {{ ... }}

REQUIREMENTS:
- Use CSS custom properties for colors
- Mobile-first responsive design
- Accessible color contrast (WCAG AA)
- Smooth transitions for interactive elements

Output ONLY CSS rules (no comments, no explanations)."""


# Mapping of template types to prompt generators
PROMPT_GENERATORS = {
    'header': get_header_prompt,
    'footer': get_footer_prompt,
    'functions': get_functions_prompt,
    'index': get_index_prompt,
    'style': get_style_css_prompt,
}


def get_prompt_for_template(
    template_type: str,
    theme_name: str,
    theme_slug: str,
    requirements: Dict[str, Any]
) -> str:
    """Get appropriate prompt for a template type.

    Args:
        template_type: Type of template (header, footer, index, etc.)
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        requirements: Theme requirements dictionary

    Returns:
        Complete prompt string including system prompt

    Raises:
        ValueError: If template_type is not recognized
    """
    generator = PROMPT_GENERATORS.get(template_type)

    if not generator:
        raise ValueError(f"Unknown template type: {template_type}")

    system_prompt = get_base_system_prompt()
    template_prompt = generator(theme_name, theme_slug, requirements)

    return f"{system_prompt}\n\n{template_prompt}"
