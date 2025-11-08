"""Configuration schema validation for wpgen.

This module provides Pydantic models for validating config.yaml with clear error messages.
Supports environment variable overrides for key settings.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .utils.logger import get_logger

logger = get_logger(__name__)


class LLMProviderEnum(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_LMSTUDIO = "local-lmstudio"
    LOCAL_OLLAMA = "local-ollama"


class OpenAIConfig(BaseModel):
    """OpenAI provider configuration."""
    model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model name")
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    api_key: Optional[str] = Field(default=None, description="API key (from env OPENAI_API_KEY)")

    @model_validator(mode='after')
    def load_from_env(self):
        """Load API key from environment if not set."""
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        return self


class AnthropicConfig(BaseModel):
    """Anthropic provider configuration."""
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Anthropic model name")
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    api_key: Optional[str] = Field(default=None, description="API key (from env ANTHROPIC_API_KEY)")

    @model_validator(mode='after')
    def load_from_env(self):
        """Load API key from environment if not set."""
        if not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        return self


class LocalLLMConfig(BaseModel):
    """Local LLM provider configuration (LM Studio or Ollama)."""
    brains_model: str = Field(..., description="Brains model name for text-only reasoning")
    brains_base_url: str = Field(..., description="Brains model base URL")
    vision_model: Optional[str] = Field(
        default=None, description="Vision model name for image analysis"
    )
    vision_base_url: Optional[str] = Field(default=None, description="Vision model base URL")
    max_tokens: int = Field(default=2048, ge=1, le=128000)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    timeout: int = Field(default=60, ge=10, le=600, description="Request timeout in seconds")


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: LLMProviderEnum = Field(default=LLMProviderEnum.OPENAI)
    openai: Optional[OpenAIConfig] = Field(default_factory=OpenAIConfig)
    anthropic: Optional[AnthropicConfig] = Field(default_factory=AnthropicConfig)
    local_lmstudio: Optional[LocalLLMConfig] = Field(
        default=None,
        alias="local-lmstudio",
        description="LM Studio configuration"
    )
    local_ollama: Optional[LocalLLMConfig] = Field(
        default=None,
        alias="local-ollama",
        description="Ollama configuration"
    )

    @model_validator(mode='after')
    def check_provider_config(self):
        """Ensure selected provider has configuration."""
        provider_map = {
            LLMProviderEnum.OPENAI: self.openai,
            LLMProviderEnum.ANTHROPIC: self.anthropic,
            LLMProviderEnum.LOCAL_LMSTUDIO: self.local_lmstudio,
            LLMProviderEnum.LOCAL_OLLAMA: self.local_ollama,
        }

        selected_config = provider_map.get(self.provider)
        if selected_config is None:
            raise ValueError(
                f"Provider '{self.provider}' is selected but not configured. "
                f"Please add '{self.provider}' section to config.yaml"
            )

        return self

    @model_validator(mode='after')
    def override_from_env(self):
        """Override provider and models from environment variables."""
        # Override provider
        env_provider = os.getenv("WPGEN_LLM_PROVIDER")
        if env_provider:
            try:
                self.provider = LLMProviderEnum(env_provider.lower())
                logger.info(f"Overriding LLM provider from env: {self.provider}")
            except ValueError:
                logger.warning(f"Invalid WPGEN_LLM_PROVIDER: {env_provider}")

        # Override OpenAI model
        env_openai_model = os.getenv("WPGEN_OPENAI_MODEL")
        if env_openai_model and self.openai:
            self.openai.model = env_openai_model
            logger.info(f"Overriding OpenAI model from env: {env_openai_model}")

        # Override Anthropic model
        env_anthropic_model = os.getenv("WPGEN_ANTHROPIC_MODEL")
        if env_anthropic_model and self.anthropic:
            self.anthropic.model = env_anthropic_model
            logger.info(f"Overriding Anthropic model from env: {env_anthropic_model}")

        # Override Ollama model
        env_ollama_model = os.getenv("WPGEN_OLLAMA_MODEL")
        if env_ollama_model and self.local_ollama:
            self.local_ollama.brains_model = env_ollama_model
            logger.info(f"Overriding Ollama model from env: {env_ollama_model}")

        return self


class GitHubConfig(BaseModel):
    """GitHub integration configuration."""
    api_url: str = Field(default="https://api.github.com")
    repo_name_pattern: str = Field(default="wp-{theme_name}-{timestamp}")
    auto_create: bool = Field(default=True)
    private: bool = Field(default=False)
    default_branch: str = Field(default="main")
    token: Optional[str] = Field(default=None, description="GitHub token (from env GITHUB_TOKEN)")

    @model_validator(mode='after')
    def load_from_env(self):
        """Load token from environment if not set."""
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN")
        return self


class WordPressConfig(BaseModel):
    """WordPress theme generation configuration."""
    theme_prefix: str = Field(default="wpgen")
    wp_version: str = Field(default="6.4")
    include_sample_content: bool = Field(default=True)
    theme_type: str = Field(default="standalone")
    author: str = Field(default="WPGen")
    license: str = Field(default="GPL-2.0-or-later")

    @field_validator('theme_type')
    @classmethod
    def validate_theme_type(cls, v: str) -> str:
        """Validate theme type."""
        if v not in ["standalone", "child"]:
            raise ValueError(f"Invalid theme_type: {v}. Must be 'standalone' or 'child'")
        return v


class OutputConfig(BaseModel):
    """Output configuration."""
    output_dir: str = Field(default="output")
    clean_before_generate: bool = Field(default=False)
    keep_local_copy: bool = Field(default=True)

    @field_validator('output_dir')
    @classmethod
    def validate_output_dir(cls, v: str) -> str:
        """Ensure output directory is valid."""
        if not v or not v.strip():
            raise ValueError("output_dir cannot be empty")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    log_file: str = Field(default="logs/wpgen.jsonl")
    format: str = Field(default="text")
    console_output: bool = Field(default=True)
    colored_console: bool = Field(default=True)

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of: {', '.join(valid_levels)}")
        return v_upper

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate log format."""
        if v not in ["json", "text"]:
            raise ValueError(f"Invalid log format: {v}. Must be 'json' or 'text'")
        return v


