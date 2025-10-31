"""Gradio-based GUI interface for WPGen.

Provides a user-friendly graphical interface for generating WordPress themes
with support for text prompts, image uploads, and document uploads.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple
import gradio as gr

from ..parsers import PromptParser
from ..generators import WordPressGenerator
from ..github import GitHubIntegration
from ..utils import setup_logger, get_logger, get_llm_provider, FileHandler


logger = get_logger(__name__)


def create_gradio_interface(config: dict) -> gr.Blocks:
    """Create and configure the Gradio interface.

    Args:
        config: Configuration dictionary from config.yaml

    Returns:
        Configured Gradio Blocks interface
    """
    # Setup logging
    log_config = config.get("logging", {})
    setup_logger(
        "wpgen.gui",
        log_file=log_config.get("log_file", "logs/wpgen.log"),
        level=log_config.get("level", "INFO"),
        format_type=log_config.get("format", "text"),
        colored_console=log_config.get("colored_console", True),
        console_output=log_config.get("console_output", True)
    )

    logger.info("Creating Gradio interface")

    # Initialize file handler
    file_handler = FileHandler()

    def generate_theme(
        prompt: str,
        image_files: Optional[List] = None,
        text_files: Optional[List] = None,
        push_to_github: bool = False,
        repo_name: str = ""
    ) -> Tuple[str, str, str]:
        """Generate WordPress theme from inputs.

        Args:
            prompt: Natural language description
            image_files: List of uploaded image files
            text_files: List of uploaded text files
            push_to_github: Whether to push to GitHub
            repo_name: Optional repository name

        Returns:
            Tuple of (status_message, theme_info, file_tree)
        """
        try:
            # Validate inputs
            if not prompt or not prompt.strip():
                return "❌ Error: Please provide a description of your website.", "", ""

            status = "🔄 Starting theme generation...\n"
            yield status, "", ""

            # Process uploaded files
            status += "📁 Processing uploaded files...\n"
            yield status, "", ""

            image_paths = [f.name for f in image_files] if image_files else []
            text_paths = [f.name for f in text_files] if text_files else []

            processed_files = file_handler.process_uploads(
                image_files=image_paths if image_paths else None,
                text_files=text_paths if text_paths else None
            )

            if image_paths:
                status += f"  ✓ Processed {len(processed_files['images'])} image(s)\n"
            if text_paths:
                status += f"  ✓ Extracted content from {len(text_paths)} file(s)\n"
            yield status, "", ""

            # Initialize LLM provider
            status += "🤖 Initializing AI provider...\n"
            yield status, "", ""

            llm_provider = get_llm_provider(config)

            # Parse prompt with multi-modal inputs
            status += "🔍 Analyzing your requirements"
            if processed_files['images']:
                status += " and design references"
            status += "...\n"
            yield status, "", ""

            parser = PromptParser(llm_provider)

            if processed_files['images'] or processed_files['text_content']:
                requirements = parser.parse_multimodal(
                    prompt,
                    images=processed_files['images'] if processed_files['images'] else None,
                    additional_context=processed_files['text_content'] if processed_files['text_content'] else None
                )
            else:
                requirements = parser.parse(prompt)

            status += f"  ✓ Theme: {requirements['theme_display_name']}\n"
            status += f"  ✓ Features: {', '.join(requirements['features'][:5])}\n"
            if 'design_notes' in requirements and requirements['design_notes']:
                status += f"  ✓ Design insights extracted from images\n"
            yield status, "", ""

            # Generate theme
            status += "🏗️  Generating WordPress theme files...\n"
            yield status, "", ""

            output_dir = config.get("output", {}).get("output_dir", "output")
            generator = WordPressGenerator(
                llm_provider,
                output_dir,
                config.get("wordpress", {})
            )

            theme_dir = generator.generate(requirements)

            status += f"  ✓ Theme generated: {theme_dir}\n"
            yield status, "", ""

            # Build theme info
            theme_info = f"""## Theme Information

**Name:** {requirements['theme_display_name']}
**Description:** {requirements['description']}
**Color Scheme:** {requirements.get('color_scheme', 'default')}
**Layout:** {requirements.get('layout', 'full-width')}

**Features:**
{chr(10).join(f'- {feature}' for feature in requirements.get('features', []))}

