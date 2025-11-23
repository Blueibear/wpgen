"""Flask web application for WPGen.

Provides a web-based interface for generating WordPress themes.
"""

import os
import sys
import traceback
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from wpgen.github.integration import GitHubIntegration
from wpgen.parsers.prompt_parser import PromptParser
from wpgen.generators.wordpress_generator import WordPressGenerator
from wpgen.utils.config import get_llm_provider as get_provider
from wpgen.utils.logger import setup_logger
from wpgen.config_schema import load_and_validate_config, get_redacted_config_summary


def create_app(config: dict = None, validate_config: bool = True):
    """Create and configure Flask application.

    Args:
        config: Configuration dictionary (if None, loads from config.yaml)
        validate_config: Whether to validate config on startup

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load and validate config
    if config is None:
        config_file = Path("config.yaml")
        if validate_config:
            try:
                # Use Pydantic validation
                validated_config = load_and_validate_config(str(config_file))
                config = validated_config.model_dump()
            except ValidationError as e:
                print(f"❌ Configuration validation failed:\n", file=sys.stderr)
                for error in e.errors():
                    field = " -> ".join(str(x) for x in error["loc"])
                    print(f"  • {field}: {error['msg']}", file=sys.stderr)
                print("\nPlease fix your config.yaml file.", file=sys.stderr)
                sys.exit(78)  # EX_CONFIG
            except Exception as e:
                print(f"❌ Failed to load configuration: {e}", file=sys.stderr)
                sys.exit(78)
        else:
            import yaml
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}

    app.config["WPGEN_CONFIG"] = config
    app.config["SECRET_KEY"] = config.get("web", {}).get("secret_key", "dev-secret-key")

    # Setup CORS if enabled
    cors_enabled = config.get("web", {}).get("cors_enabled", False)
    if cors_enabled:
        try:
            from flask_cors import CORS
            cors_origins = config.get("web", {}).get("cors_origins", "*")
            CORS(app, origins=cors_origins)
            print(f"✓ CORS enabled for origins: {cors_origins}")
        except ImportError:
            print("⚠ flask-cors not installed, CORS disabled", file=sys.stderr)

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

    # Error handlers for structured error responses
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            "code": 400,
            "message": "Bad Request",
            "details": str(error.description) if hasattr(error, "description") else str(error)
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            "code": 404,
            "message": "Not Found",
            "details": "The requested resource was not found"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            "code": 500,
            "message": "Internal Server Error",
            "details": "An unexpected error occurred. Please check the logs."
        }), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions with structured response."""
        # Pass through HTTP errors
        if isinstance(error, HTTPException):
            return jsonify({
                "code": error.code,
                "message": error.name,
                "details": error.description
            }), error.code

        # Log unexpected errors
        logger.error(f"Unhandled exception: {error}", exc_info=True)

        # Return generic error in production, detailed in development
        if app.debug:
            return jsonify({
                "code": 500,
                "message": "Internal Server Error",
                "details": str(error),
                "traceback": traceback.format_exc()
            }), 500
        else:
            return jsonify({
                "code": 500,
                "message": "Internal Server Error",
                "details": "An unexpected error occurred"
            }), 500

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

    @app.route("/version")
    def version():
        """Version information endpoint."""
        from wpgen import __version__
        return jsonify({
            "version": __version__,
            "app": "wpgen-web"
        })

    @app.post("/api/config/validate")
    def api_config_validate():
        """Validate configuration from request or file.

        Expected JSON payload (optional):
        {
            "config": {...}  # Config dict to validate
        }

        If no payload, validates current config.yaml.

        Returns:
            JSON response with validation results
        """
        try:
            data = request.get_json(silent=True) or {}
            config_to_validate = data.get("config")

            if config_to_validate:
                # Validate provided config
                from wpgen.config_schema import WPGenConfig
                validated = WPGenConfig(**config_to_validate)
                summary = get_redacted_config_summary(validated)
                return jsonify({
                    "ok": True,
                    "message": "Configuration is valid",
                    "config": summary
                }), 200
            else:
                # Validate current config file
                validated = load_and_validate_config("config.yaml")
                summary = get_redacted_config_summary(validated)
                return jsonify({
                    "ok": True,
                    "message": "Configuration file is valid",
                    "config": summary
                }), 200

        except ValidationError as ve:
            errors = []
            for error in ve.errors():
                field = " -> ".join(str(x) for x in error["loc"])
                errors.append({
                    "field": field,
                    "message": error["msg"],
                    "type": error["type"]
                })
            return jsonify({
                "ok": False,
                "message": "Configuration validation failed",
                "errors": errors
            }), 400
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return jsonify({
                "ok": False,
                "message": f"Validation error: {str(e)}"
            }), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
