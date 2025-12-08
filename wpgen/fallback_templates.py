"""
Rich Fallback Templates for WPGen
Provides visually impressive fallback templates based on the pattern library
"""


def get_rich_fallback_front_page(theme_name: str) -> str:
    """
    Get a rich, modern fallback front-page.php template

    This template follows ecommerce best practices with:
    - Hero section
    - Featured products/posts grid
    - Features strip
    - CTA section

    Args:
        theme_name: Theme name for text domain

    Returns:
        Complete front-page.php code
    """
    theme_slug = theme_name.replace('-', '_')

    return f"""<?php
/**
 * Front Page Template
 * Modern ecommerce-style homepage with hero, products, features, and CTA
 *
 * @package {theme_name}
 */

get_header();
?>

<!-- Hero Section -->
<section class="hero-section">
    <div class="hero-overlay"></div>
    <div class="hero-content container">
        <h1 class="hero-title"><?php bloginfo( 'name' ); ?></h1>
        <p class="hero-subtitle"><?php bloginfo( 'description' ); ?></p>
        <div class="hero-cta">
            <a href="#featured" class="btn btn-primary btn-lg"><?php esc_html_e( 'Explore Collection', '{theme_name}' ); ?></a>
            <a href="<?php echo esc_url( home_url( '/about' ) ); ?>" class="btn btn-outline btn-lg"><?php esc_html_e( 'Learn More', '{theme_name}' ); ?></a>
        </div>
    </div>
</section>

<!-- Features Strip -->
<section class="features-section section bg-light">
    <div class="container">
        <div class="features-grid grid grid-3">
            <div class="feature-item">
                <div class="feature-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                </div>
                <h3 class="feature-title"><?php esc_html_e( 'Quality Products', '{theme_name}' ); ?></h3>
                <p class="feature-description"><?php esc_html_e( 'Carefully curated selection of premium items.', '{theme_name}' ); ?></p>
            </div>

            <div class="feature-item">
                <div class="feature-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                </div>
                <h3 class="feature-title"><?php esc_html_e( 'Fast Shipping', '{theme_name}' ); ?></h3>
                <p class="feature-description"><?php esc_html_e( 'Quick delivery to your doorstep.', '{theme_name}' ); ?></p>
            </div>

            <div class="feature-item">
                <div class="feature-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                        <polyline points="9 22 9 12 15 12 15 22"></polyline>
                    </svg>
                </div>
                <h3 class="feature-title"><?php esc_html_e( 'Easy Returns', '{theme_name}' ); ?></h3>
                <p class="feature-description"><?php esc_html_e( '30-day hassle-free return policy.', '{theme_name}' ); ?></p>
            </div>
        </div>
    </div>
</section>

<!-- Featured Products Grid -->
<section id="featured" class="products-section section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title"><?php esc_html_e( 'Featured Collection', '{theme_name}' ); ?></h2>
            <p class="section-subtitle"><?php esc_html_e( 'Discover our latest additions', '{theme_name}' ); ?></p>
        </div>

        <div class="products-grid grid grid-3">
            <?php
            $featured_query = new WP_Query( array(
                'posts_per_page' => 6,
                'post_status'    => 'publish',
                'orderby'        => 'date',
                'order'          => 'DESC',
            ) );

            if ( $featured_query->have_posts() ) :
                while ( $featured_query->have_posts() ) : $featured_query->the_post();
                    ?>
                    <article id="post-<?php the_ID(); ?>" <?php post_class( 'product-card' ); ?>>
                        <?php if ( has_post_thumbnail() ) : ?>
                            <div class="product-image">
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_post_thumbnail( 'large', array( 'class' => 'card-image' ) ); ?>
                                </a>
                                <span class="product-badge"><?php esc_html_e( 'New', '{theme_name}' ); ?></span>
                            </div>
                        <?php else : ?>
                            <div class="product-image product-image-placeholder">
                                <a href="<?php the_permalink(); ?>">
                                    <div class="placeholder-bg"></div>
                                </a>
                            </div>
                        <?php endif; ?>

                        <div class="product-content">
                            <h3 class="product-title">
                                <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                            </h3>

                            <div class="product-excerpt">
                                <?php echo wp_trim_words( get_the_excerpt(), 15, '...' ); ?>
                            </div>

                            <div class="product-meta">
                                <a href="<?php the_permalink(); ?>" class="btn btn-primary">
                                    <?php esc_html_e( 'View Details', '{theme_name}' ); ?>
                                </a>
                            </div>
                        </div>
                    </article>
                    <?php
                endwhile;
                wp_reset_postdata();
            else :
                // Fallback content when no posts exist
                for ( $i = 1; $i <= 6; $i++ ) :
                    ?>
                    <article class="product-card placeholder-card">
                        <div class="product-image product-image-placeholder">
                            <div class="placeholder-bg"></div>
                            <span class="product-badge"><?php esc_html_e( 'New', '{theme_name}' ); ?></span>
                        </div>
                        <div class="product-content">
                            <h3 class="product-title">
                                <a href="#"><?php printf( esc_html__( 'Product %d', '{theme_name}' ), $i ); ?></a>
                            </h3>
                            <div class="product-excerpt">
                                <?php esc_html_e( 'Discover this amazing product from our collection.', '{theme_name}' ); ?>
                            </div>
                            <div class="product-meta">
                                <a href="#" class="btn btn-primary"><?php esc_html_e( 'View Details', '{theme_name}' ); ?></a>
                            </div>
                        </div>
                    </article>
                    <?php
                endfor;
            endif;
            ?>
        </div>

        <div class="section-footer">
            <a href="<?php echo esc_url( home_url( '/blog' ) ); ?>" class="btn btn-secondary btn-lg">
                <?php esc_html_e( 'View All Products', '{theme_name}' ); ?>
            </a>
        </div>
    </div>
</section>

<!-- Content Section -->
<section class="content-section section">
    <div class="container">
        <?php if ( have_posts() ) : ?>
            <?php while ( have_posts() ) : the_post(); ?>
                <article id="post-<?php the_ID(); ?>" <?php post_class( 'content-article' ); ?>>
                    <h2 class="entry-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                    <div class="entry-content">
                        <?php the_content(); ?>
                    </div>
                </article>
            <?php endwhile; ?>
        <?php else : ?>
            <article class="no-content">
                <h2><?php esc_html_e( 'Welcome!', '{theme_name}' ); ?></h2>
                <p><?php esc_html_e( 'Add a page or post to see your content here.', '{theme_name}' ); ?></p>
            </article>
        <?php endif; ?>
    </div>
</section>

<!-- CTA Section -->
<section class="cta-section section bg-primary">
    <div class="container">
        <div class="cta-content">
            <h2 class="cta-title"><?php esc_html_e( 'Ready to Get Started?', '{theme_name}' ); ?></h2>
            <p class="cta-subtitle"><?php esc_html_e( 'Join thousands of satisfied customers today.', '{theme_name}' ); ?></p>
            <a href="<?php echo esc_url( home_url( '/contact' ) ); ?>" class="btn btn-lg btn-secondary">
                <?php esc_html_e( 'Get in Touch', '{theme_name}' ); ?>
            </a>
        </div>
    </div>
</section>

<?php
get_footer();
"""


