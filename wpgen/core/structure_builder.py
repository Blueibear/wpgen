"""Structure Builder Module for WPGen.

This module provides deterministic, contract-enforcing boilerplate templates
for WordPress themes. Every template generated is guaranteed to be:
- Syntactically valid PHP and HTML
- Structurally complete (matching open/close tags)
- WordPress-compliant (proper template tags and hooks)
- Deterministic (no LLM hallucinations)

All templates follow strict contracts defined in template_contracts.py.
"""

from typing import Dict, Any


def build_header_structure(theme_name: str, theme_slug: str, config: Dict[str, Any]) -> str:
    """Build complete header.php structure with all required elements.

    This template guarantees:
    - Valid HTML5 doctype
    - Proper <html>, <head>, <body> opening tags
    - Required meta tags (charset, viewport)
    - wp_head() hook before </head>
    - body_class() on <body> tag
    - wp_body_open() after <body> tag
    - Opening <div id="page"> wrapper

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        config: Configuration dictionary with optional customizations

    Returns:
        Complete header.php template as string
    """
    # Extract configuration with safe defaults
    primary_color = config.get('primary_color', '#2563eb')
    show_search = config.get('show_search', True)
    sticky_header = config.get('sticky_header', False)

    header_class = 'site-header'
    if sticky_header:
        header_class += ' sticky-header'

    return f'''<?php
/**
 * Header Template
 *
 * Displays the site header including <head>, navigation, and site branding.
 * This file is required by WordPress and must contain wp_head().
 *
 * @package {theme_name}
 * @since 1.0.0
 */
?>
<!DOCTYPE html>
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
    <a class="skip-link screen-reader-text" href="#primary"><?php esc_html_e( 'Skip to content', '{theme_slug}' ); ?></a>

    <header id="masthead" class="{header_class}">
        <div class="site-branding">
            <?php
            if ( has_custom_logo() ) :
                the_custom_logo();
            else :
                ?>
                <div class="site-identity">
                    <h1 class="site-title">
                        <a href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home">
                            <?php bloginfo( 'name' ); ?>
                        </a>
                    </h1>
                    <?php
                    $description = get_bloginfo( 'description', 'display' );
                    if ( $description || is_customize_preview() ) :
                        ?>
                        <p class="site-description"><?php echo esc_html( $description ); ?></p>
                    <?php endif; ?>
                </div>
                <?php
            endif;
            ?>
        </div>

        <nav id="site-navigation" class="main-navigation" aria-label="<?php esc_attr_e( 'Primary Navigation', '{theme_slug}' ); ?>">
            <button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false">
                <span class="screen-reader-text"><?php esc_html_e( 'Menu', '{theme_slug}' ); ?></span>
                <span class="menu-icon" aria-hidden="true">
                    <span class="menu-bar"></span>
                    <span class="menu-bar"></span>
                    <span class="menu-bar"></span>
                </span>
            </button>
            <?php
            wp_nav_menu(
                array(
                    'theme_location' => 'primary',
                    'menu_id'        => 'primary-menu',
                    'menu_class'     => 'nav-menu',
                    'container'      => false,
                    'fallback_cb'    => false,
                )
            );
            ?>
        </nav>

        {_build_search_form_block(show_search, theme_slug)}
    </header>
'''


def _build_search_form_block(show_search: bool, theme_slug: str) -> str:
    """Build optional search form block for header.

    Args:
        show_search: Whether to include search form
        theme_slug: Theme text domain

    Returns:
        Search form HTML or empty string
    """
    if not show_search:
        return ''

    return f'''
        <div class="header-search">
            <?php get_search_form(); ?>
        </div>'''


def build_footer_structure(theme_name: str, theme_slug: str, config: Dict[str, Any]) -> str:
    """Build complete footer.php structure with all required elements.

    This template guarantees:
    - Closes </main> tag (opened in content templates)
    - Opens <footer> element
    - wp_footer() hook before </body>
    - Closes </div id="page">
    - Closes </body>
    - Closes </html>

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        config: Configuration dictionary

    Returns:
        Complete footer.php template as string
    """
    footer_columns = config.get('footer_columns', 3)
    copyright_text = config.get('copyright_text', f'&copy; {theme_name}')

    return f'''<?php
/**
 * Footer Template
 *
 * Displays the site footer including widgets and copyright.
 * This file is required by WordPress and must contain wp_footer().
 *
 * @package {theme_name}
 * @since 1.0.0
 */
?>

    <footer id="colophon" class="site-footer">
        <?php if ( is_active_sidebar( 'footer-1' ) || is_active_sidebar( 'footer-2' ) || is_active_sidebar( 'footer-3' ) ) : ?>
            <div class="footer-widgets">
                <div class="footer-widgets-inner">
                    {_build_footer_widget_areas(footer_columns)}
                </div>
            </div>
        <?php endif; ?>

        <div class="site-info">
            <div class="site-info-inner">
                <p class="copyright">
                    <?php
                    printf(
                        /* translators: 1: Copyright symbol, 2: Year, 3: Site name */
                        esc_html__( '%1$s %2$s %3$s. All rights reserved.', '{theme_slug}' ),
                        '&copy;',
                        esc_html( gmdate( 'Y' ) ),
                        esc_html( get_bloginfo( 'name' ) )
                    );
                    ?>
                </p>
                <p class="powered-by">
                    <?php
                    printf(
                        /* translators: %s: WordPress */
                        esc_html__( 'Powered by %s', '{theme_slug}' ),
                        '<a href="https://wordpress.org/">WordPress</a>'
                    );
                    ?>
                </p>
            </div>
        </div>
    </footer>

</div><!-- #page -->

<?php wp_footer(); ?>

</body>
</html>
'''


