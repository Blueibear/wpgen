#!/usr/bin/env python3
"""Check Flask-CORS version to verify CVE-2024-6839 mitigation.

This script verifies that Flask-CORS version >= 6.0.1 is installed,
which includes the fix for CVE-2024-6839 (overlapping regex vulnerability).
"""

import sys

try:
    import flask_cors
    version = flask_cors.__version__
    print(f"Flask-CORS version: {version}")

    # Parse version and check if >= 6.0.1
    version_parts = version.split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1]) if len(version_parts) > 1 else 0
    patch = int(version_parts[2].split('-')[0]) if len(version_parts) > 2 else 0

    if major > 6 or (major == 6 and minor > 0) or (major == 6 and minor == 0 and patch >= 1):
        print("✓ Flask-CORS version is safe (>= 6.0.1)")
        sys.exit(0)
    else:
        print("✗ Flask-CORS version is vulnerable (< 6.0.1)")
        print("  Please upgrade: pip install 'flask-cors>=6.0.1'")
        sys.exit(1)

except ImportError:
    print("✗ Flask-CORS is not installed")
    print("  Install it with: pip install 'flask-cors>=6.0.1'")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error checking Flask-CORS version: {e}")
    sys.exit(1)
