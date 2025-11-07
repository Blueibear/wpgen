"""Type definitions for WPGen API boundaries.

Provides TypedDict models for structured data at API boundaries.
"""

from typing import Dict, List, Optional, TypedDict


class GenerationRequestDict(TypedDict, total=False):
    """Type for theme generation request payload."""

    prompt: str  # Required
    push_to_github: bool
    repo_name: Optional[str]
    llm_provider: Optional[str]
    llm_model: Optional[str]
    image_files: Optional[List[str]]
    text_files: Optional[List[str]]
    strict_validation: bool
    deploy_to_wordpress: bool


class GenerationResultDict(TypedDict, total=False):
    """Type for theme generation result."""

    success: bool  # Required
    theme_name: str
    theme_display_name: str
    description: str
    theme_dir: Optional[str]
    features: List[str]
    github_url: Optional[str]
    repo_name: Optional[str]
    deployment_workflow: bool
    validation_errors: List[str]
    validation_warnings: List[str]
    error: Optional[str]
    error_details: Optional[str]


class ValidationReportDict(TypedDict, total=False):
    """Type for code validation report."""

    errors: List[str]
    warnings: List[str]
    info: List[str]
    passed: bool
    strict_mode: bool


class GitHubPushResultDict(TypedDict, total=False):
    """Type for GitHub push operation result."""

    success: bool  # Required
    url: Optional[str]
    repo_name: Optional[str]
    error: Optional[str]


class ConfigSummaryDict(TypedDict, total=False):
    """Type for redacted configuration summary."""

    llm: Dict[str, str]
    github: Dict[str, bool]
    wordpress: Dict[str, str]
    output: Dict[str, str]
    validation: Dict[str, bool]
    wordpress_api: Dict[str, str]