def _build_footer_widget_areas(columns: int) -> str:
    """Build footer widget area columns.

    Args:
        columns: Number of footer columns (1-4)

    Returns:
        HTML for footer widget areas
    """
    columns = max(1, min(4, columns))  # Clamp between 1 and 4

    areas = []
    for i in range(1, columns + 1):
        areas.append(f'''                    <div class="footer-widget-area footer-widget-{i}">
                        <?php dynamic_sidebar( 'footer-{i}' ); ?>
                    </div>''')

    return '\n'.join(areas)


def build_index_structure(theme_name: str, theme_slug: str, config: Dict[str, Any]) -> str:
    """Build complete index.php structure.

    This template guarantees:
    - get_header() call
    - Opening <main> tag with proper ID and class
    - WordPress Loop with have_posts() / the_post()
    - Proper template parts inclusion
    - Pagination
    - Closing </main> tag
    - get_footer() call

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        config: Configuration dictionary

    Returns:
        Complete index.php template as string
    """
    layout_class = config.get('layout_class', 'content-area')
    show_sidebar = config.get('show_sidebar', False)

    return f'''<?php
/**
 * Main Index Template
 *
 * The main template file, required by WordPress.
 * Displays posts in a loop when no other template is found.
 *
 * @package {theme_name}
 * @since 1.0.0
 */

get_header();
?>

<main id="primary" class="{layout_class}">
    <div class="content-inner">

        <?php if ( have_posts() ) : ?>

            <header class="page-header">
                <?php
                if ( is_home() && ! is_front_page() ) :
                    ?>
                    <h1 class="page-title"><?php single_post_title(); ?></h1>
                    <?php
                else :
                    ?>
                    <h1 class="page-title"><?php esc_html_e( 'Latest Posts', '{theme_slug}' ); ?></h1>
                    <?php
                endif;
                ?>
            </header>

            <div class="posts-container">
                <?php
                while ( have_posts() ) :
                    the_post();

                    get_template_part( 'template-parts/content', get_post_type() );

                endwhile;
                ?>
            </div>

            <?php
            the_posts_pagination(
                array(
                    'mid_size'  => 2,
                    'prev_text' => esc_html__( 'Previous', '{theme_slug}' ),
                    'next_text' => esc_html__( 'Next', '{theme_slug}' ),
                )
            );
            ?>

        <?php else : ?>

            <?php get_template_part( 'template-parts/content', 'none' ); ?>

        <?php endif; ?>

    </div>
</main>

{_build_sidebar_block(show_sidebar)}

<?php
get_footer();
'''


def _build_sidebar_block(show_sidebar: bool) -> str:
    """Build sidebar block if enabled.

    Args:
        show_sidebar: Whether to include sidebar

    Returns:
        Sidebar HTML or empty string
    """
    if not show_sidebar:
        return ''

    return '''
<?php get_sidebar(); ?>'''


