"""GitHub integration for pushing generated themes.

This module handles:
- Repository creation
- Git operations (init, add, commit, push)
- Authentication using personal access tokens
"""

import requests
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import git

from ..utils.logger import get_logger


logger = get_logger(__name__)


class GitHubIntegration:
    """Handle GitHub operations for generated themes."""

    def __init__(self, token: str, config: Dict[str, Any] = None):
        """Initialize GitHub integration.

        Args:
            token: GitHub personal access token
            config: GitHub configuration from config.yaml
        """
        self.token = token
        self.config = config or {}
        self.api_url = self.config.get("api_url", "https://api.github.com")
        self.default_owner = self.config.get("default_owner", "")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        logger.info("Initialized GitHubIntegration")

    def create_repository(
        self, name: str, description: str = "", private: bool = False
    ) -> Dict[str, Any]:
        """Create a new GitHub repository.

        Args:
            name: Repository name
            description: Repository description
            private: Whether to make the repository private

        Returns:
            Repository information dictionary

        Raises:
            Exception: If repository creation fails
        """
        logger.info(f"Creating GitHub repository: {name}")

        url = f"{self.api_url}/user/repos"
        data = {"name": name, "description": description, "private": private, "auto_init": False}

        try:
            response = requests.post(url, headers=self.headers, json=data)

            if response.status_code == 201:
                repo_data = response.json()
                logger.info(f"Repository created successfully: {repo_data['html_url']}")
                return repo_data
            elif response.status_code == 422:
                # Repository might already exist
                logger.warning(f"Repository {name} might already exist")
                # Try to get existing repository
                return self.get_repository(name)
            else:
                response.raise_for_status()

        except Exception as e:
            logger.error(f"Failed to create repository: {str(e)}")
            raise

    def get_repository(self, name: str, owner: Optional[str] = None) -> Dict[str, Any]:
        """Get information about an existing repository.

        Args:
            name: Repository name
            owner: Repository owner (uses authenticated user if not specified)

        Returns:
            Repository information dictionary

        Raises:
            Exception: If repository doesn't exist or request fails
        """
        if not owner:
            # Get authenticated user
            user_response = requests.get(f"{self.api_url}/user", headers=self.headers)
            user_response.raise_for_status()
            owner = user_response.json()["login"]

        url = f"{self.api_url}/repos/{owner}/{name}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get repository: {str(e)}")
            raise

    def push_to_github(
        self, theme_dir: str, repo_name: str, requirements: Dict[str, Any], branch: str = "main"
    ) -> str:
        """Initialize git, commit changes, and push to GitHub.

        Args:
            theme_dir: Path to the theme directory
            repo_name: Name of the GitHub repository
            requirements: Theme requirements (for commit message)
            branch: Branch name to push to

        Returns:
            Repository URL

        Raises:
            Exception: If git operations fail
        """
        theme_path = Path(theme_dir)
        logger.info(f"Pushing {theme_path} to GitHub repository: {repo_name}")

        try:
            # Initialize git repository
            repo = git.Repo.init(theme_path)
            logger.info("Initialized git repository")

            # Create or get GitHub repository
            if self.config.get("auto_create", True):
                try:
                    repo_data = self.create_repository(
                        repo_name,
                        requirements.get("description", ""),
                        self.config.get("private", False),
                    )
                except Exception as e:
                    logger.warning(f"Could not create repository: {str(e)}")
                    # Try to get existing repository
                    repo_data = self.get_repository(repo_name)
            else:
                repo_data = self.get_repository(repo_name)

            remote_url = repo_data["clone_url"]
            # Use token authentication in URL
            auth_url = remote_url.replace("https://", f"https://{self.token}@")

            # Add remote
            try:
                origin = repo.remote("origin")
                origin.set_url(auth_url)
                logger.info("Updated existing remote origin")
            except ValueError:
                origin = repo.create_remote("origin", auth_url)
                logger.info("Added remote origin")

            # Add all files
            # Get all files in the directory recursively
            all_files = [
                str(f.relative_to(theme_path)) for f in theme_path.rglob("*") if f.is_file()
            ]
            if all_files:
                repo.index.add(all_files)
            logger.info(f"Added {len(all_files)} files to git index")

            # Create commit
            commit_message = f"""Initial commit: {requirements['theme_display_name']}

Generated WordPress theme with the following features:
{chr(10).join(f'- {feature}' for feature in requirements.get('features', []))}

Generated by WPGen on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            repo.index.commit(commit_message)
            logger.info("Created initial commit")

            # Push to GitHub
            try:
                # Get current branch name
                if not repo.heads:
                    # No branches yet, create initial branch
                    current_branch = repo.create_head(branch)
                    repo.head.reference = current_branch
                else:
                    current_branch = repo.active_branch

                # Rename branch if needed
                if current_branch.name != branch:
                    current_branch.rename(branch)

                origin.push(refspec=f"{branch}:{branch}")
                logger.info(f"Pushed to GitHub: {branch} branch")

            except Exception as e:
                logger.error(f"Failed to push to GitHub: {str(e)}")
                raise

            repo_url = repo_data["html_url"]
            logger.info(f"Successfully pushed theme to: {repo_url}")
            return repo_url

        except Exception as e:
            logger.error(f"Failed to push to GitHub: {str(e)}")
            raise

    def generate_repo_name(self, theme_name: str) -> str:
        """Generate a repository name based on pattern.

        Args:
            theme_name: Base theme name

        Returns:
            Generated repository name
        """
        pattern = self.config.get("repo_name_pattern", "wp-{theme_name}-{timestamp}")
        timestamp = datetime.now().strftime("%Y%m%d")

        repo_name = pattern.format(theme_name=theme_name, timestamp=timestamp)

        logger.debug(f"Generated repository name: {repo_name}")
        return repo_name

    def create_deployment_workflow(self, theme_dir: str, deployment_config: Dict[str, Any]) -> None:
        """Create GitHub Actions workflow for deployment.

        Args:
            theme_dir: Path to theme directory
            deployment_config: Deployment configuration
        """
        logger.info("Creating GitHub Actions deployment workflow")

        workflow_dir = Path(theme_dir) / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)

        method = deployment_config.get("method", "ftp")

        if method == "ftp":
            workflow_content = self._generate_ftp_workflow(deployment_config)
        elif method == "ssh":
            workflow_content = self._generate_ssh_workflow(deployment_config)
        else:
            workflow_content = self._generate_manual_workflow()

        workflow_file = workflow_dir / "deploy.yml"
        workflow_file.write_text(workflow_content, encoding="utf-8")
        logger.info("Created deployment workflow")

    def _generate_ftp_workflow(self, config: Dict[str, Any]) -> str:
        """Generate FTP deployment workflow."""
        return """name: Deploy to WordPress via FTP

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Deploy via FTP
        uses: SamKirkland/FTP-Deploy-Action@4.3.3
        with:
          server: ${{ secrets.FTP_HOST }}
          username: ${{ secrets.FTP_USERNAME }}
          password: ${{ secrets.FTP_PASSWORD }}
          server-dir: /public_html/wp-content/themes/
          exclude: |
            **/.git*
            **/.git*/**
            **/node_modules/**
            **/README.md

      - name: Deployment complete
        run: echo "Theme deployed successfully!"
