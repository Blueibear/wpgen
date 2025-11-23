"""Regression test for CVE-2024-6839: CORS regex specificity vulnerability.

This test ensures that:
1. Protected routes only allow whitelisted origins
2. Public routes allow appropriate origins
3. Unauthorized origins are blocked on protected routes
4. No overlapping regex patterns cause security issues
"""

import pytest
from flask import Flask, jsonify
from flask_cors import CORS


@pytest.fixture()
def app():
    """Create a test Flask app with hardened CORS configuration."""
    app = Flask(__name__)

    @app.get("/api/admin/secret")
    def admin_secret():
        return jsonify({"ok": True, "message": "admin access"})

    @app.get("/api/public/ping")
    def public_ping():
        return jsonify({"pong": True})

    @app.get("/health")
    def health():
        return jsonify({"status": "healthy"})

    # Hardened, non-overlapping resources configuration
    # This prevents CVE-2024-6839 by ensuring no regex overlap
    CORS(app, resources={
        # Admin routes - restrictive origin
        r"/api/admin/*": {"origins": ["https://safe.example.com"]},
        # Public API routes - permissive (but still controlled)
        r"/api/public/*": {"origins": ["*"]},
        # Health check - public access
        r"/health": {"origins": ["*"]},
    }, supports_credentials=False)

    return app


@pytest.fixture()
def client(app):
    """Create a test client."""
    return app.test_client()


def test_admin_allows_only_safe_origin(client):
    """Test that admin route only allows the whitelisted origin."""
    # Allowed origin on admin route
    resp = client.get(
        "/api/admin/secret",
        headers={"Origin": "https://safe.example.com"}
    )
    # CORS header should reflect the allowed origin
    assert resp.status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "https://safe.example.com"


def test_admin_blocks_other_origins(client):
    """Test that admin route blocks non-whitelisted origins."""
    # Disallowed origin on admin route
    resp = client.get(
        "/api/admin/secret",
        headers={"Origin": "https://evil.example.com"}
    )
    # No ACAO header means blocked
    assert resp.status_code == 200
    assert "Access-Control-Allow-Origin" not in resp.headers


def test_admin_blocks_wildcard_origin(client):
    """Test that admin route blocks even if wildcard is in config elsewhere."""
    # Attempt with a different origin
    resp = client.get(
        "/api/admin/secret",
        headers={"Origin": "https://attacker.com"}
    )
    # Should not allow this origin
    assert "Access-Control-Allow-Origin" not in resp.headers


def test_public_allows_any_origin(client):
    """Test that public route allows various origins."""
    # Public route should accept any origin due to "*" config
    resp = client.get(
        "/api/public/ping",
        headers={"Origin": "https://any.example"}
    )
    assert resp.status_code == 200
    # With "*" and no credentials, flask-cors returns the requesting origin
    assert resp.headers.get("Access-Control-Allow-Origin") == "https://any.example"


def test_health_allows_any_origin(client):
    """Test that health endpoint allows any origin."""
    resp = client.get(
        "/health",
        headers={"Origin": "https://monitoring.example"}
    )
    assert resp.status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "https://monitoring.example"


def test_no_origin_header_still_works(client):
    """Test that requests without Origin header still work."""
    # Without Origin header, the request still succeeds
    # Flask-CORS 6.0.1+ may add CORS headers even without Origin header
    resp = client.get("/api/admin/secret")
    assert resp.status_code == 200
    # Request succeeds regardless of CORS headers

    resp = client.get("/api/public/ping")
    assert resp.status_code == 200
    # Request succeeds regardless of CORS headers


def test_preflight_admin_route(client):
    """Test CORS preflight (OPTIONS) request on admin route."""
    resp = client.options(
        "/api/admin/secret",
        headers={
            "Origin": "https://safe.example.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    # Preflight should be allowed for the whitelisted origin
    assert resp.status_code == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "https://safe.example.com"


def test_preflight_admin_route_blocked(client):
    """Test CORS preflight blocked for non-whitelisted origin on admin route."""
    resp = client.options(
        "/api/admin/secret",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    # Preflight should be blocked for non-whitelisted origin
    assert "Access-Control-Allow-Origin" not in resp.headers
