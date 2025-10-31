# WPGen GUI - Graphical User Interface

## Overview

WPGen now includes a powerful **Gradio-based graphical user interface** that makes theme generation even easier. The GUI provides an intuitive way to:

- Input natural language descriptions
- Upload design mockup images
- Upload content documents (text, markdown, PDF)
- Generate themes with AI-powered multi-modal analysis
- Push directly to GitHub

---

## Features

### 🎨 Multi-Modal Input

The GUI supports three types of input:

1. **Text Prompt** - Describe your website in natural language
2. **Design References** - Upload screenshots, mockups, or inspiration images
3. **Content Files** - Upload documents with site content or requirements

### 🤖 AI-Powered Vision

- **OpenAI GPT-4 Vision** - Analyzes uploaded images for design patterns
- **Anthropic Claude 3+** - Understands visual layouts and color schemes
- **Smart Context** - Combines text, images, and documents for comprehensive analysis

### 📊 Real-Time Feedback

- Live status updates during generation
- Progress indicators for each step
- Theme information preview
- Generated file tree visualization

### 🚀 GitHub Integration

- One-click push to GitHub
- Automatic repository creation
- Custom repository naming
- Deployment workflow generation

---

## Installation

The GUI requires additional dependencies. Make sure you have them installed:

```bash
pip install -r requirements.txt
```

**New Dependencies:**
- `gradio` - Web-based GUI framework
- `PyPDF2` - PDF text extraction

---

## Usage

### Starting the GUI

#### Basic Launch

```bash
python main.py gui
```

The GUI will be available at `http://localhost:7860`

#### Custom Port

```bash
python main.py gui --port 8080
```

#### Public Share Link

Create a temporary public URL (useful for remote access):

```bash
python main.py gui --share
```

#### Custom Configuration

```bash
python main.py gui --config my-config.yaml
```

---

## Using the GUI

### 1. Describe Your Website

In the **Website Description** field, enter a detailed description:

```
Create a modern photography portfolio website with:
- Dark theme with elegant typography
- Masonry-style gallery layout
- Blog section for photo stories
- Contact form for booking inquiries
- Mobile-responsive design
```

### 2. Upload Design References (Optional)

Click **"Browse files"** under "Design Mockups / Screenshots" to upload:

- ✅ **PNG, JPG, JPEG, GIF, WEBP** images
- 📏 Max 5MB per image
- 🖼️  Multiple images supported

**What AI looks for in images:**
- Color schemes and palettes
- Layout structures and grids
- Typography styles
- Navigation patterns
- Visual hierarchy
- Component designs

### 3. Upload Content Files (Optional)

Upload documents containing:

- Site content and copy
- Feature requirements
- Page structures
- Brand guidelines

**Supported formats:**
- `.txt` - Plain text files
- `.md` - Markdown documents
- `.pdf` - PDF documents (text extracted automatically)

### 4. Configure Options

- **Push to GitHub**: Enable to automatically create a repository
- **Repository Name**: Custom name (or leave empty for auto-generation)

### 5. Generate!

Click **"🚀 Generate WordPress Theme"** and watch the magic happen!

---

