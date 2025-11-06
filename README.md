# WPGen - AI-Powered WordPress Theme Generator

WPGen is a complete Python-based tool that generates WordPress themes from natural language descriptions. Simply describe your website, and WPGen will create a fully functional WordPress theme with all necessary files, then push it to GitHub.

## Features

- **🎨 Graphical User Interface**: Modern Gradio-based GUI with drag-and-drop file uploads
- **🖼️  Multi-Modal AI**: Upload design mockups and screenshots - AI analyzes visual layouts and styles
- **📄 Document Processing**: Upload content files (PDF, Markdown, Text) to guide theme generation
- **💬 Natural Language Input**: Describe your website in plain English
- **🤖 AI-Powered Generation**: Uses OpenAI GPT-4 Vision, Anthropic Claude 3+, **or local LLMs (LM Studio, Ollama)** for intelligent theme creation
- **🔒 Local LLM Support**: Run 100% locally with LM Studio or Ollama - no cloud API keys required!
- **📦 Complete WordPress Themes**: Generates all necessary files (style.css, functions.php, templates, etc.)
- **🎭 Theme Identity**: Every theme includes a valid style.css header and auto-generated screenshot.png (from your uploads or a branded placeholder)
- **✨ Optional Features**: WooCommerce support, custom Gutenberg blocks, dark mode toggle, animated preloader
- **🚀 Always-On UX**: Smooth page transitions and mobile-first, thumb-friendly navigation in every theme
- **🐙 GitHub Integration**: Automatically pushes generated themes to GitHub repositories
- **🖥️  Three Interfaces**: Graphical UI, Web UI, or CLI - choose your preference
- **🏗️  Modular Architecture**: Clean, extensible codebase
- **🚀 Deployment Ready**: Optional GitHub Actions workflows for automated deployment

## Requirements

- Python 3.10 or higher (3.10, 3.11, 3.12 supported)
- **One of the following AI providers:**
  - OpenAI API key, OR
  - Anthropic API key, OR
  - Local LLM via LM Studio or Ollama (free, no API key needed!)
- GitHub personal access token (optional, for GitHub integration)
- Git installed on your system (optional, for GitHub integration)

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

WPGen supports optional dependency groups for different use cases:

**Basic installation (CLI only):**
```bash
pip install -e .
```

**For development (includes testing and linting tools):**
```bash
pip install -e .[dev]
```

**For web UI and Gradio GUI:**
```bash
pip install -e .[ui]
```

**For WordPress REST API integration:**
```bash
pip install -e .[wp]
```

**For GitHub integration:**
```bash
pip install -e .[git]
```

**Full installation (all features):**
```bash
pip install -e .[dev,ui,git,wp]
```

This flexible installation allows you to install only what you need. Contributors should use the full installation.

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
- ✅ **Guided Mode** for structured theme specifications
- ✅ Real-time generation status
- ✅ Visual file tree preview
- ✅ One-click GitHub push

#### Guided Mode (optional)

Alongside the natural-language prompt, Guided Mode lets you specify:

- **Brand basics**: Site name, tagline, primary goal (inform/convert/sell)
- **Pages**: Select top-level pages (Home, About, Blog, Contact, Services, etc.)
- **Style**: Mood (modern-minimal, playful, brutalist, elegant), color palette (hex codes), typography (sans/serif/mono)
- **Layout**: Header style (centered/split/stacked), hero type (image/video/text), sidebar position, container width
- **Components**: Blog, cards, gallery, testimonials, pricing, FAQ, contact form, newsletter, CTA, breadcrumbs
- **Accessibility**: Keyboard navigation, high-contrast mode, reduced-motion support
- **Integrations**: WooCommerce, SEO, analytics, newsletter
- **Performance**: LCP (Largest Contentful Paint) target in milliseconds

These explicit choices override AI inferences and are translated into CSS variables, template parts, and generator options for more consistent, production-ready themes.

#### Optional Features

WPGen now includes advanced optional features you can enable via checkboxes:

- **WooCommerce support & styling**: Adds WooCommerce template compatibility, basic product loop styles, and shop page support (theme works even without WooCommerce plugin installed)
- **Custom Gutenberg blocks**:
  - **Featured Products**: Showcase product highlights
  - **Lifestyle Image**: Large image block with overlay text
  - **Promo Banner**: Call-to-action banner with custom styling