class WebConfig(BaseModel):
    """Web UI configuration."""
    enabled: bool = Field(default=True)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5000, ge=1, le=65535)
    debug: bool = Field(default=False)
    secret_key: Optional[str] = Field(default=None)


class DeploymentMethod(str, Enum):
    """Supported deployment methods."""
    GITHUB_ACTIONS = "github_actions"
    FTP = "ftp"
    SSH = "ssh"


class DeploymentConfig(BaseModel):
    """Deployment configuration."""
    enabled: bool = Field(default=False)
    method: DeploymentMethod = Field(default=DeploymentMethod.GITHUB_ACTIONS)


class WordPressAPIConfig(BaseModel):
    """WordPress REST API configuration."""
    enabled: bool = Field(default=False)
    site_url: Optional[str] = Field(
        default=None, description="WordPress site URL (from env WP_SITE_URL)"
    )
    username: Optional[str] = Field(
        default=None, description="WordPress username (from env WP_USERNAME)"
    )
    app_password: Optional[str] = Field(
        default=None, description="WordPress app password (from env WP_APP_PASSWORD)"
    )
    auto_deploy: bool = Field(default=False)
    auto_activate: bool = Field(default=False)

    @model_validator(mode='after')
    def load_from_env(self):
        """Load credentials from environment if not set."""
        if not self.site_url:
            self.site_url = os.getenv("WP_SITE_URL")
        if not self.username:
            self.username = os.getenv("WP_USERNAME")
        if not self.app_password:
            self.app_password = os.getenv("WP_APP_PASSWORD")
        return self

    @model_validator(mode='after')
    def validate_credentials(self):
        """Validate that if enabled, credentials are provided."""
        if self.enabled and not all([self.site_url, self.username, self.app_password]):
            raise ValueError(
                "WordPress API is enabled but credentials are missing. "
                "Set WP_SITE_URL, WP_USERNAME, and WP_APP_PASSWORD environment variables "
                "or configure them in config.yaml"
            )
        return self