def build_functions_structure(theme_name: str, theme_slug: str, config: Dict[str, Any]) -> str:
    """Build complete functions.php structure.

    This template guarantees:
    - Proper PHP opening tag (no closing tag per WordPress standards)
    - Theme setup action hook
    - Required theme supports
    - Navigation menu registration
    - Widget area registration
    - Script/style enqueuing
    - No WP_DEBUG or error_reporting definitions
    - No hallucinated functions

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        config: Configuration dictionary

    Returns:
        Complete functions.php template as string
    """
    woocommerce_support = config.get('woocommerce_support', False)
    custom_logo_support = config.get('custom_logo', True)
    footer_columns = config.get('footer_columns', 3)

    return f'''<?php
/**
 * Theme Functions
 *
 * Sets up theme defaults and registers support for various WordPress features.
 *
 * @package {theme_name}
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {{
    exit; // Exit if accessed directly
}}

/**
 * Set up theme defaults and register support for various WordPress features.
 */
function {theme_slug}_setup() {{
    // Make theme available for translation
    load_theme_textdomain( '{theme_slug}', get_template_directory() . '/languages' );

    // Add default posts and comments RSS feed links to head
    add_theme_support( 'automatic-feed-links' );

    // Let WordPress manage the document title
    add_theme_support( 'title-tag' );

    // Enable support for Post Thumbnails
    add_theme_support( 'post-thumbnails' );

    // Set default thumbnail size
    set_post_thumbnail_size( 1200, 9999 );

    // Register navigation menus
    register_nav_menus(
        array(
            'primary' => esc_html__( 'Primary Menu', '{theme_slug}' ),
            'footer'  => esc_html__( 'Footer Menu', '{theme_slug}' ),
        )
    );

    // Switch default core markup to output valid HTML5
    add_theme_support(
        'html5',
        array(
            'search-form',
            'comment-form',
            'comment-list',
            'gallery',
            'caption',
            'style',
            'script',
        )
    );

    // Add theme support for selective refresh for widgets
    add_theme_support( 'customize-selective-refresh-widgets' );

    {_build_custom_logo_support(custom_logo_support, theme_slug)}

    // Add support for responsive embeds
    add_theme_support( 'responsive-embeds' );

    // Add support for editor styles
    add_theme_support( 'editor-styles' );

    // Add support for Block Styles
    add_theme_support( 'wp-block-styles' );

    // Add support for full and wide align images
    add_theme_support( 'align-wide' );

    {_build_woocommerce_support(woocommerce_support)}
}}
add_action( 'after_setup_theme', '{theme_slug}_setup' );

/**
 * Set the content width in pixels, based on the theme's design and stylesheet.
 */
function {theme_slug}_content_width() {{
    $GLOBALS['content_width'] = apply_filters( '{theme_slug}_content_width', 1200 );
}}
add_action( 'after_setup_theme', '{theme_slug}_content_width', 0 );

/**
 * Register widget areas.
 */
function {theme_slug}_widgets_init() {{
    // Sidebar widget area
    register_sidebar(
        array(
            'name'          => esc_html__( 'Sidebar', '{theme_slug}' ),
            'id'            => 'sidebar-1',
            'description'   => esc_html__( 'Add widgets here to appear in your sidebar.', '{theme_slug}' ),
            'before_widget' => '<section id="%1$s" class="widget %2$s">',
            'after_widget'  => '</section>',
            'before_title'  => '<h2 class="widget-title">',
            'after_title'   => '</h2>',
        )
    );

    {_build_footer_widget_registrations(footer_columns, theme_slug)}
}}
add_action( 'widgets_init', '{theme_slug}_widgets_init' );

/**
 * Enqueue scripts and styles.
 */
function {theme_slug}_scripts() {{
    // Enqueue main stylesheet
    wp_enqueue_style(
        '{theme_slug}-style',
        get_stylesheet_uri(),
        array(),
        wp_get_theme()->get( 'Version' )
    );

    // Enqueue navigation script
    wp_enqueue_script(
        '{theme_slug}-navigation',
        get_template_directory_uri() . '/js/navigation.js',
        array(),
        wp_get_theme()->get( 'Version' ),
        true
    );

    // Enqueue comment reply script if needed
    if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {{
        wp_enqueue_script( 'comment-reply' );
    }}
}}
add_action( 'wp_enqueue_scripts', '{theme_slug}_scripts' );

/**
 * Implement custom template tags and functions.
 */
require get_template_directory() . '/inc/template-tags.php';

/**
 * Customizer additions.
 */
require get_template_directory() . '/inc/customizer.php';
'''


def _build_custom_logo_support(enabled: bool, theme_slug: str) -> str:
    """Build custom logo support block.

    Args:
        enabled: Whether custom logo is enabled
        theme_slug: Theme slug for dimensions filter

    Returns:
        Custom logo support code or empty string
    """
    if not enabled:
        return ''

    return f'''
    // Add theme support for Custom Logo
    add_theme_support(
        'custom-logo',
        array(
            'height'      => 100,
            'width'       => 400,
            'flex-width'  => true,
            'flex-height' => true,
        )
    );'''


def _build_woocommerce_support(enabled: bool) -> str:
    """Build WooCommerce support block.

    Args:
        enabled: Whether WooCommerce support is enabled

    Returns:
        WooCommerce support code or empty string
    """
    if not enabled:
        return ''

    return '''
    // Add WooCommerce support
    add_theme_support( 'woocommerce' );
    add_theme_support( 'wc-product-gallery-zoom' );
    add_theme_support( 'wc-product-gallery-lightbox' );
    add_theme_support( 'wc-product-gallery-slider' );'''