**Page Templates:**
{chr(10).join(f'- {page}' for page in requirements.get('pages', []))}
"""

            if 'design_notes' in requirements and requirements['design_notes']:
                theme_info += f"\n**Design Notes:** {requirements['design_notes']}\n"

            # Generate file tree
            file_tree = generate_file_tree(Path(theme_dir))

            # Push to GitHub if requested
            if push_to_github:
                github_token = os.getenv("GITHUB_TOKEN")
                if not github_token:
                    status += "⚠️  GITHUB_TOKEN not found, skipping GitHub push\n"
                    yield status, theme_info, file_tree
                else:
                    status += "📤 Pushing to GitHub...\n"
                    yield status, theme_info, file_tree

                    github = GitHubIntegration(github_token, config.get("github", {}))

                    if not repo_name or not repo_name.strip():
                        repo_name = github.generate_repo_name(requirements["theme_name"])

                    repo_url = github.push_to_github(
                        theme_dir,
                        repo_name,
                        requirements
                    )

                    status += f"  ✓ Pushed to GitHub: {repo_url}\n"
                    theme_info += f"\n**GitHub Repository:** [{repo_name}]({repo_url})\n"
                    yield status, theme_info, file_tree

            status += "\n✅ **Theme generation complete!**\n"
            yield status, theme_info, file_tree

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}\n"
            logger.error(f"Theme generation failed: {str(e)}")
            yield error_msg, "", ""

    def generate_file_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
        """Generate a text representation of the file tree.

        Args:
            path: Path to directory
            prefix: Prefix for tree formatting
            max_depth: Maximum depth to traverse
            current_depth: Current recursion depth

        Returns:
            String representation of file tree
        """
        if current_depth >= max_depth:
            return ""

        tree = ""
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                tree += f"{prefix}{current_prefix}{item.name}\n"

                if item.is_dir() and current_depth < max_depth - 1:
                    extension = "    " if is_last else "│   "
                    tree += generate_file_tree(item, prefix + extension, max_depth, current_depth + 1)
        except PermissionError:
            pass

        return tree

    # Create Gradio interface
    with gr.Blocks(
        title="WPGen - AI WordPress Theme Generator",
        theme=gr.themes.Soft()
    ) as interface:
        gr.Markdown("""
        # 🎨 WPGen - AI-Powered WordPress Theme Generator

        Generate complete WordPress themes from natural language descriptions, design mockups, and content files.
        """)

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📝 Describe Your Website")

                prompt_input = gr.Textbox(
                    label="Website Description",
                    placeholder="Example: Create a dark-themed photography portfolio site with a blog and contact form...",
                    lines=5,
                    info="Describe your desired website in detail"
                )

                gr.Markdown("### 🖼️ Upload Design References (Optional)")

                image_upload = gr.File(
                    label="Design Mockups / Screenshots",
                    file_types=["image"],
                    file_count="multiple",
                    type="filepath",
                    info="Upload images (.png, .jpg) to guide the theme's visual design"
                )

                gr.Markdown("### 📄 Upload Content Files (Optional)")

                text_upload = gr.File(
                    label="Content Documents",
                    file_types=[".txt", ".md", ".pdf"],
                    file_count="multiple",
                    type="filepath",
                    info="Upload text files (.txt, .md, .pdf) with site content or requirements"
                )

                gr.Markdown("### ⚙️ Generation Options")

                with gr.Row():
                    push_checkbox = gr.Checkbox(
                        label="Push to GitHub",
                        value=True,
                        info="Automatically create and push to a GitHub repository"
                    )

                repo_input = gr.Textbox(
                    label="Repository Name (Optional)",
                    placeholder="Leave empty for auto-generated name",
                    info="Custom repository name (e.g., 'my-wordpress-theme')"
                )

                generate_btn = gr.Button(
                    "🚀 Generate WordPress Theme",
                    variant="primary",
                    size="lg"
                )

            with gr.Column(scale=2):
                gr.Markdown("### 📊 Generation Status")

                status_output = gr.Textbox(
                    label="Status",
                    lines=15,
                    max_lines=20,
                    interactive=False
                )

                gr.Markdown("### ℹ️ Theme Information")

                theme_info_output = gr.Markdown()

                gr.Markdown("### 📁 Generated Files")

                file_tree_output = gr.Code(
                    label="File Structure",
                    language="text",
                    lines=15
                )

        gr.Markdown("""
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
        """)

        # Connect the generate button
        generate_btn.click(
            fn=generate_theme,
            inputs=[
                prompt_input,
                image_upload,
                text_upload,
                push_checkbox,
                repo_input
            ],
            outputs=[
                status_output,
                theme_info_output,
                file_tree_output
            ]
        )

    logger.info("Gradio interface created successfully")
    return interface


def launch_gui(config: dict, share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
    """Launch the Gradio GUI interface.

    Args:
        config: Configuration dictionary
        share: Whether to create a public share link
        server_name: Server hostname
        server_port: Server port

    Returns:
        Gradio app instance
    """
    interface = create_gradio_interface(config)

    logger.info(f"Launching Gradio interface on {server_name}:{server_port}")

    interface.launch(
        share=share,
        server_name=server_name,
        server_port=server_port,
        show_error=True
    )

    return interface
