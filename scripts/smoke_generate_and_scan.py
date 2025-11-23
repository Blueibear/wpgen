#!/usr/bin/env python3
"""
Smoke test script for WPGen theme generator.

This script generates a test theme and validates that it meets all requirements:
1. Contains required WordPress hooks (wp_head, wp_body_open, wp_footer)
2. No mixed-content (insecure http:// URLs)
3. Proper enqueue separation (no editor deps on front-end)
4. Valid block categories

Usage:
    python scripts/smoke_generate_and_scan.py
"""

import json
import re
import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import wpgen
sys.path.insert(0, str(Path(__file__).parent.parent))

from wpgen.generators.wordpress_generator import WordPressGenerator
from wpgen.utils.code_validator import scan_mixed_content


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """Print an info message."""
    print(f"   {text}")


def check_required_hooks(theme_dir: Path) -> tuple[bool, list[str]]:
    """Check that theme contains required WordPress hooks."""
    print_header("Checking Required WordPress Hooks")

    errors = []
    passed = True

    # Check header.php
    header_file = theme_dir / "header.php"
    if header_file.exists():
        header_content = header_file.read_text(encoding='utf-8')

        required_hooks = [
            ('wp_head()', 'wp_head hook'),
            ('wp_body_open()', 'wp_body_open hook'),
            ('language_attributes()', 'language_attributes function'),
            ('body_class()', 'body_class function'),
        ]

        print_info("Checking header.php...")
        for hook, description in required_hooks:
            if hook in header_content:
                print_success(f"Found {description}")
            else:
                print_error(f"Missing {description}")
                errors.append(f"header.php missing {description}")
                passed = False
    else:
        print_error("header.php not found")
        errors.append("header.php not found")
        passed = False

    # Check footer.php
    footer_file = theme_dir / "footer.php"
    if footer_file.exists():
        footer_content = footer_file.read_text(encoding='utf-8')

        print_info("\nChecking footer.php...")
        if 'wp_footer()' in footer_content:
            print_success("Found wp_footer hook")
        else:
            print_error("Missing wp_footer hook")
            errors.append("footer.php missing wp_footer hook")
            passed = False

        if '</body>' in footer_content and '</html>' in footer_content:
            print_success("Has proper closing tags")
        else:
            print_error("Missing proper closing tags")
            errors.append("footer.php missing closing tags")
            passed = False
    else:
        print_error("footer.php not found")
        errors.append("footer.php not found")
        passed = False

    return passed, errors


def check_mixed_content(theme_dir: Path) -> tuple[bool, list[str]]:
    """Check for insecure HTTP URLs in theme files."""
    print_header("Checking for Mixed-Content (Insecure HTTP URLs)")

    results = scan_mixed_content(theme_dir, enforce_https=True)

    if results['valid']:
        print_success("No insecure HTTP URLs found")
        return True, []
    else:
        print_error(f"Found {len(results['http_urls'])} insecure HTTP URL(s):")
        for item in results['http_urls']:
            print_warning(f"  {item['file']}:{item['line']} → {item['url']}")
        return False, results['errors']


def check_enqueue_separation(theme_dir: Path) -> tuple[bool, list[str]]:
    """Check that enqueue hooks are properly separated."""
    print_header("Checking Enqueue Separation (Front-end vs Editor)")

    errors = []
    passed = True

    functions_file = theme_dir / "functions.php"
    if not functions_file.exists():
        print_error("functions.php not found")
        return False, ["functions.php not found"]

    functions_content = functions_file.read_text(encoding='utf-8')

    # Extract wp_enqueue_scripts function
    pattern = r"function\s+\w+_scripts\(\)\s*\{(.*?)\}\s*add_action\(\s*'wp_enqueue_scripts'"
    match = re.search(pattern, functions_content, re.DOTALL)

    if match:
        enqueue_scripts_content = match.group(1)

        print_info("Checking wp_enqueue_scripts function...")

        # Check for forbidden dependencies in front-end enqueue
        forbidden_deps = ['react', 'react-dom', 'wp-blocks', 'wp-element', 'jetpack']
        found_forbidden = []

        for dep in forbidden_deps:
            if dep in enqueue_scripts_content.lower():
                found_forbidden.append(dep)

        if found_forbidden:
            print_error(f"Found editor dependencies in wp_enqueue_scripts: {', '.join(found_forbidden)}")
            errors.append(f"wp_enqueue_scripts contains editor deps: {', '.join(found_forbidden)}")
            passed = False
        else:
            print_success("No editor dependencies in wp_enqueue_scripts")
    else:
        print_warning("Could not find wp_enqueue_scripts function")

    # Check for enqueue_block_editor_assets hook
    if 'enqueue_block_editor_assets' in functions_content:
        print_success("Has enqueue_block_editor_assets hook for editor scripts")
    else:
        print_warning("No enqueue_block_editor_assets hook (optional but recommended)")

    return passed, errors


