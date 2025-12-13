"""Template Contract System for WPGen.

This module defines and enforces strict contracts that all WordPress theme
templates must follow. These contracts prevent common issues that cause
WordPress themes to break or malfunction.

Contract violations are detected early and trigger automatic fallback to
safe templates, preventing broken themes from being generated.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TemplateContract:
    """Defines a contract that a template must satisfy."""

    name: str
    description: str
    required_elements: List[str]
    forbidden_elements: List[str]
    must_open_tags: List[str]
    must_close_tags: List[str]
    required_functions: List[str]
    forbidden_functions: List[str]


# Template Contracts Definition
CONTRACTS: Dict[str, TemplateContract] = {
    'header': TemplateContract(
        name='header.php',
        description='Site header template with HTML document start',
        required_elements=[
            '<!DOCTYPE',
            '<html',
            '<head>',
            '</head>',
            '<body',
            'wp_head()',
            'wp_body_open()',
        ],
        forbidden_elements=[
            '</body>',
            '</html>',
        ],
        must_open_tags=['html', 'head', 'body'],
        must_close_tags=['head'],
        required_functions=['wp_head', 'language_attributes', 'bloginfo', 'body_class'],
        forbidden_functions=['wp_footer', 'get_footer'],
    ),

    'footer': TemplateContract(
        name='footer.php',
        description='Site footer template with HTML document end',
        required_elements=[
            'wp_footer()',
            '</body>',
            '</html>',
        ],
        forbidden_elements=[
            '<!DOCTYPE',
            '<html',
            '<head>',
        ],
        must_open_tags=[],
        must_close_tags=['body', 'html'],
        required_functions=['wp_footer'],
        forbidden_functions=['wp_head', 'get_header'],
    ),

    'index': TemplateContract(
        name='index.php',
        description='Main template file (fallback for all template types)',
        required_elements=[
            'get_header()',
            'get_footer()',
            '<main',
            '</main>',
            'have_posts()',
            'the_post()',
        ],
        forbidden_elements=[
            '<!DOCTYPE',
            '<html',
            '</body>',
            '</html>',
        ],
        must_open_tags=['main'],
        must_close_tags=['main'],
        required_functions=['get_header', 'get_footer', 'have_posts', 'the_post'],
        forbidden_functions=['wp_head', 'wp_footer'],
    ),

    'single': TemplateContract(
        name='single.php',
        description='Single post template',
        required_elements=[
            'get_header()',
            'get_footer()',
            '<main',
            '</main>',
            'have_posts()',
            'the_post()',
            'the_content()',
        ],
        forbidden_elements=[
            '<!DOCTYPE',
            '<html',
            '</body>',
            '</html>',
        ],
        must_open_tags=['main'],
        must_close_tags=['main'],
        required_functions=['get_header', 'get_footer', 'have_posts', 'the_post', 'the_content'],
        forbidden_functions=['wp_head', 'wp_footer'],
    ),

    'page': TemplateContract(
        name='page.php',
        description='Static page template',
        required_elements=[
            'get_header()',
            'get_footer()',
            '<main',
            '</main>',
            'have_posts()',
            'the_post()',
            'the_content()',
        ],
        forbidden_elements=[
            '<!DOCTYPE',
            '<html',
            '</body>',
            '</html>',
        ],
        must_open_tags=['main'],
        must_close_tags=['main'],
        required_functions=['get_header', 'get_footer', 'have_posts', 'the_post', 'the_content'],
        forbidden_functions=['wp_head', 'wp_footer'],
    ),

    'functions': TemplateContract(
        name='functions.php',
        description='Theme functions and hooks',
        required_elements=[
            '<?php',
            'add_action(',
        ],
        forbidden_elements=[
            "define('WP_DEBUG'",
            'define("WP_DEBUG"',
            "define('WP_DEBUG_LOG'",
            "ini_set('display_errors'",
            'error_reporting(',
        ],
        must_open_tags=[],
        must_close_tags=[],
        required_functions=['add_action'],
        forbidden_functions=[
            'get_header',
            'get_footer',
            'wp_head',
            'wp_footer',
            'the_post',
            'the_content',
        ],
    ),
}


class ContractViolation(Exception):
    """Exception raised when a template violates its contract."""

    def __init__(self, template_name: str, violations: List[str]):
        self.template_name = template_name
        self.violations = violations
        message = f"Template '{template_name}' violates contract:\n  - " + "\n  - ".join(violations)
        super().__init__(message)


def get_contract(template_name: str) -> Optional[TemplateContract]:
    """Get contract for a template by name.

    Args:
        template_name: Template filename (e.g., 'header.php', 'index.php')

    Returns:
        TemplateContract or None if no contract exists
    """
    # Extract base name without .php extension
    base_name = template_name.replace('.php', '').replace('template-parts/', '')

    # Map common variations
    if base_name.startswith('content-'):
        base_name = 'content'
    elif base_name in ['archive', 'category', 'tag', 'author', 'date']:
        base_name = 'archive'

    return CONTRACTS.get(base_name)


def validate_template(template_name: str, content: str, strict: bool = True) -> Tuple[bool, List[str]]:
    """Validate that template content satisfies its contract.

    Args:
        template_name: Template filename
        content: Template content to validate
        strict: If True, fail on any violation. If False, only fail on critical violations.

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    contract = get_contract(template_name)

    if not contract:
        # No contract defined for this template
        return True, []

    violations = []

    # Check required elements
    for element in contract.required_elements:
        if element not in content:
            violations.append(f"Missing required element: {element}")

    # Check forbidden elements
    for element in contract.forbidden_elements:
        if element in content:
            violations.append(f"Contains forbidden element: {element}")

    # Check that opened tags are closed
    for tag in contract.must_open_tags:
        open_pattern = f'<{tag}[\\s>]'
        close_pattern = f'</{tag}>'

        opens = len(re.findall(open_pattern, content, re.IGNORECASE))
        closes = len(re.findall(close_pattern, content, re.IGNORECASE))

        if opens > 0 and opens != closes:
            violations.append(f"Unmatched <{tag}> tags: {opens} open, {closes} close")

    # Check that tags that must be closed are indeed closed
    for tag in contract.must_close_tags:
        close_pattern = f'</{tag}>'
        if close_pattern not in content:
            violations.append(f"Missing required closing tag: </{tag}>")

    # Check required functions
    for func in contract.required_functions:
        if f'{func}(' not in content:
            violations.append(f"Missing required function call: {func}()")

    # Check forbidden functions
    for func in contract.forbidden_functions:
        if f'{func}(' in content:
            violations.append(f"Contains forbidden function call: {func}()")

    # Additional validation: Check for common structural errors
    structural_violations = _check_structural_integrity(template_name, content)
    violations.extend(structural_violations)

    is_valid = len(violations) == 0

    return is_valid, violations


