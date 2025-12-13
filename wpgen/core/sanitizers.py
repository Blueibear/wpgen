"""Sanitization Module for WPGen.

This module provides comprehensive sanitization functions to clean and
fix LLM-generated code before validation. All sanitization is deterministic
and prevents common issues like:
- Invisible Unicode characters
- Stray backslashes and escape sequences
- Unquoted barewords in PHP arrays
- HTML/CSS mixed inside PHP blocks
- Unclosed or duplicate tags
- Markdown artifacts and explanatory text

Every function is pure and predictable - same input always produces same output.
"""

import re
import unicodedata
from typing import Tuple, List


# Invisible Unicode characters that cause syntax errors
INVISIBLE_CHARS = [
    '\u200b',  # Zero-width space
    '\u200c',  # Zero-width non-joiner
    '\u200d',  # Zero-width joiner
    '\ufeff',  # Zero-width no-break space (BOM)
    '\u2060',  # Word joiner
    '\u180e',  # Mongolian vowel separator
    '\u061c',  # Arabic letter mark
    '\u202a',  # Left-to-right embedding
    '\u202b',  # Right-to-left embedding
    '\u202c',  # Pop directional formatting
    '\u202d',  # Left-to-right override
    '\u202e',  # Right-to-left override
    '\u2061',  # Function application
    '\u2062',  # Invisible times
    '\u2063',  # Invisible separator
    '\u2064',  # Invisible plus
]


# Valid PHP constants and keywords that should NOT be quoted
VALID_PHP_KEYWORDS = {
    'true', 'false', 'null', 'TRUE', 'FALSE', 'NULL',
    '__FILE__', '__LINE__', '__DIR__', '__FUNCTION__', '__CLASS__',
    '__METHOD__', '__NAMESPACE__', '__TRAIT__',
    'self', 'parent', 'static',
}

VALID_WP_CONSTANTS = {
    'ABSPATH', 'WP_DEBUG', 'WP_DEBUG_LOG', 'WP_DEBUG_DISPLAY',
    'WP_CONTENT_DIR', 'WP_CONTENT_URL', 'WP_PLUGIN_DIR', 'WP_PLUGIN_URL',
    'WPINC', 'WP_LANG_DIR', 'WP_MEMORY_LIMIT', 'WP_MAX_MEMORY_LIMIT',
}


def strip_invisible_unicode(code: str) -> Tuple[str, int]:
    """Strip all invisible and problematic Unicode characters from code.

    This removes zero-width spaces, BOMs, directional formatting, and other
    invisible control characters that cause PHP syntax errors.

    Args:
        code: Code string that may contain invisible Unicode

    Returns:
        Tuple of (cleaned_code, number_of_characters_removed)

    Example:
        >>> code = "<?php\\u200b echo 'test';"
        >>> cleaned, count = strip_invisible_unicode(code)
        >>> count
        1
    """
    original_length = len(code)

    # Remove all defined invisible characters
    for char in INVISIBLE_CHARS:
        code = code.replace(char, '')

    # Remove other control characters except newline, tab, and carriage return
    cleaned = []
    for char in code:
        if char in ['\n', '\r', '\t'] or unicodedata.category(char)[0] != 'C':
            cleaned.append(char)

    code = ''.join(cleaned)

    chars_removed = original_length - len(code)

    return code, chars_removed


