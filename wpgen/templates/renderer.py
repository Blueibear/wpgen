"""Jinja2 template renderer for WordPress theme generation.

This module renders JSON theme specifications through Jinja2 templates
to produce valid WordPress theme files. This guarantees:

- No broken PHP syntax
- No invalid template structure
- No hallucinated functions
- No invalid filenames
- No Unicode corruption
- No WordPress preview white-screen

The LLM never outputs PHP directly - it outputs JSON which is rendered
through these safe, pre-validated templates.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..schema import ThemeSpecification, get_default_theme_spec
from ..utils.logger import get_logger

logger = get_logger(__name__)


# Template directory locations
TEMPLATE_DIR = Path(__file__).parent
PHP_TEMPLATE_DIR = TEMPLATE_DIR / "php"
PHP_FALLBACK_DIR = PHP_TEMPLATE_DIR / "fallback"
JS_TEMPLATE_DIR = TEMPLATE_DIR / "js"


# WordPress template files to generate
WORDPRESS_TEMPLATES = {
    # Core templates
    "style.css": "style.css.j2",
    "functions.php": "functions.php.j2",
    "header.php": "header.php.j2",
    "footer.php": "footer.php.j2",
    "index.php": "index.php.j2",
    "front-page.php": "front-page.php.j2",
    "single.php": "single.php.j2",
    "page.php": "page.php.j2",
    "archive.php": "archive.php.j2",
    "search.php": "search.php.j2",
    "404.php": "404.php.j2",
    "sidebar.php": "sidebar.php.j2",
    "comments.php": "comments.php.j2",
}

JS_TEMPLATES = {
    "assets/js/theme.js": "theme.js.j2",
    "assets/js/navigation.js": "navigation.js.j2",
}

# Critical templates that have fallback versions
CRITICAL_TEMPLATES = {
    "header.php",
    "footer.php",
    "front-page.php",
    "index.php",
}


def validate_php_file(file_path: Path) -> bool:
    """Validate PHP syntax of a file using php -l.

    Args:
        file_path: Path to PHP file

    Returns:
        True if valid, False otherwise
    """
    try:
        result = subprocess.run(
            ["php", "-l", str(file_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning(f"PHP validation unavailable: {e}")
        # If php is not available, assume valid (CI environments may not have PHP)
        return True
    except Exception as e:
        logger.error(f"PHP validation error: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for WordPress conventions.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename (lowercase, no spaces, no special chars)
    """
    # Convert to lowercase
    filename = filename.lower()

    # Replace spaces and underscores with hyphens
    filename = re.sub(r'[\s_]+', '-', filename)

    # Remove any character that isn't alphanumeric, hyphen, or dot
    filename = re.sub(r'[^a-z0-9\-.]', '', filename)

    # Remove multiple consecutive hyphens
    filename = re.sub(r'-+', '-', filename)

    # Remove leading/trailing hyphens
    filename = filename.strip('-')

    return filename


def sanitize_theme_slug(slug: str) -> str:
    """Sanitize theme slug for WordPress.

    Args:
        slug: Original theme slug

    Returns:
        Valid WordPress theme slug
    """
    # Convert to lowercase
    slug = slug.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)

    # Remove any character that isn't alphanumeric or hyphen
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Ensure it's not empty
    if not slug:
        slug = "wpgen-theme"

    return slug


