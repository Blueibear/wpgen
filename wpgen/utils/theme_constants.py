"""Shared constants for classic WordPress theme validation and rendering.

This module is the single source of truth for required and recommended files
in the current classic-theme pipeline. Both the renderer and the validator
must import from here so that their expectations cannot drift apart.
"""

# Files that MUST be present in every generated classic WordPress theme.
# The renderer produces all of these; the validator enforces their presence.
REQUIRED_CLASSIC_THEME_FILES: frozenset[str] = frozenset(
    {
        "style.css",
        "functions.php",
        "header.php",
        "footer.php",
        "index.php",
        "front-page.php",
        "single.php",
        "page.php",
        "archive.php",
        "search.php",
        "404.php",
    }
)

# Files that are recommended but not strictly required.
RECOMMENDED_CLASSIC_THEME_FILES: frozenset[str] = frozenset(
    {
        "sidebar.php",
        "comments.php",
    }
)
