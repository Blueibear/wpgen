"""Generate an absolute minimal WordPress theme that is guaranteed to work.

This is a last-resort tool to create a theme with ZERO dependencies,
ZERO external files, and ZERO advanced features. Just the bare minimum
required for WordPress to activate it.
"""

from pathlib import Path


def create_minimal_theme(output_dir="output"):
    """Create a minimal WordPress theme."""

    theme_name = "wpgen-minimal-safe"
    theme_dir = Path(output_dir) / theme_name
    theme_dir.mkdir(parents=True, exist_ok=True)

    # style.css - REQUIRED
    style_css = """/*
Theme Name: WPGen Minimal Safe Theme
Theme URI: https://wpgen.local/
Author: WPGen
Description: Absolute minimal theme for testing. If this doesn't work, the issue is with WordPress itself.
Version: 1.0.0
License: GPL-2.0-or-later
Text Domain: wpgen-minimal-safe
*/

body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

header {
    padding: 20px 0;
    border-bottom: 2px solid #333;
    margin-bottom: 20px;
}

h1 {
    margin: 0;
}

article {
    margin-bottom: 40px;
    padding-bottom: 20px;
    border-bottom: 1px solid #ddd;
}

footer {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 2px solid #333;
    text-align: center;
}
"""

    # index.php - REQUIRED
    index_php = """<?php
/**
 * Main template file - Minimal Safe Theme
 */
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?php bloginfo( 'name' ); ?></title>
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>

    <header>
        <h1><?php bloginfo( 'name' ); ?></h1>
        <p><?php bloginfo( 'description' ); ?></p>
    </header>

    <main>
        <?php
        if ( have_posts() ) :
            while ( have_posts() ) : the_post();
                ?>
                <article>
                    <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                    <div><?php the_content(); ?></div>
                </article>
                <?php
            endwhile;
        else :
            ?>
            <p>No content found.</p>
            <?php
        endif;
        ?>
    </main>

    <footer>
        <p>&copy; <?php echo date( 'Y' ); ?> <?php bloginfo( 'name' ); ?></p>
    </footer>

    <?php wp_footer(); ?>
</body>
</html>
"""

    # functions.php - Absolute minimum
    functions_php = """<?php
/**
 * Minimal theme functions - ZERO external dependencies
 */

// Theme setup
function wpgen_minimal_setup() {
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
}
add_action( 'after_setup_theme', 'wpgen_minimal_setup' );

// Enqueue stylesheet
function wpgen_minimal_scripts() {
    wp_enqueue_style( 'wpgen-minimal-style', get_stylesheet_uri() );
}
add_action( 'wp_enqueue_scripts', 'wpgen_minimal_scripts' );
"""

    # Write files
    (theme_dir / "style.css").write_text(style_css, encoding="utf-8")
    (theme_dir / "index.php").write_text(index_php, encoding="utf-8")
    (theme_dir / "functions.php").write_text(functions_php, encoding="utf-8")

    # Create screenshot
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (1200, 900), color='#f8f9fa')
        d = ImageDraw.Draw(img)

        # Draw simple text
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()

        text = "WPGen Minimal Safe Theme"
        bbox = d.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        d.text(((1200-w)/2, (900-h)/2), text, fill='#333333', font=font)
        img.save(str(theme_dir / "screenshot.png"))
    except Exception as e:
        print(f"Could not create screenshot: {e}")

    print(f"\n✅ Created minimal safe theme: {theme_dir}")
    print("\nThis theme has:")
    print("  - NO require/include statements")
    print("  - NO external dependencies")
    print("  - NO advanced features")
    print("  - Just the bare minimum WordPress needs")
    print("\nIf this theme ALSO crashes WordPress, the problem is:")
    print("  - WordPress installation is corrupted")
    print("  - PHP version incompatibility")
    print("  - Server configuration issue")
    print("  - Database/hosting problem")
    print("\nTry installing this theme in WordPress.")

    return str(theme_dir)


if __name__ == "__main__":
    create_minimal_theme()
