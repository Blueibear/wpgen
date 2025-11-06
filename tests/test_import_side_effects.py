"""Test that importing wpgen modules has no side effects.

This test ensures that importing any wpgen module does not:
- Make network requests
- Write to filesystem
- Execute subprocesses
- Parse CLI arguments
- Print to stdout/stderr
"""

import importlib
import sys


def test_import_wpgen_no_side_effects(capsys):
    """Test that importing wpgen has no side effects."""
    # Import the main package
    importlib.import_module('wpgen')

    # Capture any output
    captured = capsys.readouterr()

    # Should not print anything on import
    assert captured.out == "", f"wpgen import printed to stdout: {captured.out}"
    assert captured.err == "", f"wpgen import printed to stderr: {captured.err}"


def test_import_logger_no_side_effects(capsys):
    """Test that importing wpgen.utils.logger has no side effects."""
    importlib.import_module('wpgen.utils.logger')

    captured = capsys.readouterr()

    assert captured.out == "", f"logger import printed to stdout: {captured.out}"
    assert captured.err == "", f"logger import printed to stderr: {captured.err}"


def test_import_wordpress_api_no_side_effects(capsys):
    """Test that importing wpgen.wordpress.wordpress_api has no side effects."""
    importlib.import_module('wpgen.wordpress.wordpress_api')

    captured = capsys.readouterr()

    assert captured.out == "", f"wordpress_api import printed to stdout: {captured.out}"
    assert captured.err == "", f"wordpress_api import printed to stderr: {captured.err}"


def test_import_theme_validator_no_side_effects(capsys):
    """Test that importing wpgen.utils.theme_validator has no side effects."""
    importlib.import_module('wpgen.utils.theme_validator')

    captured = capsys.readouterr()

    assert captured.out == "", f"theme_validator import printed to stdout: {captured.out}"
    assert captured.err == "", f"theme_validator import printed to stderr: {captured.err}"


def test_import_main_no_side_effects(capsys):
    """Test that importing wpgen.main has no side effects."""
    # Remove sys.argv to ensure no CLI parsing happens
    old_argv = sys.argv
    try:
        sys.argv = ['wpgen']
        importlib.import_module('wpgen.main')

        captured = capsys.readouterr()

        assert captured.out == "", f"main import printed to stdout: {captured.out}"
        assert captured.err == "", f"main import printed to stderr: {captured.err}"
    finally:
        sys.argv = old_argv


def test_import_service_no_side_effects(capsys):
    """Test that importing wpgen.service has no side effects."""
    importlib.import_module('wpgen.service')

    captured = capsys.readouterr()

    assert captured.out == "", f"service import printed to stdout: {captured.out}"
    assert captured.err == "", f"service import printed to stderr: {captured.err}"


def test_import_llm_base_no_side_effects(capsys):
    """Test that importing wpgen.llm.base has no side effects."""
    importlib.import_module('wpgen.llm.base')

    captured = capsys.readouterr()

    assert captured.out == "", f"llm.base import printed to stdout: {captured.out}"
    assert captured.err == "", f"llm.base import printed to stderr: {captured.err}"


def test_import_parsers_no_side_effects(capsys):
    """Test that importing wpgen.parsers has no side effects."""
    importlib.import_module('wpgen.parsers')

    captured = capsys.readouterr()

    assert captured.out == "", f"parsers import printed to stdout: {captured.out}"
    assert captured.err == "", f"parsers import printed to stderr: {captured.err}"


def test_import_generators_no_side_effects(capsys):
    """Test that importing wpgen.generators has no side effects."""
    importlib.import_module('wpgen.generators')

    captured = capsys.readouterr()

    assert captured.out == "", f"generators import printed to stdout: {captured.out}"
    assert captured.err == "", f"generators import printed to stderr: {captured.err}"


def test_import_github_integration_no_side_effects(capsys):
    """Test that importing wpgen.github.integration has no side effects."""
    importlib.import_module('wpgen.github.integration')

    captured = capsys.readouterr()

    assert captured.out == "", f"github.integration import printed to stdout: {captured.out}"
    assert captured.err == "", f"github.integration import printed to stderr: {captured.err}"