- **Light/Dark mode toggle**: Floating toggle button with localStorage persistence and `prefers-color-scheme` support
- **Animated loading logo (preloader)**: Smooth page preloader with spinner (auto-hides after load, max 3s timeout)

**Always-on defaults** (included in every theme):
- **Smooth page transitions**: CSS opacity fade on navigation + hover transitions
- **Thumb-friendly mobile navigation**: Minimum 44×44px tap targets, responsive hamburger menu, mobile-first CSS

**Note on generation time**: When the GUI displays "🏗️ Generating WordPress theme files…", theme generation can take **a couple of minutes** depending on complexity. Please keep the tab open during this process.

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
  # Options: "openai", "anthropic", "local-lmstudio", "local-ollama"
  provider: "openai"

  openai:
    model: "gpt-4-turbo-preview"
    max_tokens: 4096
    temperature: 0.7

  anthropic:
    model: "claude-3-5-sonnet-20241022"
    max_tokens: 4096
    temperature: 0.7

  # Local LLM providers (no API key required!) - Dual-Model Configuration
  local-lmstudio:
    # Brains model (text-only reasoning)
    brains_model: "Meta-Llama-3.1-8B-Instruct"
    brains_base_url: "http://localhost:1234/v1"

    # Vision model (image analysis, optional)
    vision_model: "Llama-3.2-Vision-11B-Instruct"
    vision_base_url: "http://localhost:1234/v1"

  local-ollama:
    # Brains model (text-only reasoning)
    brains_model: "llama3.1:8b-instruct"
    brains_base_url: "http://localhost:11434/v1"

    # Vision model (image analysis, optional)
    vision_model: "llama3.2-vision:11b-instruct"
    vision_base_url: "http://localhost:11434/v1"
```

See the **"Using Local LLMs with LM Studio or Ollama (Dual-Model)"** section below for complete setup instructions.

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

WPGen uses **secure authentication** via GIT_ASKPASS - your token is **never embedded in Git remote URLs** or stored in Git config.

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select minimal scopes needed:
   - `repo` (for repository creation and push)
   - `workflow` (optional, only if using GitHub Actions)
4. Click "Generate token"
5. Copy the token and add it to your `.env` file

**Security Note**: WPGen uses a temporary GIT_ASKPASS script to provide credentials securely. Your token will never appear in:
- Git remote URLs
- Git configuration files
- Log output (automatically redacted)
- Command history

## Using Local LLMs with LM Studio or Ollama (Dual-Model)

WPGen now supports running **100% locally** with **dual-model configuration**: separate **brains** (text-only reasoning) and **vision** (image analysis) models. No cloud API keys required! Both LM Studio and Ollama provide OpenAI-compatible API servers.

### Why Use Local LLMs?

- **Privacy**: All theme generation happens on your machine
- **Cost**: No API usage fees after initial setup
- **Offline**: Works without internet connection
- **Control**: Full control over model selection and parameters
- **Dual-Model**: Use separate brains (text) and vision (images) models for optimal performance

### Dual-Model Architecture

WPGen's local LLM support uses **two models**:

1. **Brains Model** (Text-Only)
   - Used for: Prompt analysis, code generation without images, text-based reasoning
   - Examples: `Llama-3.1-8B-Instruct`, `Qwen2.5-14B-Instruct`
   - Faster, lighter, handles all text-only tasks

2. **Vision Model** (Image-Capable)
   - Used for: Design analysis, image-guided code generation, mockup interpretation
   - Examples: `Llama-3.2-Vision-11B-Instruct`, `qwen2-vl:7b-instruct`, `llava:13b`
   - Required ONLY when uploading design images/mockups

**Automatic Routing**: WPGen automatically routes requests to the appropriate model:
- Images present → Uses vision model
- Text-only → Uses brains model

**Vision Model is Optional**: If you only provide text prompts (no images), you don't need a vision model.

---

### Option A: LM Studio (Recommended for Beginners)

[LM Studio](https://lmstudio.ai/) provides a user-friendly interface for running local LLMs with an OpenAI-compatible server.

#### Setup Steps (Dual-Model)

1. **Install LM Studio**
   - Download from [lmstudio.ai](https://lmstudio.ai/)
   - Available for Windows, macOS, and Linux

2. **Download Both Models**

   **Brains Model (Text-Only - Required):**
   - Open LM Studio's model search
   - Download one of:
     - `Meta-Llama-3.1-8B-Instruct` (balanced, ~8GB RAM)
     - `Qwen2.5-14B-Instruct` (stronger reasoning, ~14GB RAM)
     - `Mixtral-8x7B-Instruct` (best quality, needs GPU ~30GB VRAM)

   **Vision Model (Image Analysis - Optional):**
   - Download one of:
     - `Llama-3.2-Vision-11B-Instruct` (recommended, ~11GB RAM)
     - `Qwen2-VL-7B-Instruct` (lighter, ~7GB RAM)
     - `Phi-3.5-Vision-Instruct` (lightweight, ~3.8GB RAM)

3. **Start the OpenAI-Compatible Server**
   - In LM Studio, go to the "Local Server" tab
   - Load your **brains model** first (e.g., `Meta-Llama-3.1-8B-Instruct`)
   - Click "Start Server"
   - Default endpoint: `http://localhost:1234/v1`
   - **Note**: LM Studio can switch models on the fly. When WPGen requests vision, manually switch to your vision model in LM Studio, or run two instances on different ports.

