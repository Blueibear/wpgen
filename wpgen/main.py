#!/usr/bin/env python3
"""WPGen - WordPress Theme Generator CLI.

Command-line interface for generating WordPress themes from natural language descriptions.
"""

import os
import sys
from pathlib import Path

import click
import yaml

from wpgen.generators import WordPressGenerator
from wpgen.github import GitHubIntegration

# Import directly from submodules to avoid import-time SDK crashes
from wpgen.parsers import PromptParser
from wpgen.utils import get_llm_provider, setup_logger


def _ensure_env_loaded():
    """Lazily load environment variables when needed."""
    from dotenv import load_dotenv
    load_dotenv()


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    if not config_file.exists():
        click.echo(f"Warning: Config file not found: {config_path}", err=True)
        return {}

    with open(config_file, "r") as f:
        return yaml.safe_load(f)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """WPGen - WordPress Theme Generator.

    Generate WordPress themes from natural language descriptions using AI.
    """
    pass


@cli.command()
@click.argument("prompt", required=False)
@click.option(
    "--config", "-c", "config_path", default="config.yaml", help="Path to configuration file"
)
@click.option("--output", "-o", default=None, help="Output directory for generated theme")
@click.option("--push/--no-push", default=True, help="Push to GitHub after generation")
@click.option(
    "--repo-name",
    "-r",
    default=None,
    help="GitHub repository name (auto-generated if not specified)",
)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode - prompt for input")
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["openai", "anthropic", "local-lmstudio", "local-ollama"], case_sensitive=False),
    default=None,
    help="LLM provider (overrides config file)",
)
@click.option(
    "--model",
    "-m",
    default=None,
    help="Model name (overrides config file)",
)
@click.option(
    "--design-profile",
    "-d",
    type=click.Choice(["modern_streetwear", "minimalist", "corporate", "vibrant_bold", "earthy_natural"], case_sensitive=False),
    default=None,
    help="Design profile for theme styling (modern_streetwear, minimalist, corporate, vibrant_bold, earthy_natural)",
)
def generate(
    prompt: str | None,
    config_path: str,
    output: str | None,
    push: bool,
    repo_name: str | None,
    interactive: bool,
    provider: str | None,
    model: str | None,
    design_profile: str | None,
):
    """Generate a WordPress theme from a description.

    PROMPT: Natural language description of the WordPress site.

    Example:
        wpgen generate "Create a dark-themed photography portfolio with blog"
    """
    try:
        # Load environment variables
        _ensure_env_loaded()

        # Load configuration
        cfg = load_config(config_path)

        # Apply CLI overrides to config
        if provider:
            if "llm" not in cfg:
                cfg["llm"] = {}
            cfg["llm"]["provider"] = provider
        if model:
            if "llm" not in cfg:
                cfg["llm"] = {}
            cfg["llm"]["model"] = model

        # Setup logging
        log_config = cfg.get("logging", {})
        logger = setup_logger(
            "wpgen",
            log_file=log_config.get("log_file", "logs/wpgen.log"),
            level=log_config.get("level", "INFO"),
            format_type=log_config.get("format", "text"),
            colored_console=log_config.get("colored_console", True),
            console_output=log_config.get("console_output", True),
        )

        logger.info("Starting WPGen theme generation")

        # Get prompt
        if interactive or not prompt:
            click.echo("\n🎨 WPGen - WordPress Theme Generator\n")
            prompt = click.prompt("Describe your WordPress website", type=str)

        if not prompt:
            click.echo("Error: Prompt is required", err=True)
            sys.exit(1)

        click.echo(f"\n📝 Analyzing prompt: {prompt}\n")

        # Initialize LLM provider
        provider_name = cfg.get("llm", {}).get("provider", "openai")
        click.echo(f"🤖 Using LLM provider: {provider_name}")
        llm_provider = get_llm_provider(cfg)
        logger.info(f"Initialized LLM provider: {provider_name}")

        # Parse prompt
        click.echo("🔍 Parsing requirements...")
        parser = PromptParser(llm_provider)
        requirements = parser.parse(prompt)

        click.echo(f"✅ Theme: {requirements['theme_display_name']}")
        click.echo(f"   Description: {requirements['description']}")
        click.echo(f"   Features: {', '.join(requirements['features'])}")

        # Apply design profile if specified
        if design_profile:
            from wpgen.design_profiles import get_design_profile
            profile = get_design_profile(design_profile)
            requirements["design_profile"] = profile.to_dict()
            click.echo(f"   Design Profile: {design_profile}")

        click.echo()

        # Generate theme
        click.echo("🏗️  Generating WordPress theme...")
        output_dir = output or cfg.get("output", {}).get("output_dir", "output")
        generator = WordPressGenerator(llm_provider, output_dir, cfg.get("wordpress", {}))
        theme_dir = generator.generate(requirements)

        click.echo(f"✅ Theme generated successfully: {theme_dir}\n")

        # Push to GitHub
        if push:
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                click.echo("⚠️  GITHUB_TOKEN not found, skipping GitHub push", err=True)
                logger.warning("GITHUB_TOKEN not set, skipping push")
            else:
                click.echo("📤 Pushing to GitHub...")
                github = GitHubIntegration(github_token, cfg.get("github", {}))

                if not repo_name:
                    repo_name = github.generate_repo_name(requirements["theme_name"])

                repo_url = github.push_to_github(theme_dir, repo_name, requirements)

                click.echo(f"✅ Pushed to GitHub: {repo_url}\n")

                # Create deployment workflow if enabled
                if cfg.get("deployment", {}).get("enabled", False):
                    click.echo("📦 Creating deployment workflow...")
                    github.create_deployment_workflow(theme_dir, cfg.get("deployment", {}))
                    click.echo("✅ Deployment workflow created\n")

        click.echo("🎉 Done! Your WordPress theme is ready.\n")

        # Show next steps
        click.echo("Next steps:")
        click.echo(f"  1. Review the generated theme in: {theme_dir}")
        click.echo("  2. Test the theme locally with WordPress")
        if push and github_token:
            click.echo("  3. Configure deployment secrets in GitHub (if using deployment)")
        click.echo("  4. Customize the theme as needed\n")

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}\n", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--config", "-c", "config_path", default="config.yaml", help="Path to configuration file"
)
def serve(config_path: str):
    """Start the web UI server.

    Launch a Flask web server for the WPGen web interface.
    """
    try:
        _ensure_env_loaded()
        cfg = load_config(config_path)
        web_config = cfg.get("web", {})

        if not web_config.get("enabled", True):
            click.echo("Web UI is disabled in configuration", err=True)
            sys.exit(1)

        # Import Flask app
        from web.app import create_app

        app = create_app(cfg)

        host = web_config.get("host", "0.0.0.0")
        port = web_config.get("port", 5000)
        debug = web_config.get("debug", False)

        click.echo(f"\n🌐 Starting WPGen Web UI on http://{host}:{port}\n")
        click.echo("Press CTRL+C to stop\n")

        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}\n", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--config", "-c", "config_path", default="config.yaml", help="Path to configuration file"
)
@click.option("--share", is_flag=True, help="Create a public share link")
@click.option(
    "--server-name",
    default="0.0.0.0",
    show_default=True,
    help="Gradio host to bind (use 127.0.0.1 on Windows)",
)
@click.option(
    "--server-port",
    "-p",
    default=7860,
    show_default=True,
    type=int,
    help="Port to run the GUI server on",
)
def gui(config_path: str, share: bool, server_name: str, server_port: int):
    """Launch the graphical user interface.

    Start a Gradio-based GUI for generating WordPress themes with
    support for image uploads and document processing.
    """
    try:
        _ensure_env_loaded()
        cfg = load_config(config_path)

        # Env var overrides
        server_name = os.getenv("GRADIO_SERVER_NAME", server_name)
        server_port = int(os.getenv("GRADIO_SERVER_PORT", server_port))

        # Import GUI module
        from wpgen.gui import launch_gui

        shown_host = "localhost" if server_name in ("0.0.0.0", "::") else server_name
        click.echo(f"\n🎨 Launching WPGen GUI on http://{shown_host}:{server_port}\n")
        if share:
            click.echo("📡 Creating public share link...\n")
        click.echo("Press CTRL+C to stop\n")

        launch_gui(cfg, share=share, server_name=server_name, server_port=server_port)

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}\n", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.argument("theme_path")
def validate(theme_path: str):
    """Validate a WordPress theme for syntax errors.

    THEME_PATH: Path to the theme directory to validate.

    This command checks all PHP files in the theme for syntax errors
    that could cause WordPress to crash.

    Example:
        wpgen validate output/my-theme
    """
    try:
        _ensure_env_loaded()
        from wpgen.utils.theme_validator import print_validation_report, validate_theme_directory

        click.echo(f"\n🔍 Validating theme: {theme_path}\n")

        results = validate_theme_directory(theme_path)
        print_validation_report(results)

        # Exit with error code if validation failed
        if results.get('invalid_files', 0) > 0 or results.get('errors'):
            sys.exit(1)

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}\n", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command()
def init():
    """Initialize WPGen configuration.

    Create a new .env file with required environment variables.
    """
    env_file = Path(".env")

    if env_file.exists():
        if not click.confirm("⚠️  .env file already exists. Overwrite?"):
            click.echo("Aborted.")
            return

    env_content = """# WPGen Environment Configuration

# LLM Provider API Keys
# Get OpenAI key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Get Anthropic key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GitHub Configuration
# Get token from: https://github.com/settings/tokens
# Required scopes: repo, workflow
GITHUB_TOKEN=your_github_token_here

# Deployment Configuration (optional)
FTP_HOST=
FTP_USERNAME=
FTP_PASSWORD=

SSH_HOST=
SSH_USERNAME=
SSH_PRIVATE_KEY=
SSH_REMOTE_PATH=
"""

    env_file.write_text(env_content)
    click.echo(f"✅ Created .env file: {env_file}")
    click.echo("\n📝 Next steps:")
    click.echo("  1. Edit .env and add your API keys")
    click.echo("  2. Run 'wpgen generate \"your description\"' to create a theme\n")


