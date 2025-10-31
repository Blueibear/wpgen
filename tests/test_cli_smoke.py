"""Smoke tests for the wpgen CLI."""

from click.testing import CliRunner

from wpgen.main import cli


def test_cli_help_displays_usage() -> None:
    """Invoking the CLI with --help should exit cleanly and show the description."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "WPGen" in result.output
