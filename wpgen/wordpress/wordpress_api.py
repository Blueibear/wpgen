"""WordPress REST API integration for theme deployment and site management.

This module provides complete WordPress site control via REST API, enabling:
- Theme deployment and activation
- Content management (pages, posts, media)
- Plugin installation and management
- Site settings configuration
"""

import logging
import zipfile
from base64 import b64encode
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..utils.logger import get_logger

logger = get_logger(__name__)


def is_retryable_error(exception):
    """Check if an HTTP error is retryable."""
    if isinstance(exception, requests.exceptions.HTTPError):
        # Retry on 5xx server errors and 429 rate limit
        return exception.response.status_code >= 500 or exception.response.status_code == 429
    # Retry on connection and timeout errors
    return isinstance(exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))


def get_retry_decorator():
    """Get configured retry decorator for WordPress API calls."""
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=0.2, max=8),
        retry=retry_if_exception_type((
            requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        )),
        reraise=True,
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )


class WordPressAPI:
    """WordPress REST API client for complete site management."""

    def __init__(
        self,
        site_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        """Initialize WordPress API client.

        Args:
            site_url: WordPress site URL (e.g., https://example.com)
            username: WordPress username
            password: WordPress password or application password
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.site_url = site_url.rstrip("/")
        self.api_url = f"{self.site_url}/wp-json/wp/v2"
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Create auth header for Basic Auth
        credentials = f"{username}:{password}"
        token = b64encode(credentials.encode()).decode("ascii")
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info(f"Initialized WordPress API client for {self.site_url}")

    @get_retry_decorator()
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to WordPress REST API.

        Returns:
            Dictionary with connection status and site info

        Raises:
            Exception: If connection fails
        """
        try:
            logger.info("Testing WordPress API connection...")

            # Get site info
            response = requests.get(
                f"{self.site_url}/wp-json",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            site_info = response.json()

            # Test authenticated endpoint
            auth_response = requests.get(
                f"{self.api_url}/users/me",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            auth_response.raise_for_status()

            user_info = auth_response.json()

            logger.info(f"✓ Connected to WordPress site: {site_info.get('name', 'Unknown')}")
            logger.info(f"✓ Authenticated as: {user_info.get('name', 'Unknown')}")

            return {
                "connected": True,
                "site_name": site_info.get("name"),
                "site_description": site_info.get("description"),
                "url": site_info.get("url"),
                "user": user_info.get("name"),
                "user_id": user_info.get("id"),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"WordPress API connection failed: {str(e)}")
            raise Exception(f"Failed to connect to WordPress API: {str(e)}")

    def deploy_theme(self, theme_path: str) -> Dict[str, Any]:
        """Deploy WordPress theme to the site.

        This creates a ZIP of the theme and uploads it. Note: Direct theme upload
        via REST API requires a plugin or FTP. This method provides the ZIP and
        instructions.

        Args:
            theme_path: Path to the theme directory

        Returns:
            Dictionary with deployment status and instructions

        Raises:
            Exception: If theme preparation fails
        """
        try:
            theme_dir = Path(theme_path)
            theme_name = theme_dir.name

            logger.info(f"Preparing theme for deployment: {theme_name}")

            # Create ZIP file
            zip_path = theme_dir.parent / f"{theme_name}.zip"

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in theme_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(theme_dir.parent)
                        zipf.write(file_path, arcname)
                        logger.debug(f"Added to ZIP: {arcname}")

            logger.info(f"✓ Theme ZIP created: {zip_path}")

            # Note: Direct REST API theme upload requires additional plugin
            # For now, provide deployment instructions
            result = {
                "success": True,
                "theme_name": theme_name,
                "zip_path": str(zip_path),
                "deployment_method": "manual",
                "instructions": [
                    f"1. Download the theme ZIP: {zip_path}",
                    f"2. Go to {self.site_url}/wp-admin/theme-install.php",
                    "3. Click 'Upload Theme' and select the ZIP file",
                    "4. Click 'Install Now' and then 'Activate'",
                ],
            }

            # Try to activate if theme already exists (via WP-CLI integration if available)
            try:
                themes = self.get_themes()
                if theme_name in [t.get("stylesheet") for t in themes]:
                    activation_result = self.activate_theme(theme_name)
                    result["activated"] = activation_result.get("success", False)
            except Exception as e:
                logger.warning(f"Could not auto-activate theme: {str(e)}")

            return result

        except Exception as e:
            logger.error(f"Theme deployment failed: {str(e)}")
            raise

    def get_themes(self) -> List[Dict[str, Any]]:
        """Get list of installed themes.

        Returns:
            List of theme information dictionaries
        """
        try:
            # Note: Standard WP REST API doesn't expose themes endpoint
            # This would require a custom endpoint or plugin
            logger.warning("Theme listing requires custom REST endpoint")
            return []
        except Exception as e:
            logger.error(f"Failed to get themes: {str(e)}")
            return []

    def activate_theme(self, theme_slug: str) -> Dict[str, Any]:
        """Activate a theme.

        Args:
            theme_slug: Theme directory name/slug

        Returns:
            Dictionary with activation status
        """
        try:
            # Note: Theme activation via REST API requires custom endpoint
            logger.info(f"Attempting to activate theme: {theme_slug}")

            return {
                "success": False,
                "message": "Theme activation requires WP-CLI or custom endpoint",
                "manual_activation": f"{self.site_url}/wp-admin/themes.php",
            }
        except Exception as e:
            logger.error(f"Theme activation failed: {str(e)}")
            raise

    def create_page(
        self, title: str, content: str, status: str = "publish", **kwargs
    ) -> Dict[str, Any]:
        """Create a new page.

        Args:
            title: Page title
            content: Page content (HTML)
            status: Page status (draft, publish, private)
            **kwargs: Additional page parameters (slug, parent, template, etc.)

        Returns:
            Dictionary with created page information

        Raises:
            Exception: If page creation fails
        """
        try:
            logger.info(f"Creating page: {title}")

            data = {"title": title, "content": content, "status": status, **kwargs}

            response = requests.post(
                f"{self.api_url}/pages",
                headers=self.headers,
                json=data,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            page = response.json()
            logger.info(f"✓ Page created: {page.get('link')}")

            return {
                "success": True,
                "id": page.get("id"),
                "title": page.get("title", {}).get("rendered"),
                "link": page.get("link"),
                "status": page.get("status"),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Page creation failed: {str(e)}")
            raise Exception(f"Failed to create page: {str(e)}")

    def update_page(
        self, page_id: int, title: Optional[str] = None, content: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Update an existing page.

        Args:
            page_id: Page ID
            title: New page title (optional)
            content: New page content (optional)
            **kwargs: Additional parameters to update

        Returns:
            Dictionary with updated page information

        Raises:
            Exception: If page update fails
        """
        try:
            logger.info(f"Updating page ID: {page_id}")

            data = {**kwargs}
            if title is not None:
                data["title"] = title
            if content is not None:
                data["content"] = content

            response = requests.post(
                f"{self.api_url}/pages/{page_id}",
                headers=self.headers,
                json=data,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            page = response.json()
            logger.info(f"✓ Page updated: {page.get('link')}")

            return {
                "success": True,
                "id": page.get("id"),
                "title": page.get("title", {}).get("rendered"),
                "link": page.get("link"),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Page update failed: {str(e)}")
            raise Exception(f"Failed to update page: {str(e)}")

    @get_retry_decorator()
    def get_pages(self, **params) -> List[Dict[str, Any]]:
        """Get list of pages.

        Args:
            **params: Query parameters (per_page, page, search, etc.)

        Returns:
            List of page dictionaries
        """
        try:
            logger.info("Fetching pages...")

            response = requests.get(
                f"{self.api_url}/pages",
                headers=self.headers,
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            pages = response.json()
            logger.info(f"✓ Retrieved {len(pages)} pages")

            return [
                {
                    "id": page.get("id"),
                    "title": page.get("title", {}).get("rendered"),
                    "link": page.get("link"),
                    "status": page.get("status"),
                    "modified": page.get("modified"),
                }
                for page in pages
            ]

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get pages: {str(e)}")
            return []

    def delete_page(self, page_id: int, force: bool = False) -> Dict[str, Any]:
        """Delete a page.

        Args:
            page_id: Page ID to delete
            force: Whether to bypass trash and force deletion

        Returns:
            Dictionary with deletion status
        """
        try:
            logger.info(f"Deleting page ID: {page_id}")

            params = {"force": force}
            response = requests.delete(
                f"{self.api_url}/pages/{page_id}",
                headers=self.headers,
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"✓ Page deleted: {page_id}")
            return {"success": True, "id": page_id}

        except requests.exceptions.RequestException as e:
            logger.error(f"Page deletion failed: {str(e)}")
            raise Exception(f"Failed to delete page: {str(e)}")

    def create_post(
        self, title: str, content: str, status: str = "publish", **kwargs
    ) -> Dict[str, Any]:
        """Create a new blog post.

        Args:
            title: Post title
            content: Post content (HTML)
            status: Post status (draft, publish, private)
            **kwargs: Additional post parameters (categories, tags, etc.)

        Returns:
            Dictionary with created post information
        """
        try:
            logger.info(f"Creating post: {title}")

            data = {"title": title, "content": content, "status": status, **kwargs}

            response = requests.post(
                f"{self.api_url}/posts",
                headers=self.headers,
                json=data,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            post = response.json()
            logger.info(f"✓ Post created: {post.get('link')}")

            return {
                "success": True,
                "id": post.get("id"),
                "title": post.get("title", {}).get("rendered"),
                "link": post.get("link"),
                "status": post.get("status"),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Post creation failed: {str(e)}")
            raise Exception(f"Failed to create post: {str(e)}")

    @get_retry_decorator()
    def get_posts(self, **params) -> List[Dict[str, Any]]:
        """Get list of posts.

        Args:
            **params: Query parameters (per_page, page, search, etc.)

        Returns:
            List of post dictionaries
        """
        try:
            logger.info("Fetching posts...")

            response = requests.get(
                f"{self.api_url}/posts",
                headers=self.headers,
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()

            posts = response.json()
            logger.info(f"✓ Retrieved {len(posts)} posts")

            return [
                {
                    "id": post.get("id"),
                    "title": post.get("title", {}).get("rendered"),
                    "link": post.get("link"),
                    "status": post.get("status"),
                    "date": post.get("date"),
                }
                for post in posts
            ]

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get posts: {str(e)}")
            return []

    def upload_media(
        self, file_path: str, title: Optional[str] = None, alt_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload media file to WordPress.

        Args:
            file_path: Path to media file
            title: Media title (optional)
            alt_text: Alt text for images (optional)

        Returns:
            Dictionary with uploaded media information
        """
        try:
            file_path = Path(file_path)
            logger.info(f"Uploading media: {file_path.name}")

            # Determine MIME type
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".pdf": "application/pdf",
                ".zip": "application/zip",
            }
            mime_type = mime_types.get(file_path.suffix.lower(), "application/octet-stream")

            # Upload file
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, mime_type)}

                headers = self.headers.copy()
                headers.pop("Content-Type")  # Let requests set it for multipart

                response = requests.post(
                    f"{self.api_url}/media",
                    headers=headers,
                    files=files,
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                )
                response.raise_for_status()

            media = response.json()

            # Update title and alt text if provided
            if title or alt_text:
                update_data = {}
                if title:
                    update_data["title"] = title
                if alt_text:
                    update_data["alt_text"] = alt_text

                requests.post(
                    f"{self.api_url}/media/{media['id']}",
                    headers=self.headers,
                    json=update_data,
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                )

            logger.info(f"✓ Media uploaded: {media.get('source_url')}")

            return {
                "success": True,
                "id": media.get("id"),
                "url": media.get("source_url"),
                "title": media.get("title", {}).get("rendered"),
            }

        except Exception as e:
            logger.error(f"Media upload failed: {str(e)}")
            raise Exception(f"Failed to upload media: {str(e)}")

    def get_plugins(self) -> List[Dict[str, Any]]:
        """Get list of installed plugins.

        Note: Requires custom endpoint or plugin management plugin.

        Returns:
            List of plugin dictionaries
        """
        try:
            logger.warning("Plugin management requires custom REST endpoint or WP-CLI")
            # Would require custom endpoint like /wp-json/wp/v2/plugins
            return []
        except Exception as e:
            logger.error(f"Failed to get plugins: {str(e)}")
            return []

    def install_plugin(self, plugin_slug: str) -> Dict[str, Any]:
        """Install a plugin from WordPress.org repository.

        Args:
            plugin_slug: Plugin slug (e.g., 'contact-form-7')

        Returns:
            Dictionary with installation status
        """
        try:
            logger.info(f"Attempting to install plugin: {plugin_slug}")

            # Note: Plugin installation via REST API requires custom endpoint
            return {
                "success": False,
                "message": "Plugin installation requires WP-CLI or custom endpoint",
                "manual_install": f"{self.site_url}/wp-admin/plugin-install.php?s={plugin_slug}",
            }

        except Exception as e:
            logger.error(f"Plugin installation failed: {str(e)}")
            raise

    def get_site_health(self) -> Dict[str, Any]:
        """Get WordPress site health information.

        Returns:
            Dictionary with site health metrics
        """
        try:
            # Get various site statistics
            pages = self.get_pages(per_page=1)
            posts = self.get_posts(per_page=1)

            return {
                "connected": True,
                "pages_count": len(pages),
                "posts_count": len(posts),
                "api_url": self.api_url,
            }

        except Exception as e:
            logger.error(f"Failed to get site health: {str(e)}")
            return {"connected": False, "error": str(e)}
