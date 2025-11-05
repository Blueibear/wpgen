"""End-to-end test for theme generation service (mocked)."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from wpgen.service import (
    GenerationRequest,
    GenerationResult,
    ThemeGenerationService,
)


@pytest.fixture
def mock_config():
    """Fixture providing test configuration."""
    return {
        "llm": {
            "provider": "openai",
            "openai": {
                "model": "gpt-4-turbo",
                "max_tokens": 4096,
            }
        },
        "output": {
            "output_dir": "output"
        },
        "wordpress": {
            "theme_prefix": "wpgen",
            "author": "Test"
        },
        "validation": {
            "strict": False
        }
    }


@pytest.fixture
def mock_llm_provider():
    """Fixture providing a mock LLM provider."""
    provider = MagicMock()

    # Mock generate method to return deterministic response
    def mock_generate(prompt, **kwargs):
        return {
            "theme_name": "test-theme",
            "theme_display_name": "Test Theme",
            "description": "A test WordPress theme",
            "features": ["responsive", "dark-mode"],
            "pages": ["home", "about", "contact"],
            "color_scheme": ["#000000", "#FFFFFF"],
        }

    provider.generate.side_effect = mock_generate
    return provider


@pytest.fixture
def minimal_theme_structure(tmp_path):
    """Create a minimal valid theme structure."""
    theme_dir = tmp_path / "test-theme"
    theme_dir.mkdir()

    # Create required files
    (theme_dir / "style.css").write_text("""