def remove_stray_backslashes(code: str) -> Tuple[str, int]:
    r"""Remove stray backslashes that aren't part of valid escape sequences.

    This fixes common LLM errors like:
    - Escaped quotes in PHP: date(\'Y\') → date('Y')
    - Backslashes before HTML: \< → <
    - Backslashes before punctuation: \, → ,

    Valid escape sequences (\\, \n, \t, etc.) are preserved.

    Args:
        code: Code string to clean

    Returns:
        Tuple of (cleaned_code, number_of_backslashes_removed)

    Example:
        >>> code = "date(\\'Y\\')"
        >>> cleaned, count = remove_stray_backslashes(code)
        >>> cleaned
        "date('Y')"
        >>> count
        2
    """
    original = code

    # CRITICAL FIX: Remove escaped quotes inside PHP code
    code = re.sub(r"\\'", "'", code)
    code = re.sub(r'\\"', '"', code)

    # Replace obvious stray backslashes before common characters
    replacements = [
        (r'\\ +', ' '),      # Backslash + space
        (r'\\<', '<'),       # Backslash before <
        (r'\\>', '>'),       # Backslash after >
        (r'\\,', ','),       # Backslash before comma
        (r'\\;', ';'),       # Backslash before semicolon
        (r'\\\(', '('),      # Backslash before paren
        (r'\\\)', ')'),      # Backslash after paren
        (r'\\\{', '{'),      # Backslash before brace
        (r'\\\}', '}'),      # Backslash after brace
        (r'\\\[', '['),      # Backslash before bracket
        (r'\\\]', ']'),      # Backslash after bracket
    ]

    for pattern, replacement in replacements:
        code = re.sub(pattern, replacement, code)

    removed = len(original) - len(code)

    return code, removed


def sanitize_barewords(php_code: str) -> Tuple[str, List[str]]:
    """Sanitize unquoted barewords in PHP arrays and function calls.

    This fixes the critical bug where LLMs generate PHP code with unquoted
    string values:
        'height' => auto,      # WRONG - causes PHP error
        'height' => 'auto',    # CORRECT

    Args:
        php_code: PHP code to sanitize

    Returns:
        Tuple of (sanitized_code, list_of_fixes_applied)

    Example:
        >>> code = "'width' => auto,"
        >>> sanitized, fixes = sanitize_barewords(code)
        >>> sanitized
        "'width' => 'auto',"
        >>> len(fixes)
        1
    """
    fixes = []
    sanitized = php_code

    # Pattern to find array assignments: 'key' => bareword,
    array_pattern = r'''
        (['"])([^'"]+)\1       # Quoted key
        \s*=>\s*               # Arrow
        ([a-zA-Z_][a-zA-Z0-9_-]*)  # Bareword value
        \s*([,\)])             # Terminator
    '''

    def should_quote_value(value: str) -> bool:
        """Check if a value should be quoted."""
        if value in VALID_PHP_KEYWORDS or value in VALID_WP_CONSTANTS:
            return False
        if value.isdigit() or re.match(r'^\d+\.\d+$', value):
            return False
        if '(' in value or ')' in value:
            return False
        return True

    def fix_bareword(match):
        quote_char = match.group(1)
        key = match.group(2)
        value = match.group(3)
        terminator = match.group(4)

        if should_quote_value(value):
            fixes.append(f"Quoted bareword '{value}' in array key '{key}'")
            return f"{quote_char}{key}{quote_char} => '{value}'{terminator}"
        return match.group(0)

    sanitized = re.sub(
        array_pattern,
        fix_bareword,
        sanitized,
        flags=re.VERBOSE | re.MULTILINE
    )

    return sanitized, fixes


def clean_llm_markdown_artifacts(code: str) -> Tuple[str, List[str]]:
    """Remove markdown code fences and explanatory text from LLM output.

    LLMs often wrap code in markdown or add explanatory text like
    "Here's the code:" before the actual code. This function removes
    all such artifacts to extract clean code.

    Args:
        code: Generated code from LLM

    Returns:
        Tuple of (cleaned_code, list_of_artifacts_removed)

    Example:
        >>> code = "```php\\n<?php echo 'hi'; ?>\\n```"
        >>> cleaned, artifacts = clean_llm_markdown_artifacts(code)
        >>> '```' in cleaned
        False
    """
    artifacts = []
    code = code.strip()

    # Remove markdown code fences
    if '```' in code:
        code = re.sub(r'^```(?:php|css|javascript|js|html)?\s*\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n```\s*$', '', code)
        code = code.replace('```', '')
        artifacts.append("Removed markdown code fences")

    # Remove common explanatory phrases at the start
    explanatory_patterns = [
        (r'^(?:Here\'s|Here is|This is|Below is|I\'ve created|I have created).*?:\s*\n+',
         "Removed explanatory introduction"),
        (r'^(?:Sure|Certainly|Of course)[,!].*?\n+',
         "Removed conversational prefix"),
        (r'^(?:This code|This file|This template).*?\n+',
         "Removed descriptive prefix"),
    ]

    for pattern, description in explanatory_patterns:
        if re.match(pattern, code, re.IGNORECASE):
            code = re.sub(pattern, '', code, flags=re.IGNORECASE)
            artifacts.append(description)

    return code.strip(), artifacts


