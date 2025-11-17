"""Type definitions for WPGen API boundaries.

Provides TypedDict models for structured data at API boundaries.
"""

from typing import TypedDict


class GenerationRequestDict(TypedDict, total=False):
    """Type for theme generation request payload."""

    prompt: str  # Required
    push_to_github: bool
    repo_name: str | None
    llm_provider: str | None
    llm_model: str | None
    image_files: list[str] | None
    text_files: list[str] | None
    strict_validation: bool
    deploy_to_wordpress: bool


class GenerationResultDict(TypedDict, total=False):
    """Type for theme generation result."""

    success: bool  # Required
    theme_name: str
    theme_display_name: str
    description: str
    theme_dir: str | None
    features: list[str]
    github_url: str | None
    repo_name: str | None
    deployment_workflow: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    error: str | None
    error_details: str | None


class ValidationReportDict(TypedDict, total=False):
    """Type for code validation report."""

    errors: list[str]
    warnings: list[str]
    info: list[str]
    passed: bool
    strict_mode: bool


class GitHubPushResultDict(TypedDict, total=False):
    """Type for GitHub push operation result."""

    success: bool  # Required
    url: str | None
    repo_name: str | None
    error: str | None


class ConfigSummaryDict(TypedDict, total=False):
    """Type for redacted configuration summary."""

    llm: dict[str, str]
    github: dict[str, bool]
    wordpress: dict[str, str]
    output: dict[str, str]
    validation: dict[str, bool]
    wordpress_api: dict[str, str]
