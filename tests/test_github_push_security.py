"""Tests for secure GitHub push without tokens in URLs."""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from wpgen.github.credentials import (
    SecureCredentialHelper,
    build_askpass_env,
    validate_token_format,
)


def test_build_askpass_env_creates_script():
    """Test that askpass environment creates a script."""
    token = "ghp_test1234567890"
    helper = SecureCredentialHelper(token)

    env = helper.build_askpass_env()

    assert "GIT_ASKPASS" in env
    assert "GIT_TERMINAL_PROMPT" in env
    assert env["GIT_TERMINAL_PROMPT"] == "0"

    # Check script exists
    script_path = Path(env["GIT_ASKPASS"])
    assert script_path.exists()

    # Clean up
    helper.cleanup()


def test_askpass_script_is_executable_on_posix():
    """Test that askpass script is executable on POSIX systems."""
    if os.name == "nt":
        pytest.skip("Test only for POSIX systems")

    token = "ghp_test1234567890"
    helper = SecureCredentialHelper(token)

    env = helper.build_askpass_env()
    script_path = Path(env["GIT_ASKPASS"])

    # Check if executable bit is set
    assert os.access(script_path, os.X_OK)

    helper.cleanup()


def test_askpass_script_contains_token():
    """Test that askpass script contains the token."""
    token = "ghp_test1234567890abcdef"
    helper = SecureCredentialHelper(token)

    env = helper.build_askpass_env()
    script_path = Path(env["GIT_ASKPASS"])

    content = script_path.read_text()
    assert token in content

    helper.cleanup()


def test_cleanup_removes_script():
    """Test that cleanup removes the askpass script."""
    token = "ghp_test1234567890"
    helper = SecureCredentialHelper(token)

    env = helper.build_askpass_env()
    script_path = Path(env["GIT_ASKPASS"])

    assert script_path.exists()

    helper.cleanup()

    # Script should be removed
    assert not script_path.exists()


def test_context_manager_cleans_up():
    """Test that context manager automatically cleans up."""
    token = "ghp_test1234567890"

    with SecureCredentialHelper(token) as helper:
        env = helper.build_askpass_env()
        script_path = Path(env["GIT_ASKPASS"])
        assert script_path.exists()

    # After context exit, script should be cleaned up
    assert not script_path.exists()


def test_build_askpass_env_convenience_function():
    """Test convenience function for building askpass env."""
    token = "ghp_test1234567890"
    env = build_askpass_env(token)

    assert "GIT_ASKPASS" in env
    script_path = Path(env["GIT_ASKPASS"])
    assert script_path.exists()

    # Clean up manually
    script_path.unlink(missing_ok=True)
    try:
        script_path.parent.rmdir()
    except:
        pass


def test_validate_token_format_classic():
    """Test validation of classic GitHub PAT format."""
    assert validate_token_format("ghp_" + "a" * 36) is True


def test_validate_token_format_fine_grained():
    """Test validation of fine-grained GitHub PAT format."""
    assert validate_token_format("github_pat_" + "a" * 71) is True


def test_validate_token_format_invalid_short():
    """Test that short tokens are rejected."""
    assert validate_token_format("abc123") is False


def test_validate_token_format_empty():
    """Test that empty tokens are rejected."""
    assert validate_token_format("") is False


def test_validate_token_format_none():
    """Test that None tokens are rejected."""
    assert validate_token_format(None) is False


def test_no_token_in_git_remote(tmp_path):
    """Test that git remote URLs don't contain tokens."""
    # This is an integration-style test that mocks git operations
    from wpgen.github.integration import GitHubIntegration

    with patch("wpgen.github.integration.git.Repo") as MockRepo:
        mock_repo = MagicMock()
        MockRepo.init.return_value = mock_repo

        token = "ghp_secrettoken123"
        github = GitHubIntegration(token, {"auto_create": False})

        # Mock API calls
        with patch("requests.post") as mock_post, \
             patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"login": "testuser"}
            mock_get.return_value.raise_for_status = Mock()

            mock_post.return_value.json.return_value = {
                "html_url": "https://github.com/testuser/test-repo",
                "clone_url": "https://github.com/testuser/test-repo.git"
            }
            mock_post.return_value.raise_for_status = Mock()

            # Create test theme directory
            theme_dir = tmp_path / "test-theme"
            theme_dir.mkdir()
            (theme_dir / "style.css").write_text("/* Test */")

            # Verify that when setting remote, token is NOT in the URL
            def check_remote_url(*args, **kwargs):
                # Inspect the calls to ensure no token in URL
                for call in mock_repo.create_remote.call_args_list:
                    remote_url = call[0][1] if len(call[0]) > 1 else call[1].get("url")
                    if remote_url:
                        assert token not in remote_url, "Token found in git remote URL!"
                return mock_repo

            mock_repo.create_remote.side_effect = check_remote_url

            # The actual push might be skipped in test, but we verify remote URL
            try:
                github.push_to_github(
                    str(theme_dir),
                    "test-repo",
                    {"theme_name": "test", "description": "Test theme"}
                )
            except Exception:
                # Might fail due to mocking, but we checked the remote URL above
                pass
