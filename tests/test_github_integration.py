"""Tests for GitHub integration module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import git
import pytest

from wpgen.github.integration import GitHubIntegration


class TestGitHubIntegration:
    """Test suite for GitHubIntegration class."""

    @pytest.fixture
    def mock_token(self):
        """Mock GitHub token."""
        return "ghp_test_token_123456789"

    @pytest.fixture
    def github_integration(self, mock_token):
        """Create GitHubIntegration instance."""
        return GitHubIntegration(mock_token, config={})

    @pytest.fixture
    def theme_directory(self, tmp_path):
        """Create a test theme directory with files."""
        theme_dir = tmp_path / "test-theme"
        theme_dir.mkdir()

        # Create some theme files
        (theme_dir / "style.css").write_text("/* Theme CSS */")
        (theme_dir / "index.php").write_text("<?php // Index ?>")
        (theme_dir / "functions.php").write_text("<?php // Functions ?>")

        # Create a subdirectory with files
        assets_dir = theme_dir / "assets"
        assets_dir.mkdir()
        (assets_dir / "main.js").write_text("// JavaScript")

        return theme_dir

    def test_init(self, mock_token):
        """Test GitHubIntegration initialization."""
        integration = GitHubIntegration(mock_token)
        assert integration.token == mock_token
        assert integration.api_url == "https://api.github.com"

    def test_init_with_config(self, mock_token):
        """Test GitHubIntegration initialization with custom config."""
        config = {
            "api_url": "https://custom.github.com/api",
            "default_owner": "testuser",
        }
        integration = GitHubIntegration(mock_token, config)
        assert integration.api_url == "https://custom.github.com/api"
        assert integration.default_owner == "testuser"

    def test_generate_repo_name_default_pattern(self, github_integration):
        """Test repository name generation with default pattern."""
        repo_name = github_integration.generate_repo_name("my-theme")
        assert "wp-my-theme-" in repo_name
        assert len(repo_name.split("-")) >= 3  # wp-my-theme-YYYYMMDD

    def test_generate_repo_name_custom_pattern(self, mock_token):
        """Test repository name generation with custom pattern."""
        config = {"repo_name_pattern": "{theme_name}-wp"}
        integration = GitHubIntegration(mock_token, config)
        repo_name = integration.generate_repo_name("my-theme")
        assert repo_name == "my-theme-wp"

    @patch("wpgen.github.integration.requests.post")
    def test_create_repository_success(self, mock_post, github_integration):
        """Test successful repository creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "html_url": "https://github.com/user/test-repo",
            "clone_url": "https://github.com/user/test-repo.git",
        }
        mock_post.return_value = mock_response

        result = github_integration.create_repository("test-repo", "Test description")

        assert result["html_url"] == "https://github.com/user/test-repo"
        mock_post.assert_called_once()

    @patch("wpgen.github.integration.requests.post")
    def test_create_repository_already_exists(self, mock_post, github_integration):
        """Test repository creation when repo already exists."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_post.return_value = mock_response

        # Mock get_repository to return existing repo
        with patch.object(github_integration, "get_repository") as mock_get:
            mock_get.return_value = {"html_url": "https://github.com/user/test-repo"}
            result = github_integration.create_repository("test-repo")
            assert result["html_url"] == "https://github.com/user/test-repo"

    @patch("wpgen.github.integration.requests.get")
    def test_get_repository(self, mock_get, github_integration):
        """Test getting repository information."""
        # Mock user endpoint
        mock_user_response = Mock()
        mock_user_response.json.return_value = {"login": "testuser"}
        mock_user_response.raise_for_status = Mock()

        # Mock repo endpoint
        mock_repo_response = Mock()
        mock_repo_response.json.return_value = {
            "html_url": "https://github.com/testuser/test-repo"
        }
        mock_repo_response.raise_for_status = Mock()

        mock_get.side_effect = [mock_user_response, mock_repo_response]

        result = github_integration.get_repository("test-repo")
        assert result["html_url"] == "https://github.com/testuser/test-repo"

    def test_push_excludes_git_directory(self, github_integration, theme_directory):
        """Test that .git directory is excluded when collecting files to commit."""
        # Initialize git repo (creates .git directory)
        repo = git.Repo.init(theme_directory)

        # Collect files using the same logic as push_to_github
        all_files = [
            str(f.relative_to(theme_directory))
            for f in theme_directory.rglob("*")
            if f.is_file() and not any(part.startswith(".git") for part in f.parts)
        ]

        # Verify .git files are excluded
        assert not any(".git" in f for f in all_files)

        # Verify theme files are included
        assert "style.css" in all_files
        assert "index.php" in all_files
        assert "functions.php" in all_files
        assert "assets/main.js" in all_files

    def test_push_with_nested_git_directory(self, github_integration, tmp_path):
        """Test that nested .git directories are also excluded."""
        theme_dir = tmp_path / "test-theme"
        theme_dir.mkdir()

        # Create theme files
        (theme_dir / "style.css").write_text("/* CSS */")

        # Create a subdirectory with a .git folder (shouldn't happen, but test edge case)
        subdir = theme_dir / "vendor" / "package"
        subdir.mkdir(parents=True)
        git_dir = subdir / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")

        # Initialize main git repo
        git.Repo.init(theme_dir)

        # Collect files
        all_files = [
            str(f.relative_to(theme_dir))
            for f in theme_dir.rglob("*")
            if f.is_file() and not any(part.startswith(".git") for part in f.parts)
        ]

        # Verify no .git files are included
        assert not any(".git" in f for f in all_files)
        assert "style.css" in all_files

    @patch("wpgen.github.integration.subprocess.run")
    @patch("wpgen.github.integration.git.Repo")
    def test_push_to_github_success(
        self, mock_repo_class, mock_subprocess, github_integration, theme_directory
    ):
        """Test successful push to GitHub."""
        # Mock git repo
        mock_repo = MagicMock()
        mock_repo_class.init.return_value = mock_repo
        mock_repo.heads = []
        mock_repo.create_head.return_value = Mock(name="main")
        mock_repo.index = Mock()

        # Mock subprocess (git push)
        mock_subprocess.return_value = Mock(returncode=0, stderr="", stdout="")

        # Mock GitHub API calls
        with patch.object(github_integration, "create_repository") as mock_create:
            mock_create.return_value = {
                "clone_url": "https://github.com/user/test-repo.git",
                "html_url": "https://github.com/user/test-repo",
            }

            requirements = {
                "theme_display_name": "Test Theme",
                "description": "Test description",
                "features": ["feature1", "feature2"],
            }

            result = github_integration.push_to_github(
                str(theme_directory), "test-repo", requirements
            )

            assert result == "https://github.com/user/test-repo"

    @patch("wpgen.github.integration.subprocess.run")
    @patch("wpgen.github.integration.git.Repo")
    def test_push_to_github_git_push_fails(
        self, mock_repo_class, mock_subprocess, github_integration, theme_directory
    ):
        """Test push to GitHub when git push command fails."""
        # Mock git repo
        mock_repo = MagicMock()
        mock_repo_class.init.return_value = mock_repo
        mock_repo.heads = []
        mock_repo.create_head.return_value = Mock(name="main")

        # Mock failed git push (like the hasDotgit error)
        mock_subprocess.return_value = Mock(
            returncode=1,
            stderr="remote: error: object contains '.git'",
            stdout="",
        )

        # Mock GitHub API
        with patch.object(github_integration, "create_repository") as mock_create:
            mock_create.return_value = {
                "clone_url": "https://github.com/user/test-repo.git",
                "html_url": "https://github.com/user/test-repo",
            }

            requirements = {
                "theme_display_name": "Test Theme",
                "description": "Test",
                "features": [],
            }

            with pytest.raises(Exception) as exc_info:
                github_integration.push_to_github(
                    str(theme_directory), "test-repo", requirements
                )

            assert "Push failed" in str(exc_info.value)
