"""Safe Fallback Templates for WPGen.

This module provides comprehensive, tested fallback templates that are
guaranteed to work with WordPress. These templates are used when:
- LLM generation fails
- Generated code fails validation
- Generated code violates template contracts

All templates in this module are:
- Fully WordPress-compliant
- Syntactically valid (tested)
- Structurally complete (all tags balanced)
- Free from hallucinations
- Production-ready

NO PLACEHOLDERS - NO TODOs - ONLY WORKING CODE.
"""


def get_safe_header(theme_name: str, theme_slug: str) -> str:
    """Get safe, tested header.php template.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug

    Returns:
        Complete header.php content
    """
    return f'''<?php
/**
 * Header Template
 *
 * @package {theme_name}
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

    <header id="masthead" class="site-header">
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
                <span class="menu-icon" aria-hidden="true"></span>
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
    </header>
'''


def get_safe_footer(theme_name: str, theme_slug: str) -> str:
    """Get safe, tested footer.php template.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug

    Returns:
        Complete footer.php content
    """
    return f'''<?php
/**
 * Footer Template
 *
 * @package {theme_name}
 */
?>

    <footer id="colophon" class="site-footer">
        <?php if ( is_active_sidebar( 'footer-1' ) || is_active_sidebar( 'footer-2' ) || is_active_sidebar( 'footer-3' ) ) : ?>
            <div class="footer-widgets">
                <div class="footer-widgets-inner">
                    <?php if ( is_active_sidebar( 'footer-1' ) ) : ?>
                        <div class="footer-widget-area footer-widget-1">
                            <?php dynamic_sidebar( 'footer-1' ); ?>
                        </div>
                    <?php endif; ?>

                    <?php if ( is_active_sidebar( 'footer-2' ) ) : ?>
                        <div class="footer-widget-area footer-widget-2">
                            <?php dynamic_sidebar( 'footer-2' ); ?>
                        </div>
                    <?php endif; ?>

                    <?php if ( is_active_sidebar( 'footer-3' ) ) : ?>
                        <div class="footer-widget-area footer-widget-3">
                            <?php dynamic_sidebar( 'footer-3' ); ?>
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        <?php endif; ?>

        <div class="site-info">
            <div class="site-info-inner">
                <p class="copyright">
                    <?php
                    printf(
                        esc_html__( '&copy; %1$s %2$s. All rights reserved.', '{theme_slug}' ),
                        esc_html( gmdate( 'Y' ) ),
                        esc_html( get_bloginfo( 'name' ) )
                    );
                    ?>
                </p>
                <p class="powered-by">
                    <?php
                    printf(
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


def get_safe_index(theme_name: str, theme_slug: str) -> str:
    """Get safe, tested index.php template.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug

    Returns:
        Complete index.php content
    """
    return f'''<?php
/**
 * Main Index Template
 *
 * @package {theme_name}
 */

get_header();
?>

<main id="primary" class="site-main">
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

<?php
get_footer();
'''


def get_safe_single(theme_name: str, theme_slug: str) -> str:
    """Get safe, tested single.php template.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug

    Returns:
        Complete single.php content
    """
    return f'''<?php
/**
 * Single Post Template
 *
 * @package {theme_name}
 */

get_header();
?>

<main id="primary" class="site-main">
    <div class="content-inner">

        <?php
        while ( have_posts() ) :
            the_post();

            get_template_part( 'template-parts/content', 'single' );

            the_post_navigation(
                array(
                    'prev_text' => '<span class="nav-subtitle">' . esc_html__( 'Previous:', '{theme_slug}' ) . '</span> <span class="nav-title">%title</span>',
                    'next_text' => '<span class="nav-subtitle">' . esc_html__( 'Next:', '{theme_slug}' ) . '</span> <span class="nav-title">%title</span>',
                )
            );

            if ( comments_open() || get_comments_number() ) :
                comments_template();
            endif;

        endwhile;
        ?>

    </div>
</main>

<?php
get_footer();
'''


def get_safe_page(theme_name: str, theme_slug: str) -> str:
    """Get safe, tested page.php template.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug

    Returns:
        Complete page.php content
    """
    return f'''<?php
/**
 * Page Template
 *
 * @package {theme_name}
 */

get_header();
?>

<main id="primary" class="site-main">
    <div class="content-inner">

        <?php
        while ( have_posts() ) :
            the_post();
            ?>

            <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                <header class="entry-header">
                    <?php the_title( '<h1 class="entry-title">', '</h1>' ); ?>
                </header>

                <?php if ( has_post_thumbnail() ) : ?>
                    <div class="post-thumbnail">
                        <?php the_post_thumbnail( 'large' ); ?>
                    </div>
                <?php endif; ?>

                <div class="entry-content">
                    <?php the_content(); ?>
                </div>
            </article>

            <?php
            if ( comments_open() || get_comments_number() ) :
                comments_template();
            endif;

        endwhile;
        ?>

    </div>
</main>

<?php
get_footer();
'''


def get_safe_functions(theme_name: str, theme_slug: str, woocommerce: bool = False) -> str:
    """Get safe, tested functions.php template.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        woocommerce: Whether to include WooCommerce support

    Returns:
        Complete functions.php content
    """
    woo_support = ""
    if woocommerce:
        woo_support = """
    // WooCommerce support
    add_theme_support( 'woocommerce' );
    add_theme_support( 'wc-product-gallery-zoom' );
    add_theme_support( 'wc-product-gallery-lightbox' );
    add_theme_support( 'wc-product-gallery-slider' );"""

    return f'''<?php
/**
 * Theme Functions
 *
 * @package {theme_name}
 */

