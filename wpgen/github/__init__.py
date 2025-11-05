"""GitHub integration modules for wpgen."""

from .credentials import SecureCredentialHelper, build_askpass_env
from .integration import GitHubIntegration

__all__ = ["GitHubIntegration", "SecureCredentialHelper", "build_askpass_env"]