"""

    def _generate_ssh_workflow(self, config: Dict[str, Any]) -> str:
        """Generate SSH deployment workflow."""
        return """name: Deploy to WordPress via SSH

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Deploy via SSH
        uses: easingthemes/ssh-deploy@main
        env:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          REMOTE_HOST: ${{ secrets.SSH_HOST }}
          REMOTE_USER: ${{ secrets.SSH_USERNAME }}
          TARGET: ${{ secrets.SSH_REMOTE_PATH }}

      - name: Deployment complete
        run: echo "Theme deployed successfully!"
"""

    def _generate_manual_workflow(self) -> str:
        """Generate manual deployment instructions workflow."""
        return """name: Manual Deployment Instructions

on:
  workflow_dispatch:

jobs:
  instructions:
    runs-on: ubuntu-latest

    steps:
      - name: Display deployment instructions
        run: |
          echo "=== Manual Deployment Instructions ==="
          echo ""
          echo "1. Download the theme from this repository"
          echo "2. Create a ZIP file of the theme directory"
          echo "3. In WordPress admin, go to Appearance > Themes > Add New"
          echo "4. Click 'Upload Theme' and select your ZIP file"
          echo "5. Click 'Install Now' and then 'Activate'"
          echo ""
          echo "Alternatively, use FTP:"
          echo "1. Connect to your server via FTP"
          echo "2. Navigate to /wp-content/themes/"
          echo "3. Upload the entire theme directory"
          echo "4. Activate the theme from WordPress admin"
"""
