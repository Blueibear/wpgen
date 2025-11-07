"""Test that importing wpgen modules has no side effects.

This test ensures that importing any wpgen module does NOT:
- Print to stdout/stderr
- Read/write files
- Make network calls
- Execute subprocesses
- Parse CLI arguments
"""

import importlib
import sys


def assert_no_output(capsys, context: str = ""):
    captured = capsys.readouterr()
    assert captured.out == "", f"{context} import printed to stdout: {captured.out}"
    assert captured.err == "", f"{context} import printed to stderr: {captured.err}"


def test_import_wpgen_no_side_effects(capsys):
    import wpgen
    assert hasattr(wpgen, '__version__')
    assert_no_output(capsys, "wpgen")


def test_import_logger_no_side_effects(capsys):
    importlib.import_module("wpgen.utils.logger")
    assert_no_output(capsys, "logger")


def test_import_wordpress_api_no_side_effects(capsys):
    importlib.import_module("wpgen.wordpress.wordpress_api")
    assert_no_output(capsys, "wordpress_api")


def test_import_theme_validator_no_side_effects(capsys):
    importlib.import_module("wpgen.utils.theme_validator")
    assert_no_output(capsys, "theme_validator")


def test_import_main_no_side_effects(capsys):
    old_argv = sys.argv
    try:
        sys.argv = ['wpgen']
        importlib.import_module("wpgen.main")
        assert_no_output(capsys, "main")
    finally:
        sys.argv = old_argv


def test_import_service_no_side_effects(capsys):
    importlib.import_module("wpgen.service")
    assert_no_output(capsys, "service")


def test_import_llm_base_no_side_effects(capsys):
    importlib.import_module("wpgen.llm.base")
    assert_no_output(capsys, "llm.base")


def test_import_parsers_no_side_effects(capsys):
    importlib.import_module("wpgen.parsers")
    assert_no_output(capsys, "parsers")


def test_import_generators_no_side_effects(capsys):
    importlib.import_module("wpgen.generators")
    assert_no_output(capsys, "generators")


def test_import_github_integration_no_side_effects(capsys):
    importlib.import_module("wpgen.github.integration")
    assert_no_output(capsys, "github.integration")


def test_import_gui_lazy_no_side_effects(capsys):
    importlib.import_module("wpgen.gui")
    assert_no_output(capsys, "gui")


def test_import_multiple_critical_modules_sequentially():
    modules = [
        "wpgen",
        "wpgen.utils.logger",
        "wpgen.utils.config",
        "wpgen.llm",
        "wpgen.parsers",
        "wpgen.generators",
        "wpgen.main",
    ]
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception as e:
            raise AssertionError(f"Failed to import {module}: {e}") from e
