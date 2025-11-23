"""Test that generated Gutenberg blocks use valid core categories."""

import json
import tempfile
from pathlib import Path

import pytest


# Valid WordPress core block categories
# https://developer.wordpress.org/block-editor/reference-guides/block-api/block-registration/#category
VALID_CORE_CATEGORIES = {
    'text',
    'media',
    'design',
    'widgets',
    'theme',
    'embed',
}

# Invalid categories that we've seen in the past
INVALID_CATEGORIES = {
    'design_layout',  # Should be 'design'
    'layout',         # Should be 'design'
    'common',         # Deprecated, use 'text' or 'design'
    'formatting',     # Deprecated, use 'text'
    'custom',         # Not a core category
}


def test_block_configs_use_valid_categories():
    """Test that block configurations in generator use valid core categories."""
    from wpgen.generators.wordpress_generator import WordPressGenerator

    # Read the block_configs from the _generate_gutenberg_blocks method
    # We need to check the hardcoded block configurations

    # Create a minimal generator instance
    with tempfile.TemporaryDirectory() as tmp_dir:
        # We'll directly check the block_configs dictionary in the source
        # by inspecting the method

        import inspect
        source = inspect.getsource(WordPressGenerator._generate_gutenberg_blocks)

        # Extract block_configs dictionary from source
        # Look for category values
        if 'block_configs' in source:
            # Find all category definitions
            import re
            categories = re.findall(r'"category":\s*"([^"]+)"', source)

            for category in categories:
                assert category in VALID_CORE_CATEGORIES, \
                    f"Invalid block category '{category}'. Must be one of: {VALID_CORE_CATEGORIES}"

                assert category not in INVALID_CATEGORIES, \
                    f"Deprecated/invalid category '{category}' found. Use one of: {VALID_CORE_CATEGORIES}"


def test_generated_block_json_has_valid_category():
    """Test that generated block.json files have valid categories."""
    import tempfile
    from pathlib import Path
    from unittest.mock import MagicMock

    with tempfile.TemporaryDirectory() as tmp_dir:
        theme_dir = Path(tmp_dir) / "test-theme"
        theme_dir.mkdir()

        # Generate blocks using the generator
        from wpgen.generators.wordpress_generator import WordPressGenerator

        # We'll test the actual block generation
        # Create a mock LLM provider (not needed for block generation)
        mock_llm = MagicMock()
        generator = WordPressGenerator(output_dir=tmp_dir, llm_provider=mock_llm)

        # Generate Gutenberg blocks
        blocks_to_generate = ['featured_products', 'lifestyle_image', 'promo_banner']
        generator._generate_gutenberg_blocks(theme_dir, blocks_to_generate)

        # Check each generated block.json
        blocks_dir = theme_dir / "blocks"

        if blocks_dir.exists():
            for block_name in blocks_to_generate:
                block_json_path = blocks_dir / block_name / "block.json"

                if block_json_path.exists():
                    with open(block_json_path, 'r') as f:
                        block_data = json.load(f)

                    category = block_data.get('category')

                    assert category, f"Block {block_name} missing category in block.json"
                    assert category in VALID_CORE_CATEGORIES, \
                        f"Block {block_name} has invalid category '{category}'. Must be one of: {VALID_CORE_CATEGORIES}"
                    assert category not in INVALID_CATEGORIES, \
                        f"Block {block_name} has deprecated category '{category}'"


def test_no_design_layout_category_in_codebase():
    """Test that the invalid 'design_layout' category doesn't appear anywhere."""
    from pathlib import Path
    import os

    # Get the wpgen directory
    wpgen_dir = Path(__file__).parent.parent / "wpgen"

    # Search for 'design_layout' in Python files
    found_in_files = []

    for py_file in wpgen_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')

            # Skip test files and documentation
            if 'test_' in py_file.name or 'test' in py_file.parts:
                continue

            if 'design_layout' in content:
                # Get line numbers where it appears
                lines = content.split('\n')
                line_numbers = [i + 1 for i, line in enumerate(lines) if 'design_layout' in line]
                found_in_files.append((str(py_file.relative_to(wpgen_dir.parent)), line_numbers))

        except Exception:
            continue

    if found_in_files:
        error_msg = "Found 'design_layout' (invalid category) in:\n"
        for file_path, line_nums in found_in_files:
            error_msg += f"  {file_path}: lines {line_nums}\n"
        pytest.fail(error_msg)


def test_category_mapping_if_exists():
    """Test that if a CATEGORY_MAP exists, it maps invalid categories to valid ones."""
    from pathlib import Path

    # Check if there's a category mapping in the generator
    wpgen_dir = Path(__file__).parent.parent / "wpgen"
    generator_file = wpgen_dir / "generators" / "wordpress_generator.py"

    if generator_file.exists():
        content = generator_file.read_text(encoding='utf-8')

        # If there's a CATEGORY_MAP, verify it maps to valid categories
        if 'CATEGORY_MAP' in content:
            import re

            # Extract the mapping
            mappings = re.findall(r"'(\w+)':\s*'(\w+)'", content)

            for invalid_cat, valid_cat in mappings:
                assert valid_cat in VALID_CORE_CATEGORIES, \
                    f"CATEGORY_MAP maps '{invalid_cat}' to invalid category '{valid_cat}'"


def test_block_registration_js_uses_valid_category():
    """Test that generated block registration JS uses valid categories."""
    import tempfile
    from pathlib import Path
    from unittest.mock import MagicMock

    with tempfile.TemporaryDirectory() as tmp_dir:
        theme_dir = Path(tmp_dir) / "test-theme"
        theme_dir.mkdir()

        # Generate blocks
        from wpgen.generators.wordpress_generator import WordPressGenerator

        # Create a mock LLM provider (not needed for block generation)
        mock_llm = MagicMock()
        generator = WordPressGenerator(output_dir=tmp_dir, llm_provider=mock_llm)
        blocks_to_generate = ['featured_products', 'lifestyle_image', 'promo_banner']
        generator._generate_gutenberg_blocks(theme_dir, blocks_to_generate)

        # Check generated index.js files for registerBlockType calls
        blocks_dir = theme_dir / "blocks"

        if blocks_dir.exists():
            for block_name in blocks_to_generate:
                index_js_path = blocks_dir / block_name / "index.js"

                if index_js_path.exists():
                    js_content = index_js_path.read_text(encoding='utf-8')

                    # Extract category from registerBlockType if present
                    import re
                    category_match = re.search(r"category:\s*['\"](\w+)['\"]", js_content)

                    if category_match:
                        category = category_match.group(1)
                        assert category in VALID_CORE_CATEGORIES, \
                            f"Block {block_name} JS has invalid category '{category}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