def _check_structural_integrity(template_name: str, content: str) -> List[str]:
    """Check for common structural errors that break WordPress themes.

    Args:
        template_name: Template filename
        content: Template content

    Returns:
        List of violations found
    """
    violations = []

    # Check for duplicate footers (common LLM error)
    footer_count = content.count('</body>')
    if footer_count > 1:
        violations.append(f"Duplicate </body> tags found ({footer_count} occurrences)")

    html_count = content.count('</html>')
    if html_count > 1:
        violations.append(f"Duplicate </html> tags found ({html_count} occurrences)")

    # Check for misplaced wp_head or wp_footer
    if template_name != 'header.php' and 'wp_head()' in content:
        violations.append("wp_head() must only be in header.php")

    if template_name != 'footer.php' and 'wp_footer()' in content:
        violations.append("wp_footer() must only be in footer.php")

    # Check for opening <main> without closing </main>
    if '<main' in content:
        main_opens = len(re.findall(r'<main[\s>]', content))
        main_closes = content.count('</main>')

        if main_opens != main_closes:
            violations.append(f"Unmatched <main> tags: {main_opens} open, {main_closes} close")

    # Check for PHP syntax issues that contract should catch
    if '<?php' in content:
        # Check for empty PHP blocks
        if re.search(r'<\?php\s*\?>', content):
            violations.append("Empty PHP blocks found (<?php ?>)")

        # Check for stray semicolons after control structures
        if re.search(r'\b(if|while|foreach|for)\s*\([^)]+\)\s*;', content):
            violations.append("Stray semicolon after control structure")

    return violations


