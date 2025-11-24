"""Runtime dependency checks for WPGen.

This module provides startup checks for external dependencies like PHP.
"""

import subprocess
import sys
from typing import Optional

from .logger import get_logger

logger = get_logger(__name__)


def check_php_available(php_path: str = "php") -> tuple[bool, Optional[str]]:
    """Check if PHP is available on the system.

    Args:
        php_path: Path to PHP binary (default: "php")

    Returns:
        Tuple of (is_available, version_string)
    """
    try:
        result = subprocess.run(
            [php_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.splitlines()[0] if result.stdout else "unknown"
            logger.debug(f"PHP is available: {version}")
            return True, version
        logger.warning(f"PHP command failed with code {result.returncode}")
        return False, None
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError) as e:
        logger.warning(f"PHP is not available: {e}")
        return False, None


def check_dependencies(strict: bool = False) -> dict[str, bool]:
    """Check all runtime dependencies.

    Args:
        strict: If True, exit on missing dependencies

    Returns:
        Dictionary of dependency status
    """
    results = {}

    # Check PHP
    php_available, php_version = check_php_available()
    results["php"] = php_available

    if not php_available:
        print("⚠ Warning: PHP is not installed or not in PATH", file=sys.stderr)
        print("  - PHP validation will be skipped for generated themes", file=sys.stderr)
        print("  - This may allow broken PHP code to be generated", file=sys.stderr)
        print("  - Install PHP to enable validation:", file=sys.stderr)
        print("    Ubuntu/Debian: sudo apt-get install php-cli", file=sys.stderr)
        print("    macOS: brew install php", file=sys.stderr)
        print("    Windows: https://windows.php.net/download/", file=sys.stderr)

        if strict:
            print("\n❌ Strict mode: PHP is required but not found", file=sys.stderr)
            sys.exit(1)
    else:
        logger.info(f"✓ PHP is available: {php_version}")

    return results


def warn_missing_dependencies():
    """Display warnings for missing optional dependencies."""
    results = check_dependencies(strict=False)

    missing = [dep for dep, available in results.items() if not available]

    if missing:
        logger.warning(f"Missing optional dependencies: {', '.join(missing)}")
        print("\n⚠ Some optional dependencies are missing.", file=sys.stderr)
        print("  The tool will work but with reduced functionality.", file=sys.stderr)
        print("  Run 'wpgen check-deps' for installation instructions.\n", file=sys.stderr)
