"""WordPress theme code generator.

This module generates complete WordPress themes based on parsed requirements.
It creates all necessary files including style.css, functions.php, templates, etc.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ..llm.base import BaseLLMProvider
from ..utils.logger import get_logger


logger = get_logger(__name__)


class WordPressGenerator:
    """Generator for WordPress theme code."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        output_dir: str = "output",
        config: Dict[str, Any] = None
    ):
        """Initialize the WordPress generator.

        Args:
            llm_provider: LLM provider for code generation
            output_dir: Base output directory for generated themes
            config: WordPress configuration from config.yaml
        """
        self.llm_provider = llm_provider
        self.output_dir = Path(output_dir)
        self.config = config or {}
        logger.info(f"Initialized WordPressGenerator with output dir: {output_dir}")

    def generate(self, requirements: Dict[str, Any]) -> str:
        """Generate a complete WordPress theme from requirements.

        Args:
            requirements: Parsed theme requirements

        Returns:
            Path to the generated theme directory

        Raises:
            Exception: If generation fails
        """
        theme_name = requirements["theme_name"]
        logger.info(f"Starting theme generation: {theme_name}")

        # Create theme directory
        theme_dir = self.output_dir / theme_name
        if theme_dir.exists() and self.config.get("clean_before_generate", False):
            logger.warning(f"Cleaning existing theme directory: {theme_dir}")
            shutil.rmtree(theme_dir)

        theme_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created theme directory: {theme_dir}")

        try:
            # Generate core files
            self._generate_style_css(theme_dir, requirements)
            self._generate_functions_php(theme_dir, requirements)
            self._generate_index_php(theme_dir, requirements)
            self._generate_header_php(theme_dir, requirements)
            self._generate_footer_php(theme_dir, requirements)
            self._generate_sidebar_php(theme_dir, requirements)

            # Generate template files
            self._generate_templates(theme_dir, requirements)

            # Generate additional files
            self._generate_screenshot(theme_dir, requirements)
            self._generate_readme(theme_dir, requirements)
            self._generate_gitignore(theme_dir)

            # Generate wp-config sample if requested
            if self.config.get("include_wp_config", True):
                self._generate_wp_config(theme_dir.parent, requirements)

            logger.info(f"Successfully generated theme: {theme_name}")
            return str(theme_dir)

        except Exception as e:
            logger.error(f"Failed to generate theme: {str(e)}")
            raise

    def _generate_style_css(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate style.css file with theme header and styles.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating style.css")

        # Generate the header comment
        author = self.config.get("author", "WPGen")
        license = self.config.get("license", "GPL-2.0-or-later")
        version = "1.0.0"
        wp_version = self.config.get("wp_version", "6.4")

        header = f"""/*
Theme Name: {requirements['theme_display_name']}
Theme URI: https://github.com/yourusername/{requirements['theme_name']}
Author: {author}
Author URI: https://github.com/yourusername
Description: {requirements['description']}
Version: {version}
Requires at least: {wp_version}
Tested up to: {wp_version}
Requires PHP: 7.4
License: {license}
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Text Domain: {requirements['theme_name']}
Tags: {', '.join(requirements.get('features', [])[:5])}
*/

"""

        # Generate CSS using LLM
        context = {
            "theme_name": requirements["theme_name"],
            "color_scheme": requirements.get("color_scheme", "default"),
            "layout": requirements.get("layout", "full-width"),
            "features": requirements.get("features", [])
        }

        description = f"""Create a complete CSS stylesheet for a WordPress theme.
The theme should have a {context['color_scheme']} color scheme with {context['layout']} layout.
Include:
- Reset/normalize styles
- Typography (headings, paragraphs, links)
- Layout structure (header, main, sidebar, footer)
- Navigation menu styles
- Post/page content styles
- Widget styles
- Responsive design (mobile-first)
- Utility classes"""

        try:
            css_code = self.llm_provider.generate_code(description, "css", context)
            full_css = header + css_code

            style_file = theme_dir / "style.css"
            style_file.write_text(full_css, encoding="utf-8")
            logger.info("Generated style.css successfully")

        except Exception as e:
            logger.error(f"Failed to generate style.css: {str(e)}")
            # Write minimal fallback
            style_file = theme_dir / "style.css"
            style_file.write_text(header + "\n/* Add your styles here */\n", encoding="utf-8")

    def _generate_functions_php(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate functions.php file.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating functions.php")

        context = {
            "theme_name": requirements["theme_name"],
            "features": requirements.get("features", []),
            "navigation": requirements.get("navigation", []),
            "post_types": requirements.get("post_types", []),
            "integrations": requirements.get("integrations", [])
        }

        description = f"""Create a complete functions.php file for a WordPress theme.
Include:
- Theme setup function with theme support declarations
- Enqueue scripts and styles
- Register navigation menus: {', '.join(context['navigation'])}
- Register widget areas
- Custom post types: {', '.join(context['post_types'])}
- Theme customizer settings
- Helper functions
- Security best practices (sanitization, escaping)"""

        try:
            php_code = self.llm_provider.generate_code(description, "php", context)

            # Ensure PHP opening tag
            if not php_code.strip().startswith("<?php"):
                php_code = "<?php\n" + php_code

            functions_file = theme_dir / "functions.php"
            functions_file.write_text(php_code, encoding="utf-8")
            logger.info("Generated functions.php successfully")

        except Exception as e:
            logger.error(f"Failed to generate functions.php: {str(e)}")
            raise

    def _generate_index_php(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate index.php template file.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating index.php")

        context = {
            "theme_name": requirements["theme_name"],
            "layout": requirements.get("layout", "full-width")
        }

        description = """Create the main index.php template file for WordPress.
This is the fallback template. Include:
- get_header() call
- The WordPress loop
- Post title, content, meta
- Pagination
- get_sidebar() if applicable
- get_footer() call
Use modern WordPress template tags and best practices."""

        try:
            php_code = self.llm_provider.generate_code(description, "php", context)

            if not php_code.strip().startswith("<?php"):
                php_code = "<?php\n" + php_code

            index_file = theme_dir / "index.php"
            index_file.write_text(php_code, encoding="utf-8")
            logger.info("Generated index.php successfully")

        except Exception as e:
            logger.error(f"Failed to generate index.php: {str(e)}")
            raise

    def _generate_header_php(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate header.php template file.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating header.php")

        context = {
            "theme_name": requirements["theme_name"],
            "navigation": requirements.get("navigation", [])
        }

        description = """Create header.php template for WordPress theme.
Include:
- DOCTYPE and opening HTML tags
- wp_head() call
- Site title/logo
- Primary navigation menu
- Mobile-responsive header
Follow WordPress coding standards."""

        try:
            php_code = self.llm_provider.generate_code(description, "php", context)

            if not php_code.strip().startswith("<!DOCTYPE") and not php_code.strip().startswith("<?php"):
                php_code = "<?php\n" + php_code

            header_file = theme_dir / "header.php"
            header_file.write_text(php_code, encoding="utf-8")
            logger.info("Generated header.php successfully")

        except Exception as e:
            logger.error(f"Failed to generate header.php: {str(e)}")
            raise

    def _generate_footer_php(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate footer.php template file.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating footer.php")

        context = {
            "theme_name": requirements["theme_name"]
        }

        description = """Create footer.php template for WordPress theme.
Include:
- Footer widget areas
- Copyright notice
- wp_footer() call
- Closing body and html tags
Follow WordPress coding standards."""

        try:
            php_code = self.llm_provider.generate_code(description, "php", context)

            if not php_code.strip().startswith("<?php"):
                php_code = "<?php\n" + php_code

            footer_file = theme_dir / "footer.php"
            footer_file.write_text(php_code, encoding="utf-8")
            logger.info("Generated footer.php successfully")

        except Exception as e:
            logger.error(f"Failed to generate footer.php: {str(e)}")
            raise

    def _generate_sidebar_php(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate sidebar.php template file.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating sidebar.php")

        context = {
            "theme_name": requirements["theme_name"]
        }

        description = """Create sidebar.php template for WordPress theme.
Include:
- Check if sidebar is active
- Display dynamic sidebar
- Follow WordPress coding standards."""

        try:
            php_code = self.llm_provider.generate_code(description, "php", context)

            if not php_code.strip().startswith("<?php"):
                php_code = "<?php\n" + php_code

            sidebar_file = theme_dir / "sidebar.php"
            sidebar_file.write_text(php_code, encoding="utf-8")
            logger.info("Generated sidebar.php successfully")

        except Exception as e:
            logger.error(f"Failed to generate sidebar.php: {str(e)}")
            raise

    def _generate_templates(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate additional template files based on requirements.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating template files")

        templates_to_generate = {
            "single.php": "Single post template",
            "page.php": "Static page template",
            "archive.php": "Archive listing template",
            "search.php": "Search results template",
            "404.php": "404 error page template",
        }

        # Add custom page templates
        for page in requirements.get("pages", []):
            if page not in ["index", "single", "archive", "search", "404"]:
                template_file = f"page-{page}.php"
                templates_to_generate[template_file] = f"Custom page template for {page}"

        for template_file, description in templates_to_generate.items():
            try:
                logger.info(f"Generating {template_file}")

                context = {
                    "theme_name": requirements["theme_name"],
                    "template_type": template_file
                }

                full_description = f"""Create {template_file} for WordPress theme.
{description}. Include appropriate WordPress loop and template tags.
Follow WordPress template hierarchy and coding standards."""

                php_code = self.llm_provider.generate_code(full_description, "php", context)

                if not php_code.strip().startswith("<?php"):
                    php_code = "<?php\n" + php_code

                (theme_dir / template_file).write_text(php_code, encoding="utf-8")
                logger.info(f"Generated {template_file} successfully")

            except Exception as e:
                logger.warning(f"Failed to generate {template_file}: {str(e)}")
                continue

    def _generate_screenshot(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate placeholder screenshot file.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating screenshot placeholder")

        # Create a simple text file as placeholder
        # In production, you'd generate an actual image
        screenshot_file = theme_dir / "screenshot.txt"
        content = f"""Screenshot Placeholder for {requirements['theme_display_name']}

To add a proper screenshot:
1. Create a 1200x900px PNG or JPG image
2. Name it screenshot.png or screenshot.jpg
3. Place it in the theme root directory

The screenshot should show the theme's appearance and will be displayed
in the WordPress theme selector.
"""
        screenshot_file.write_text(content, encoding="utf-8")
        logger.info("Generated screenshot placeholder")

    def _generate_readme(self, theme_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate README.md for the theme.

        Args:
            theme_dir: Theme directory path
            requirements: Theme requirements
        """
        logger.info("Generating README.md")

        readme_content = f"""# {requirements['theme_display_name']}

{requirements['description']}

## Description

This WordPress theme was automatically generated using WPGen.

## Features

{chr(10).join(f'- {feature}' for feature in requirements.get('features', []))}

## Installation

1. Download the theme ZIP file
2. In WordPress admin, go to Appearance > Themes > Add New > Upload Theme
3. Choose the ZIP file and click Install Now
4. After installation, click Activate

## Development

This theme was generated with the following specifications:

- **Color Scheme**: {requirements.get('color_scheme', 'default')}
- **Layout**: {requirements.get('layout', 'full-width')}
- **Pages**: {', '.join(requirements.get('pages', []))}

## Customization

You can customize this theme using:

1. WordPress Customizer (Appearance > Customize)
2. Editing the theme files directly
3. Using a child theme (recommended for major modifications)

## Support

For issues and questions:
- Check the [WordPress Codex](https://codex.wordpress.org/)
- Visit [WordPress Support Forums](https://wordpress.org/support/)

## License

This theme is licensed under {self.config.get('license', 'GPL-2.0-or-later')}.

## Credits

- Generated by: WPGen
- Generated on: {datetime.now().strftime('%Y-%m-%d')}
"""

        readme_file = theme_dir / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")
        logger.info("Generated README.md successfully")

    def _generate_gitignore(self, theme_dir: Path) -> None:
        """Generate .gitignore file for the theme.

        Args:
            theme_dir: Theme directory path
        """
        logger.info("Generating .gitignore")

        gitignore_content = """# WordPress
wp-config.php
wp-content/uploads/
wp-content/cache/
wp-content/backup-db/

# Theme development
node_modules/
*.sass-cache/
.DS_Store
Thumbs.db
*.log

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Build files
dist/
build/
"""

        gitignore_file = theme_dir / ".gitignore"
        gitignore_file.write_text(gitignore_content, encoding="utf-8")
        logger.info("Generated .gitignore successfully")

    def _generate_wp_config(self, output_dir: Path, requirements: Dict[str, Any]) -> None:
        """Generate sample wp-config.php file.

        Args:
            output_dir: Output directory (parent of theme dir)
            requirements: Theme requirements
        """
        logger.info("Generating wp-config-sample.php")

        wp_config_content = """<?php
/**
 * Sample WordPress Configuration File
 *
 * This file contains sample configuration for WordPress.
 * Copy this file to 'wp-config.php' and fill in the values.
 *
 * @package WordPress
 */

// ** Database settings ** //
define( 'DB_NAME', 'database_name_here' );
define( 'DB_USER', 'username_here' );
define( 'DB_PASSWORD', 'password_here' );
define( 'DB_HOST', 'localhost' );
define( 'DB_CHARSET', 'utf8' );
define( 'DB_COLLATE', '' );

// ** Authentication unique keys and salts ** //
// Get these from: https://api.wordpress.org/secret-key/1.1/salt/
define( 'AUTH_KEY',         'put your unique phrase here' );
define( 'SECURE_AUTH_KEY',  'put your unique phrase here' );
define( 'LOGGED_IN_KEY',    'put your unique phrase here' );
define( 'NONCE_KEY',        'put your unique phrase here' );
define( 'AUTH_SALT',        'put your unique phrase here' );
define( 'SECURE_AUTH_SALT', 'put your unique phrase here' );
define( 'LOGGED_IN_SALT',   'put your unique phrase here' );
define( 'NONCE_SALT',       'put your unique phrase here' );

// ** WordPress database table prefix ** //
$table_prefix = 'wp_';

// ** WordPress debugging mode ** //
define( 'WP_DEBUG', false );

/* That's all, stop editing! Happy publishing. */

if ( ! defined( 'ABSPATH' ) ) {
    define( 'ABSPATH', __DIR__ . '/' );
}

require_once ABSPATH . 'wp-settings.php';
"""

        wp_config_file = output_dir / "wp-config-sample.php"
        wp_config_file.write_text(wp_config_content, encoding="utf-8")
        logger.info("Generated wp-config-sample.php successfully")
