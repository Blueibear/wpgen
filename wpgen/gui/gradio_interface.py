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

    file_handler = FileHandler()
    image_analyzer = None
    text_processor = TextProcessor()

    def generate_theme(
        prompt: str,
        image_files: Optional[List] = None,
        text_files: Optional[List] = None,
        push_to_github: bool = False,
        repo_name: str = "",
        deploy_to_wordpress: bool = False,
    ) -> Tuple[str, str, str]:
        try:
            if not prompt or not prompt.strip():
                return "❌ Error: Please provide a description of your website.", "", ""

            status = "🔀 Starting theme generation...\n"
            yield status, "", ""

            status += "🤖 Initializing AI provider...\n"
            yield status, "", ""

            llm_provider = get_llm_provider(config)
            nonlocal image_analyzer
            image_analyzer = ImageAnalyzer(llm_provider)

            status += "📁 Processing uploaded files...\n"
            yield status, "", ""

            image_paths = [f.name for f in image_files] if image_files else []
            text_paths = [f.name for f in text_files] if text_files else []

            processed_files = file_handler.process_uploads(
                image_files=image_paths if image_paths else None,
                text_files=text_paths if text_paths else None,
            )

            image_summaries = None
            if processed_files["images"]:
                status += (
                    "🖼️  Analyzing "
                    f"{len(processed_files['images'])} design reference(s) with AI vision...\n"
                )
                yield status, "", ""

                image_analyses = image_analyzer.batch_analyze_images(
                    processed_files["images"], use_llm=True
                )

                image_summaries = image_analyzer.generate_image_summary(image_analyses)

                status += "  ✓ Extracted design insights: layout, colors, typography, components\n"
                yield status, "", ""

            text_content = None
            file_descriptions = []
            if text_paths:
                status += f"📄 Processing {len(text_paths)} content file(s)...\n"
                yield status, "", ""

                batch_result = text_processor.batch_process_files(text_paths)
                text_content = batch_result["combined_content"]

                for file_info in batch_result["files"]:
                    metadata = file_info.get("metadata", {})
                    filename = metadata.get("filename", "unknown")
                    summary = file_info.get("summary", "")
                    if summary:
                        file_descriptions.append(f"{filename}: {summary}")
                    else:
                        file_descriptions.append(filename)

                status += f"  ✓ Extracted {batch_result['total_size']} characters from documents\n"
                yield status, "", ""

            if image_summaries or text_content:
                status += "📋 Creating structured context from all inputs...\n"
                yield status, "", ""

                structured_context = text_processor.create_structured_context(
                    user_prompt=prompt,
                    image_summaries=image_summaries,
                    text_content=text_content,
                    file_descriptions=file_descriptions if file_descriptions else None,
                )

                status += "  ✓ Combined user prompt, image analysis, and file content\n"
                yield status, "", ""
            else:
                structured_context = None

            status += "🔍 Analyzing requirements with AI...\n"
            yield status, "", ""

            parser = PromptParser(llm_provider)

            if structured_context:
                requirements = parser.parse_multimodal(
                    prompt,
                    images=processed_files["images"] if processed_files["images"] else None,
                    additional_context=structured_context,
                )
            elif processed_files["images"]:
                requirements = parser.parse_multimodal(prompt, images=processed_files["images"])
            else:
                requirements = parser.parse(prompt)

            status += f"  ✓ Theme: {requirements['theme_display_name']}\n"
            status += f"  ✓ Features: {', '.join(requirements['features'][:5])}\n"
            if "design_notes" in requirements and requirements["design_notes"]:
                status += "  ✓ Design insights extracted from images\n"
            yield status, "", ""

            status += "🎗️  Generating WordPress theme files...\n"
            yield status, "", ""

            output_dir = config.get("output", {}).get("output_dir", "output")
            generator = WordPressGenerator(llm_provider, output_dir, config.get("wordpress", {}))
            theme_dir = generator.generate(requirements, images=processed_files["images"])

            status += f"  ✓ Theme generated: {theme_dir}\n"
            yield status, "", ""

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

            if "design_notes" in requirements and requirements["design_notes"]:
                theme_info += f"\n**Design Notes:** {requirements['design_notes']}\n"

            file_tree = generate_file_tree(Path(theme_dir))

            yield status + "\n✅ **Theme generation complete!**\n", theme_info, file_tree

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}\n"
            logger.error(f"Theme generation failed: {str(e)}")
            yield error_msg, "", ""

    def generate_file_tree(path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
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
                    tree += generate_file_tree(
                        item, prefix + extension, max_depth, current_depth + 1
                    )
        except PermissionError:
            pass
        return tree

    with gr.Blocks(title="WPGen - AI WordPress Theme Generator", theme=gr.themes.Soft()) as interface:
        gr.Markdown("""
        # 🎨 WPGen - AI-Powered WordPress Theme Generator

        Generate complete WordPress themes from descriptions, mockups, and content.
        """)
        with gr.Row():
            with gr.Column(scale=2):
                prompt_input = gr.Textbox(
                    label="Website Description",
                    placeholder="Describe your website (e.g., A modern blog with dark theme...)",
                    lines=5,
                )
                image_upload = gr.File(
                    label="Images",
                    file_types=["image"],
                    file_count="multiple",
                    type="filepath",
                )
                text_upload = gr.File(
                    label="Documents",
                    file_types=[".txt", ".md", ".pdf"],
                    file_count="multiple",
                    type="filepath",
                )
                push_checkbox = gr.Checkbox(label="Push to GitHub", value=True)
                deploy_wp_checkbox = gr.Checkbox(label="Deploy to WordPress", value=False)
                repo_input = gr.Textbox(label="Repository Name", placeholder="Leave blank for auto-generated name")
                generate_btn = gr.Button("🚀 Generate WordPress Theme", variant="primary")

            with gr.Column(scale=2):
                status_output = gr.Textbox(label="Status", lines=15, interactive=False)
                theme_info_output = gr.Markdown()
                file_tree_output = gr.Code(label="File Tree", language="plaintext")

        generate_btn.click(
            fn=generate_theme,
            inputs=[prompt_input, image_upload, text_upload, push_checkbox, repo_input, deploy_wp_checkbox],
            outputs=[status_output, theme_info_output, file_tree_output],
        )

    return interface

def launch_gui(config: dict, share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
    interface = create_gradio_interface(config)
    logger.info(f"Launching Gradio interface on {server_name}:{server_port}")
    interface.launch(share=share, server_name=server_name, server_port=server_port, show_error=True)
    return interface