4. **Configure WPGen (Dual-Model)**

Edit `config.yaml`:

```yaml
llm:
  provider: "local-lmstudio"
  temperature: 0.4
  max_tokens: 2048
  timeout: 60

  local-lmstudio:
    # Brains model (text-only reasoning)
    brains_model: "Meta-Llama-3.1-8B-Instruct"
    brains_base_url: "http://localhost:1234/v1"

    # Vision model (for image analysis)
    vision_model: "Llama-3.2-Vision-11B-Instruct"
    vision_base_url: "http://localhost:1234/v1"  # Same server, switch models manually
```

**For separate servers (recommended for production):**
```yaml
  local-lmstudio:
    brains_model: "Meta-Llama-3.1-8B-Instruct"
    brains_base_url: "http://localhost:1234/v1"  # First LM Studio instance

    vision_model: "Llama-3.2-Vision-11B-Instruct"
    vision_base_url: "http://localhost:1235/v1"  # Second LM Studio instance on different port
```

5. **Generate Your Theme**

```bash
# CLI (text-only, uses brains model)
wpgen generate "Modern portfolio with dark mode" --provider local-lmstudio

# GUI with image uploads (uses both brains + vision models)
wpgen gui
# 1. Select "local-lmstudio" from LLM Provider
# 2. Upload design mockups
# 3. Generate (automatically routes to vision model for images)
```

#### Recommended LM Studio Models & Settings

**Brains Models (Text-Only Reasoning):**

| Model | Best For | RAM | Settings |
|-------|----------|-----|----------|
| `Meta-Llama-3.1-8B-Instruct` | General theming, balanced | ~8GB | temp: 0.4-0.6, max_tokens: 2048 |
| `Qwen2.5-14B-Instruct` | Complex layouts, stronger reasoning | ~14GB | temp: 0.3-0.5, max_tokens: 4096 |
| `Mixtral-8x7B-Instruct` | Best quality, detailed specs | ~30GB VRAM | temp: 0.3-0.5, max_tokens: 4096 |

**Vision Models (Image Analysis):**

| Model | Best For | RAM | Settings |
|-------|----------|-----|----------|
| `Llama-3.2-Vision-11B-Instruct` | Best balance, design analysis | ~11GB | temp: 0.4-0.6, max_tokens: 2048 |
| `Qwen2-VL-7B-Instruct` | Lighter, good color/layout extraction | ~7GB | temp: 0.4-0.6, max_tokens: 2048 |
| `Phi-3.5-Vision-Instruct` | Fastest, basic mockup analysis | ~3.8GB | temp: 0.5-0.7, max_tokens: 2048 |

#### Example System Prompts

**Brains Model (Text):**
```
You are WPGen's Theme Architect. Generate precise WordPress theme requirements (pages, template parts, color tokens, typography, accessibility defaults). Be deterministic: choose defaults when input is missing. Output clean, production-ready specs.
```

**Vision Model (Images):**
```
You are a design analyst. Extract layout patterns, color palette (hex codes), typography vibe, spacing density, and component list from design mockups. Output concise, structured findings: colors, fonts, layout type, key components.
```

---

### Option B: Ollama (Recommended for Developers)