def balance_html_tags(html: str) -> Tuple[str, List[str]]:
    """Balance HTML tags by adding missing closing tags or removing extra ones.

    This ensures that all opened tags are properly closed in the correct order,
    preventing broken HTML that can crash WordPress template rendering.

    Args:
        html: HTML string to balance

    Returns:
        Tuple of (balanced_html, list_of_fixes_applied)

    Example:
        >>> html = "<div><p>Text</div>"
        >>> balanced, fixes = balance_html_tags(html)
        >>> '</p>' in balanced
        True
    """
    fixes = []

    # Tags that must be balanced (self-closing tags excluded)
    balanced_tags = ['div', 'section', 'article', 'main', 'header', 'footer',
                     'nav', 'aside', 'p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                     'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'form', 'body', 'html']

    for tag in balanced_tags:
        open_pattern = f'<{tag}[\\s>]'
        close_pattern = f'</{tag}>'

        opens = len(re.findall(open_pattern, html, re.IGNORECASE))
        closes = len(re.findall(close_pattern, html, re.IGNORECASE))

        if opens > closes:
            # Add missing closing tags
            missing = opens - closes
            html = html.rstrip() + (f'</{tag}>' * missing)
            fixes.append(f"Added {missing} missing </{tag}> closing tag(s)")

        elif closes > opens:
            # Remove extra closing tags
            extra = closes - opens
            for _ in range(extra):
                html = html.replace(f'</{tag}>', '', 1)
            fixes.append(f"Removed {extra} extra </{tag}> closing tag(s)")

    return html, fixes


def remove_duplicate_tags(code: str, tag: str) -> Tuple[str, int]:
    """Remove duplicate occurrences of a specific tag, keeping only the last one.

    This fixes LLM errors where closing tags like </body> or </html> appear
    multiple times, breaking the page structure.

    Args:
        code: Code string
        tag: Tag name (without < >)

    Returns:
        Tuple of (cleaned_code, number_of_duplicates_removed)

    Example:
        >>> code = "content</body>\\nmore</body>"
        >>> cleaned, count = remove_duplicate_tags(code, 'body')
        >>> count
        1
    """
    close_tag = f'</{tag}>'
    count = code.count(close_tag)

    if count <= 1:
        return code, 0

    # Keep only the last occurrence
    parts = code.rsplit(close_tag, count)
    # Remove all but join back the last one
    cleaned = ''.join(parts[:-1]) + close_tag + parts[-1]

    removed = count - 1

    return cleaned, removed


def align_php_tags(code: str) -> Tuple[str, List[str]]:
    """Ensure PHP tags are properly aligned and valid.

    Fixes:
    - Empty PHP blocks: <?php ?> → removed
    - Unclosed PHP blocks in pure PHP files
    - Multiple opening tags without closing

    Args:
        code: PHP code to align

    Returns:
        Tuple of (aligned_code, list_of_fixes_applied)

    Example:
        >>> code = "<?php ?> text <?php echo 'hi';"
        >>> aligned, fixes = align_php_tags(code)
        >>> '<?php ?>' not in aligned
        True
    """
    fixes = []

    # Remove empty PHP blocks
    empty_blocks = len(re.findall(r'<\?php\s*\?>', code))
    if empty_blocks > 0:
        code = re.sub(r'<\?php\s*\?>', '', code)
        fixes.append(f"Removed {empty_blocks} empty PHP block(s)")

    # For pure PHP files (starting with <?php), remove closing ?> at the end
    # This follows WordPress coding standards
    if code.strip().startswith('<?php') and '<!DOCTYPE' not in code and '<html' not in code:
        if code.rstrip().endswith('?>'):
            code = code.rstrip()[:-2].rstrip()
            fixes.append("Removed closing ?> tag from pure PHP file (WordPress standard)")

    return code, fixes


