"""Theme validation tool to diagnose WordPress crashes.

This module provides tools to validate an existing theme directory
and identify which files are causing WordPress to crash.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict
from .logger import get_logger


logger = get_logger(__name__)


def validate_theme_directory(theme_path: str) -> Dict[str, any]:
    """Validate all PHP files in a theme directory.

    Args:
        theme_path: Path to the theme directory

    Returns:
        Dictionary with validation results
    """
    theme_dir = Path(theme_path)

    if not theme_dir.exists():
        return {"error": f"Theme directory not found: {theme_path}"}

    if not theme_dir.is_dir():
        return {"error": f"Not a directory: {theme_path}"}

    results = {
        "theme_name": theme_dir.name,
        "total_files": 0,
        "php_files": 0,
        "valid_files": 0,
        "invalid_files": 0,
        "errors": [],
        "warnings": [],
    }

    # Required WordPress theme files
    required_files = ["style.css", "index.php"]
    recommended_files = ["functions.php", "header.php", "footer.php"]

    # Check required files
    for required_file in required_files:
        file_path = theme_dir / required_file
        if not file_path.exists():
            results["errors"].append(f"Missing required file: {required_file}")

    # Check recommended files
    for recommended_file in recommended_files:
        file_path = theme_dir / recommended_file
        if not file_path.exists():
            results["warnings"].append(f"Missing recommended file: {recommended_file}")

    # Validate all PHP files
    php_files = list(theme_dir.rglob("*.php"))
    results["php_files"] = len(php_files)

    for php_file in php_files:
        results["total_files"] += 1

        # Read file content
        try:
            with open(php_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            results["invalid_files"] += 1
            results["errors"].append(f"Cannot read {php_file.relative_to(theme_dir)}: {str(e)}")
            continue

        # Check for common issues
        relative_path = php_file.relative_to(theme_dir)

        # Issue 1: Missing PHP opening tag
        if not content.strip().startswith("<?php") and not content.strip().startswith("<!DOCTYPE"):
            results["warnings"].append(f"{relative_path}: Missing <?php opening tag")

        # Issue 2: Markdown code blocks
        if "```" in content:
            results["errors"].append(f"{relative_path}: Contains markdown code blocks (```)")
            results["invalid_files"] += 1
            continue

        # Issue 3: Explanatory text at the start (common LLM mistake)
        first_line = content.split("\n")[0].strip()
        if first_line and not first_line.startswith("<?php") and not first_line.startswith("<!DOCTYPE") and not first_line.startswith("/**"):
            if any(phrase in first_line.lower() for phrase in ["here's", "here is", "this is", "below is", "sure", "certainly"]):
                results["errors"].append(f"{relative_path}: Contains explanatory text before PHP code")
                results["invalid_files"] += 1
                continue

        # Issue 4: PHP syntax validation
        is_valid, error_msg = validate_php_syntax_file(str(php_file))
        if not is_valid:
            results["invalid_files"] += 1
            results["errors"].append(f"{relative_path}: PHP syntax error - {error_msg}")
        else:
            results["valid_files"] += 1

    return results


def validate_php_syntax_file(file_path: str) -> Tuple[bool, str]:
    """Validate PHP syntax of a file.

    Args:
        file_path: Path to PHP file

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if PHP is available
    try:
        result = subprocess.run(
            ["php", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return True, "PHP command not available"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True, "PHP command not available"

    # Run php -l to check syntax
    try:
        result = subprocess.run(
            ["php", "-l", file_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return True, ""
        else:
            error_msg = result.stderr or result.stdout
            # Extract just the error message, not the full path
            if "Parse error:" in error_msg:
                error_msg = error_msg.split("Parse error:")[1].split(" in ")[0].strip()
            return False, error_msg

    except Exception as e:
        return True, f"Validation failed: {str(e)}"


def print_validation_report(results: Dict[str, any]) -> None:
    """Print a formatted validation report.

    Args:
        results: Validation results dictionary
    """
    print("\n" + "="*70)
    print(f"WordPress Theme Validation Report: {results['theme_name']}")
    print("="*70)

    if "error" in results:
        print(f"\n❌ ERROR: {results['error']}")
        return

    # Summary
    print(f"\n📊 Summary:")
    print(f"   Total PHP files: {results['php_files']}")
    print(f"   Valid files: {results['valid_files']} ✅")
    print(f"   Invalid files: {results['invalid_files']} ❌")

    # Errors
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   • {error}")

    # Warnings
    if results['warnings']:
        print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
        for warning in results['warnings']:
            print(f"   • {warning}")

    # Conclusion
    print("\n" + "="*70)
    if results['invalid_files'] == 0 and not results['errors']:
        print("✅ Theme validation passed! No critical errors found.")
    else:
        print("❌ Theme has critical errors that will cause WordPress to crash.")
        print("   Please fix the errors listed above before activating the theme.")

    print("="*70 + "\n")


def validate_php_syntax_file(file_path: str) -> Tuple[bool, str]:
    """Validate PHP syntax of a file.

    Args:
        file_path: Path to PHP file

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if PHP is available
    try:
        result = subprocess.run(
            ["php", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return True, "PHP command not available"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True, "PHP command not available"

    # Run php -l to check syntax
    try:
        result = subprocess.run(
            ["php", "-l", file_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return True, ""
        else:
            error_msg = result.stderr or result.stdout
            # Extract just the error message, not the full path
            if "Parse error:" in error_msg:
                error_msg = error_msg.split("Parse error:")[1].split(" in ")[0].strip()
            return False, error_msg

    except Exception as e:
        return True, f"Validation failed: {str(e)}"