## GUI Interface Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                    WPGen - AI WordPress Theme Generator          │
├─────────────────────────────────┬───────────────────────────────┤
│  INPUT PANEL                    │  OUTPUT PANEL                 │
│                                 │                               │
│  📝 Website Description         │  📊 Generation Status         │
│  ┌────────────────────────┐   │  ┌────────────────────────┐  │
│  │ [Text area]            │   │  │ [Status messages]      │  │
│  └────────────────────────┘   │  └────────────────────────┘  │
│                                 │                               │
│  🖼️  Design References          │  ℹ️  Theme Information        │
│  [Upload button]                │  ┌────────────────────────┐  │
│                                 │  │ [Theme details]        │  │
│  📄 Content Documents           │  └────────────────────────┘  │
│  [Upload button]                │                               │
│                                 │  📁 Generated Files           │
│  ⚙️  Options                    │  ┌────────────────────────┐  │
│  ☐ Push to GitHub              │  │ [File tree]            │  │
│  [Repository name]              │  └────────────────────────┘  │
│                                 │                               │
│  [🚀 Generate WordPress Theme]  │                               │
└─────────────────────────────────┴───────────────────────────────┘
```

---

## Example Workflows

### Workflow 1: Text-Only Generation

1. Enter description: "Create a minimal blog theme"
2. Click generate
3. ✅ Theme created in ~2 minutes

### Workflow 2: Design-Driven Generation

1. Enter description: "Create a portfolio website"
2. Upload 2-3 design mockups showing desired layout
3. AI analyzes images for:
   - Color palette
   - Layout structure
   - Typography choices
4. Click generate
5. ✅ Theme matches visual references

### Workflow 3: Content-Rich Generation

1. Enter description: "Create a corporate website"
2. Upload `about.md` with company info
3. Upload `services.txt` with service descriptions
4. AI extracts content and creates appropriate pages
5. Click generate
6. ✅ Theme includes pre-populated content

### Workflow 4: Full Multi-Modal

1. Enter detailed description
2. Upload design mockups (3 images)
3. Upload content files (2 documents)
4. Enable GitHub push
5. Click generate
6. ✅ Complete theme pushed to GitHub

---

## Multi-Modal AI Analysis

### How It Works

1. **Text Processing**
   - Extracts requirements from your description
   - Identifies features, pages, and integrations

2. **Image Analysis** (if images uploaded)
   - Detects color schemes and palettes
   - Analyzes layout patterns and grids
   - Identifies UI components
   - Recognizes typography styles
   - Notes design patterns

3. **Document Processing** (if files uploaded)
   - Extracts text from PDFs
   - Reads markdown and text files
   - Incorporates content into theme requirements

4. **Synthesis**
   - Combines all inputs
   - Generates comprehensive theme specification
   - Creates WordPress files matching all criteria

### Example AI Analysis

**Input:**
- Text: "Create a photography portfolio"
- Image: Screenshot of dark-themed gallery site
- File: `bio.md` with photographer bio

**AI Extracts:**
```json
{
  "theme_name": "dark-photography-portfolio",
  "color_scheme": "dark (from image: #1a1a1a background)",
  "layout": "masonry grid (detected in image)",
  "features": ["portfolio", "blog", "contact-form"],
  "design_notes": "Dark theme with elegant serif headers,
                   masonry gallery layout, minimal navigation"
}
```

---

## Tips for Best Results

### Writing Effective Prompts

✅ **Good:**
```
Create a modern e-commerce website with:
- Clean, minimal design
- Product showcase with filtering
- Shopping cart and checkout
- Customer reviews section
- Blog for product updates
```

❌ **Too Vague:**
```
Make a website
```

### Choosing Good Reference Images

✅ **Effective images:**
- Full page screenshots
- Clear layout examples
- Consistent design language
- Professional mockups

❌ **Less effective:**
- Small thumbnails
- Blurry screenshots
- Multiple conflicting styles

### Preparing Content Files

✅ **Well-organized:**
```markdown
# About Us
We are a photography studio...

# Services
- Wedding Photography
- Portrait Sessions
- Event Coverage
```

❌ **Unstructured:**
```
photography studio weddings portraits...
```

---

## Troubleshooting

### GUI Won't Start

**Error:** `ModuleNotFoundError: No module named 'gradio'`

**Solution:**
```bash
pip install gradio PyPDF2
```

### Images Not Processing

**Issue:** "Unsupported image format"

**Solution:**
- Use PNG, JPG, or WEBP formats
- Ensure images are under 5MB
- Check file isn't corrupted

### PDF Text Not Extracted

**Issue:** PDF shows "[PDF file - install PyPDF2]"

**Solution:**
```bash
pip install PyPDF2
```

### Multi-Modal Not Working

**Issue:** Images uploaded but not analyzed

**Solutions:**
- Ensure you're using OpenAI GPT-4 Vision or Anthropic Claude 3+
- Check API key is valid
- Verify model supports vision in config.yaml:
  ```yaml
  llm:
    openai:
      model: "gpt-4-vision-preview"  # or "gpt-4-turbo"
  ```

---

## Configuration

### Enable Vision Models

**For OpenAI (config.yaml):**
```yaml
llm:
  provider: "openai"
  openai:
    model: "gpt-4-vision-preview"  # or "gpt-4-turbo"
    max_tokens: 4096
