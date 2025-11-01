# WPGen - AI-Powered WordPress Theme Generator

WPGen is a complete Python-based tool that generates WordPress themes from natural language descriptions. Simply describe your website, and WPGen will create a fully functional WordPress theme with all necessary files, then push it to GitHub.

## Features

- **🎨 Graphical User Interface**: Modern Gradio-based GUI with drag-and-drop file uploads
- **🖼️  Multi-Modal AI**: Upload design mockups and screenshots - AI analyzes visual layouts and styles
- **📄 Document Processing**: Upload content files (PDF, Markdown, Text) to guide theme generation
- **💬 Natural Language Input**: Describe your website in plain English
- **🤖 AI-Powered Generation**: Uses OpenAI GPT-4 Vision or Anthropic Claude 3+ for intelligent theme creation
- **📦 Complete WordPress Themes**: Generates all necessary files (style.css, functions.php, templates, etc.)
- **🐙 GitHub Integration**: Automatically pushes generated themes to GitHub repositories
- **🖥️  Three Interfaces**: Graphical UI, Web UI, or CLI - choose your preference
- **🏗️  Modular Architecture**: Clean, extensible codebase
- **🚀 Deployment Ready**: Optional GitHub Actions workflows for automated deployment

## Requirements

- Python 3.11 or higher
- OpenAI or Anthropic API key
- GitHub personal access token (optional, for GitHub integration)
- Git installed on your system

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/blueibear/wpgen.git
cd wpgen
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e .
```

This installs wpgen in editable mode with all dependencies.

### 4. Initialize configuration

```bash
wpgen init
```

This creates a `.env` file. Edit it and add your API keys:

```env
# LLM Provider API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
```

### 5. Configure settings

Edit `config.yaml` to customize settings:
- Choose between OpenAI or Anthropic
- Configure output directory
- Set GitHub repository options
- Adjust logging preferences

## Usage

### 🎨 Graphical User Interface (Recommended)

The easiest way to use WPGen is through the graphical interface:

```bash
wpgen gui
```

Or use the module launcher:

```bash
python -m wpgen gui
```

Then open your browser to `http://localhost:7860`

**Features:**
- ✅ Upload design mockups and screenshots
- ✅ Upload content documents (PDF, Markdown, Text)
- ✅ Real-time generation status
- ✅ Visual file tree preview
- ✅ One-click GitHub push

#### Windows tip: bind to IPv4 explicitly

Windows sometimes resolves `localhost` to IPv6. Use IPv4:

```powershell
set GRADIO_SERVER_NAME=127.0.0.1
wpgen gui --server-name 127.0.0.1 --server-port 7860
```

**CLI flags:**

- `--server-name` - Host to bind (default 0.0.0.0)
- `--server-port` - Port to bind (default 7860)
- `--share` - Create a Gradio public share link

**Create a public share link:**
```bash
wpgen gui --share
```

**Custom port:**
```bash
wpgen gui --server-port 8080
```

**Using environment variables:**
```bash
export GRADIO_SERVER_NAME=127.0.0.1
export GRADIO_SERVER_PORT=7860
wpgen gui
```

📖 **See [GUI_FEATURES.md](GUI_FEATURES.md) for complete GUI documentation**

---

### Command Line Interface (CLI)

#### Generate a theme

```bash
wpgen generate "Create a dark-themed photography portfolio site with a blog and contact form"
```

#### Interactive mode

```bash
wpgen generate --interactive
```

#### Generate without pushing to GitHub

```bash
wpgen generate "Your description" --no-push
```

#### Specify custom repository name

```bash
wpgen generate "Your description" --repo-name my-custom-theme
```

#### Use custom config file

```bash
wpgen generate "Your description" --config my-config.yaml
```

### Web Interface

#### Start the web server

```bash
wpgen serve
```

Then open your browser to `http://localhost:5000`

The web interface provides:
- Visual form for entering descriptions
- Quick example prompts
- Real-time generation status
- Analysis-only mode to preview requirements

### Examples

Here are some example prompts to get you started:

**Photography Portfolio**
```
Create a dark-themed photography portfolio site with a blog and contact form
```

**Corporate Website**
```
Build a modern corporate website with services page, team page, testimonials, and a light blue color scheme
```

**Minimal Blog**
```
Design a minimal blog theme with clean typography, full-width layout, and sidebar
```

**E-commerce**
```
Create an e-commerce ready theme with WooCommerce support, product showcase, and shopping cart
```

**Magazine**
```
Build a magazine-style theme with featured posts, multiple categories, and advertisement areas
```

## Project Structure

```
wpgen/
├── wpgen/                      # Main package
│   ├── __init__.py
│   ├── llm/                    # LLM provider abstractions
│   │   ├── base.py             # Base provider interface
│   │   ├── openai_provider.py # OpenAI implementation
│   │   └── anthropic_provider.py # Anthropic implementation
│   ├── parsers/                # Prompt parsing
│   │   └── prompt_parser.py
│   ├── generators/             # WordPress code generation
│   │   └── wordpress_generator.py
│   ├── github/                 # GitHub integration
│   │   └── integration.py
│   └── utils/                  # Utilities
│       └── logger.py
├── web/                        # Flask web application
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Deployment workflow template
├── config.yaml                 # Configuration file
├── main.py                     # CLI entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Example environment variables
└── README.md                   # This file
```

## Configuration

### config.yaml

The `config.yaml` file contains all configuration options:

#### LLM Provider Settings

