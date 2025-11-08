"""Secure credential management for Git operations.

This module provides secure authentication for Git push operations using
GIT_ASKPASS environment variable instead of embedding tokens in URLs.
"""

import os
import platform
import stat
import tempfile
from pathlib import Path
from typing import Dict, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class SecureCredentialHelper:
    """Helper for creating secure Git askpass scripts."""

    def __init__(self, token: str):
        """Initialize credential helper.

        Args:
            token: GitHub personal access token or credentials
        """
        self.token = token
        self._askpass_script: Optional[Path] = None
        self._temp_dir: Optional[str] = None

    def build_askpass_env(self) -> Dict[str, str]:
        """Build environment variables for secure Git authentication.

        Creates a temporary askpass script that provides credentials without
        embedding them in the Git remote URL.

        Returns:
            Dictionary of environment variables to set for Git operations

        Raises:
            RuntimeError: If askpass script creation fails
        """
        try:
            # Create temporary directory and script
            self._temp_dir = tempfile.mkdtemp(prefix="wpgen_git_")
            temp_path = Path(self._temp_dir)

            is_windows = platform.system() == "Windows"

            if is_windows:
                # Windows: Create a batch script
                script_path = temp_path / "git-askpass.bat"
                script_content = f'@echo off\necho {self.token}\n'
                script_path.write_text(script_content, encoding="utf-8")
            else:
                # POSIX (Linux/macOS): Create a shell script
                script_path = temp_path / "git-askpass.sh"
                script_content = f'#!/bin/sh\necho "{self.token}"\n'
                script_path.write_text(script_content, encoding="utf-8")

                # Make script executable (chmod +x)
                script_path.chmod(
                    script_path.stat().st_mode
                    | stat.S_IXUSR
                    | stat.S_IXGRP
                    | stat.S_IXOTH
                )

            self._askpass_script = script_path
            logger.debug(f"Created askpass script at: {script_path}")

            # Build environment variables
            env = os.environ.copy()
            env['GIT_ASKPASS'] = str(script_path)
            env['GIT_TERMINAL_PROMPT'] = '0'  # Disable interactive prompts

            # On Windows, also set these for better compatibility
            if is_windows:
                env['GCM_INTERACTIVE'] = 'never'

            logger.debug("Built secure askpass environment")
            return env

        except Exception as e:
            logger.error(f"Failed to create askpass script: {e}")
            self.cleanup()
            raise RuntimeError(f"Failed to create secure credential helper: {e}")

    def cleanup(self):
        """Clean up temporary askpass script and directory."""
        if self._askpass_script and self._askpass_script.exists():
            try:
                self._askpass_script.unlink()
                logger.debug(f"Removed askpass script: {self._askpass_script}")
            except Exception as e:
                logger.warning(f"Failed to remove askpass script: {e}")

        if self._temp_dir:
            try:
                Path(self._temp_dir).rmdir()
                logger.debug(f"Removed temporary directory: {self._temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove temp directory: {e}")

        self._askpass_script = None
        self._temp_dir = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()


def build_askpass_env(token: str) -> Dict[str, str]:
    """Build environment variables for secure Git authentication.

    Convenience function that creates a temporary askpass script and returns
    environment variables. Note: The script must be cleaned up manually or
    use SecureCredentialHelper as a context manager.

    Args:
        token: GitHub personal access token

    Returns:
        Dictionary of environment variables for Git operations with GIT_ASKPASS set
    """
    helper = SecureCredentialHelper(token)
    return helper.build_askpass_env()


def validate_token_format(token: str) -> bool:
    """Validate that a token looks like a valid GitHub PAT.

    Args:
        token: Token to validate

    Returns:
        True if token appears valid, False otherwise
    """
    if not token or not isinstance(token, str):
        return False

    # GitHub PAT formats:
    # - Classic: ghp_... (36+ chars)
    # - Fine-grained: github_pat_... (82+ chars)
    if token.startswith('ghp_') and len(token) >= 40:
        return True
    if token.startswith('github_pat_') and len(token) >= 82:
        return True

    # Warn about potentially insecure token
    if len(token) < 20:
        logger.warning("Token appears too short to be a valid GitHub PAT")
        return False

    return True
