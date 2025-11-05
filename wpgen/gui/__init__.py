"""GUI interface package for WPGen."""

# Lazy imports to avoid requiring gradio at import time
__all__ = ["create_gradio_interface", "launch_gui"]


def create_gradio_interface(config: dict):
    """Create a Gradio interface for WPGen.

    Args:
        config: Configuration dictionary

    Returns:
        Gradio Blocks interface

    Raises:
        ImportError: If gradio is not installed
    """
    try:
        from .gradio_interface import create_gradio_interface as _create
        return _create(config)
    except ImportError as e:
        raise ImportError(
            "gradio is not installed. Install it with: pip install wpgen[ui]"
        ) from e


def launch_gui(config: dict, share: bool = False, server_name: str = "0.0.0.0",
               server_port: int = 7860):
    """Launch the Gradio GUI for WPGen.

    Args:
        config: Configuration dictionary
        share: Create a public share link
        server_name: Server host to bind
        server_port: Server port to use

    Raises:
        ImportError: If gradio is not installed
    """
    try:
        from .gradio_interface import launch_gui as _launch
        return _launch(config, share=share, server_name=server_name,
                      server_port=server_port)
    except ImportError as e:
        raise ImportError(
            "gradio is not installed. Install it with: pip install wpgen[ui]"
        ) from e