class ValidationConfig(BaseModel):
    """Code validation configuration."""
    enabled: bool = Field(default=True)
    strict: bool = Field(default=False, description="Fail on warnings in addition to errors")
    php_path: Optional[str] = Field(default="php", description="Path to PHP binary")


class WPGenConfig(BaseModel):
    """Complete wpgen configuration schema."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    wordpress: WordPressConfig = Field(default_factory=WordPressConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
    wordpress_api: WordPressAPIConfig = Field(default_factory=WordPressAPIConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)

    class Config:
        """Pydantic configuration."""
        populate_by_name = True  # Allow field aliases


def load_and_validate_config(config_path: str = "config.yaml") -> WPGenConfig:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to config.yaml file

    Returns:
        Validated WPGenConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    import yaml

    config_file = Path(config_path)

    if not config_file.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        # Return default config
        return WPGenConfig()

    try:
        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f) or {}

        logger.info(f"Loading configuration from: {config_path}")

        # Validate with Pydantic
        config = WPGenConfig(**config_dict)

        logger.info("Configuration validated successfully")
        return config

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ValueError(
            f"Invalid configuration in {config_path}:\n{str(e)}\n\n"
            f"Please check your config.yaml file against the documentation."
        )


def get_redacted_config_summary(config: WPGenConfig) -> Dict[str, Any]:
    """Get a summary of configuration with secrets redacted.

    Args:
        config: Configuration instance

    Returns:
        Dictionary with redacted configuration summary
    """
    summary = {
        "llm": {
            "provider": config.llm.provider.value,
        },
        "github": {
            "auto_create": config.github.auto_create,
            "private": config.github.private,
            "token_set": bool(config.github.token),
        },
        "wordpress": {
            "theme_prefix": config.wordpress.theme_prefix,
            "wp_version": config.wordpress.wp_version,
        },
        "output": {
            "output_dir": config.output.output_dir,
        },
        "validation": {
            "enabled": config.validation.enabled,
            "strict": config.validation.strict,
        },
        "wordpress_api": {
            "enabled": config.wordpress_api.enabled,
            "site_url": (
                config.wordpress_api.site_url
                if config.wordpress_api.site_url
                else "not_set"
            ),
            "credentials_set": bool(
                config.wordpress_api.username and config.wordpress_api.app_password
            ),
        },
    }

    # Add model info based on provider
    if config.llm.provider == LLMProviderEnum.OPENAI and config.llm.openai:
        summary["llm"]["model"] = config.llm.openai.model
        summary["llm"]["api_key_set"] = bool(config.llm.openai.api_key)
    elif config.llm.provider == LLMProviderEnum.ANTHROPIC and config.llm.anthropic:
        summary["llm"]["model"] = config.llm.anthropic.model
        summary["llm"]["api_key_set"] = bool(config.llm.anthropic.api_key)
    elif config.llm.provider == LLMProviderEnum.LOCAL_LMSTUDIO and config.llm.local_lmstudio:
        summary["llm"]["brains_model"] = config.llm.local_lmstudio.brains_model
        summary["llm"]["vision_model"] = config.llm.local_lmstudio.vision_model or "not_set"
    elif config.llm.provider == LLMProviderEnum.LOCAL_OLLAMA and config.llm.local_ollama:
        summary["llm"]["brains_model"] = config.llm.local_ollama.brains_model
        summary["llm"]["vision_model"] = config.llm.local_ollama.vision_model or "not_set"

    return summary