@cli.group()
def wordpress():
    """WordPress site management commands."""
    pass


@wordpress.command()
@click.option("--config", "-c", "config_path", default="config.yaml", help="Path to config file")
@click.option("--site-url", "site_url_arg", help="WordPress site URL (overrides config)")
@click.option("--username", "username_arg", help="WordPress username (overrides config)")
@click.option("--password", "password_arg", help="WordPress password (overrides config)")
def test(config_path, site_url_arg, username_arg, password_arg):
    """Test WordPress REST API connection."""
    try:
        _ensure_env_loaded()
        from wpgen.wordpress import WordPressAPI

        # Load config
        config = load_config(config_path)
        wp_config = config.get("wordpress_api", {})

        # Get credentials (CLI args override config override env)
        site_url = site_url_arg or os.getenv("WP_SITE_URL", wp_config.get("site_url", ""))
        username_val = username_arg or os.getenv("WP_USERNAME", wp_config.get("username", ""))
        password_val = password_arg or os.getenv(
            "WP_APP_PASSWORD", os.getenv("WP_PASSWORD", wp_config.get("password", ""))
        )

        if not all([site_url, username_val, password_val]):
            click.echo("❌ Error: WordPress credentials not configured.")
            click.echo(
                "Set WP_SITE_URL, WP_USERNAME, and WP_APP_PASSWORD in .env or use CLI options."
            )
            sys.exit(1)

        click.echo(f"🔄 Testing connection to {site_url}...")

        # Initialize API
        wp_api = WordPressAPI(
            site_url=site_url,
            username=username_val,
            password=password_val,
            verify_ssl=wp_config.get("verify_ssl", True),
            timeout=wp_config.get("timeout", 30),
        )

        # Test connection
        info = wp_api.test_connection()

        click.echo("\n✅ Connection successful!")
        click.echo("\n📊 Site Information:")
        click.echo(f"  Site Name: {info.get('site_name', 'N/A')}")
        click.echo(f"  Description: {info.get('site_description', 'N/A')}")
        click.echo(f"  URL: {info.get('url', 'N/A')}")
        click.echo(f"  User: {info.get('user', 'N/A')} (ID: {info.get('user_id', 'N/A')})")

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}\n", err=True)
        sys.exit(1)


