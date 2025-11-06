"""Theme validation tool to diagnose WordPress crashes.

This module provides tools to validate an existing theme directory
and identify which files are causing WordPress to crash.
"""

import subprocess
from pathlib import Path
from typing import Dict, Tuple

from .logger import get_logger

logger = get_logger(__name__)


class ThemeValidator:
    """Theme validator with strict mode support."""

    def __init__(self, strict: bool = False, php_path: str = "php"):
        """Initialize theme validator.

        Args:
            strict: If True, fail on warnings. If False, only fail on errors.
            php_path: Path to PHP binary (default: "php")
        """
        self.strict = strict
        self.php_path = php_path
        self.php_available = self._check_php_available()

    def _check_php_available(self) -> bool:
        """Check if PHP is available on the system."""
        try:
            result = subprocess.run(
                [self.php_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.debug(f"PHP is available: {result.stdout.splitlines()[0]}")
                return True
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def validate(self, theme_path: str) -> Dict[str, any]:
        """Validate a WordPress theme directory.

        Args:
            theme_path: Path to the theme directory

        Returns:
            Dictionary with validation results
        """
        theme_dir = Path(theme_path)

        if not theme_dir.exists():
            return {"error": f"Theme directory not found: {theme_path}", "valid": False}

        if not theme_dir.is_dir():
            return {"error": f"Not a directory: {theme_path}", "valid": False}

        results = {
            "theme_name": theme_dir.name,
            "total_files": 0,
            "php_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "errors": [],
            "warnings": [],
            "valid": True,
        }

        # Required WordPress theme files
        required_files = ["style.css", "index.php"]
        recommended_files = ["functions.php", "header.php", "footer.php"]

        # Check required files
        for required_file in required_files:
            file_path = theme_dir / required_file
            if not file_path.exists():
                error_msg = f"Missing required file: {required_file}"
                results["errors"].append(error_msg)
                results["valid"] = False

        # Check recommended files
        for recommended_file in recommended_files:
            file_path = theme_dir / recommended_file
            if not file_path.exists():
                warning_msg = f"Missing recommended file: {recommended_file}"
                results["warnings"].append(warning_msg)

        # Check PHP availability for validation
        if not self.php_available:
            warning_msg = f"PHP binary not found at '{self.php_path}' - skipping syntax validation"
            if self.strict:
                logger.error(f"STRICT MODE: {warning_msg}")
                results["errors"].append(warning_msg)
                results["valid"] = False
            else:
                logger.warning(warning_msg)
                results["warnings"].append(warning_msg)
                # Don't fail validation if PHP is not available in non-strict mode
                return results

        # Validate all PHP files
        php_files = list(theme_dir.rglob("*.php"))
        results["php_files"] = len(php_files)

        for php_file in php_files:
            results["total_files"] += 1
            file_result = self._validate_php_file(php_file, theme_dir)

            if file_result.get("errors"):
                results["invalid_files"] += 1
                results["errors"].extend(file_result["errors"])
                results["valid"] = False
            else:
                results["valid_files"] += 1

            if file_result.get("warnings"):
                results["warnings"].extend(file_result["warnings"])

        # In strict mode, warnings make the overall result invalid
        if self.strict and results["warnings"]:
            results["valid"] = False
            logger.warning(f"STRICT MODE: Validation failed due to {len(results['warnings'])} warnings")

        return results

    def _validate_php_file(self, php_file: Path, theme_dir: Path) -> Dict[str, any]:
        """Validate a single PHP file.

        Args:
            php_file: Path to PHP file
            theme_dir: Path to theme directory (for relative paths)

        Returns:
            Dictionary with file validation results
        """
        result = {
            "file": str(php_file.relative_to(theme_dir)),
            "errors": [],
            "warnings": [],
        }

        # Read file content
        try:
            content = php_file.read_text(encoding="utf-8")
        except Exception as e:
            result["errors"].append(f"Cannot read file: {str(e)}")
            return result

        relative_path = php_file.relative_to(theme_dir)

        # Check for common issues
        # Issue 1: Missing PHP opening tag
        if not content.strip().startswith("<?php") and not content.strip().startswith("<!DOCTYPE"):
            result["warnings"].append(f"{relative_path}: Missing <?php opening tag")

        # Issue 2: Markdown code blocks
        if "```" in content:
            result["errors"].append(f"{relative_path}: Contains markdown code blocks (```)")
            return result

        # Issue 3: Explanatory text at the start (common LLM mistake)
        first_line = content.split("\n")[0].strip()
        if first_line and not first_line.startswith("<?php") and not first_line.startswith("<!DOCTYPE") and not first_line.startswith("/**"):
            if any(phrase in first_line.lower() for phrase in ["here's", "here is", "this is", "below is", "sure", "certainly"]):
                result["errors"].append(f"{relative_path}: Contains explanatory text before PHP code")
                return result

        # Issue 4: PHP syntax validation
        is_valid, error_msg = self._validate_php_syntax_file(str(php_file))
        if not is_valid:
            result["errors"].append(f"{relative_path}: PHP syntax error - {error_msg}")

        return result

    def _validate_php_syntax_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate PHP syntax of a file.

        Args:
            file_path: Path to PHP file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.php_available:
            return True, "PHP command not available"

        try:
            result = subprocess.run(
                [self.php_path, "-l", file_path],
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
    print("\n📊 Summary:")
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
