"""Theme self-test module for WordPress theme validation.

This module performs comprehensive pre-packaging validation to ensure
generated themes are complete, valid, and ready for deployment.
"""

import re
from pathlib import Path
from typing import Any

from .logger import get_logger
from .php_validation import PHPValidator, validate_and_fix_php
from .filename_sanitizer import FilenameSanitizer

logger = get_logger(__name__)


class ThemeSelfTest:
    """Comprehensive theme validation before packaging."""

    # Required core files that MUST exist
    REQUIRED_FILES = [
        'style.css',
        'functions.php',
        'index.php',
    ]

    # Recommended files that should exist
    RECOMMENDED_FILES = [
        'header.php',
        'footer.php',
        'front-page.php',
        'page.php',
        'single.php',
        'archive.php',
        'search.php',
        'sidebar.php',
        '404.php',
        'comments.php',
    ]

    # Required hooks in templates
    REQUIRED_HOOKS = {
        'header.php': ['wp_head()'],
        'footer.php': ['wp_footer()'],
        'functions.php': ['add_action', 'add_theme_support'],
    }

    def __init__(self, theme_dir: Path | str):
        """Initialize the theme self-test.

        Args:
            theme_dir: Path to theme directory
        """
        self.theme_dir = Path(theme_dir)
        self.validator = PHPValidator()
        self.sanitizer = FilenameSanitizer()
        self.errors = []
        self.warnings = []
        self.fixes = []

    def run_all_tests(self) -> dict[str, Any]:
        """Run all theme validation tests.

        Returns:
            Dict with test results
        """
        logger.info(f"Running theme self-test: {self.theme_dir.name}")

        results = {
            'theme_name': self.theme_dir.name,
            'theme_path': str(self.theme_dir),
            'passed': False,
            'errors': [],
            'warnings': [],
            'fixes': [],
            'tests': {},
        }

        # Test 1: Check all core template files exist
        results['tests']['file_existence'] = self._test_file_existence()

        # Test 2: Validate all PHP files
        results['tests']['php_syntax'] = self._test_php_syntax()

        # Test 3: Check for required hooks
        results['tests']['required_hooks'] = self._test_required_hooks()

        # Test 4: Validate header/footer structure
        results['tests']['template_structure'] = self._test_template_structure()

        # Test 5: Check for invalid filenames
        results['tests']['filename_validity'] = self._test_filename_validity()

        # Test 6: Validate style.css header
        results['tests']['style_css_header'] = self._test_style_css_header()

        # Test 7: Check for screenshot
        results['tests']['screenshot'] = self._test_screenshot()

        # Test 8: Check for unmatched braces
        results['tests']['brace_matching'] = self._test_brace_matching()

        # Compile results
        results['errors'] = self.errors
        results['warnings'] = self.warnings
        results['fixes'] = self.fixes

        # Theme passes if no errors
        results['passed'] = len(self.errors) == 0

        # Log summary
        if results['passed']:
            logger.info(f"✅ Theme self-test PASSED: {self.theme_dir.name}")
            if self.warnings:
                logger.warning(f"⚠️  {len(self.warnings)} warning(s) found")
        else:
            logger.error(f"❌ Theme self-test FAILED: {self.theme_dir.name}")
            logger.error(f"   {len(self.errors)} error(s) found")

        return results

    def _test_file_existence(self) -> dict[str, Any]:
        """Test that required and recommended files exist."""
        test_result = {'passed': True, 'missing_required': [], 'missing_recommended': []}

        # Check required files
        for filename in self.REQUIRED_FILES:
            file_path = self.theme_dir / filename
            if not file_path.exists():
                self.errors.append(f"CRITICAL: Required file missing: {filename}")
                test_result['missing_required'].append(filename)
                test_result['passed'] = False

        # Check recommended files
        for filename in self.RECOMMENDED_FILES:
            file_path = self.theme_dir / filename
            if not file_path.exists():
                self.warnings.append(f"Recommended file missing: {filename}")
                test_result['missing_recommended'].append(filename)

        return test_result

    def _test_php_syntax(self) -> dict[str, Any]:
        """Test PHP syntax in all PHP files."""
        test_result = {'passed': True, 'invalid_files': []}

        php_files = list(self.theme_dir.glob('**/*.php'))

        for php_file in php_files:
            try:
                code = php_file.read_text(encoding='utf-8')
                file_type = self._determine_file_type(php_file.name)

                # Validate syntax
                is_valid, error_msg = self.validator.validate_php_syntax(code, php_file.name)

                if not is_valid:
                    self.errors.append(f"PHP syntax error in {php_file.name}: {error_msg}")
                    test_result['invalid_files'].append(str(php_file.relative_to(self.theme_dir)))
                    test_result['passed'] = False

            except Exception as e:
                self.errors.append(f"Failed to read {php_file.name}: {str(e)}")
                test_result['passed'] = False

        return test_result

    def _test_required_hooks(self) -> dict[str, Any]:
        """Test that required WordPress hooks are present."""
        test_result = {'passed': True, 'missing_hooks': {}}

        for filename, required_hooks in self.REQUIRED_HOOKS.items():
            file_path = self.theme_dir / filename

            if not file_path.exists():
                continue  # Already flagged in file existence test

            try:
                code = file_path.read_text(encoding='utf-8')

                for hook in required_hooks:
                    if hook not in code:
                        self.errors.append(f"Missing required hook '{hook}' in {filename}")
                        if filename not in test_result['missing_hooks']:
                            test_result['missing_hooks'][filename] = []
                        test_result['missing_hooks'][filename].append(hook)
                        test_result['passed'] = False

            except Exception as e:
                self.errors.append(f"Failed to check hooks in {filename}: {str(e)}")
                test_result['passed'] = False

        return test_result

    def _test_template_structure(self) -> dict[str, Any]:
        """Test header and footer have proper structure."""
        test_result = {'passed': True, 'structural_errors': []}

        # Check header.php
        header_path = self.theme_dir / 'header.php'
        if header_path.exists():
            code = header_path.read_text(encoding='utf-8')

            # Header should have <main> opening but NOT closing
            if '<main' not in code and '<div id="main"' not in code and '<div id="content"' not in code:
                self.warnings.append('header.php should open a <main> or #content container')

            if '</main>' in code:
                self.errors.append('header.php should NOT close </main> tag (footer should close it)')
                test_result['structural_errors'].append('header.php closes </main>')
                test_result['passed'] = False

        # Check footer.php
        footer_path = self.theme_dir / 'footer.php'
        if footer_path.exists():
            code = footer_path.read_text(encoding='utf-8')

            # Footer should have </main> closing
            if '</main>' not in code and '</div><!-- #main -->' not in code and '</div><!-- #content -->' not in code:
                self.warnings.append('footer.php should close the main content container')

            # Footer must have wp_footer()
            if 'wp_footer()' not in code:
                self.errors.append('CRITICAL: footer.php missing wp_footer() - theme will break!')
                test_result['structural_errors'].append('footer.php missing wp_footer()')
                test_result['passed'] = False

        return test_result

    def _test_filename_validity(self) -> dict[str, Any]:
        """Test that all filenames are valid (no .php.php, etc.)."""
        test_result = {'passed': True, 'invalid_filenames': []}

        all_files = list(self.theme_dir.glob('**/*'))

        for file_path in all_files:
            if file_path.is_dir():
                continue

            filename = file_path.name
            is_valid, error_msg = self.sanitizer.validate(filename)

            if not is_valid:
                self.errors.append(f"Invalid filename '{filename}': {error_msg}")
                test_result['invalid_filenames'].append(str(file_path.relative_to(self.theme_dir)))
                test_result['passed'] = False

        return test_result

    def _test_style_css_header(self) -> dict[str, Any]:
        """Test that style.css has a valid WordPress theme header."""
        test_result = {'passed': True, 'header_errors': []}

        style_path = self.theme_dir / 'style.css'
        if not style_path.exists():
            return test_result  # Already flagged in file existence

        try:
            code = style_path.read_text(encoding='utf-8')

            # Check for required header fields
            required_fields = ['Theme Name:', 'Author:', 'Version:']
            for field in required_fields:
                if field not in code:
                    self.errors.append(f"style.css missing required field: {field}")
                    test_result['header_errors'].append(f"Missing {field}")
                    test_result['passed'] = False

            # Check if header is at the start
            if not code.strip().startswith('/*'):
                self.errors.append('style.css must start with a comment block containing theme metadata')
                test_result['header_errors'].append('Header not at start of file')
                test_result['passed'] = False

        except Exception as e:
            self.errors.append(f"Failed to read style.css: {str(e)}")
            test_result['passed'] = False

        return test_result

    def _test_screenshot(self) -> dict[str, Any]:
        """Test that a screenshot exists."""
        test_result = {'passed': True, 'has_screenshot': False}

        screenshot_exts = ['.png', '.jpg', '.jpeg']
        for ext in screenshot_exts:
            if (self.theme_dir / f'screenshot{ext}').exists():
                test_result['has_screenshot'] = True
                break

        if not test_result['has_screenshot']:
            self.warnings.append('No screenshot found (screenshot.png recommended)')

        return test_result

    def _test_brace_matching(self) -> dict[str, Any]:
        """Test that all PHP files have matched braces."""
        test_result = {'passed': True, 'unmatched_files': []}

        php_files = list(self.theme_dir.glob('**/*.php'))

        for php_file in php_files:
            try:
                code = php_file.read_text(encoding='utf-8')

                is_valid, error_msg = self.validator.check_brace_matching(code, php_file.name)

                if not is_valid:
                    self.errors.append(f"Brace mismatch in {php_file.name}: {error_msg}")
                    test_result['unmatched_files'].append(str(php_file.relative_to(self.theme_dir)))
                    test_result['passed'] = False

            except Exception as e:
                self.errors.append(f"Failed to check braces in {php_file.name}: {str(e)}")
                test_result['passed'] = False

        return test_result

    def _determine_file_type(self, filename: str) -> str:
        """Determine file type from filename."""
        if filename == 'header.php':
            return 'header'
        elif filename == 'footer.php':
            return 'footer'
        elif filename == 'functions.php':
            return 'functions'
        else:
            return 'template'


def run_theme_self_test(theme_dir: Path | str) -> dict[str, Any]:
    """Run theme self-test and return results.

    Convenience function for running theme validation.

    Args:
        theme_dir: Path to theme directory

    Returns:
        Dict with test results
    """
    tester = ThemeSelfTest(theme_dir)
    return tester.run_all_tests()