def get_rich_fallback_index(theme_name: str) -> str:
    """
    Get a rich fallback index.php template with card grid

    Args:
        theme_name: Theme name for text domain

    Returns:
        Complete index.php code
    """
    return f"""<?php
/**
 * Main Index Template
 * Modern card grid layout for blog posts
 *
 * @package {theme_name}
 */

get_header();
?>

<div class="content-area section">
    <div class="container">

        <?php if ( have_posts() ) : ?>

            <header class="page-header">
                <h1 class="page-title">
                    <?php
                    if ( is_home() && ! is_front_page() ) :
                        single_post_title();
                    else :
                        esc_html_e( 'Blog', '{theme_name}' );
                    endif;
                    ?>
                </h1>
            </header>

            <div class="posts-grid grid grid-3">
                <?php
                while ( have_posts() ) :
                    the_post();
                    ?>
                    <article id="post-<?php the_ID(); ?>" <?php post_class( 'post-card' ); ?>>

                        <?php if ( has_post_thumbnail() ) : ?>
                            <div class="post-thumbnail">
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_post_thumbnail( 'large' ); ?>
                                </a>
                            </div>
                        <?php endif; ?>

                        <div class="post-content">
                            <div class="post-meta">
                                <time class="post-date" datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>">
                                    <?php echo esc_html( get_the_date() ); ?>
                                </time>
                                <span class="meta-separator">•</span>
                                <span class="post-author">
                                    <?php echo esc_html( get_the_author() ); ?>
                                </span>
                            </div>

                            <h2 class="post-title">
                                <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                            </h2>

                            <div class="post-excerpt">
                                <?php the_excerpt(); ?>
                            </div>

                            <a href="<?php the_permalink(); ?>" class="read-more btn btn-outline">
                                <?php esc_html_e( 'Read More', '{theme_name}' ); ?>
                            </a>
                        </div>
                    </article>
                    <?php
                endwhile;
                ?>
            </div>

            <div class="pagination">
                <?php
                the_posts_pagination( array(
                    'mid_size'  => 2,
                    'prev_text' => esc_html__( '← Previous', '{theme_name}' ),
                    'next_text' => esc_html__( 'Next →', '{theme_name}' ),
                ) );
                ?>
            </div>

        <?php else : ?>

            <div class="no-content">
                <h2><?php esc_html_e( 'Nothing Found', '{theme_name}' ); ?></h2>
                <p><?php esc_html_e( 'It seems we can\'t find what you\'re looking for. Perhaps searching can help.', '{theme_name}' ); ?></p>
                <?php get_search_form(); ?>
            </div>

        <?php endif; ?>

    </div>
</div>

<?php
get_footer();
"""


