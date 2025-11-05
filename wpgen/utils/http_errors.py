"""HTTP error handling utilities with detailed error messages."""


import requests


def format_http_error(
    exception: requests.exceptions.HTTPError,
    method: str,
    endpoint: str,
    max_body_length: int = 200
) -> str:
    """Format HTTP error with status, method, endpoint, and truncated body.

    Args:
        exception: The HTTP error exception
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        max_body_length: Maximum length of body snippet to include

    Returns:
        Formatted error message string
    """
    status = exception.response.status_code if exception.response else "unknown"
    error_msg = f"HTTP {status} {method} {endpoint}"

    # Add truncated body snippet if available
    if exception.response and exception.response.text:
        body = exception.response.text
        if len(body) > max_body_length:
            body_snippet = body[:max_body_length] + "..."
        else:
            body_snippet = body
        error_msg += f"\nResponse: {body_snippet}"

    return error_msg


def handle_http_error(
    exception: Exception,
    method: str,
    endpoint: str,
    operation: str = "Request"
) -> Exception:
    """Handle HTTP errors and return a well-formatted exception.

    Args:
        exception: The original exception
        method: HTTP method
        endpoint: API endpoint
        operation: Description of the operation (e.g., "Page creation")

    Returns:
        New exception with formatted message
    """
    if isinstance(exception, requests.exceptions.HTTPError):
        error_msg = format_http_error(exception, method, endpoint)
        return Exception(f"{operation} failed: {error_msg}")

    return Exception(f"{operation} failed: {str(exception)}")
