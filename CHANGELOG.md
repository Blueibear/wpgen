# Changelog

All notable changes to wpgen will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-31

### Added
- Initial release of wpgen
- AI-powered WordPress theme generation using OpenAI GPT-4 and Anthropic Claude
- Multi-modal support with vision AI for design mockup analysis
- Image analysis with OCR fallback using Tesseract
- Text processing for PDF, Markdown, and plain text files
- GitHub integration for automatic repository creation and pushing
- WordPress REST API integration for theme deployment
- LLM-powered natural language WordPress site management
- Gradio-based GUI with file upload support
- Flask-based web UI
- CLI tool with commands:
  - `wpgen generate` - Generate themes from prompts
  - `wpgen serve` - Launch Flask web UI
  - `wpgen gui` - Launch Gradio GUI
  - `wpgen wordpress test` - Test WordPress API connection
  - `wpgen wordpress manage` - Manage WordPress via natural language
- Comprehensive logging with JSON and text formats
- Configuration via config.yaml and .env files
- Theme deployment with ZIP packaging
- Content management (pages, posts, media)
- Plugin installation support

### Features
- Vision API integration for Claude 3 and GPT-4 Vision
- Exact color, layout, and typography extraction from mockups
- Structured prompt formatting with clear sections
- Real-time status updates during generation
- Complete WordPress theme file generation
- Security best practices (Application Passwords, SSL verification)
- Mock mode for testing without real API calls

[1.0.0]: https://github.com/yourusername/wpgen/releases/tag/v1.0.0