@wordpress.command()
@click.argument("command_text")
@click.option("--config", "-c", "config_path", default="config.yaml", help="Path to config file")
def manage(command_text, config_path):
    """Execute WordPress management commands using natural language.

    Examples:
      wpgen wordpress manage "Add a contact page"
      wpgen wordpress manage "List all pages"
      wpgen wordpress manage "Create a blog post about AI"
    """
    try:
        _ensure_env_loaded()
        from wpgen.utils import get_llm_provider
        from wpgen.wordpress import WordPressAPI, WordPressManager

        # Load config
        config = load_config(config_path)
        wp_config = config.get("wordpress_api", {})

        if not wp_config.get("enable_llm_control", True):
            click.echo("❌ LLM control is disabled in config.yaml")
            sys.exit(1)

        # Get credentials
        site_url = os.getenv("WP_SITE_URL", wp_config.get("site_url", ""))
        username = os.getenv("WP_USERNAME", wp_config.get("username", ""))
        password = os.getenv(
            "WP_APP_PASSWORD", os.getenv("WP_PASSWORD", wp_config.get("password", ""))
        )

        if not all([site_url, username, password]):
            click.echo("❌ Error: WordPress credentials not configured.")
            sys.exit(1)

        click.echo(f"🤖 Processing command: {command_text}")

        # Initialize WordPress API
        wp_api = WordPressAPI(
            site_url=site_url,
            username=username,
            password=password,
            verify_ssl=wp_config.get("verify_ssl", True),
            timeout=wp_config.get("timeout", 30),
        )

        # Initialize LLM provider
        llm_provider = get_llm_provider(config)

        # Initialize WordPress Manager
        wp_manager = WordPressManager(wp_api, llm_provider)

        # Execute command
        result = wp_manager.execute_command(command_text)

        # Display result
        if result.get("success"):
            click.echo(f"\n✅ {result.get('message', 'Command executed successfully')}")

            # Show additional details based on action
            if "pages" in result:
                click.echo(f"\n📄 Pages ({result.get('count', 0)}):")
                for page in result["pages"]:
                    click.echo(f"  - {page.get('title')} ({page.get('link')})")
            elif "posts" in result:
                click.echo(f"\n📝 Posts ({result.get('count', 0)}):")
                for post in result["posts"]:
                    click.echo(f"  - {post.get('title')} ({post.get('link')})")
            elif "result" in result and isinstance(result["result"], dict):
                if "link" in result["result"]:
                    click.echo(f"  URL: {result['result']['link']}")

        else:
            click.echo(f"\n❌ {result.get('error', 'Command failed')}")
            if "suggestion" in result:
                click.echo(f"💡 {result['suggestion']}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}\n", err=True)
        sys.exit(1)


def main():
    """Main entry point for the wpgen CLI tool."""
    cli()


if __name__ == "__main__":
    main()
