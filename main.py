#!/usr/bin/env python3
"""WPGen - WordPress Theme Generator CLI.

Command-line interface for generating WordPress themes from natural language descriptions.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from dotenv import load_dotenv

from wpgen import (
    OpenAIProvider,
    AnthropicProvider,
    PromptParser,
    WordPressGenerator,
    GitHubIntegration,
    setup_logger,
    get_logger,
)


# Load environment variables
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


def get_llm_provider(config: dict):
    """Initialize and return the configured LLM provider.

    Args:
        config: Configuration dictionary

    Returns:
        LLM provider instance

    Raises:
        ValueError: If provider is not configured correctly
    """
    provider_name = config.get("llm", {}).get("provider", "openai")

    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        provider_config = config.get("llm", {}).get("openai", {})
        return OpenAIProvider(api_key, provider_config)

    elif provider_name == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        provider_config = config.get("llm", {}).get("anthropic", {})
        return AnthropicProvider(api_key, provider_config)

    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")


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
    "--config",
    "-c",
    default="config.yaml",
    help="Path to configuration file"
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output directory for generated theme"
)
@click.option(
    "--push/--no-push",
    default=True,
    help="Push to GitHub after generation"
)
@click.option(
    "--repo-name",
    "-r",
    default=None,
    help="GitHub repository name (auto-generated if not specified)"
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive mode - prompt for input"
)
def generate(
    prompt: Optional[str],
    config: str,
    output: Optional[str],
    push: bool,
    repo_name: Optional[str],
    interactive: bool
):
    """Generate a WordPress theme from a description.

    PROMPT: Natural language description of the WordPress site.

    Example:
        wpgen generate "Create a dark-themed photography portfolio with blog"
    """
    try:
        # Load configuration
        cfg = load_config(config)

        # Setup logging
        log_config = cfg.get("logging", {})
        logger = setup_logger(
            "wpgen",
            log_file=log_config.get("log_file", "logs/wpgen.log"),
            level=log_config.get("level", "INFO"),
            format_type=log_config.get("format", "text"),
            colored_console=log_config.get("colored_console", True),
            console_output=log_config.get("console_output", True)
        )

        logger.info("Starting WPGen theme generation")

        # Get prompt
        if interactive or not prompt:
            click.echo("\n🎨 WPGen - WordPress Theme Generator\n")
            prompt = click.prompt(
                "Describe your WordPress website",
                type=str
            )

        if not prompt:
            click.echo("Error: Prompt is required", err=True)
            sys.exit(1)

        click.echo(f"\n📝 Analyzing prompt: {prompt}\n")

        # Initialize LLM provider
        llm_provider = get_llm_provider(cfg)
        logger.info(f"Initialized LLM provider: {cfg.get('llm', {}).get('provider', 'openai')}")

        # Parse prompt
        click.echo("🔍 Parsing requirements...")
        parser = PromptParser(llm_provider)
        requirements = parser.parse(prompt)

        click.echo(f"✅ Theme: {requirements['theme_display_name']}")
        click.echo(f"   Description: {requirements['description']}")
        click.echo(f"   Features: {', '.join(requirements['features'])}")
        click.echo()

        # Generate theme
        click.echo("🏗️  Generating WordPress theme...")
        output_dir = output or cfg.get("output", {}).get("output_dir", "output")
        generator = WordPressGenerator(
            llm_provider,
            output_dir,
            cfg.get("wordpress", {})
        )
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

                repo_url = github.push_to_github(
                    theme_dir,
                    repo_name,
                    requirements
                )

                click.echo(f"✅ Pushed to GitHub: {repo_url}\n")

                # Create deployment workflow if enabled
                if cfg.get("deployment", {}).get("enabled", False):
                    click.echo("📦 Creating deployment workflow...")
                    github.create_deployment_workflow(
                        theme_dir,
                        cfg.get("deployment", {})
                    )
                    click.echo("✅ Deployment workflow created\n")

        click.echo("🎉 Done! Your WordPress theme is ready.\n")

        # Show next steps
        click.echo("Next steps:")
        click.echo(f"  1. Review the generated theme in: {theme_dir}")
        click.echo("  2. Test the theme locally with WordPress")
        if push and github_token:
            click.echo(f"  3. Configure deployment secrets in GitHub (if using deployment)")
        click.echo("  4. Customize the theme as needed\n")

    except Exception as e:
        click.echo(f"\n❌ Error: {str(e)}\n", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to configuration file"
)
def serve(config: str):
    """Start the web UI server.

    Launch a Flask web server for the WPGen web interface.
    """
    try:
        cfg = load_config(config)
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


if __name__ == "__main__":
    cli()