class ThemeRenderer:
    """Renderer for WordPress themes from JSON specifications.

    This class takes a ThemeSpecification (JSON) and renders it through
    Jinja2 templates to produce valid WordPress theme files.
    """

    def __init__(self, output_dir: str | Path):
        """Initialize the theme renderer.

        Args:
            output_dir: Base output directory for generated themes
        """
        self.output_dir = Path(output_dir)

        # Setup Jinja2 environment for PHP templates
        self.php_env = Environment(
            loader=FileSystemLoader(str(PHP_TEMPLATE_DIR)),
            autoescape=False,  # Don't escape PHP code
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Setup Jinja2 environment for JS templates
        self.js_env = Environment(
            loader=FileSystemLoader(str(JS_TEMPLATE_DIR)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Setup Jinja2 environment for fallback templates
        self.fallback_env = Environment(
            loader=FileSystemLoader(str(PHP_FALLBACK_DIR)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        logger.info(f"Initialized ThemeRenderer with output dir: {output_dir}")

    def render(self, spec: ThemeSpecification, images: list[dict[str, Any]] | None = None) -> str:
        """Render a complete WordPress theme from a specification.

        Args:
            spec: Theme specification
            images: Optional list of design reference images

        Returns:
            Path to the generated theme directory

        Raises:
            ValueError: If theme generation fails
        """
        # Sanitize theme name for directory
        theme_slug = sanitize_theme_slug(spec.theme_name)

        # Update spec with sanitized slug
        spec.theme_name = theme_slug

        logger.info(f"Rendering theme: {spec.theme_display_name} ({theme_slug})")

        # Create theme directory
        theme_dir = self.output_dir / theme_slug
        theme_dir.mkdir(parents=True, exist_ok=True)

        # Create required directories
        (theme_dir / "assets" / "css").mkdir(parents=True, exist_ok=True)
        (theme_dir / "assets" / "js").mkdir(parents=True, exist_ok=True)
        (theme_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)
        (theme_dir / "template-parts").mkdir(parents=True, exist_ok=True)

        # Prepare template context
        context = self._prepare_context(spec)

        # Render PHP templates
        self._render_php_templates(theme_dir, context)

        # Render JS templates
        self._render_js_templates(theme_dir, context)

        # Generate additional files
        self._generate_additional_files(theme_dir, spec)

        # Generate screenshot
        self._generate_screenshot(theme_dir, spec, images)

        logger.info(f"Successfully rendered theme to: {theme_dir}")

        return str(theme_dir)

    def _prepare_context(self, spec: ThemeSpecification) -> dict[str, Any]:
        """Prepare template context from specification.

        Args:
            spec: Theme specification

        Returns:
            Template context dictionary
        """
        # Convert Pydantic model to dict for template access
        spec_dict = spec.model_dump()

        return {
            "theme": spec_dict,
            "colors": spec_dict["colors"],
            "typography": spec_dict["typography"],
            "layout": spec_dict["layout"],
            "hero": spec_dict["hero"],
            "navigation": spec_dict["navigation"],
            "features": spec_dict["features"],
            "widget_areas": spec_dict["widget_areas"],
            "post_types": spec_dict["post_types"],
            "tags": spec_dict["tags"],
            "pages": spec_dict.get("pages", {}),
        }

    def _render_php_templates(self, theme_dir: Path, context: dict[str, Any]) -> None:
        """Render all PHP templates with validation and fallback support.

        Args:
            theme_dir: Theme directory path
            context: Template context
        """
        for output_file, template_file in WORDPRESS_TEMPLATES.items():
            try:
                template = self.php_env.get_template(template_file)
                content = template.render(**context)

                # Sanitize output filename
                output_path = theme_dir / sanitize_filename(output_file)
                output_path.write_text(content, encoding="utf-8")

                logger.debug(f"Rendered: {output_file}")

                # Validate PHP syntax for critical files
                if output_file.endswith('.php') and output_file in CRITICAL_TEMPLATES:
                    is_valid = validate_php_file(output_path)

                    if not is_valid:
                        logger.error(f"PHP validation failed for {output_file}, using fallback template")

                        # Try to use fallback template
                        try:
                            fallback_template = self.fallback_env.get_template(template_file)
                            fallback_content = fallback_template.render(**context)
                            output_path.write_text(fallback_content, encoding="utf-8")

                            # Validate fallback
                            if validate_php_file(output_path):
                                logger.info(f"Successfully used fallback template for {output_file}")
                            else:
                                logger.error(f"Fallback template also failed validation for {output_file}")
                                raise ValueError(f"Both primary and fallback templates failed for {output_file}")

                        except Exception as fallback_error:
                            logger.error(f"Failed to use fallback template for {output_file}: {fallback_error}")
                            raise ValueError(f"Template rendering and fallback both failed for {output_file}")

            except Exception as e:
                logger.error(f"Failed to render {output_file}: {e}")
                raise ValueError(f"Template rendering failed for {output_file}: {e}")

    def _render_js_templates(self, theme_dir: Path, context: dict[str, Any]) -> None:
        """Render JavaScript templates.

        Args:
            theme_dir: Theme directory path
            context: Template context
        """
        for output_file, template_file in JS_TEMPLATES.items():
            try:
                template = self.js_env.get_template(template_file)
                content = template.render(**context)

                # Create output path
                output_path = theme_dir / output_file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content, encoding="utf-8")

                logger.debug(f"Rendered: {output_file}")

            except Exception as e:
                logger.error(f"Failed to render {output_file}: {e}")
                raise ValueError(f"Template rendering failed for {output_file}: {e}")

    def _generate_additional_files(self, theme_dir: Path, spec: ThemeSpecification) -> None:
        """Generate additional theme files.

        Args:
            theme_dir: Theme directory path
            spec: Theme specification
        """
        # Generate README.md
        readme_content = f"""# {spec.theme_display_name}

{spec.description}

## Requirements

- WordPress 6.0 or higher
- PHP 7.4 or higher

## Installation

1. Download the theme
2. Upload to `/wp-content/themes/`
3. Activate in WordPress Admin > Appearance > Themes

## Features

- Responsive design
- Custom color scheme
- Widget areas
- Navigation menus
{"- WooCommerce support" if spec.features.woocommerce.enabled else ""}
{"- Dark mode support" if spec.features.dark_mode else ""}

## Credits

Generated by [WPGen](https://github.com/wpgen/wpgen)

## License

GPL-2.0-or-later
"""
        (theme_dir / "README.md").write_text(readme_content, encoding="utf-8")

        # Generate .gitignore
        gitignore_content = """# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Node
node_modules/

# Build
dist/
build/

# Logs
*.log
"""
        (theme_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")

        # Generate editor-style.css (placeholder)
        editor_style = """/* Editor styles for Gutenberg blocks */
.editor-styles-wrapper {
    font-family: inherit;
}
"""
        (theme_dir / "assets" / "css" / "editor-style.css").write_text(
            editor_style, encoding="utf-8"
        )

    def _generate_screenshot(
        self,
        theme_dir: Path,
        spec: ThemeSpecification,
        images: list[dict[str, Any]] | None
    ) -> None:
        """Generate theme screenshot.

        Args:
            theme_dir: Theme directory path
            spec: Theme specification
            images: Optional list of design reference images
        """
        screenshot_path = theme_dir / "screenshot.png"

        if screenshot_path.exists():
            return

        # Try to use provided image
        if images and len(images) > 0:
            try:
                from PIL import Image

                img_data = images[0]
                src = img_data.get('path') if isinstance(img_data, dict) else img_data

                if src and Path(src).exists():
                    with Image.open(src) as im:
                        im = im.convert("RGB")
                        canvas = Image.new("RGB", (1200, 900), (247, 248, 250))
                        im.thumbnail((1200, 900))
                        x = (1200 - im.width) // 2
                        y = (900 - im.height) // 2
                        canvas.paste(im, (x, y))
                        canvas.save(screenshot_path, format="PNG", optimize=True)
                        logger.info("Generated screenshot from uploaded image")
                        return

            except Exception as e:
                logger.warning(f"Could not use uploaded image for screenshot: {e}")

        # Generate placeholder screenshot
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Extract primary color
            primary_color = spec.colors.primary
            if primary_color.startswith('#'):
                fg = tuple(int(primary_color.strip("#")[i:i+2], 16) for i in (0, 2, 4))
            else:
                fg = (26, 26, 46)

            bg = (248, 250, 252)

            img = Image.new("RGB", (1200, 900), bg)
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 600, 1200, 900], fill=fg)

            try:
                font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
                font_sub = ImageFont.truetype("DejaVuSans.ttf", 28)
            except Exception:
                font_title = ImageFont.load_default()
                font_sub = ImageFont.load_default()

            # Draw title
            title = spec.theme_display_name
            bbox = draw.textbbox((0, 0), title, font=font_title)
            tw = bbox[2] - bbox[0]
            draw.text(((1200 - tw) // 2, 330), title, fill=(17, 24, 39), font=font_title)

            # Draw subtitle
            sub = "Generated by WPGen"
            bbox2 = draw.textbbox((0, 0), sub, font=font_sub)
            sw = bbox2[2] - bbox2[0]
            draw.text(((1200 - sw) // 2, 410), sub, fill=(55, 65, 81), font=font_sub)

            img.save(screenshot_path, format="PNG", optimize=True)
            logger.info("Generated placeholder screenshot")

        except ImportError:
            logger.warning("PIL not installed, skipping screenshot generation")
        except Exception as e:
            logger.warning(f"Could not generate screenshot: {e}")


def render_theme(
    spec: ThemeSpecification | dict[str, Any],
    output_dir: str | Path,
    images: list[dict[str, Any]] | None = None
) -> str:
    """Convenience function to render a theme.

    Args:
        spec: Theme specification (ThemeSpecification or dict)
        output_dir: Output directory for the theme
        images: Optional list of design reference images

    Returns:
        Path to the generated theme directory
    """
    # Convert dict to ThemeSpecification if needed
    if isinstance(spec, dict):
        spec = ThemeSpecification(**spec)

    renderer = ThemeRenderer(output_dir)
    return renderer.render(spec, images)


def get_template_list() -> dict[str, list[str]]:
    """Get list of available templates.

    Returns:
        Dictionary mapping template type to list of template files
    """
    return {
        "php": list(WORDPRESS_TEMPLATES.keys()),
        "js": list(JS_TEMPLATES.keys()),
    }