def sanitize_file_complete(
    code: str,
    file_type: str = 'php'
) -> Tuple[str, Dict[str, List[str]]]:
    """Complete sanitization pipeline for a generated file.

    This applies all sanitization steps in the correct order:
    1. Strip invisible Unicode
    2. Clean markdown artifacts
    3. Remove stray backslashes
    4. Sanitize barewords (PHP only)
    5. Align PHP tags
    6. Balance HTML tags (if mixed PHP/HTML)
    7. Remove duplicate closing tags

    Args:
        code: Generated code to sanitize
        file_type: Type of file ('php', 'css', 'js', 'html')

    Returns:
        Tuple of (sanitized_code, dict_of_all_fixes_by_category)

    Example:
        >>> code = "\\u200b<?php\\n'width' => auto;\\n?>"
        >>> sanitized, fixes = sanitize_file_complete(code)
        >>> 'unicode_removed' in fixes
        True
    """
    all_fixes = {
        'unicode_removed': [],
        'markdown_cleaned': [],
        'backslashes_removed': [],
        'barewords_fixed': [],
        'php_aligned': [],
        'html_balanced': [],
        'duplicates_removed': [],
    }

    # Step 1: Strip invisible Unicode
    code, unicode_count = strip_invisible_unicode(code)
    if unicode_count > 0:
        all_fixes['unicode_removed'].append(f"Removed {unicode_count} invisible character(s)")

    # Step 2: Clean markdown artifacts
    code, markdown_fixes = clean_llm_markdown_artifacts(code)
    all_fixes['markdown_cleaned'].extend(markdown_fixes)

    # Step 3: Remove stray backslashes
    code, backslash_count = remove_stray_backslashes(code)
    if backslash_count > 0:
        all_fixes['backslashes_removed'].append(f"Removed {backslash_count} stray backslash(es)")

    # Step 4: Sanitize barewords (PHP only)
    if file_type == 'php':
        code, bareword_fixes = sanitize_barewords(code)
        all_fixes['barewords_fixed'].extend(bareword_fixes)

    # Step 5: Align PHP tags
    if file_type == 'php':
        code, php_fixes = align_php_tags(code)
        all_fixes['php_aligned'].extend(php_fixes)

    # Step 6: Balance HTML tags (if HTML present)
    if '<' in code and '>' in code:
        code, html_fixes = balance_html_tags(code)
        all_fixes['html_balanced'].extend(html_fixes)

    # Step 7: Remove duplicate closing tags
    for tag in ['body', 'html', 'head', 'main']:
        code, dup_count = remove_duplicate_tags(code, tag)
        if dup_count > 0:
            all_fixes['duplicates_removed'].append(f"Removed {dup_count} duplicate </{tag}> tag(s)")

    return code, all_fixes


def extract_code_from_llm_response(response: str, expected_start: str = '<?php') -> str:
    """Extract actual code from LLM response, removing all non-code content.

    This is a specialized extractor that finds the actual code portion
    in an LLM response that may contain explanations, markdown, or other text.

    Args:
        response: Full LLM response
        expected_start: Expected code start marker (e.g., '<?php', '<!DOCTYPE')

    Returns:
        Extracted code string

    Example:
        >>> response = "Here's your code:\\n```php\\n<?php echo 'hi'; ?>\\n```"
        >>> code = extract_code_from_llm_response(response)
        >>> code.startswith('<?php')
        True
    """
    # First clean markdown
    cleaned, _ = clean_llm_markdown_artifacts(response)

    # Find the actual code start
    if expected_start in cleaned:
        start_idx = cleaned.find(expected_start)
        cleaned = cleaned[start_idx:]

    return cleaned.strip()
