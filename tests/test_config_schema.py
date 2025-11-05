"""Tests for configuration schema validation."""

import os
import pytest
import yaml
from pathlib import Path
from wpgen.config_schema import (
    load_and_validate_config,
    WPGenConfig,
    LLMProviderEnum,
    get_redacted_config_summary,
)


def test_load_valid_config(tmp_path):
    """Test loading a valid config file."""
    config_file = tmp_path / "config.yaml"
    config_data = {
        "llm": {
            "provider": "openai",
            "openai": {
                "model": "gpt-4-turbo",
                "max_tokens": 4096,
            }
        },
        "output": {
            "output_dir": "output"
        }
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_and_validate_config(str(config_file))

    assert config.llm.provider == LLMProviderEnum.OPENAI
    assert config.llm.openai.model == "gpt-4-turbo"
    assert config.output.output_dir == "output"


def test_load_missing_config():
    """Test loading a missing config file returns defaults."""
    config = load_and_validate_config("nonexistent.yaml")

    assert isinstance(config, WPGenConfig)
    assert config.llm.provider == LLMProviderEnum.OPENAI


def test_invalid_provider():
    """Test invalid provider raises error."""
    with pytest.raises(ValueError, match="provider"):
        WPGenConfig(llm={"provider": "invalid_provider"})


def test_missing_provider_config(tmp_path):
    """Test selecting provider without configuration raises error."""
    config_file = tmp_path / "config.yaml"
    config_data = {
        "llm": {
            "provider": "local-ollama",
            # No local-ollama configuration
        }
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ValueError, match="not configured"):
        load_and_validate_config(str(config_file))


def test_env_override_provider(monkeypatch, tmp_path):
    """Test environment variable overrides provider."""
    config_file = tmp_path / "config.yaml"
    config_data = {
        "llm": {
            "provider": "openai",
        }
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setenv("WPGEN_LLM_PROVIDER", "anthropic")
    config = load_and_validate_config(str(config_file))

    assert config.llm.provider == LLMProviderEnum.ANTHROPIC


def test_env_override_openai_model(monkeypatch, tmp_path):
    """Test environment variable overrides OpenAI model."""
    config_file = tmp_path / "config.yaml"
    config_data = {
        "llm": {
            "provider": "openai",
            "openai": {
                "model": "gpt-4-turbo"
            }
        }
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setenv("WPGEN_OPENAI_MODEL", "gpt-4o")
    config = load_and_validate_config(str(config_file))

    assert config.llm.openai.model == "gpt-4o"


def test_env_override_anthropic_model(monkeypatch, tmp_path):
    """Test environment variable overrides Anthropic model."""
    config_file = tmp_path / "config.yaml"
    config_data = {
        "llm": {
            "provider": "anthropic",
            "anthropic": {
                "model": "claude-3-5-sonnet-20241022"
            }
        }
    }

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setenv("WPGEN_ANTHROPIC_MODEL", "claude-3-opus-20240229")
    config = load_and_validate_config(str(config_file))

    assert config.llm.anthropic.model == "claude-3-opus-20240229"


def test_invalid_log_level():
    """Test invalid log level raises error."""
    with pytest.raises(ValueError, match="log level"):
        WPGenConfig(logging={"level": "INVALID"})


def test_invalid_theme_type():
    """Test invalid theme type raises error."""
    with pytest.raises(ValueError, match="theme_type"):
        WPGenConfig(wordpress={"theme_type": "invalid"})


def test_wordpress_api_credentials_validation():
    """Test WordPress API credentials validation."""
    with pytest.raises(ValueError, match="credentials are missing"):
        WPGenConfig(wordpress_api={
            "enabled": True,
            "site_url": "https://example.com",
            # Missing username and password
        })


def test_redacted_config_summary():
    """Test configuration summary redacts secrets."""
    config = WPGenConfig(
        llm={
            "provider": "openai",
            "openai": {
                "model": "gpt-4-turbo",
                "api_key": "sk-secret123456789"
            }
        },
        github={
            "token": "ghp_secrettoken123"
        }
    )

    summary = get_redacted_config_summary(config)

    assert summary["llm"]["provider"] == "openai"
    assert summary["llm"]["model"] == "gpt-4-turbo"
    assert summary["llm"]["api_key_set"] is True
    assert "sk-secret" not in str(summary)

    assert summary["github"]["token_set"] is True
    assert "ghp_secret" not in str(summary)


def test_validation_strict_mode():
    """Test validation strict mode configuration."""
    config = WPGenConfig(validation={"strict": True})
    assert config.validation.strict is True

    config2 = WPGenConfig(validation={"strict": False})
    assert config2.validation.strict is False
