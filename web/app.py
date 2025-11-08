"""Flask web application for WPGen.

Provides a web-based interface for generating WordPress themes.
"""

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from wpgen import (
    GitHubIntegration,
    PromptParser,
    WordPressGenerator,
    setup_logger,
)
from wpgen import (
    get_llm_provider as get_provider,
)


def create_app(config: dict = None):
    """Create and configure Flask application.

    Args:
        config: Configuration dictionary

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load config
    if config is None:
        import yaml

        config_file = Path("config.yaml")
        if config_file.exists():
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
        else:
            config = {}

    app.config["WPGEN_CONFIG"] = config
    app.config["SECRET_KEY"] = config.get("web", {}).get("secret_key", "dev-secret-key")

    # Setup logging
    log_config = config.get("logging", {})
    logger = setup_logger(
        "wpgen.web",
        log_file=log_config.get("log_file", "logs/wpgen.log"),
        level=log_config.get("level", "INFO"),
        format_type=log_config.get("format", "text"),
        colored_console=log_config.get("colored_console", True),
        console_output=log_config.get("console_output", True),
    )

    def get_llm_provider():
        """Get configured LLM provider from app config."""
        cfg = app.config["WPGEN_CONFIG"]
        return get_provider(cfg)

    @app.route("/")
    def index():
        """Render home page."""
        return render_template("index.html")

    @app.route("/api/generate", methods=["POST"])
    def api_generate():
        """API endpoint to generate a WordPress theme.

        Expected JSON payload:
        {
            "prompt": "description of the website",
            "push_to_github": true/false,
            "repo_name": "optional-repo-name"
        }

        Returns:
            JSON response with generation results
        """
        try:
            data = request.get_json()
            prompt = data.get("prompt", "").strip()

            if not prompt:
                return jsonify({"success": False, "error": "Prompt is required"}), 400

            push_to_github = data.get("push_to_github", False)
            repo_name = data.get("repo_name", "").strip()

            logger.info(f"Web API: Generating theme from prompt: {prompt[:100]}")

            # Initialize LLM provider
            llm_provider = get_llm_provider()

            # Parse prompt
            parser = PromptParser(llm_provider)
            requirements = parser.parse(prompt)

            # Generate theme
            cfg = app.config["WPGEN_CONFIG"]
            output_dir = cfg.get("output", {}).get("output_dir", "output")
            generator = WordPressGenerator(llm_provider, output_dir, cfg.get("wordpress", {}))
            theme_dir = generator.generate(requirements)

            result = {
                "success": True,
                "theme_name": requirements["theme_name"],
                "theme_display_name": requirements["theme_display_name"],
                "description": requirements["description"],
                "features": requirements["features"],
                "theme_dir": theme_dir,
            }

            # Push to GitHub if requested
            if push_to_github:
                github_token = os.getenv("GITHUB_TOKEN")
                if not github_token:
                    result["github_warning"] = "GITHUB_TOKEN not found, skipping push"
                    logger.warning("GITHUB_TOKEN not set, skipping push")
                else:
                    github = GitHubIntegration(github_token, cfg.get("github", {}))

                    if not repo_name:
                        repo_name = github.generate_repo_name(requirements["theme_name"])

                    repo_url = github.push_to_github(theme_dir, repo_name, requirements)

                    result["github_url"] = repo_url
                    result["repo_name"] = repo_name

                    # Create deployment workflow if enabled
                    if cfg.get("deployment", {}).get("enabled", False):
                        github.create_deployment_workflow(theme_dir, cfg.get("deployment", {}))
                        result["deployment_workflow"] = True

            logger.info(f"Web API: Successfully generated theme: {requirements['theme_name']}")
            return jsonify(result)

        except Exception as e:
            logger.error(f"Web API: Generation failed: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/analyze", methods=["POST"])
    def api_analyze():
        """API endpoint to analyze a prompt without generating.

        Expected JSON payload:
        {
            "prompt": "description of the website"
        }

        Returns:
            JSON response with parsed requirements
        """
        try:
            data = request.get_json()
            prompt = data.get("prompt", "").strip()

            if not prompt:
                return jsonify({"success": False, "error": "Prompt is required"}), 400

            logger.info(f"Web API: Analyzing prompt: {prompt[:100]}")

            # Initialize LLM provider
            llm_provider = get_llm_provider()

            # Parse prompt
            parser = PromptParser(llm_provider)
            requirements = parser.parse(prompt)

            logger.info("Web API: Successfully analyzed prompt")
            return jsonify({"success": True, "requirements": requirements})

        except Exception as e:
            logger.error(f"Web API: Analysis failed: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/config", methods=["GET"])
    def api_config():
        """Get current configuration (safe fields only)."""
        cfg = app.config["WPGEN_CONFIG"]

        safe_config = {
            "llm_provider": cfg.get("llm", {}).get("provider", "openai"),
            "wordpress": {
                "theme_prefix": cfg.get("wordpress", {}).get("theme_prefix", "wpgen"),
                "wp_version": cfg.get("wordpress", {}).get("wp_version", "6.4"),
            },
            "github": {
                "enabled": bool(os.getenv("GITHUB_TOKEN")),
                "auto_create": cfg.get("github", {}).get("auto_create", True),
            },
            "deployment": {
                "enabled": cfg.get("deployment", {}).get("enabled", False),
                "method": cfg.get("deployment", {}).get("method", "github_actions"),
            },
        }

        return jsonify(safe_config)

    @app.route("/health")
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
