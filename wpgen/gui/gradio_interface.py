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
        console_output=log_config.get("console_output", True),
    )

    logger.info("Creating Gradio interface")

    # Initialize file handler, image analyzer, and text processor
    file_handler = FileHandler()
    image_analyzer = None  # Initialized later with LLM provider
    text_processor = TextProcessor()

    # [The generate_theme function remains unchanged; it’s long but already clean]
    # [The generate_file_tree function remains unchanged]

    # Create Gradio interface
    with gr.Blocks(
        title="WPGen - AI WordPress Theme Generator", theme=gr.themes.Soft()
    ) as interface:
        gr.Markdown(
            "\n".join(
                [
                    "# 🎨 WPGen - AI-Powered WordPress Theme Generator",
                    "",
                    (
                        "Generate complete WordPress themes from natural language descriptions, "
                        "design mockups, and content files."
                    ),
                ]
            )
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

                status_output = gr.Textbox(
                    label="Status", lines=15, max_lines=20, interactive=False
                )

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

        # Connect the generate button
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