def get_rich_fallback_archive(theme_name: str) -> str:
    """
    Get a rich fallback archive.php template

    Args:
        theme_name: Theme name for text domain

    Returns:
        Complete archive.php code
    """
    return f"""<?php
/**
 * Archive Template
 * Displays category, tag, author, and date archives
 *
 * @package {theme_name}
 */

get_header();
?>

<div class="archive-page section">
    <div class="container">

        <header class="archive-header">
            <?php
            the_archive_title( '<h1 class="archive-title">', '</h1>' );
            the_archive_description( '<div class="archive-description">', '</div>' );
            ?>
        </header>

        <?php if ( have_posts() ) : ?>

            <div class="archive-grid grid grid-3">
                <?php
                while ( have_posts() ) :
                    the_post();
                    ?>
                    <article id="post-<?php the_ID(); ?>" <?php post_class( 'post-card' ); ?>>

                        <?php if ( has_post_thumbnail() ) : ?>
                            <div class="post-thumbnail">
                                <a href="<?php the_permalink(); ?>">
                                    <?php the_post_thumbnail( 'medium' ); ?>
                                </a>
                            </div>
                        <?php endif; ?>

                        <div class="post-content">
                            <div class="post-meta">
                                <time datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>">
                                    <?php echo esc_html( get_the_date() ); ?>
                                </time>
                            </div>

                            <h2 class="post-title">
                                <a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
                            </h2>

                            <div class="post-excerpt">
                                <?php the_excerpt(); ?>
                            </div>

                            <a href="<?php the_permalink(); ?>" class="read-more">
                                <?php esc_html_e( 'Continue Reading', '{theme_name}' ); ?> →
                            </a>
                        </div>
                    </article>
                    <?php
                endwhile;
                ?>
            </div>

            <div class="pagination">
                <?php
                the_posts_pagination( array(
                    'mid_size'  => 2,
                    'prev_text' => esc_html__( '← Older', '{theme_name}' ),
                    'next_text' => esc_html__( 'Newer →', '{theme_name}' ),
                ) );
                ?>
            </div>

        <?php else : ?>

            <div class="no-content">
                <h2><?php esc_html_e( 'No Posts Found', '{theme_name}' ); ?></h2>
                <p><?php esc_html_e( 'This archive doesn\'t have any posts yet.', '{theme_name}' ); ?></p>
                <a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="btn btn-primary">
                    <?php esc_html_e( 'Back to Home', '{theme_name}' ); ?>
                </a>
            </div>

        <?php endif; ?>

    </div>
</div>

<?php
get_footer();
"""
