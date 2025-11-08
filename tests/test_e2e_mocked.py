"""End-to-end smoke test with mock provider.

Tests the full theme generation flow without network dependencies.
"""

from pathlib import Path

import pytest

from wpgen.llm.mock_provider import MockLLMProvider


def test_mock_provider_analyze_prompt():
    """Test mock provider can analyze prompts deterministically."""
    provider = MockLLMProvider()
    analysis = provider.analyze_prompt("Generate a basic blog theme")

    assert "theme_name" in analysis
    assert "description" in analysis
    assert "features" in analysis
    assert isinstance(analysis["features"], list)
    assert "files" in analysis
    assert isinstance(analysis["files"], list)


def test_mock_provider_generate_code():
    """Test mock provider can generate code for different file types."""
    provider = MockLLMProvider()

    # Test style.css generation
    style_css = provider.generate_code(
        description="Main stylesheet",
        file_type="style.css",
        context={"theme_name": "test-theme"},
    )
    assert "Theme Name:" in style_css
    assert "test-theme" in style_css.lower() or "Test Theme" in style_css

    # Test functions.php generation
    functions_php = provider.generate_code(
        description="Theme functions", file_type="functions.php"
    )
    assert "<?php" in functions_php
    assert "function" in functions_php

    # Test index.php generation
    index_php = provider.generate_code(description="Main template", file_type="index.php")
    assert "<?php" in index_php
    assert "get_header" in index_php or "get_footer" in index_php


def test_mocked_end_to_end(tmp_path: Path):
    """Test complete theme generation flow with mock provider."""
    provider = MockLLMProvider()

    # Step 1: Analyze prompt
    analysis = provider.analyze_prompt("Generate a basic blog theme")
    assert analysis["theme_name"]

    # Step 2: Generate files based on analysis
    theme_name = analysis["theme_name"]
    files = {}

    for file_name in analysis["files"]:
        if file_name.endswith(".css"):
            file_type = "style.css"
        elif file_name.endswith(".php"):
            file_type = file_name
        else:
            continue

        content = provider.generate_code(
            description=f"Generate {file_name}",
            file_type=file_type,
            context={"theme_name": theme_name},
        )
        files[file_name] = content

    # Step 3: Write files to output directory
    outdir = tmp_path / theme_name
    outdir.mkdir()

    for name, content in files.items():
        (outdir / name).write_text(content, encoding="utf-8")

    # Step 4: Verify required files exist and contain expected content
    style = (outdir / "style.css").read_text(encoding="utf-8")
    assert "Theme Name:" in style

    functions = (outdir / "functions.php").read_text(encoding="utf-8")
    assert "<?php" in functions

    index = (outdir / "index.php").read_text(encoding="utf-8")
    assert "<?php" in index


def test_mock_provider_multimodal():
    """Test mock provider handles multimodal inputs."""
    provider = MockLLMProvider()

    # Test with images
    mock_images = [
        {"data": "base64data", "mime_type": "image/png", "name": "mockup.png"}
    ]

    analysis = provider.analyze_prompt_multimodal(
        prompt="Create theme based on this design",
        images=mock_images,
        additional_context="Professional business theme",
    )

    assert "theme_name" in analysis
    assert "images_processed" in analysis
    assert analysis["images_processed"] == 1
    assert "additional_context" in analysis


def test_mock_provider_image_analysis():
    """Test mock provider image analysis."""
    provider = MockLLMProvider()

    result = provider.analyze_image(
        image_data={"data": "base64", "mime_type": "image/png", "name": "test.png"},
        prompt="What colors are in this image?",
    )

    assert "analysis" in result
    assert "colors" in result


def test_mock_provider_validate_api_key():
    """Test mock provider API key validation always succeeds."""
    provider = MockLLMProvider()
    assert provider.validate_api_key() is True


@pytest.mark.integration
def test_integration_placeholder():
    """Placeholder for integration tests requiring network.

    This test is marked as 'integration' and skipped by default.
    Run with: pytest -m integration
    """
    pytest.skip("Integration tests require network and real API keys")
