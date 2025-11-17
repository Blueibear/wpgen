#!/usr/bin/env python3
"""Test script for bareword sanitizer.

This script tests the sanitize_barewords() function to ensure it correctly
quotes unquoted barewords in PHP arrays.
"""

import sys
import re
from pathlib import Path

# Add wpgen to path
sys.path.insert(0, str(Path(__file__).parent))

# Import sanitize_barewords function directly by loading the module
# This avoids triggering full wpgen initialization
def load_sanitize_barewords():
    """Load the sanitize_barewords function without triggering full imports."""
    php_validation_path = Path(__file__).parent / "wpgen" / "utils" / "php_validation.py"

    # Create a minimal mock logger to avoid import issues
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def debug(self, msg): pass
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")

    # Read and execute the sanitize_barewords function
    namespace = {
        're': re,
        'logger': MockLogger(),
    }

    with open(php_validation_path, 'r') as f:
        code = f.read()

    # Extract just the sanitize_barewords function
    func_start = code.find('def sanitize_barewords(')
    if func_start == -1:
        raise RuntimeError("sanitize_barewords function not found")

    # Find the end of the function (next function or class definition)
    func_end = code.find('\nclass ', func_start)
    if func_end == -1:
        func_end = code.find('\ndef ', func_start + 100)
    if func_end == -1:
        func_end = len(code)

    func_code = code[func_start:func_end]

    # Execute the function definition
    exec(func_code, namespace)

    return namespace['sanitize_barewords']

sanitize_barewords = load_sanitize_barewords()


def test_array_barewords():
    """Test sanitizing barewords in PHP arrays."""
    print("=" * 70)
    print("TEST 1: Sanitizing barewords in PHP arrays")
    print("=" * 70)

    malformed_code = """<?php
// This is malformed PHP that would cause fatal errors
$config = array(
    'height' => auto,
    'text-align' => center,
    'background-size' => cover,
    'layout' => full,
    'sidebar' => none,
    'enabled' => true,
    'width' => 100,
    'debug' => WP_DEBUG,
);
"""

    print("\nBEFORE sanitization:")
    print(malformed_code)

    sanitized, fixes = sanitize_barewords(malformed_code, "test.php")

    print("\nAFTER sanitization:")
    print(sanitized)

    print(f"\nFixes applied: {len(fixes)}")
    for fix in fixes:
        print(f"  ✓ {fix}")

    # Verify fixes
    expected_fixes = ['auto', 'center', 'cover', 'full', 'none']
    for expected in expected_fixes:
        if f"'{expected}'" in sanitized:
            print(f"  ✅ '{expected}' is now quoted")
        else:
            print(f"  ❌ '{expected}' was NOT quoted (FAIL)")
            return False

    # Verify true, 100, and WP_DEBUG remain unquoted
    if 'true' in sanitized and "'true'" not in sanitized:
        print("  ✅ 'true' remains unquoted (correct)")
    else:
        print("  ❌ 'true' was incorrectly quoted (FAIL)")
        return False

    if 'WP_DEBUG' in sanitized and "'WP_DEBUG'" not in sanitized:
        print("  ✅ 'WP_DEBUG' remains unquoted (correct)")
    else:
        print("  ❌ 'WP_DEBUG' was incorrectly quoted (FAIL)")
        return False

    return True


def test_function_args():
    """Test sanitizing barewords in function arguments."""
    print("\n" + "=" * 70)
    print("TEST 2: Sanitizing barewords in function arguments")
    print("=" * 70)

    malformed_code = """<?php
add_theme_support(woocommerce);
add_theme_support('wc-product-gallery-zoom');
register_sidebar(array(
    'name' => 'Sidebar',
    'id' => sidebar-1,
));
"""

    print("\nBEFORE sanitization:")
    print(malformed_code)

    sanitized, fixes = sanitize_barewords(malformed_code, "functions.php")

    print("\nAFTER sanitization:")
    print(sanitized)

    print(f"\nFixes applied: {len(fixes)}")
    for fix in fixes:
        print(f"  ✓ {fix}")

    # Verify woocommerce and sidebar-1 are now quoted
    if "'woocommerce'" in sanitized or '"woocommerce"' in sanitized:
        print("  ✅ 'woocommerce' is now quoted")
    else:
        print("  ❌ 'woocommerce' was NOT quoted (FAIL)")
        return False

    if "'sidebar-1'" in sanitized or '"sidebar-1"' in sanitized:
        print("  ✅ 'sidebar-1' is now quoted")
    else:
        print("  ❌ 'sidebar-1' was NOT quoted (FAIL)")
        return False

    return True


def test_complex_example():
    """Test a complex real-world example."""
    print("\n" + "=" * 70)
    print("TEST 3: Complex real-world example")
    print("=" * 70)

    malformed_code = """<?php
function theme_setup() {
    add_theme_support('post-thumbnails');

    $defaults = array(
        'flex-height' => true,
        'flex-width' => false,
        'header-text' => none,
        'default-text-color' => inherit,
        'wp-head-callback' => 'my_header_callback',
        'width' => 1920,
        'height' => auto,
    );

    add_theme_support('custom-header', $defaults);
}
"""

    print("\nBEFORE sanitization:")
    print(malformed_code)

    sanitized, fixes = sanitize_barewords(malformed_code, "functions.php")

    print("\nAFTER sanitization:")
    print(sanitized)

    print(f"\nFixes applied: {len(fixes)}")
    for fix in fixes:
        print(f"  ✓ {fix}")

    # Verify none, inherit, and auto are quoted
    # But true, false, and 1920 remain unquoted
    if "'none'" in sanitized:
        print("  ✅ 'none' is now quoted")
    else:
        print("  ❌ 'none' was NOT quoted (FAIL)")
        return False

    if "'inherit'" in sanitized:
        print("  ✅ 'inherit' is now quoted")
    else:
        print("  ❌ 'inherit' was NOT quoted (FAIL)")
        return False

    if "'auto'" in sanitized:
        print("  ✅ 'auto' is now quoted")
    else:
        print("  ❌ 'auto' was NOT quoted (FAIL)")
        return False

    if 'true' in sanitized and "'true'" not in sanitized:
        print("  ✅ 'true' remains unquoted (correct)")
    else:
        print("  ❌ 'true' handling incorrect (FAIL)")
        return False

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("BAREWORD SANITIZER TEST SUITE")
    print("=" * 70)

    results = []

    results.append(("Array barewords", test_array_barewords()))
    results.append(("Function arguments", test_function_args()))
    results.append(("Complex example", test_complex_example()))

    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Bareword sanitizer is working correctly!")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Bareword sanitizer needs fixes!")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
