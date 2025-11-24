#!/usr/bin/env python3
"""
PHP Lint Script for Generated Themes

This script runs php -l (lint) on all PHP files in a generated theme directory.
If PHP is not available on PATH, it prints a skip message and exits successfully.

Usage:
    python scripts/php_lint_generated.py /path/to/generated/theme

Exit codes:
    0 - All files passed lint or PHP not available (skip)
    1 - One or more files have PHP syntax errors
"""

import sys
import subprocess
import shutil
from pathlib import Path


def check_php_available() -> bool:
    """Check if php command is available on PATH.

    Returns:
        True if php is available, False otherwise
    """
    return shutil.which('php') is not None


def lint_php_file(file_path: Path) -> tuple[bool, str]:
    """Run php -l on a single PHP file.

    Args:
        file_path: Path to PHP file to lint

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ['php', '-l', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        # php -l returns 0 for valid syntax, non-zero for errors
        success = result.returncode == 0
        output = result.stdout + result.stderr

        return success, output

    except subprocess.TimeoutExpired:
        return False, f"Timeout while linting {file_path}"
    except Exception as e:
        return False, f"Error linting {file_path}: {str(e)}"


def lint_theme_directory(theme_dir: Path) -> dict:
    """Lint all PHP files in theme directory.

    Args:
        theme_dir: Path to theme directory

    Returns:
        Dictionary with results:
        {
            'total_files': int,
            'passed': int,
            'failed': int,
            'errors': list of dicts with {'file': str, 'output': str}
        }
    """
    results = {
        'total_files': 0,
        'passed': 0,
        'failed': 0,
        'errors': []
    }

    # Find all PHP files recursively
    php_files = list(theme_dir.rglob('*.php'))
    results['total_files'] = len(php_files)

    print(f"Found {len(php_files)} PHP file(s) to lint")
    print()

    for php_file in php_files:
        relative_path = php_file.relative_to(theme_dir)
        print(f"Linting {relative_path}...", end=' ')

        success, output = lint_php_file(php_file)

        if success:
            print("✓ OK")
            results['passed'] += 1
        else:
            print("✗ FAILED")
            results['failed'] += 1
            results['errors'].append({
                'file': str(relative_path),
                'output': output
            })

    return results


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/php_lint_generated.py /path/to/theme")
        sys.exit(1)

    theme_path = Path(sys.argv[1])

    if not theme_path.exists():
        print(f"Error: Theme directory does not exist: {theme_path}")
        sys.exit(1)

    if not theme_path.is_dir():
        print(f"Error: Not a directory: {theme_path}")
        sys.exit(1)

    # Check if PHP is available
    if not check_php_available():
        print("INFO: php not found on PATH - skipping PHP lint")
        print("To enable PHP linting, install PHP CLI and ensure it's on your PATH")
        sys.exit(0)  # Exit successfully (not a failure)

    print(f"PHP Lint Check for: {theme_path}")
    print(f"Using PHP: {shutil.which('php')}")
    print("=" * 60)
    print()

    # Lint all PHP files
    results = lint_theme_directory(theme_path)

    # Print summary
    print()
    print("=" * 60)
    print(f"SUMMARY: {results['passed']}/{results['total_files']} files passed")
    print()

    if results['failed'] > 0:
        print(f"✗ {results['failed']} file(s) FAILED lint check:")
        print()

        for error in results['errors']:
            print(f"  File: {error['file']}")
            print(f"  {error['output']}")
            print()

        sys.exit(1)
    else:
        print("✓ All PHP files passed lint check")
        sys.exit(0)


if __name__ == '__main__':
    main()
