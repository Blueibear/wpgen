"""WordPress site manager with LLM-powered natural language control.

This module enables complete WordPress site management through natural language
commands, using an LLM to parse instructions and execute appropriate API calls.
"""

import json
from typing import Any, Dict

from ..llm.base import BaseLLMProvider
from ..utils.logger import get_logger
from .wordpress_api import WordPressAPI

logger = get_logger(__name__)


class WordPressManager:
    """Manage WordPress site through natural language commands using LLM."""

    def __init__(self, wordpress_api: WordPressAPI, llm_provider: BaseLLMProvider):
        """Initialize WordPress Manager.

        Args:
            wordpress_api: WordPress API client instance
            llm_provider: LLM provider for command parsing
        """
        self.api = wordpress_api
        self.llm = llm_provider
        logger.info("Initialized WordPress Manager with LLM control")

    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a natural language command on the WordPress site.

        Args:
            command: Natural language instruction (e.g., "Add a contact page")

        Returns:
            Dictionary with execution results

        Raises:
            Exception: If command execution fails
        """
        try:
            logger.info(f"Executing WordPress command: {command}")

            # Parse command using LLM
            parsed_command = self._parse_command(command)

            logger.info(f"Parsed command: {parsed_command.get('action')}")

            # Route to appropriate handler
            action = parsed_command.get("action")
            params = parsed_command.get("parameters", {})

            if action == "create_page":
                result = self._handle_create_page(params)
            elif action == "update_page":
                result = self._handle_update_page(params)
            elif action == "delete_page":
                result = self._handle_delete_page(params)
            elif action == "create_post":
                result = self._handle_create_post(params)
            elif action == "list_pages":
                result = self._handle_list_pages(params)
            elif action == "list_posts":
                result = self._handle_list_posts(params)
            elif action == "upload_media":
                result = self._handle_upload_media(params)
            elif action == "install_plugin":
                result = self._handle_install_plugin(params)
            elif action == "get_site_info":
                result = self._handle_get_site_info()
            else:
                result = {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "suggestion": "Try commands like: 'Add a contact page' or 'List all pages'",
                }

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return {"success": False, "error": str(e), "command": command}

    def _parse_command(self, command: str) -> Dict[str, Any]:
        """Parse natural language command using LLM.

        Args:
            command: Natural language instruction

        Returns:
            Dictionary with parsed action and parameters
        """
        system_prompt = """You are a WordPress site management assistant. Parse natural language
        commands into structured actions and parameters for WordPress REST API operations.

        Available actions:
        - create_page: Create a new page (params: title, content, status)
        - update_page: Update existing page (params: page_id or title, new_title, new_content)
        - delete_page: Delete a page (params: page_id or title)
        - create_post: Create a blog post (params: title, content, status)
        - list_pages: List all pages (params: search, per_page)
        - list_posts: List all posts (params: search, per_page)
        - upload_media: Upload media file (params: file_path, title, alt_text)
        - install_plugin: Install a plugin (params: plugin_slug)
        - get_site_info: Get site information and health

        Return ONLY valid JSON with this structure:
        {
          "action": "action_name",
          "parameters": {
            "param1": "value1",
            "param2": "value2"
          },
          "confidence": 0.95
        }"""

        parse_prompt = f"""Parse this WordPress command:

Command: "{command}"

Identify the action and extract all relevant parameters. If the command requires content
generation (like page content), generate appropriate placeholder content.