def enforce_contract(template_name: str, content: str, fallback_content: str) -> str:
    """Enforce contract on template content, using fallback if validation fails.

    This is the primary entry point for contract enforcement. It validates
    the content and automatically falls back to safe content if violations
    are found.

    Args:
        template_name: Template filename
        content: Generated template content
        fallback_content: Safe fallback content to use if validation fails

    Returns:
        Valid template content (original or fallback)
    """
    is_valid, violations = validate_template(template_name, content, strict=True)

    if not is_valid:
        from ..utils.logger import get_logger
        logger = get_logger(__name__)

        logger.error(f"Template {template_name} failed contract validation:")
        for violation in violations:
            logger.error(f"  - {violation}")
        logger.warning(f"Using safe fallback template for {template_name}")

        return fallback_content

    return content


def repair_template(template_name: str, content: str) -> Tuple[str, List[str]]:
    """Attempt to automatically repair template to meet contract.

    This function tries to fix common issues automatically before
    falling back to the safe template.

    Args:
        template_name: Template filename
        content: Template content to repair

    Returns:
        Tuple of (repaired_content, list_of_repairs_made)
    """
    contract = get_contract(template_name)

    if not contract:
        return content, []

    repairs = []
    repaired = content

    # Repair 1: Add missing get_header() call
    if 'get_header' in contract.required_functions and 'get_header()' not in repaired:
        if '<?php' in repaired:
            # Insert after first PHP opening tag
            repaired = repaired.replace('<?php', '<?php\nget_header();\n?>\n\n<?php', 1)
        else:
            repaired = '<?php get_header(); ?>\n\n' + repaired
        repairs.append("Added missing get_header() call")

    # Repair 2: Add missing get_footer() call
    if 'get_footer' in contract.required_functions and 'get_footer()' not in repaired:
        if repaired.rstrip().endswith('?>'):
            repaired = repaired.rstrip()[:-2] + '\nget_footer();\n'
        else:
            repaired = repaired.rstrip() + '\n\n<?php\nget_footer();\n'
        repairs.append("Added missing get_footer() call")

    # Repair 3: Add missing wp_head() call (header.php only)
    if template_name == 'header.php' and 'wp_head()' not in repaired:
        if '</head>' in repaired:
            repaired = repaired.replace('</head>', '<?php wp_head(); ?>\n</head>', 1)
            repairs.append("Added missing wp_head() before </head>")

    # Repair 4: Add missing wp_footer() call (footer.php only)
    if template_name == 'footer.php' and 'wp_footer()' not in repaired:
        if '</body>' in repaired:
            repaired = repaired.replace('</body>', '<?php wp_footer(); ?>\n</body>', 1)
            repairs.append("Added missing wp_footer() before </body>")

    # Repair 5: Close unclosed <main> tags
    if '<main' in repaired:
        main_opens = len(re.findall(r'<main[\s>]', repaired))
        main_closes = repaired.count('</main>')

        if main_opens > main_closes:
            missing = main_opens - main_closes
            # Add closing tags before get_footer() if present
            if 'get_footer()' in repaired:
                repaired = repaired.replace('get_footer()', '</main>\n\nget_footer()', missing)
            else:
                repaired = repaired.rstrip() + '\n</main>\n'
            repairs.append(f"Added {missing} missing </main> closing tag(s)")

    # Repair 6: Remove duplicate </body> or </html> tags
    body_count = repaired.count('</body>')
    if body_count > 1:
        # Keep only the last occurrence
        parts = repaired.rsplit('</body>', body_count)
        repaired = '</body>'.join(parts[:-1]) + parts[-1]
        repaired = repaired.replace('</body>', '', body_count - 1) + '</body>'
        repairs.append(f"Removed {body_count - 1} duplicate </body> tag(s)")

    html_count = repaired.count('</html>')
    if html_count > 1:
        parts = repaired.rsplit('</html>', html_count)
        repaired = '</html>'.join(parts[:-1]) + parts[-1]
        repaired = repaired.replace('</html>', '', html_count - 1) + '</html>'
        repairs.append(f"Removed {html_count - 1} duplicate </html> tag(s)")

    return repaired, repairs


def get_contract_summary() -> Dict[str, Dict[str, any]]:
    """Get a summary of all template contracts for documentation.

    Returns:
        Dictionary mapping template names to contract requirements
    """
    summary = {}

    for name, contract in CONTRACTS.items():
        summary[name] = {
            'description': contract.description,
            'required_elements': contract.required_elements,
            'forbidden_elements': contract.forbidden_elements,
            'required_functions': contract.required_functions,
            'forbidden_functions': contract.forbidden_functions,
        }

    return summary
