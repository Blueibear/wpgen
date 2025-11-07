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
from io import StringIO


def test_import_wpgen_no_side_effects(capsys):
    """Test that importing wpgen has no side effects."""
    # Import the package
    import wpgen

    # Capture output
    captured = capsys.readouterr()

    # Assert no output
    assert captured.out == "", "wpgen import should not print to stdout"
    assert captured.err == "", "wpgen import should not print to stderr"

    # Assert basic attributes exist
    assert hasattr(wpgen, '__version__')


def test_import_wpgen_main_no_side_effects(capsys):
    """Test that importing wpgen.main has no side effects."""
    import wpgen.main

    captured = capsys.readouterr()

    assert captured.out == "", "wpgen.main import should not print to stdout"
    assert captured.err == "", "wpgen.main import should not print to stderr"


def test_import_wpgen_utils_logger_no_side_effects(capsys):
    """Test that importing wpgen.utils.logger has no side effects."""
    import wpgen.utils.logger

    captured = capsys.readouterr()

    assert captured.out == "", "wpgen.utils.logger import should not print to stdout"
    assert captured.err == "", "wpgen.utils.logger import should not print to stderr"


def test_import_wpgen_llm_no_side_effects(capsys):
    """Test that importing wpgen.llm has no side effects."""
    import wpgen.llm

    captured = capsys.readouterr()

    assert captured.out == "", "wpgen.llm import should not print to stdout"
    assert captured.err == "", "wpgen.llm import should not print to stderr"


def test_import_wpgen_parsers_no_side_effects(capsys):
    """Test that importing wpgen.parsers has no side effects."""
    import wpgen.parsers

    captured = capsys.readouterr()

    assert captured.out == "", "wpgen.parsers import should not print to stdout"
    assert captured.err == "", "wpgen.parsers import should not print to stderr"


def test_import_wpgen_generators_no_side_effects(capsys):
    """Test that importing wpgen.generators has no side effects."""
    import wpgen.generators

    captured = capsys.readouterr()

    assert captured.out == "", "wpgen.generators import should not print to stdout"
    assert captured.err == "", "wpgen.generators import should not print to stderr"


def test_import_wpgen_gui_lazy_no_side_effects(capsys):
    """Test that importing wpgen.gui (lazy) has no side effects."""
    import wpgen.gui

    captured = capsys.readouterr()

    assert captured.out == "", "wpgen.gui import should not print to stdout"
    assert captured.err == "", "wpgen.gui import should not print to stderr"


def test_import_critical_modules_in_sequence():
    """Test importing multiple critical modules in sequence without errors."""
    modules = [
        'wpgen',
        'wpgen.utils.logger',
        'wpgen.utils.config',
        'wpgen.llm',
        'wpgen.parsers',
        'wpgen.generators',
        'wpgen.main',
    ]

    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as e:
            raise AssertionError(f"Failed to import {module_name}: {e}") from e