Return JSON only."""

        try:
            response = self.llm.generate(parse_prompt, system_prompt)

            # Extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1]) if len(lines) > 2 else response
                response = response.replace("```json", "").replace("```", "").strip()

            parsed = json.loads(response)
            logger.info(f"LLM parsed command with {parsed.get('confidence', 0):.0%} confidence")

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            # Fallback: simple keyword-based parsing
            return self._fallback_parse(command)
        except Exception as e:
            logger.error(f"Command parsing failed: {str(e)}")
            return self._fallback_parse(command)

    def _fallback_parse(self, command: str) -> Dict[str, Any]:
        """Fallback parser using simple keyword matching.

        Args:
            command: Natural language command

        Returns:
            Dictionary with best-guess action and parameters
        """
        command_lower = command.lower()

        # Detect action from keywords
        if (
            any(word in command_lower for word in ["add", "create", "new"])
            and "page" in command_lower
        ):
            # Extract title from command
            title = (
                command.replace("add", "")
                .replace("create", "")
                .replace("new", "")
                .replace("page", "")
                .strip()
            )
            if not title:
                title = "New Page"

            return {
                "action": "create_page",
                "parameters": {
                    "title": title.title(),
                    "content": f"<p>This is the {title} page.</p>",
                    "status": "publish",
                },
                "confidence": 0.7,
            }

        elif (
            any(word in command_lower for word in ["list", "show", "get"])
            and "page" in command_lower
        ):
            return {"action": "list_pages", "parameters": {}, "confidence": 0.8}

        elif "install" in command_lower and "plugin" in command_lower:
            # Try to extract plugin name
            words = command.split()
            plugin_slug = words[-1] if words else "unknown"

            return {
                "action": "install_plugin",
                "parameters": {"plugin_slug": plugin_slug.lower()},
                "confidence": 0.6,
            }

        else:
            return {"action": "get_site_info", "parameters": {}, "confidence": 0.3}

    def _handle_create_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create page action.

        Args:
            params: Page parameters (title, content, status, etc.)

        Returns:
            Dictionary with creation result
        """
        try:
            title = params.get("title", "New Page")
            content = params.get("content", "<p>Page content goes here.</p>")
            status = params.get("status", "publish")

            # Generate content using LLM if content is placeholder or missing
            if not content or content == "<p>Page content goes here.</p>":
                content = self._generate_page_content(title)

            result = self.api.create_page(
                title=title,
                content=content,
                status=status,
                **{k: v for k, v in params.items() if k not in ["title", "content", "status"]},
            )

            return {
                "success": True,
                "action": "create_page",
                "result": result,
                "message": f"Created page: {result.get('title')}",
            }

        except Exception as e:
            logger.error(f"Failed to create page: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_update_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update page action.

        Args:
            params: Update parameters (page_id, title, content, etc.)

        Returns:
            Dictionary with update result
        """
        try:
            page_id = params.get("page_id")

            # If page_id not provided, try to find by title
            if not page_id and "title" in params:
                pages = self.api.get_pages(search=params["title"])
                if pages:
                    page_id = pages[0]["id"]

            if not page_id:
                return {
                    "success": False,
                    "error": "Page not found. Provide page_id or existing title.",
                }

            update_data = {k: v for k, v in params.items() if k not in ["page_id"]}
            result = self.api.update_page(page_id, **update_data)

            return {
                "success": True,
                "action": "update_page",
                "result": result,
                "message": f"Updated page: {result.get('title')}",
            }

        except Exception as e:
            logger.error(f"Failed to update page: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_delete_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete page action.

        Args:
            params: Deletion parameters (page_id or title)

        Returns:
            Dictionary with deletion result
        """
        try:
            page_id = params.get("page_id")

            # If page_id not provided, try to find by title
            if not page_id and "title" in params:
                pages = self.api.get_pages(search=params["title"])
                if pages:
                    page_id = pages[0]["id"]

            if not page_id:
                return {"success": False, "error": "Page not found."}

            force = params.get("force", False)
            result = self.api.delete_page(page_id, force=force)

            return {
                "success": True,
                "action": "delete_page",
                "result": result,
                "message": f"Deleted page ID: {page_id}",
            }

        except Exception as e:
            logger.error(f"Failed to delete page: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_create_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create post action.

        Args:
            params: Post parameters (title, content, status, etc.)

        Returns:
            Dictionary with creation result
        """
        try:
            title = params.get("title", "New Post")
            content = params.get("content", "<p>Post content goes here.</p>")
            status = params.get("status", "publish")

            # Generate content using LLM if needed
            if not content or content == "<p>Post content goes here.</p>":
                content = self._generate_post_content(title)

            result = self.api.create_post(
                title=title,
                content=content,
                status=status,
                **{k: v for k, v in params.items() if k not in ["title", "content", "status"]},
            )

            return {
                "success": True,
                "action": "create_post",
                "result": result,
                "message": f"Created post: {result.get('title')}",
            }

        except Exception as e:
            logger.error(f"Failed to create post: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_list_pages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list pages action.

        Args:
            params: Query parameters

        Returns:
            Dictionary with pages list
        """
        try:
            pages = self.api.get_pages(**params)

            return {
                "success": True,
                "action": "list_pages",
                "count": len(pages),
                "pages": pages,
                "message": f"Found {len(pages)} page(s)",
            }

        except Exception as e:
            logger.error(f"Failed to list pages: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_list_posts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list posts action.

        Args:
            params: Query parameters

        Returns:
            Dictionary with posts list
        """
        try:
            posts = self.api.get_posts(**params)

            return {
                "success": True,
                "action": "list_posts",
                "count": len(posts),
                "posts": posts,
                "message": f"Found {len(posts)} post(s)",
            }

        except Exception as e:
            logger.error(f"Failed to list posts: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_upload_media(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle upload media action.

        Args:
            params: Media upload parameters

        Returns:
            Dictionary with upload result
        """
        try:
            file_path = params.get("file_path")
            if not file_path:
                return {"success": False, "error": "file_path required"}

            result = self.api.upload_media(
                file_path=file_path, title=params.get("title"), alt_text=params.get("alt_text")
            )

            return {
                "success": True,
                "action": "upload_media",
                "result": result,
                "message": f"Uploaded media: {result.get('url')}",
            }

        except Exception as e:
            logger.error(f"Failed to upload media: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_install_plugin(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle install plugin action.

        Args:
            params: Plugin installation parameters

        Returns:
            Dictionary with installation result
        """
        try:
            plugin_slug = params.get("plugin_slug")
            if not plugin_slug:
                return {"success": False, "error": "plugin_slug required"}

            result = self.api.install_plugin(plugin_slug)

            return {
                "success": result.get("success", False),
                "action": "install_plugin",
                "result": result,
                "message": result.get("message", f"Plugin: {plugin_slug}"),
            }

        except Exception as e:
            logger.error(f"Failed to install plugin: {str(e)}")
            return {"success": False, "error": str(e)}

    def _handle_get_site_info(self) -> Dict[str, Any]:
        """Handle get site info action.

        Returns:
            Dictionary with site information
        """
        try:
            connection_info = self.api.test_connection()
            health_info = self.api.get_site_health()

            return {
                "success": True,
                "action": "get_site_info",
                "site_info": connection_info,
                "health": health_info,
                "message": f"Connected to: {connection_info.get('site_name')}",
            }

        except Exception as e:
            logger.error(f"Failed to get site info: {str(e)}")
            return {"success": False, "error": str(e)}

    def _generate_page_content(self, title: str) -> str:
        """Generate page content using LLM.

        Args:
            title: Page title

        Returns:
            Generated HTML content
        """
        try:
            logger.info(f"Generating content for page: {title}")

            prompt = f"""Generate professional HTML content for a WordPress page titled "{title}".

Include:
- A welcoming introduction paragraph
- 2-3 relevant sections with headings
- Appropriate HTML tags (h2, p, ul, etc.)
- Professional, engaging copy

Output only the HTML content, no explanations."""

            content = self.llm.generate(prompt)

            # Clean up any markdown formatting
            content = content.replace("```html", "").replace("```", "").strip()

            return content

        except Exception as e:
            logger.error(f"Failed to generate content: {str(e)}")
            return f"<h1>{title}</h1><p>Welcome to the {title} page.</p>"

    def _generate_post_content(self, title: str) -> str:
        """Generate blog post content using LLM.

        Args:
            title: Post title

        Returns:
            Generated HTML content
        """
        try:
            logger.info(f"Generating content for post: {title}")

            prompt = f"""Generate engaging blog post content for a post titled "{title}".

Include:
- An attention-grabbing introduction
- 3-4 main paragraphs with valuable information
- A conclusion or call-to-action
- Appropriate HTML formatting

Output only the HTML content."""

            content = self.llm.generate(prompt)

            # Clean up formatting
            content = content.replace("```html", "").replace("```", "").strip()

            return content

        except Exception as e:
            logger.error(f"Failed to generate content: {str(e)}")
            return f"<h2>{title}</h2><p>This is a blog post about {title.lower()}.</p>"