def check_block_categories(theme_dir: Path) -> tuple[bool, list[str]]:
    """Check that block.json files use valid core categories."""
    print_header("Checking Block Categories")

    valid_categories = {'text', 'media', 'design', 'widgets', 'theme', 'embed'}
    invalid_categories = {'design_layout', 'layout', 'common', 'formatting'}

    errors = []
    passed = True

    blocks_dir = theme_dir / "blocks"

    if not blocks_dir.exists():
        print_info("No blocks directory found (optional)")
        return True, []

    print_info(f"Checking blocks in {blocks_dir}...")

    for block_dir in blocks_dir.iterdir():
        if not block_dir.is_dir():
            continue

        block_json_file = block_dir / "block.json"
        if not block_json_file.exists():
            continue

        try:
            with open(block_json_file, 'r') as f:
                block_data = json.load(f)

            block_name = block_data.get('name', block_dir.name)
            category = block_data.get('category')

            if not category:
                print_error(f"Block {block_name} missing category")
                errors.append(f"Block {block_name} missing category")
                passed = False
                continue

            if category in invalid_categories:
                print_error(f"Block {block_name} has invalid category: {category}")
                errors.append(f"Block {block_name} has invalid category: {category}")
                passed = False
            elif category in valid_categories:
                print_success(f"Block {block_name} has valid category: {category}")
            else:
                print_warning(f"Block {block_name} has unknown category: {category}")

        except Exception as e:
            print_error(f"Error reading {block_json_file}: {e}")
            errors.append(f"Error reading {block_json_file}: {e}")
            passed = False

    return passed, errors


def main():
    """Run smoke test by generating a theme and validating it."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}WPGen Theme Generator - Smoke Test{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

    # Generate a test theme
    with tempfile.TemporaryDirectory() as tmp_dir:
        print_info(f"Generating test theme in: {tmp_dir}\n")

        try:
            # Create generator
            generator = WordPressGenerator(output_dir=tmp_dir, safe_mode=True)

            # Generate theme with minimal requirements
            requirements = {
                'theme_name': 'wpgen-smoke-test',
                'theme_display_name': 'WPGen Smoke Test',
                'description': 'Smoke test theme generated by WPGen',
                'author': 'WPGen',
                'version': '1.0.0',
                'design_profile': 'minimal',
            }

            print_info("Running theme generator...")
            theme_path = generator.generate(requirements)
            theme_dir = Path(theme_path)

            print_success(f"Theme generated successfully at: {theme_path}\n")

        except Exception as e:
            print_error(f"Failed to generate theme: {e}")
            return 1

        # Run validation checks
        all_passed = True
        all_errors = []

        # 1. Check required hooks
        passed, errors = check_required_hooks(theme_dir)
        all_passed = all_passed and passed
        all_errors.extend(errors)

        # 2. Check mixed-content
        passed, errors = check_mixed_content(theme_dir)
        all_passed = all_passed and passed
        all_errors.extend(errors)

        # 3. Check enqueue separation
        passed, errors = check_enqueue_separation(theme_dir)
        all_passed = all_passed and passed
        all_errors.extend(errors)

        # 4. Check block categories
        passed, errors = check_block_categories(theme_dir)
        all_passed = all_passed and passed
        all_errors.extend(errors)

        # Print summary
        print_header("Smoke Test Summary")

        if all_passed:
            print_success("All checks passed! ✨")
            print_info("\nThe theme generator is working correctly and produces valid themes.")
            return 0
        else:
            print_error(f"Found {len(all_errors)} issue(s):")
            for error in all_errors:
                print_info(f"  • {error}")
            print_info("\nPlease fix the issues above before deploying.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
