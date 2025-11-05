"""Test configuration for wpgen."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so the wpgen package can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set environment variables for offline testing
os.environ.setdefault("WPGEN_CHECK_MODELS", "0")
os.environ.setdefault("WPGEN_OFFLINE_TESTS", "1")
os.environ.setdefault("NO_COLOR", "1")