```

**For Anthropic (config.yaml):**
```yaml
llm:
  provider: "anthropic"
  anthropic:
    model: "claude-3-5-sonnet-20241022"  # Supports vision
    max_tokens: 4096
```

### Adjust File Limits

Modify `wpgen/utils/file_handler.py`:

```python
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_SIZE = 2 * 1024 * 1024    # 2MB
```

---

## API Comparison

| Feature | OpenAI GPT-4 Vision | Anthropic Claude 3+ |
|---------|-------------------|-------------------|
| Image Analysis | ✅ Excellent | ✅ Excellent |
| Multiple Images | ✅ Yes | ✅ Yes |
| Max Images | ~10 | ~20 |
| Image Format | Base64 | Base64 |
| Context Length | 128K tokens | 200K tokens |
| Cost | $$$ | $$ |

---

## Keyboard Shortcuts

- **Tab**: Navigate between fields
- **Ctrl/Cmd + Enter**: Submit form (when in text field)
- **Esc**: Clear selection

---

## Advanced Usage

### Programmatic Access

You can also use the GUI components in your own code:

```python
from wpgen.gui import create_gradio_interface

# Create custom interface
interface = create_gradio_interface(config)

# Launch with custom settings
interface.launch(
    server_name="0.0.0.0",
    server_port=8080,
    share=True
)
```

### Custom Theming

Gradio supports custom themes. Modify `gradio_interface.py`:

```python
gr.Blocks(
    title="My Custom WPGen",
    theme=gr.themes.Glass()  # or Base, Monochrome, Soft
)
```

---

## Security Notes

- 🔒 Files are processed locally before sending to AI
- 🔒 Images converted to base64 for API transmission
- 🔒 No files stored permanently by the GUI
- 🔒 GitHub token used securely via environment variables
- ⚠️  Don't upload sensitive/confidential documents

---

## Performance

### Generation Times

- **Text-only**: 1-2 minutes
- **With images** (1-3): 2-3 minutes
- **With documents**: +30 seconds
- **Full multi-modal**: 3-5 minutes

### Resource Usage

- **Memory**: ~500MB (base) + ~100MB per image
- **CPU**: Moderate during file processing
- **Network**: High during AI API calls

---

## Roadmap

Future enhancements planned:

- [ ] Drag-and-drop file upload
- [ ] Image crop/resize tools
- [ ] Real-time theme preview
- [ ] History of generated themes
- [ ] Batch generation
- [ ] Template library
- [ ] Custom color picker
- [ ] Font selector

---

## Examples Gallery

### Example 1: Photography Portfolio
**Input:** "Dark photography portfolio" + gallery mockup image
**Result:** Dark theme with masonry gallery, matching uploaded design

### Example 2: Corporate Site
**Input:** Corporate description + `services.md` file
**Result:** Professional theme with services page pre-populated

### Example 3: Blog Theme
**Input:** "Minimal blog" + typography reference images
**Result:** Clean blog theme with custom fonts from images

---

## Support

For issues with the GUI:

1. Check `logs/wpgen.log` for errors
2. Verify all dependencies are installed
3. Test with text-only first
4. Ensure API keys are valid
5. Open an issue on GitHub with screenshots

---

## Credits

- **GUI Framework**: Gradio (https://gradio.app)
- **PDF Processing**: PyPDF2
- **AI Vision**: OpenAI GPT-4 Vision, Anthropic Claude 3+

---

**Happy theme generating! 🎨✨**