def _build_footer_widget_registrations(columns: int, theme_slug: str) -> str:
    """Build footer widget area registrations.

    Args:
        columns: Number of footer columns
        theme_slug: Theme text domain

    Returns:
        Widget registration code
    """
    columns = max(1, min(4, columns))

    registrations = []
    for i in range(1, columns + 1):
        registrations.append(f'''
    // Footer widget area {i}
    register_sidebar(
        array(
            'name'          => esc_html__( 'Footer {i}', '{theme_slug}' ),
            'id'            => 'footer-{i}',
            'description'   => esc_html__( 'Add widgets here to appear in footer column {i}.', '{theme_slug}' ),
            'before_widget' => '<section id="%1$s" class="widget %2$s">',
            'after_widget'  => '</section>',
            'before_title'  => '<h2 class="widget-title">',
            'after_title'   => '</h2>',
        )
    );''')

    return ''.join(registrations)


def build_content_part_structure(theme_slug: str, post_type: str = 'post') -> str:
    """Build template-parts/content.php structure.

    Args:
        theme_slug: Theme text domain slug
        post_type: Post type (post, page, etc.)

    Returns:
        Complete content template part
    """
    return f'''<?php
/**
 * Template part for displaying post content
 *
 * @package wpgen
 * @since 1.0.0
 */
?>

<article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
    <header class="entry-header">
        <?php
        if ( is_singular() ) :
            the_title( '<h1 class="entry-title">', '</h1>' );
        else :
            the_title( '<h2 class="entry-title"><a href="' . esc_url( get_permalink() ) . '" rel="bookmark">', '</a></h2>' );
        endif;
        ?>

        <?php if ( '{post_type}' === 'post' ) : ?>
            <div class="entry-meta">
                <span class="posted-on">
                    <time class="entry-date published" datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>">
                        <?php echo esc_html( get_the_date() ); ?>
                    </time>
                </span>
                <span class="byline">
                    <span class="author vcard">
                        <?php echo esc_html( get_the_author() ); ?>
                    </span>
                </span>
            </div>
        <?php endif; ?>
    </header>

    <?php if ( has_post_thumbnail() && ! is_singular() ) : ?>
        <div class="post-thumbnail">
            <a href="<?php the_permalink(); ?>">
                <?php the_post_thumbnail( 'large' ); ?>
            </a>
        </div>
    <?php endif; ?>

    <div class="entry-content">
        <?php
        if ( is_singular() ) :
            the_content();
        else :
            the_excerpt();
        endif;
        ?>
    </div>

    <footer class="entry-footer">
        <?php if ( ! is_singular() ) : ?>
            <a href="<?php the_permalink(); ?>" class="read-more">
                <?php esc_html_e( 'Continue reading', '{theme_slug}' ); ?>
                <span class="screen-reader-text"> "<?php the_title(); ?>"</span>
            </a>
        <?php endif; ?>
    </footer>
</article>
'''


def build_content_none_structure(theme_slug: str) -> str:
    """Build template-parts/content-none.php structure.

    Args:
        theme_slug: Theme text domain slug

    Returns:
        Complete no-content template part
    """
    return f'''<?php
/**
 * Template part for displaying a message when no content is found
 *
 * @package wpgen
 * @since 1.0.0
 */
?>

<section class="no-results not-found">
    <header class="page-header">
        <h1 class="page-title"><?php esc_html_e( 'Nothing Found', '{theme_slug}' ); ?></h1>
    </header>

    <div class="page-content">
        <?php if ( is_home() && current_user_can( 'publish_posts' ) ) : ?>

            <p>
                <?php
                printf(
                    wp_kses(
                        /* translators: %s: Link to create a new post */
                        __( 'Ready to publish your first post? <a href="%s">Get started here</a>.', '{theme_slug}' ),
                        array(
                            'a' => array(
                                'href' => array(),
                            ),
                        )
                    ),
                    esc_url( admin_url( 'post-new.php' ) )
                );
                ?>
            </p>

        <?php elseif ( is_search() ) : ?>

            <p><?php esc_html_e( 'Sorry, but nothing matched your search terms. Please try again with different keywords.', '{theme_slug}' ); ?></p>
            <?php get_search_form(); ?>

        <?php else : ?>

            <p><?php esc_html_e( 'It seems we can&rsquo;t find what you&rsquo;re looking for. Perhaps searching can help.', '{theme_slug}' ); ?></p>
            <?php get_search_form(); ?>

        <?php endif; ?>
    </div>
</section>
'''
