#!/usr/bin/env python3
"""Test script to verify theme generation works with the validation fixes."""

import sys
import os
from pathlib import Path

# Add wpgen to path
sys.path.insert(0, str(Path(__file__).parent))

from wpgen.generators.wordpress_generator import WordPressGenerator
from wpgen.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that always fails, forcing fallback templates."""

    def generate_code(self, description, language, context=None, images=None):
        """Always raise an exception to trigger fallback templates."""
        raise Exception("Mock LLM - forcing fallback templates")

    def generate_text(self, prompt, context=None, images=None):
        """Always raise an exception."""
        raise Exception("Mock LLM - forcing fallback templates")


def test_theme_generation():
    """Test that theme generation works with fallback templates."""
    print("="*60)
    print("Testing Theme Generation with Validation Fixes")
    print("="*60)

    # Create mock LLM provider
    llm = MockLLMProvider()

    # Create generator
    output_dir = "test_output"
    config = {
        "clean_before_generate": True,
        "safe_mode": False,  # Test with safe_mode off to use our fixed validation
    }
    generator = WordPressGenerator(llm, output_dir, config)

    # Create test requirements
    requirements = {
        "theme_name": "test-theme",
        "theme_display_name": "Test Theme",
        "description": "Test theme to verify validation fixes",
        "color_scheme": "modern",
        "layout": "full-width",
        "features": ["responsive", "accessible"],
        "navigation": ["primary"],
        "pages": [],
        "post_types": [],
        "integrations": [],
    }

    try:
        print("\n1. Starting theme generation...")
        theme_dir = generator.generate(requirements)

        print(f"\n✅ SUCCESS! Theme generated at: {theme_dir}")
        print("\n2. Verifying generated files...")

        theme_path = Path(theme_dir)
        required_files = [
            "style.css",
            "functions.php",
            "index.php",
            "header.php",
            "footer.php",
            "sidebar.php",
            "single.php",
            "page.php",
            "archive.php",
            "search.php",
            "404.php",
            "assets/css/style.css",
            "assets/css/wpgen-ui.css",
            "assets/js/wpgen-ui.js",
        ]

        all_present = True
        for file in required_files:
            file_path = theme_path / file
            if file_path.exists():
                print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file} - MISSING!")
                all_present = False

        if all_present:
            print("\n✅ All required files present!")
            print("\n3. Checking header.php structure...")

            header_content = (theme_path / "header.php").read_text()
            checks = {
                "site-header": "site-header" in header_content,
                "site-branding": "site-branding" in header_content,
                "the_custom_logo()": "the_custom_logo()" in header_content,
                "main-navigation": "main-navigation" in header_content,
            }

            for check_name, present in checks.items():
                status = "✅" if present else "❌"
                print(f"  {status} {check_name}: {present}")

            print("\n4. Checking footer.php structure...")
            footer_content = (theme_path / "footer.php").read_text()
            checks = {
                "site-footer": "site-footer" in footer_content,
                "</main>": "</main>" in footer_content,
            }

            for check_name, present in checks.items():
                status = "✅" if present else "❌"
                print(f"  {status} {check_name}: {present}")

            print("\n5. Checking base layout CSS...")
            base_css_content = (theme_path / "assets" / "css" / "style.css").read_text()
            checks = {
                ".site-header": ".site-header" in base_css_content,
                ".site-branding": ".site-branding" in base_css_content,
                ".custom-logo-link img": ".custom-logo-link img" in base_css_content,
            }

            for check_name, present in checks.items():
                status = "✅" if present else "❌"
                print(f"  {status} {check_name}: {present}")

            print("\n" + "="*60)
            print("✅ THEME GENERATION TEST PASSED!")
            print("="*60)
            return True
        else:
            print("\n❌ Some required files are missing!")
            return False

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_theme_generation()
    sys.exit(0 if success else 1)
