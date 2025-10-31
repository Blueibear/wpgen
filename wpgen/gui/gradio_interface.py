"""Gradio-based GUI interface for WPGen.

Provides a user-friendly graphical interface for generating WordPress themes
with support for text prompts, image uploads, and document uploads.
"""

import gradio as gr
import os
from pathlib import Path
from typing import List, Optional, Tuple

from ..parsers import PromptParser
from ..generators import WordPressGenerator
from ..github import GitHubIntegration
from ..wordpress import WordPressAPI
from ..utils import setup_logger, get_logger, get_llm_provider, FileHandler
from ..utils.image_analysis import ImageAnalyzer
from ..utils.text_utils import TextProcessor

logger = get_logger(__name__)


def create_gradio_interface(config: dict) -> gr.Blocks:
    # === SETUP LOGGING ===
    log_config = config.get("logging", {})
    setup_logger(
        "wpgen.gui",
        log_file=log_config.get("log_file", "logs/wpgen.log"),
        level=log_config.get("level", "INFO"),
        format_type=log_config.get("format", "text"),
        colored_console=log_config.get("colored_console", True),
        console_output=log_config.get("console_output", True),
    )

    logger.info("Creating Gradio interface")

    # === UTILITY OBJECTS ===
    file_handler = FileHandler()
    image_analyzer = None
    text_processor = TextProcessor()

    # [Assume generate_theme and generate_file_tree are defined above this block]

    with gr.Blocks(
        title="WPGen - AI WordPress Theme Generator", theme=gr.themes.Soft()
    ) as interface:
        gr.Markdown(
            "\n".join([
                "# 🎨 WPGen - AI-Powered WordPress Theme Generator",
                "",
                "Generate complete WordPress themes from natural language descriptions, "
                "design mockups, and content files.",
            ])
        )

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📝 Describe Your Website")

                prompt_input = gr.Textbox(
                    label="Website Description",
                    placeholder=(
                        "Example: Create a dark-themed photography portfolio site with a blog "
                        "and contact form..."
                    ),
                    lines=5,
                    info="Describe your desired website in detail",
                )

                gr.Markdown("### 🖼️ Upload Design References (Optional)")
                gr.Markdown("Upload images (.png, .jpg) to guide the theme's visual design.")

                image_upload = gr.File(
                    label="Design Mockups / Screenshots",
                    file_types=["image"],
                    file_count="multiple",
                    type="filepath",
                    info="Upload images (.png, .jpg) to guide the theme's visual design",
                )

                gr.Markdown("### 📄 Upload Content Files (Optional)")
                gr.Markdown("Upload text files (.txt, .md, .pdf) with site content or requirements.")

                text_upload = gr.File(
                    label="Content Documents",
                    file_types=[".txt", ".md", ".pdf"],
                    file_count="multiple",
                    type="filepath",
                    info="Upload text files (.txt, .md, .pdf) with site content or requirements",
                )

                gr.Markdown("### ⚙️ Generation Options")

                with gr.Row():
                    push_checkbox = gr.Checkbox(
                        label="Push to GitHub",
                        value=True,
                        info="Automatically create and push to a GitHub repository",
                    )
                    deploy_wp_checkbox = gr.Checkbox(
                        label="Deploy to WordPress",
                        value=False,
                        info="Deploy theme to your WordPress site via REST API",
                    )

                repo_input = gr.Textbox(
                    label="Repository Name (Optional)",
                    placeholder="Leave empty for auto-generated name",
                    info="Custom repository name (e.g., 'my-wordpress-theme')",
                )

                generate_btn = gr.Button(
                    "🚀 Generate WordPress Theme",
                    variant="primary",
                    size="lg",
                )

            with gr.Column(scale=2):
                gr.Markdown("### 📊 Generation Status")
                status_output = gr.Textbox(label="Status", lines=15, max_lines=20, interactive=False)

                gr.Markdown("### ℹ️ Theme Information")
                theme_info_output = gr.Markdown()

                gr.Markdown("### 📁 Generated Files")
                file_tree_output = gr.Code(label="File Structure", language="text", lines=15)

        gr.Markdown(
            """
            ---
            ### 💡 Tips

            - **Be Specific**: Include details about colors, layout preferences, and features
            - **Use Images**: Upload design mockups or inspiration images for better results
            - **Add Context**: Upload documents with site content or detailed requirements
            - **GitHub Integration**: Make sure `GITHUB_TOKEN` is set in your `.env` file

            ### 📚 Example Prompts

            - "Create a dark-themed photography portfolio with a masonry gallery layout"
            - "Build a modern corporate website with services section, team page, and testimonials"
            - "Design a minimal blog theme with clean typography and sidebar widgets"
            - "Make an e-commerce theme with WooCommerce support and product showcases"
            """
        )

        generate_btn.click(
            fn=generate_theme,
            inputs=[
                prompt_input,
                image_upload,
                text_upload,
                push_checkbox,
                repo_input,
                deploy_wp_checkbox,
            ],
            outputs=[status_output, theme_info_output, file_tree_output],
        )

    logger.info("Gradio interface created successfully")
    return interface


def launch_gui(config: dict, share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
    """Launch the Gradio GUI interface."""
    interface = create_gradio_interface(config)
    logger.info(f"Launching Gradio interface on {server_name}:{server_port}")
    interface.launch(share=share, server_name=server_name, server_port=server_port, show_error=True)
    return interface