/*
Theme Name: Test Theme
Author: Test
Description: Test theme
Version: 1.0.0
*/
""")

    (theme_dir / "index.php").write_text("<?php\nget_header();\nget_footer();\n?>")
    (theme_dir / "functions.php").write_text("<?php\n// Theme functions\n?>")
    (theme_dir / "header.php").write_text("<?php\n?>\n<header></header>")
    (theme_dir / "footer.php").write_text("<footer></footer>\n<?php\n?>")

    return theme_dir


def test_service_generate_theme_success(mock_config, mock_llm_provider, minimal_theme_structure, tmp_path):
    """Test successful theme generation through service."""
    # Update config to use temp directory
    mock_config["output"]["output_dir"] = str(tmp_path)

    service = ThemeGenerationService(mock_config)

    request = GenerationRequest(
        prompt="Create a minimal blog theme",
        strict_validation=False,
    )

    # Mock the necessary components
    with patch("wpgen.service.get_llm_provider") as mock_get_llm, \
         patch("wpgen.service.PromptParser") as MockParser, \
         patch("wpgen.service.WordPressGenerator") as MockGenerator, \
         patch("wpgen.service.CodeValidator") as MockCodeValidator, \
         patch("wpgen.service.ThemeValidator") as MockThemeValidator:

        # Setup mocks
        mock_get_llm.return_value = mock_llm_provider

        mock_parser = MockParser.return_value
        mock_parser.parse.return_value = {
            "theme_name": "test-theme",
            "theme_display_name": "Test Theme",
            "description": "A test theme",
            "features": ["responsive"],
        }

        mock_generator = MockGenerator.return_value
        mock_generator.generate.return_value = minimal_theme_structure

        # Mock validators to pass
        mock_code_val = MockCodeValidator.return_value
        mock_code_val.validate_directory.return_value = {
            "errors": [],
            "warnings": [],
        }

        mock_theme_val = MockThemeValidator.return_value
        mock_theme_val.validate.return_value = {
            "errors": [],
            "warnings": [],
            "valid": True,
        }

        # Execute
        result = service.generate_theme(request)

        # Assertions
        assert isinstance(result, GenerationResult)
        assert result.success is True
        assert result.theme_name == "test-theme"
        assert result.theme_display_name == "Test Theme"
        assert len(result.validation_errors) == 0
        assert len(result.validation_warnings) == 0


def test_service_generate_theme_validation_error_strict_mode(mock_config, mock_llm_provider, minimal_theme_structure, tmp_path):
    """Test theme generation fails in strict mode with validation warnings."""
    mock_config["output"]["output_dir"] = str(tmp_path)

    service = ThemeGenerationService(mock_config)

    request = GenerationRequest(
        prompt="Create a theme",
        strict_validation=True,
    )

    with patch("wpgen.service.get_llm_provider") as mock_get_llm, \
         patch("wpgen.service.PromptParser") as MockParser, \
         patch("wpgen.service.WordPressGenerator") as MockGenerator, \
         patch("wpgen.service.CodeValidator") as MockCodeValidator, \
         patch("wpgen.service.ThemeValidator") as MockThemeValidator:

        mock_get_llm.return_value = mock_llm_provider

        mock_parser = MockParser.return_value
        mock_parser.parse.return_value = {
            "theme_name": "test-theme",
            "theme_display_name": "Test Theme",
            "description": "Test",
            "features": [],
        }

        mock_generator = MockGenerator.return_value
        mock_generator.generate.return_value = minimal_theme_structure

        # Mock validators to return warnings
        mock_code_val = MockCodeValidator.return_value
        mock_code_val.validate_directory.return_value = {
            "errors": [],
            "warnings": ["PHP not available for validation"],
        }

        mock_theme_val = MockThemeValidator.return_value
        mock_theme_val.validate.return_value = {
            "errors": [],
            "warnings": ["Missing recommended file: sidebar.php"],
            "valid": True,
        }

        # Execute
        result = service.generate_theme(request)

        # In strict mode, warnings should cause failure
        assert result.success is False
        assert "strict mode" in result.error.lower()
        assert len(result.validation_warnings) > 0


def test_service_generate_theme_with_github_push(mock_config, mock_llm_provider, minimal_theme_structure, tmp_path, monkeypatch):
    """Test theme generation with GitHub push."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
    mock_config["output"]["output_dir"] = str(tmp_path)

    service = ThemeGenerationService(mock_config)

    request = GenerationRequest(
        prompt="Create a theme",
        push_to_github=True,
        github_repo_name="test-repo",
        strict_validation=False,
    )

    with patch("wpgen.service.get_llm_provider") as mock_get_llm, \
         patch("wpgen.service.PromptParser") as MockParser, \
         patch("wpgen.service.WordPressGenerator") as MockGenerator, \
         patch("wpgen.service.GitHubIntegration") as MockGitHub, \
         patch("wpgen.service.CodeValidator") as MockCodeValidator, \
         patch("wpgen.service.ThemeValidator") as MockThemeValidator:

        mock_get_llm.return_value = mock_llm_provider

        mock_parser = MockParser.return_value
        mock_parser.parse.return_value = {
            "theme_name": "test-theme",
            "theme_display_name": "Test Theme",
            "description": "Test",
            "features": [],
        }

        mock_generator = MockGenerator.return_value
        mock_generator.generate.return_value = minimal_theme_structure

        # Mock validators
        mock_code_val = MockCodeValidator.return_value
        mock_code_val.validate_directory.return_value = {"errors": [], "warnings": []}

        mock_theme_val = MockThemeValidator.return_value
        mock_theme_val.validate.return_value = {"errors": [], "warnings": [], "valid": True}

        # Mock GitHub
        mock_github = MockGitHub.return_value
        mock_github.push_to_github.return_value = "https://github.com/user/test-repo"

        # Execute
        result = service.generate_theme(request)

        # Assertions
        assert result.success is True
        assert result.github_url == "https://github.com/user/test-repo"
        mock_github.push_to_github.assert_called_once()


def test_service_handles_exception_gracefully(mock_config):
    """Test service handles exceptions and returns error result."""
    service = ThemeGenerationService(mock_config)

    request = GenerationRequest(
        prompt="Create a theme",
    )

    with patch("wpgen.service.get_llm_provider") as mock_get_llm:
        mock_get_llm.side_effect = Exception("LLM initialization failed")

        result = service.generate_theme(request)

        assert result.success is False
        assert result.error is not None
        assert "LLM initialization failed" in result.error