[Ollama](https://ollama.ai/) is a powerful CLI tool for running LLMs locally with excellent model management and easy switching between models.

#### Setup Steps (Dual-Model)

1. **Install Ollama**

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai/download
# Windows: Download installer from ollama.ai
```

2. **Pull Both Models**

   **Brains Model (Text-Only - Required):**
   ```bash
   # Recommended baseline
   ollama pull llama3.1:8b-instruct

   # Or stronger alternatives:
   ollama pull qwen2.5:14b-instruct    # Better reasoning
   ollama pull mixtral:8x7b-instruct   # Best quality (needs GPU)
   ```

   **Vision Model (Image Analysis - Optional):**
   ```bash
   # Recommended for design analysis
   ollama pull llama3.2-vision:11b-instruct

   # Or alternatives:
   ollama pull qwen2-vl:7b-instruct    # Lighter, good color extraction
   ollama pull llava:13b                # Mature VSN model
   ```

   View all available models at [ollama.ai/library](https://ollama.ai/library)

3. **Verify Ollama Server**

Ollama automatically runs as a service on port 11434:

```bash
# Check if running
curl http://localhost:11434/v1/models

# If not running, start manually:
ollama serve
```

The OpenAI-compatible API is available at `/v1`.

4. **Configure WPGen (Dual-Model)**

Edit `config.yaml`:

```yaml
llm:
  provider: "local-ollama"
  temperature: 0.4
  max_tokens: 2048
  timeout: 60

  local-ollama:
    # Brains model (text-only reasoning)
    brains_model: "llama3.1:8b-instruct"
    brains_base_url: "http://localhost:11434/v1"

    # Vision model (for image analysis)
    vision_model: "llama3.2-vision:11b-instruct"
    vision_base_url: "http://localhost:11434/v1"  # Same server, Ollama auto-switches
```

**Ollama automatically switches models** - no need to run multiple instances!

5. **Generate Your Theme**

```bash
# CLI (text-only, uses brains model)
wpgen generate "Minimal blog with sidebar" --provider local-ollama

# GUI with image uploads (uses both brains + vision models)
wpgen gui
# 1. Select "local-ollama" from LLM Provider
# 2. Upload design mockups
# 3. Generate (automatically routes to vision model for images)
```

#### Recommended Ollama Models & Settings

**Brains Models (Text-Only Reasoning):**

| Model | Best For | RAM/VRAM | Settings |
|-------|----------|----------|----------|
| `llama3.1:8b-instruct` | General theming, baseline | ~8GB | temp: 0.4-0.6, max_tokens: 2048 |
| `qwen2.5:14b-instruct` | Complex layouts, better reasoning | ~14GB | temp: 0.3-0.5, max_tokens: 4096 |
| `mixtral:8x7b-instruct` | Best quality, detailed specs | ~30GB VRAM | temp: 0.3-0.5, max_tokens: 4096 |

**Vision Models (Image Analysis):**

| Model | Best For | RAM/VRAM | Settings |
|-------|----------|----------|----------|
| `llama3.2-vision:11b-instruct` | Best balance, design analysis | ~11GB | temp: 0.4-0.6, max_tokens: 2048 |
| `qwen2-vl:7b-instruct` | Lighter, good color/layout extraction | ~7GB | temp: 0.4-0.6, max_tokens: 2048 |
| `llava:13b` | Mature VSN, reliable mockup analysis | ~13GB | temp: 0.4-0.6, max_tokens: 2048 |

#### Example System Prompts

**Brains Model (Text):**
```
System: You are WPGen's Theme Architect. Generate precise WordPress theme requirements and file plans.
- Use user prompt + guided options.
- Define tokens: --color-primary, --color-surface, --radius-lg; fonts and fallbacks.
- Output page templates and template-parts required.
- Use accessible, mobile-first patterns with smooth transitions.
```

**Vision Model (Images):**
```
System: You are a design analyst for WordPress themes. Extract these details from design mockups:
- Color palette (hex codes for primary, secondary, background, text)
- Typography (font families, sizes, weights)
- Layout patterns (grid, flexbox, columns)
- Component list (header, hero, cards, footer, forms)
- Spacing/density (tight, balanced, spacious)
Output structured, concise findings.
```

---

### How It Works: Dual-Model Routing

WPGen's `CompositeLLMProvider` automatically routes requests to the appropriate model:

```python
from openai import OpenAI

# Create two clients (brains + vision)
brains_client = OpenAI(base_url="http://localhost:11434/v1", api_key="local")
vision_client = OpenAI(base_url="http://localhost:11434/v1", api_key="local")

# WPGen routes automatically:
# - Text-only request → uses brains_model
# - Request with images → uses vision_model

# Example text-only (brains):
response = brains_client.chat.completions.create(
    model="llama3.1:8b-instruct",  # Brains model
    messages=[
        {"role": "system", "content": "You are WPGen's Theme Architect."},
        {"role": "user", "content": "Build a modern portfolio theme..."}
    ],
    temperature=0.4,
    max_tokens=2048,
)

# Example with images (vision):
response = vision_client.chat.completions.create(
    model="llama3.2-vision:11b-instruct",  # Vision model
    messages=[
        {"role": "user", "content": [
            {"type": "text", "text": "Extract colors and layout from this mockup"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]}
    ],
    temperature=0.4,
    max_tokens=2048,
)
```

**Documentation:**
- [LM Studio OpenAI-compatible API](https://lmstudio.ai/docs/api/openai-api)
- [Ollama OpenAI Compatibility](https://github.com/ollama/ollama/blob/main/docs/openai.md)

---

### CLI Usage with Local Providers

```bash
# Text-only generation (uses brains model)
wpgen generate "Dark portfolio theme" --provider local-lmstudio

# Or with Ollama
wpgen generate "Corporate website" --provider local-ollama

# GUI allows image uploads (automatically uses vision model when images present)
wpgen gui
```

---

### GUI Usage with Local Providers

1. Launch the Gradio GUI:
```bash
wpgen gui
```

2. Expand the **"🤖 LLM Provider"** accordion

3. Select your provider:
   - `local-lmstudio` for LM Studio
   - `local-ollama` for Ollama

4. (Optional) Override the base URL or model name

5. Describe your theme and click **"🚀 Generate WordPress Theme"**

The GUI will show the selected provider in the status: `🤖 Initializing AI provider (local-ollama)...`

---

### Configuration Examples

#### Minimal Config (Uses Defaults)

```yaml
llm:
  provider: "local-ollama"
```

This automatically uses:
- LM Studio: `http://localhost:1234/v1` with `Meta-Llama-3.1-8B-Instruct`
- Ollama: `http://localhost:11434/v1` with `llama3.1:8b-instruct`

#### Full Custom Config

```yaml
llm:
  provider: "local-lmstudio"

  local-lmstudio:
    base_url: "http://192.168.1.100:1234/v1"  # Remote LM Studio server
    model: "Qwen2.5-14B-Instruct"
    temperature: 0.3
    max_tokens: 4096
    timeout: 120
```

---

### Troubleshooting Local LLMs

**LM Studio Issues:**

1. **"Connection refused"**
   - Ensure LM Studio server is running (green indicator)
   - Check port 1234 is not blocked by firewall
   - Try: `curl http://localhost:1234/v1/models`

2. **"Model not found"**
   - Model name in config.yaml must match loaded model in LM Studio
   - Check model name in LM Studio's server tab

3. **Slow generation**
   - Use GPU acceleration (Settings > Hardware)
   - Try a smaller model (8B instead of 14B)
   - Reduce `max_tokens` in config

**Ollama Issues:**

1. **"Connection refused"**
   - Start Ollama: `ollama serve`
   - Check if running: `ps aux | grep ollama`
   - Verify endpoint: `curl http://localhost:11434/v1/models`

2. **"Model not found"**
   - Pull the model first: `ollama pull llama3.1:8b-instruct`
   - List models: `ollama list`
   - Use exact tag format from `ollama list`

3. **Out of memory**
   - Use smaller model: `ollama pull llama3.1:8b-instruct`
   - Set OLLAMA_NUM_GPU=0 to use CPU only
   - Close other applications

---

### Performance Tips

**Hardware Recommendations:**
- **Minimum**: 8GB RAM, CPU-only (slow but works)
- **Recommended**: 16GB RAM, NVIDIA GPU with 8GB+ VRAM
- **Optimal**: 32GB RAM, NVIDIA GPU with 24GB+ VRAM (RTX 3090/4090)

**Speed vs Quality:**
- **Fast (1-2 min/theme)**: `llama3.1:8b-instruct`
- **Balanced (3-5 min/theme)**: `qwen2.5:14b-instruct`
- **Quality (5-10 min/theme)**: `mixtral:8x7b-instruct`

**GPU Acceleration:**
- LM Studio: Enable in Settings > Hardware > Use GPU
- Ollama: Automatically uses GPU if available (CUDA/Metal/ROCm)

---

### Comparison: Cloud vs Local

| Feature | Cloud (OpenAI/Anthropic) | Local (LM Studio/Ollama) |
|---------|--------------------------|--------------------------|
| **Cost** | Pay per token (~$0.01-0.10/theme) | Free after setup |
| **Privacy** | Data sent to cloud | 100% local |
| **Quality** | Excellent (GPT-4, Claude 3.5) | Good (Llama 3.1, Mixtral) |
| **Speed** | Fast (2-10 sec/theme) | Slower (1-10 min/theme) |
| **Setup** | API key only | Download models (~4-40GB) |
| **Hardware** | None | 8GB+ RAM, GPU recommended |
| **Offline** | No | Yes |

---

### Manual Test Plan (Dual-Model)

Test local providers with both text-only and vision scenarios:

```bash
# ===== LM Studio Dual-Model Test =====
# 1. Download models in LM Studio:
#    - Meta-Llama-3.1-8B-Instruct (brains)
#    - Llama-3.2-Vision-11B-Instruct (vision)
# 2. Start server on port 1234 with brains model loaded
# 3. Update config.yaml:
#    provider: local-lmstudio
#    brains_model: Meta-Llama-3.1-8B-Instruct
#    brains_base_url: http://localhost:1234/v1
#    vision_model: Llama-3.2-Vision-11B-Instruct
#    vision_base_url: http://localhost:1234/v1

# Test 1: Text-only generation (uses brains model)
wpgen generate "Modern blog with dark mode" --provider local-lmstudio
# Expected: Theme generates using brains model, no vision needed

# Test 2: GUI with image upload (uses vision model)
wpgen gui
# 1. Select local-lmstudio provider
# 2. Upload a design mockup image
# 3. Generate
# Expected: GUI shows "Dual-model: Brains + Vision" in status
# Manually switch to vision model in LM Studio when image analysis starts

# Test 3: Missing vision model error
# 1. In GUI, clear vision_model field
# 2. Upload an image
# 3. Try to generate
# Expected: Clear error message telling user to set vision model or remove images

# ===== Ollama Dual-Model Test =====
# 1. Pull both models:
ollama pull llama3.1:8b-instruct
ollama pull llama3.2-vision:11b-instruct

# 2. Ensure Ollama server running:
curl http://localhost:11434/v1/models

# 3. Update config.yaml:
#    provider: local-ollama
#    brains_model: llama3.1:8b-instruct
#    vision_model: llama3.2-vision:11b-instruct
#    (both use http://localhost:11434/v1)

# Test 1: Text-only (uses brains model)
wpgen generate "Minimal portfolio" --provider local-ollama
# Expected: Theme generates locally, logs show brains model usage

# Test 2: GUI with image (uses vision model)
wpgen gui
# 1. Select local-ollama
# 2. Upload mockup
# 3. Generate
# Expected: Ollama automatically switches to vision model when analyzing images

# Test 3: Verify automatic routing
# Check logs for model switching: brains → vision → brains

# ===== Verify GUI Hover Tooltips =====
# 1. Launch GUI: wpgen gui
# 2. Hover over each control and verify info tooltips appear:
#    - Website Description
#    - LLM Provider dropdown
#    - Brains Model/Base URL
#    - Vision Model/Base URL
#    - All Guided Mode fields (Site name, Tagline, Goal, etc.)
#    - Optional Features (WooCommerce, Gutenberg blocks, Dark mode, Preloader)
#    - Image upload
#    - Text upload
#    - Generation Options (Push to GitHub, Deploy to WordPress, Repo name)
# Expected: Every control has a clear 1-2 line tooltip explaining its purpose
```

---

### Resources

- **LM Studio**: [lmstudio.ai](https://lmstudio.ai/) | [Docs](https://lmstudio.ai/docs)
- **Ollama**: [ollama.ai](https://ollama.ai/) | [Model Library](https://ollama.ai/library) | [GitHub](https://github.com/ollama/ollama)
- **Recommended Models**: [DataCamp 2024 Guide](https://www.datacamp.com/blog/best-open-source-llms) | [Collabnix 2025 Roundup](https://collabnix.com/top-10-open-source-llms-you-need-to-know-in-2025/)

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

- Built with Python 3.10+
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

<a href="https://buymeacoffee.com/Blueibear" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

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