```yaml
llm:
  provider: "openai"  # or "anthropic"

  openai:
    model: "gpt-4-turbo-preview"
    max_tokens: 4096
    temperature: 0.7

  anthropic:
    model: "claude-3-5-sonnet-20241022"
    max_tokens: 4096
    temperature: 0.7
```

#### WordPress Generation Settings

```yaml
wordpress:
  theme_prefix: "wpgen"
  wp_version: "6.4"
  include_sample_content: true
  theme_type: "standalone"  # or "child"
  author: "WPGen"
  license: "GPL-2.0-or-later"
```

#### GitHub Settings

```yaml
github:
  api_url: "https://api.github.com"
  repo_name_pattern: "wp-{theme_name}-{timestamp}"
  auto_create: true
  private: false
  default_branch: "main"
```

#### Output Settings

```yaml
output:
  output_dir: "output"
  clean_before_generate: false
  keep_local_copy: true
```

#### Deployment Settings

```yaml
deployment:
  enabled: false
  method: "github_actions"  # or "ftp", "ssh"

  ftp:
    host: ""
    port: 21
    username: ""
    remote_path: "/public_html/wp-content/themes"

  ssh:
    host: ""
    port: 22
    username: ""
    remote_path: "/var/www/html/wp-content/themes"
    key_file: "~/.ssh/id_rsa"
```

## API Keys Setup

### OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Navigate to API Keys
4. Click "Create new secret key"
5. Copy the key and add it to your `.env` file

### Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to API Keys
4. Click "Create Key"
5. Copy the key and add it to your `.env` file

### GitHub Personal Access Token

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`
4. Click "Generate token"
5. Copy the token and add it to your `.env` file

## Generated Theme Structure

When you generate a theme, WPGen creates the following files:

```
theme-name/
├── style.css              # Theme stylesheet with header
├── functions.php          # Theme functions and setup
├── index.php              # Main template file
├── header.php             # Header template
├── footer.php             # Footer template
├── sidebar.php            # Sidebar template
├── single.php             # Single post template
├── page.php               # Static page template
├── archive.php            # Archive template
├── search.php             # Search results template
├── 404.php                # 404 error page
├── page-{custom}.php      # Custom page templates
├── screenshot.txt         # Screenshot placeholder
├── README.md              # Theme documentation
├── .gitignore            # Git ignore file
└── wp-config-sample.php  # WordPress config sample
```

## Deployment

### GitHub Actions

If deployment is enabled in `config.yaml`, WPGen will create a `.github/workflows/deploy.yml` file in your theme directory. This workflow can deploy your theme via FTP or SSH.

#### Setup Deployment Secrets

In your GitHub repository, add these secrets:

**For FTP deployment:**
- `FTP_HOST`: FTP server hostname
- `FTP_USERNAME`: FTP username
- `FTP_PASSWORD`: FTP password

**For SSH deployment:**
- `SSH_HOST`: SSH server hostname
- `SSH_USERNAME`: SSH username
- `SSH_PRIVATE_KEY`: SSH private key
- `SSH_REMOTE_PATH`: Remote path on server

### Manual Deployment

1. Navigate to the output directory
2. Create a ZIP file of your theme directory
3. In WordPress admin, go to Appearance > Themes > Add New > Upload Theme
4. Upload the ZIP file and activate

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=wpgen tests/
```

### Code Style

This project follows PEP 8 guidelines. Format your code with:

```bash
black wpgen/
isort wpgen/
```

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### API Key Issues

**Error: "API key is required"**
- Make sure you've created a `.env` file (run `wpgen init`)
- Verify your API key is correctly set in `.env`
- Check that you're using the correct provider (OpenAI or Anthropic)

### GitHub Push Issues

**Error: "Failed to push to GitHub"**
- Verify your GitHub token has `repo` and `workflow` scopes
- Check that the repository name is valid
- Ensure you have permission to create repositories

### Generation Issues

**Error: "Failed to generate code"**
- Check your internet connection
- Verify your API key is valid and has credits
- Try a simpler prompt first
- Check the logs in `logs/wpgen.log`

### Web UI Issues

**Error: "Address already in use"**
- Another process is using port 5000
- Change the port in `config.yaml` under `web.port`

## Logging

Logs are written to `logs/wpgen.log` by default. You can configure logging in `config.yaml`:

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: "logs/wpgen.log"
  format: "json"  # or "text"
  console_output: true
  colored_console: true
```

## Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secret
- Use environment variables for sensitive data
- Generated themes follow WordPress security best practices
- Review generated code before deploying to production

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Built with Python 3.11+
- Uses OpenAI GPT-4 or Anthropic Claude for AI generation
- Flask for web interface
- GitPython for Git operations
- WordPress coding standards

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation
- Review existing issues for solutions

If you find WPGen useful, consider supporting the project:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://buymeacoffee.com/Blueibear)

## Roadmap

Future enhancements planned:
- [ ] Support for more LLM providers
- [ ] Theme customization wizard
- [ ] Plugin generation
- [ ] Theme preview before generation
- [ ] Batch theme generation
- [ ] Custom template library
- [ ] WordPress.org theme repository compliance
- [ ] Docker support
- [ ] CI/CD integration examples

## Changelog

### Version 1.0.0 (2025-01-30)
- Initial release
- OpenAI and Anthropic support
- CLI and Web UI
- GitHub integration
- WordPress theme generation
- Deployment workflows

---

Made with ❤️ by WPGen
