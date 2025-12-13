"""Packager Module for WPGen.

This module handles theme packaging operations including:
- Creating theme directory structure
- Writing files with proper encoding and permissions
- Creating ZIP archives for distribution
- Generating required WordPress files (style.css, readme.txt)

All operations are deterministic and safe.
"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ThemePackager:
    """Handles theme directory creation and ZIP packaging."""

    def __init__(self, output_dir: str = 'output'):
        """Initialize theme packager.

        Args:
            output_dir: Base directory for theme output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_theme_directory(
        self,
        theme_name: str,
        clean_existing: bool = False
    ) -> Path:
        """Create theme directory structure.

        Args:
            theme_name: Theme folder name (slug)
            clean_existing: Whether to delete existing directory

        Returns:
            Path to created theme directory

        Raises:
            ValueError: If theme name is invalid
        """
        # Validate theme name
        if not theme_name or not isinstance(theme_name, str):
            raise ValueError("Theme name must be a non-empty string")

        # Sanitize theme name for folder use
        safe_name = theme_name.lower().replace(' ', '-')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '-_')

        theme_path = self.output_dir / safe_name

        # Clean existing if requested
        if theme_path.exists() and clean_existing:
            logger.warning(f"Removing existing theme directory: {theme_path}")
            shutil.rmtree(theme_path)

        # Create directory structure
        theme_path.mkdir(parents=True, exist_ok=True)

        # Create standard WordPress theme subdirectories
        subdirs = [
            'js',
            'css',
            'inc',
            'template-parts',
            'images',
            'languages',
        ]

        for subdir in subdirs:
            (theme_path / subdir).mkdir(parents=True, exist_ok=True)

        logger.info(f"Created theme directory structure: {theme_path}")

        return theme_path

    def write_file(
        self,
        theme_path: Path,
        filename: str,
        content: str,
        create_dirs: bool = True
    ) -> Path:
        """Write a file to the theme directory with proper encoding.

        Args:
            theme_path: Theme directory path
            filename: Relative filename (may include subdirectories)
            content: File content
            create_dirs: Whether to create parent directories if needed

        Returns:
            Path to written file
        """
        file_path = theme_path / filename

        # Create parent directories if needed
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file with UTF-8 encoding (no BOM)
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

        logger.debug(f"Wrote file: {filename}")

        return file_path

    def write_files_batch(
        self,
        theme_path: Path,
        files: Dict[str, str]
    ) -> List[Path]:
        """Write multiple files to theme directory.

        Args:
            theme_path: Theme directory path
            files: Dictionary mapping filenames to content

        Returns:
            List of paths to written files
        """
        written_paths = []

        for filename, content in files.items():
            try:
                path = self.write_file(theme_path, filename, content)
                written_paths.append(path)
            except Exception as e:
                logger.error(f"Failed to write {filename}: {e}")
                raise

        logger.info(f"Wrote {len(written_paths)} files to theme directory")

        return written_paths

    def generate_style_css_header(
        self,
        theme_name: str,
        theme_slug: str,
        description: str,
        author: str = 'WPGen',
        author_uri: str = 'https://wpgen.local',
        theme_uri: str = 'https://wpgen.local',
        version: str = '1.0.0',
        tags: Optional[List[str]] = None
    ) -> str:
        """Generate WordPress theme header for style.css.

        Args:
            theme_name: Theme display name
            theme_slug: Theme text domain
            description: Theme description
            author: Theme author name
            author_uri: Author website URL
            theme_uri: Theme website URL
            version: Theme version
            tags: WordPress theme tags

        Returns:
            Formatted style.css header
        """
        tags = tags or ['blog', 'custom-menu', 'featured-images', 'threaded-comments']
        tags_str = ', '.join(tags)

        header = f"""/*
Theme Name: {theme_name}
Theme URI: {theme_uri}
Author: {author}
Author URI: {author_uri}
Description: {description}
Version: {version}
Requires at least: 6.0
Tested up to: 6.4
Requires PHP: 7.4
License: GNU General Public License v2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Text Domain: {theme_slug}
Tags: {tags_str}
*/

"""
        return header

    def generate_readme_txt(
        self,
        theme_name: str,
        description: str,
        changelog: Optional[List[str]] = None
    ) -> str:
        """Generate readme.txt file for WordPress theme.

        Args:
            theme_name: Theme name
            description: Theme description
            changelog: List of changelog entries

        Returns:
            Formatted readme.txt content
        """
        changelog = changelog or ["Initial release"]
        changelog_str = '\n'.join(f"* {entry}" for entry in changelog)

        return f"""=== {theme_name} ===
Contributors: wpgen
Requires at least: 6.0
Tested up to: 6.4
Requires PHP: 7.4
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

== Description ==

{description}

== Installation ==

1. In your WordPress admin panel, go to Appearance > Themes and click the Add New button.
2. Click Upload Theme and Choose File, then select the theme's .zip file. Click Install Now.
3. Click Activate to use your new theme right away.

== Changelog ==

= 1.0.0 =
{changelog_str}

== Credits ==

Generated by WPGen - WordPress Theme Generator
"""

    def create_zip_archive(
        self,
        theme_path: Path,
        output_name: Optional[str] = None
    ) -> Path:
        """Create ZIP archive of theme for distribution.

        Args:
            theme_path: Path to theme directory
            output_name: Optional output filename (without .zip extension)

        Returns:
            Path to created ZIP file
        """
        if not theme_path.exists() or not theme_path.is_dir():
            raise ValueError(f"Theme path does not exist or is not a directory: {theme_path}")

        # Determine ZIP filename
        if output_name:
            zip_name = f"{output_name}.zip"
        else:
            zip_name = f"{theme_path.name}.zip"

        zip_path = theme_path.parent / zip_name

        # Remove existing ZIP if present
        if zip_path.exists():
            zip_path.unlink()

        # Create ZIP archive
        logger.info(f"Creating ZIP archive: {zip_name}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in theme_path.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for ZIP
                    arcname = file_path.relative_to(theme_path.parent)
                    zipf.write(file_path, arcname)

        zip_size = zip_path.stat().st_size / 1024  # Size in KB

        logger.info(f"Created ZIP archive: {zip_path} ({zip_size:.1f} KB)")

        return zip_path

    def validate_theme_files(self, theme_path: Path) -> Dict[str, bool]:
        """Validate that required theme files exist.

        Args:
            theme_path: Theme directory path

        Returns:
            Dictionary of file checks {filename: exists}
        """
        required_files = {
            'style.css': False,
            'index.php': False,
        }

        recommended_files = {
            'functions.php': False,
            'header.php': False,
            'footer.php': False,
            'screenshot.png': False,
        }

        all_checks = {**required_files, **recommended_files}

        for filename in all_checks.keys():
            file_path = theme_path / filename
            all_checks[filename] = file_path.exists()

        # Log missing required files
        missing_required = [f for f in required_files if not all_checks[f]]
        if missing_required:
            logger.error(f"Missing required files: {', '.join(missing_required)}")

        # Log missing recommended files
        missing_recommended = [f for f in recommended_files if not all_checks[f]]
        if missing_recommended:
            logger.warning(f"Missing recommended files: {', '.join(missing_recommended)}")

        return all_checks

    def finalize_theme(
        self,
        theme_path: Path,
        create_zip: bool = True,
        validate: bool = True
    ) -> Dict[str, any]:
        """Finalize theme package with validation and optional ZIP creation.

        Args:
            theme_path: Theme directory path
            create_zip: Whether to create ZIP archive
            validate: Whether to validate required files

        Returns:
            Dictionary with finalization results
        """
        results = {
            'theme_path': str(theme_path),
            'valid': True,
            'zip_path': None,
            'file_checks': {},
            'errors': [],
            'warnings': [],
        }

        # Validate files
        if validate:
            logger.info("Validating theme files...")
            file_checks = self.validate_theme_files(theme_path)
            results['file_checks'] = file_checks

            required_missing = []
            for filename in ['style.css', 'index.php']:
                if not file_checks.get(filename, False):
                    required_missing.append(filename)
                    results['valid'] = False

            if required_missing:
                error_msg = f"Missing required files: {', '.join(required_missing)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

        # Create ZIP
        if create_zip and results['valid']:
            try:
                zip_path = self.create_zip_archive(theme_path)
                results['zip_path'] = str(zip_path)
            except Exception as e:
                error_msg = f"Failed to create ZIP archive: {e}"
                results['errors'].append(error_msg)
                results['warnings'].append(error_msg)
                logger.error(error_msg)

        # Summary
        if results['valid']:
            logger.info(f"✓ Theme finalized successfully: {theme_path.name}")
        else:
            logger.error(f"✗ Theme finalization failed: {theme_path.name}")

        return results


def create_theme_package(
    theme_name: str,
    theme_files: Dict[str, str],
    output_dir: str = 'output',
    create_zip: bool = True,
    clean_existing: bool = False
) -> Dict[str, any]:
    """Convenience function to create complete theme package.

    Args:
        theme_name: Theme name
        theme_files: Dictionary mapping filenames to content
        output_dir: Output directory
        create_zip: Whether to create ZIP archive
        clean_existing: Whether to clean existing directory

    Returns:
        Dictionary with package results
    """
    packager = ThemePackager(output_dir)

    # Create directory
    theme_path = packager.create_theme_directory(theme_name, clean_existing)

    # Write files
    packager.write_files_batch(theme_path, theme_files)

    # Finalize
    results = packager.finalize_theme(theme_path, create_zip=create_zip)

    return results
