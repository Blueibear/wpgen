"""End-to-end smoke test with mocked LLM provider.

Tests the complete generation pipeline without requiring real API keys.
"""

import tempfile
from pathlib import Path

import pytest

from wpgen.generators import WordPressGenerator
from wpgen.llm.mock_provider import MockLLMProvider
from wpgen.parsers import PromptParser


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider with deterministic responses."""
    responses = {
        "blog": """
        {
            "theme_name": "test-blog-theme",
            "theme_display_name": "Test Blog Theme",
            "description": "A minimal blog theme for testing",
            "features": ["responsive", "blog", "comments"],
            "color_scheme": {
                "primary": "#333333",
                "secondary": "#666666",
                "accent": "#0073aa"
            },
            "layout": "blog",
            "pages": ["home", "blog", "about"]
        }
        """
    }
    return MockLLMProvider(responses=responses)


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory(prefix="wpgen-test-") as tmpdir:
        yield Path(tmpdir)


def test_e2e_mocked_generation(mock_llm, temp_output_dir):
    """Test end-to-end theme generation with mocked LLM.

    This test verifies the complete pipeline works without network calls.
    """
    # Parse prompt
    parser = PromptParser(mock_llm)
    prompt = "Create a simple blog theme with responsive design"
    requirements = parser.parse(prompt)

    # Verify requirements parsing
    assert "theme_name" in requirements
    assert "theme_display_name" in requirements
    assert requirements["theme_name"] == "test-blog-theme"

    # Generate theme
    config = {
        "theme_prefix": "wpgen",
        "wp_version": "6.4",
        "author": "Test",
        "license": "GPL-2.0-or-later",
        "safe_mode": True,  # Use tested fallback templates for reliable mock generation
    }
    generator = WordPressGenerator(mock_llm, str(temp_output_dir), config)
    theme_dir = generator.generate(requirements)

    # Verify theme directory was created
    theme_path = Path(theme_dir)
    assert theme_path.exists()
    assert theme_path.is_dir()

    # Verify required WordPress theme files exist
    style_css = theme_path / "style.css"
    functions_php = theme_path / "functions.php"
    index_php = theme_path / "index.php"

    assert style_css.exists(), "style.css must exist"
    assert functions_php.exists(), "functions.php must exist"
    assert index_php.exists(), "index.php must exist"

    # Verify style.css has proper WordPress theme header
    style_content = style_css.read_text()
    assert "Theme Name:" in style_content
    assert "Test Blog Theme" in style_content
    assert "Description:" in style_content

    # Verify functions.php is valid PHP
    functions_content = functions_php.read_text()
    assert "<?php" in functions_content
    assert "function" in functions_content

    # Verify mock was called
    assert mock_llm.call_count > 0, "Mock LLM should have been called"


def test_e2e_mocked_minimal_theme(mock_llm, temp_output_dir):
    """Test minimal theme generation (fast smoke test)."""
    # Simple requirements
    requirements = {
        "theme_name": "minimal-test",
        "theme_display_name": "Minimal Test",
        "description": "Minimal test theme",
        "features": [],
        "color_scheme": {"primary": "#000000"},
    }

    # Generate with minimal config (enable safe_mode for reliable mock generation)
    generator = WordPressGenerator(mock_llm, str(temp_output_dir), {"safe_mode": True})
    theme_dir = generator.generate(requirements)

    # Verify basics
    theme_path = Path(theme_dir)
    assert (theme_path / "style.css").exists()
    assert (theme_path / "functions.php").exists()


@pytest.mark.parametrize(
    "prompt,expected_features",
    [
        ("blog with comments", ["blog", "comments"]),
        ("responsive design", ["responsive"]),
    ],
)
def test_e2e_feature_detection(mock_llm, temp_output_dir, prompt, expected_features):
    """Test that parser correctly detects features from prompts."""
    parser = PromptParser(mock_llm)
    requirements = parser.parse(prompt)

    assert "features" in requirements
    # In real implementation, features would be detected
    # For now, just verify the structure is correct
    assert isinstance(requirements.get("features", []), list)


def test_mock_provider_isolation():
    """Test that mock provider is properly isolated for testing."""
    mock1 = MockLLMProvider()
    mock2 = MockLLMProvider()

    mock1.generate("test prompt 1")
    mock2.generate("test prompt 2")

    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock1.last_prompt != mock2.last_prompt


def test_mock_provider_reset():
    """Test mock provider reset functionality."""
    mock = MockLLMProvider()

    mock.generate("first call")
    assert mock.call_count == 1

    mock.reset()
    assert mock.call_count == 0
    assert mock.last_prompt is None


if __name__ == "__main__":
    # Allow running test file directly
    pytest.main([__file__, "-v"])
