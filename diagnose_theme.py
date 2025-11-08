#!/usr/bin/env python3
"""Diagnostic script to examine a generated WordPress theme.

This script provides detailed information about a theme to help
diagnose WordPress crashes that aren't caught by syntax validation.
"""

import sys
from pathlib import Path

# Fix Windows console encoding for UTF-8 output
USE_EMOJI = True
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        # If UTF-8 reconfiguration fails, disable emojis
        USE_EMOJI = False


def safe_print(text: str = ""):
    """Print text with emoji fallback for Windows."""
    if not USE_EMOJI:
        # Remove emojis for Windows terminals that don't support UTF-8
        emoji_map = {
            '📁': '[FILES]',
            '📋': '[REQUIRED]',
            '📝': '[RECOMMENDED]',
            '🎨': '[STYLE]',
            '🔍': '[CHECKING]',
            '📄': '[FILE]',
            '💡': '[TIP]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
        }
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
    try:
        print(text)
    except UnicodeEncodeError:
        # Last resort: encode as ASCII, ignore errors
        print(text.encode('ascii', 'ignore').decode('ascii'))


def diagnose_theme(theme_path: str):
    """Diagnose a WordPress theme directory.

    Args:
        theme_path: Path to theme directory
    """
    theme_dir = Path(theme_path)

    if not theme_dir.exists():
        safe_print(f"❌ Theme directory not found: {theme_path}")
        sys.exit(1)

    safe_print("=" * 70)
    safe_print(f"WordPress Theme Diagnostic: {theme_dir.name}")
    safe_print("=" * 70)
    safe_print()

    # Check all files
    safe_print("📁 Theme Structure:")
    all_files = sorted(theme_dir.rglob("*"))
    for f in all_files:
        if f.is_file():
            rel_path = f.relative_to(theme_dir)
            size = f.stat().st_size
            safe_print(f"   {rel_path} ({size} bytes)")
    safe_print()

    # Check required files
    safe_print("📋 Required Files:")
    required = {
        "style.css": theme_dir / "style.css",
        "index.php": theme_dir / "index.php",
    }

    for name, path in required.items():
        if path.exists():
            safe_print(f"   ✅ {name}")
        else:
            safe_print(f"   ❌ {name} MISSING")
    safe_print()

    # Check recommended files
    safe_print("📝 Recommended Files:")
    recommended = {
        "functions.php": theme_dir / "functions.php",
        "header.php": theme_dir / "header.php",
        "footer.php": theme_dir / "footer.php",
        "sidebar.php": theme_dir / "sidebar.php",
        "single.php": theme_dir / "single.php",
        "page.php": theme_dir / "page.php",
    }

    for name, path in recommended.items():
        if path.exists():
            safe_print(f"   ✅ {name}")
        else:
            safe_print(f"   ⚠️  {name} missing")
    safe_print()

    # Check style.css header
    style_css = theme_dir / "style.css"
    if style_css.exists():
        safe_print("🎨 style.css Header:")
        with open(style_css, 'r', encoding='utf-8') as f:
            content = f.read(500)
            if "Theme Name:" in content:
                safe_print("   ✅ Has WordPress theme header")
            else:
                safe_print("   ❌ Missing WordPress theme header")
    safe_print()

    # Check for common issues in PHP files
    safe_print("🔍 Checking PHP Files for Common Issues:")
    php_files = list(theme_dir.rglob("*.php"))

    issues_found = []

    for php_file in php_files:
        rel_path = php_file.relative_to(theme_dir)
        try:
            with open(php_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for common issues
            if "```" in content:
                issues_found.append(f"{rel_path}: Contains markdown code blocks")

            if "<?php" not in content and "<!DOCTYPE" not in str(content[:200]):
                issues_found.append(f"{rel_path}: Missing PHP opening tag")

            # Check for short tags (deprecated)
            if content.strip().startswith("<?") and not content.strip().startswith("<?php"):
                issues_found.append(f"{rel_path}: Uses short PHP tags (deprecated)")

            # Check for closing PHP tags in functions.php (bad practice)
            if php_file.name == "functions.php" and "?>" in content:
                issues_found.append(
                    f"{rel_path}: functions.php contains closing ?> tag "
                    "(not recommended)"
                )

            # Check for wp_head() in header
            if php_file.name == "header.php":
                if "wp_head()" not in content:
                    issues_found.append(f"{rel_path}: Missing wp_head() call")

            # Check for wp_footer() in footer
            if php_file.name == "footer.php":
                if "wp_footer()" not in content:
                    issues_found.append(f"{rel_path}: Missing wp_footer() call")

            # Check for get_header/get_footer calls
            if php_file.name in ["index.php", "single.php", "page.php", "archive.php"]:
                if "get_header()" not in content:
                    issues_found.append(f"{rel_path}: Missing get_header() call")
                if "get_footer()" not in content:
                    issues_found.append(f"{rel_path}: Missing get_footer() call")

        except Exception as e:
            issues_found.append(f"{rel_path}: Error reading file - {e}")

    if issues_found:
        safe_print("   ⚠️  Issues Found:")
        for issue in issues_found:
            safe_print(f"      • {issue}")
    else:
        safe_print("   ✅ No common issues detected")
    safe_print()

    # Print first 50 lines of functions.php if it exists
    functions_php = theme_dir / "functions.php"
    if functions_php.exists():
        safe_print("📄 functions.php (first 50 lines):")
        safe_print("-" * 70)
        with open(functions_php, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:50]
            for i, line in enumerate(lines, 1):
                safe_print(f"{i:3d} | {line.rstrip()}")
        if len(lines) >= 50:
            safe_print("... (truncated)")
        safe_print("-" * 70)
    safe_print()

    safe_print("=" * 70)
    safe_print("Diagnostic Complete")
    safe_print()
    safe_print("💡 If WordPress is still crashing:")
    safe_print("   1. Check WordPress debug.log for the actual error")
    safe_print("   2. Try activating WordPress default theme (Twenty Twenty-Four)")
    safe_print("   3. Then try this theme again to see the specific error")
    safe_print("   4. Share the functions.php content above for analysis")
    safe_print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        safe_print("Usage: python diagnose_theme.py <theme-path>")
        safe_print("Example: python diagnose_theme.py output/my-theme")
        sys.exit(1)

    diagnose_theme(sys.argv[1])
