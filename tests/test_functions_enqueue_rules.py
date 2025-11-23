"""Test that generated functions.php follows proper enqueue separation rules."""

import re

import pytest

from wpgen.utils.code_validator import get_fallback_functions_php


def test_no_editor_deps_in_wp_enqueue_scripts():
    """Test that wp_enqueue_scripts block doesn't contain editor dependencies."""
    functions_content = get_fallback_functions_php("test-theme")

    # Extract the wp_enqueue_scripts function
    # Find the function that's hooked to wp_enqueue_scripts
    pattern = r"function\s+\w+_scripts\(\)\s*\{(.*?)\}\s*add_action\(\s*'wp_enqueue_scripts'"
    match = re.search(pattern, functions_content, re.DOTALL)

    assert match, "Should find wp_enqueue_scripts function"

    enqueue_scripts_content = match.group(1)

    # Check that forbidden packages are NOT in wp_enqueue_scripts
    forbidden_deps = [
        'react',
        'react-dom',
        'wp-blocks',
        'wp-element',
        'wp-components',
        'wp-data',
        'wp-edit-post',
        'wp-editor',
        'jetpack',
    ]

    for dep in forbidden_deps:
        assert dep not in enqueue_scripts_content.lower(), \
            f"wp_enqueue_scripts should NOT contain '{dep}' dependency"


def test_editor_assets_uses_correct_hook():
    """Test that editor assets are enqueued using enqueue_block_editor_assets hook."""
    functions_content = get_fallback_functions_php("test-theme")

    # Check that enqueue_block_editor_assets hook exists
    assert "enqueue_block_editor_assets" in functions_content, \
        "Should have enqueue_block_editor_assets hook"

    # Check that there's a function hooked to it
    assert "add_action( 'enqueue_block_editor_assets'" in functions_content, \
        "Should have function hooked to enqueue_block_editor_assets"


def test_editor_assets_function_documents_proper_deps():
    """Test that editor assets function shows example of proper WordPress dependencies."""
    functions_content = get_fallback_functions_php("test-theme")

    # Extract the editor_assets function
    pattern = r"function\s+\w+_editor_assets\(\)\s*\{(.*?)\}"
    match = re.search(pattern, functions_content, re.DOTALL)

    assert match, "Should find editor_assets function"

    editor_assets_content = match.group(1)

    # Should reference proper WordPress editor dependencies (even if commented)
    assert 'wp-blocks' in editor_assets_content or 'wp-element' in editor_assets_content, \
        "Editor function should document WordPress dependencies"


def test_only_safe_scripts_in_frontend():
    """Test that only theme-specific scripts are in wp_enqueue_scripts, no external packages."""
    functions_content = get_fallback_functions_php("test-theme")

    # Extract the wp_enqueue_scripts function
    pattern = r"function\s+\w+_scripts\(\)\s*\{(.*?)\}\s*add_action\(\s*'wp_enqueue_scripts'"
    match = re.search(pattern, functions_content, re.DOTALL)

    assert match, "Should find wp_enqueue_scripts function"

    enqueue_scripts_content = match.group(1)

    # Find all wp_enqueue_script calls
    script_calls = re.findall(r"wp_enqueue_script\(\s*'([^']+)'", enqueue_scripts_content)

    # Only theme-specific scripts should be enqueued (no external packages)
    for script_handle in script_calls:
        # Should be theme-specific handles, not external package handles
        assert not script_handle.startswith('react'), f"Should not enqueue React: {script_handle}"
        assert not script_handle.startswith('wp-'), f"Should not enqueue WordPress packages: {script_handle}"
        assert not script_handle.startswith('jetpack'), f"Should not enqueue Jetpack: {script_handle}"


def test_uses_wordpress_url_helpers():
    """Test that enqueue calls use WordPress URL helpers instead of hardcoded paths."""
    functions_content = get_fallback_functions_php("test-theme")

    # Extract the wp_enqueue_scripts function
    pattern = r"function\s+\w+_scripts\(\)\s*\{(.*?)\}\s*add_action\(\s*'wp_enqueue_scripts'"
    match = re.search(pattern, functions_content, re.DOTALL)

    assert match, "Should find wp_enqueue_scripts function"

    enqueue_scripts_content = match.group(1)

    # Should use WordPress helpers
    assert "get_template_directory_uri()" in enqueue_scripts_content, \
        "Should use get_template_directory_uri() for assets"
    assert "get_stylesheet_uri()" in enqueue_scripts_content, \
        "Should use get_stylesheet_uri() for main stylesheet"


def test_scripts_load_in_footer():
    """Test that JavaScript is enqueued to load in footer for better performance."""
    functions_content = get_fallback_functions_php("test-theme")

    # Extract the wp_enqueue_scripts function
    pattern = r"function\s+\w+_scripts\(\)\s*\{(.*?)\}\s*add_action\(\s*'wp_enqueue_scripts'"
    match = re.search(pattern, functions_content, re.DOTALL)

    assert match, "Should find wp_enqueue_scripts function"

    enqueue_scripts_content = match.group(1)

    # Find all wp_enqueue_script calls and check they have 'true' for footer loading
    script_patterns = re.findall(
        r"wp_enqueue_script\([^)]+\)",
        enqueue_scripts_content
    )

    for script_call in script_patterns:
        # If it has a 5th parameter, it should be 'true' (load in footer)
        if script_call.count(',') >= 4:  # Has 5+ parameters
            assert 'true' in script_call, \
                f"Scripts should load in footer (5th param = true): {script_call}"


def test_no_customizer_preview_react():
    """Test that there's no customize_preview_init hook loading React/Gutenberg."""
    functions_content = get_fallback_functions_php("test-theme")

    # Check for customize_preview_init hook (if it exists)
    if 'customize_preview_init' in functions_content:
        # Extract that function
        pattern = r"function\s+\w+_customizer_preview\(\)\s*\{(.*?)\}"
        match = re.search(pattern, functions_content, re.DOTALL)

        if match:
            customizer_content = match.group(1)

            # Should not load React/Gutenberg in customizer preview
            forbidden = ['react', 'react-dom', 'wp-blocks', 'wp-element', 'jetpack']
            for dep in forbidden:
                assert dep not in customizer_content.lower(), \
                    f"Customizer preview should not load {dep}"


def test_enqueue_separation_is_documented():
    """Test that the importance of enqueue separation is documented in comments."""
    functions_content = get_fallback_functions_php("test-theme")

    # Should have documentation about NOT mixing editor deps with front-end
    content_lower = functions_content.lower()

    # Check for educational comments about the separation
    has_documentation = (
        'editor' in content_lower and (
            'only' in content_lower or
            'never' in content_lower or
            'important' in content_lower or
            'should not' in content_lower
        )
    )

    assert has_documentation, \
        "functions.php should document the importance of enqueue separation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