if ( ! defined( 'ABSPATH' ) ) {{
    exit;
}}

/**
 * Theme setup.
 */
function {theme_slug}_setup() {{
    load_theme_textdomain( '{theme_slug}', get_template_directory() . '/languages' );

    add_theme_support( 'automatic-feed-links' );
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );

    set_post_thumbnail_size( 1200, 9999 );

    register_nav_menus(
        array(
            'primary' => esc_html__( 'Primary Menu', '{theme_slug}' ),
            'footer'  => esc_html__( 'Footer Menu', '{theme_slug}' ),
        )
    );

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

    add_theme_support( 'customize-selective-refresh-widgets' );

    add_theme_support(
        'custom-logo',
        array(
            'height'      => 100,
            'width'       => 400,
            'flex-width'  => true,
            'flex-height' => true,
        )
    );

    add_theme_support( 'responsive-embeds' );
    add_theme_support( 'editor-styles' );
    add_theme_support( 'wp-block-styles' );
    add_theme_support( 'align-wide' );{woo_support}
}}
add_action( 'after_setup_theme', '{theme_slug}_setup' );

/**
 * Set content width.
 */
function {theme_slug}_content_width() {{
    $GLOBALS['content_width'] = apply_filters( '{theme_slug}_content_width', 1200 );
}}
add_action( 'after_setup_theme', '{theme_slug}_content_width', 0 );

/**
 * Register widget areas.
 */
function {theme_slug}_widgets_init() {{
    register_sidebar(
        array(
            'name'          => esc_html__( 'Sidebar', '{theme_slug}' ),
            'id'            => 'sidebar-1',
            'description'   => esc_html__( 'Add widgets here.', '{theme_slug}' ),
            'before_widget' => '<section id="%1$s" class="widget %2$s">',
            'after_widget'  => '</section>',
            'before_title'  => '<h2 class="widget-title">',
            'after_title'   => '</h2>',
        )
    );

    register_sidebar(
        array(
            'name'          => esc_html__( 'Footer 1', '{theme_slug}' ),
            'id'            => 'footer-1',
            'description'   => esc_html__( 'Footer column 1.', '{theme_slug}' ),
            'before_widget' => '<section id="%1$s" class="widget %2$s">',
            'after_widget'  => '</section>',
            'before_title'  => '<h2 class="widget-title">',
            'after_title'   => '</h2>',
        )
    );

    register_sidebar(
        array(
            'name'          => esc_html__( 'Footer 2', '{theme_slug}' ),
            'id'            => 'footer-2',
            'description'   => esc_html__( 'Footer column 2.', '{theme_slug}' ),
            'before_widget' => '<section id="%1$s" class="widget %2$s">',
            'after_widget'  => '</section>',
            'before_title'  => '<h2 class="widget-title">',
            'after_title'   => '</h2>',
        )
    );

    register_sidebar(
        array(
            'name'          => esc_html__( 'Footer 3', '{theme_slug}' ),
            'id'            => 'footer-3',
            'description'   => esc_html__( 'Footer column 3.', '{theme_slug}' ),
            'before_widget' => '<section id="%1$s" class="widget %2$s">',
            'after_widget'  => '</section>',
            'before_title'  => '<h2 class="widget-title">',
            'after_title'   => '</h2>',
        )
    );
}}
add_action( 'widgets_init', '{theme_slug}_widgets_init' );

/**
 * Enqueue scripts and styles.
 */
function {theme_slug}_scripts() {{
    wp_enqueue_style(
        '{theme_slug}-style',
        get_stylesheet_uri(),
        array(),
        wp_get_theme()->get( 'Version' )
    );

    if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {{
        wp_enqueue_script( 'comment-reply' );
    }}
}}
add_action( 'wp_enqueue_scripts', '{theme_slug}_scripts' );
'''


def get_safe_content_template(theme_slug: str) -> str:
    """Get safe template-parts/content.php.

    Args:
        theme_slug: Theme text domain slug

    Returns:
        Complete content.php template
    """
    return f'''<?php
/**
 * Template part for displaying posts
 *
 * @package wpgen
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

    <?php if ( ! is_singular() ) : ?>
        <footer class="entry-footer">
            <a href="<?php the_permalink(); ?>" class="read-more">
                <?php esc_html_e( 'Continue reading', '{theme_slug}' ); ?>
            </a>
        </footer>
    <?php endif; ?>
</article>
'''


def get_safe_content_none_template(theme_slug: str) -> str:
    """Get safe template-parts/content-none.php.

    Args:
        theme_slug: Theme text domain slug

    Returns:
        Complete content-none.php template
    """
    return f'''<?php
/**
 * Template part for displaying a message when no content is found
 *
 * @package wpgen
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


def get_all_safe_templates(theme_name: str, theme_slug: str, woocommerce: bool = False) -> dict:
    """Get all safe fallback templates in a single dictionary.

    Args:
        theme_name: Theme display name
        theme_slug: Theme text domain slug
        woocommerce: Whether to include WooCommerce support

    Returns:
        Dictionary mapping filenames to template content
    """
    return {
        'header.php': get_safe_header(theme_name, theme_slug),
        'footer.php': get_safe_footer(theme_name, theme_slug),
        'index.php': get_safe_index(theme_name, theme_slug),
        'single.php': get_safe_single(theme_name, theme_slug),
        'page.php': get_safe_page(theme_name, theme_slug),
        'functions.php': get_safe_functions(theme_name, theme_slug, woocommerce),
        'template-parts/content.php': get_safe_content_template(theme_slug),
        'template-parts/content-none.php': get_safe_content_none_template(theme_slug),
    }
