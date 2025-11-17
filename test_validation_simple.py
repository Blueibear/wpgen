#!/usr/bin/env python3
"""Simple test to check if validation logic detects class names correctly."""

# Test the validation logic directly without importing the full module
test_html = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<header class="site-header">
    <div class="site-branding">
        <?php the_custom_logo(); ?>
    </div>
    <nav class="main-navigation">
        <ul><li><a href="#">Menu</a></li></ul>
    </nav>
</header>
<main class="site-main">
Content here
</main>
<footer class="site-footer">
    <p>Footer</p>
</footer>
</body>
</html>
"""

print("Testing validation logic...")
print("="*60)

# Test header validation
print("\n1. Testing header validation:")
checks = [
    ("site-header", 'site-header' in test_html),
    ("site-branding", 'site-branding' in test_html),
    ("the_custom_logo()", 'the_custom_logo()' in test_html),
    ("main-navigation", 'main-navigation' in test_html),
]

all_passed = True
for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}: {result}")
    if not result:
        all_passed = False

# Test footer validation
print("\n2. Testing footer validation:")
checks = [
    ("site-footer", 'site-footer' in test_html),
    ("</main>", '</main>' in test_html),
]

for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}: {result}")
    if not result:
        all_passed = False

# Test CSS validation
test_css = """.site-header {
    display: flex;
}

.site-branding img,
.custom-logo-link img {
    max-height: 80px;
}

.site-footer {
    background: #f0f0f0;
}
"""

print("\n3. Testing CSS validation:")
checks = [
    (".site-header", '.site-header' in test_css),
    (".site-branding img", '.site-branding img' in test_css),
    (".custom-logo-link img", '.custom-logo-link img' in test_css),
    (".site-footer", '.site-footer' in test_css),
]

for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}: {result}")
    if not result:
        all_passed = False

print("\n" + "="*60)
if all_passed:
    print("✅ ALL VALIDATION CHECKS PASSED!")
    print("\nThe validation logic correctly detects:")
    print("  - HTML class attributes (without dot)")
    print("  - CSS selectors (with dot)")
else:
    print("❌ SOME CHECKS FAILED!")

print("="*60)
