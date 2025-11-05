# WPGen Examples

This directory contains example prompts and expected outputs for WPGen theme generation.

## Quick Examples

### 1. Minimal Blog Theme

**Prompt:**
```
Create a minimal blog theme with clean typography and a sidebar for widgets.
```

**Expected Features:**
- Clean, readable typography
- Sidebar widget area
- Blog post listing
- Single post template
- Responsive design

**CLI Command:**
```bash
wpgen generate "Create a minimal blog theme with clean typography and a sidebar for widgets."
```

---

### 2. Photography Portfolio

**Prompt:**
```
Build a dark-themed photography portfolio with full-width image galleries and a contact form.
```

**Expected Features:**
- Dark color scheme
- Full-width image galleries
- Portfolio/gallery template
- Contact page with form
- Lightbox for images

**CLI Command:**
```bash
wpgen generate "Build a dark-themed photography portfolio with full-width image galleries and a contact form."
```

---

### 3. Corporate Website

**Prompt:**
```
Create a modern corporate website with services section, team page, testimonials, and light blue color scheme.
```

**Expected Features:**
- Professional appearance
- Services page template
- Team/staff page
- Testimonials section
- Light blue brand colors
- Call-to-action sections

**CLI Command:**
```bash
wpgen generate "Create a modern corporate website with services section, team page, testimonials, and light blue color scheme."
```

---

### 4. E-commerce Theme

**Prompt:**
```
Design an e-commerce ready theme with WooCommerce support, product showcase, shopping cart, and modern checkout flow.
```

**Expected Features:**
- WooCommerce compatibility
- Product listing pages
- Single product templates
- Shopping cart integration
- Checkout page styling
- Product galleries

**CLI Command:**
```bash
wpgen generate "Design an e-commerce ready theme with WooCommerce support, product showcase, shopping cart, and modern checkout flow."
```

---

### 5. Magazine/News Site

**Prompt:**
```
Build a magazine-style theme with featured posts grid, multiple category sections, and advertisement areas.
```

**Expected Features:**
- Grid-based layout
- Featured posts section
- Category-based sections
- Advertisement widget areas
- Post meta information
- Social sharing

**CLI Command:**
```bash
wpgen generate "Build a magazine-style theme with featured posts grid, multiple category sections, and advertisement areas."
```

---

## Advanced Examples with Guided Mode

### Using Guided Mode (GUI Only)

When using the Gradio GUI, you can use Guided Mode for more precise control:

1. Launch GUI: `wpgen gui`
2. Expand "Guided Mode (Optional)"
3. Fill in specific requirements:

**Example Configuration:**
- **Site Name:** "TechBlog Pro"
- **Tagline:** "Insights on Technology"
- **Primary Goal:** "Convert (capture leads)"
- **Pages:** Home, Blog, About, Contact, Services
- **Mood:** Modern & Minimal
- **Colors:** #2563eb (primary), #1e293b (surface)
- **Typography:** Sans-serif
- **Header Style:** Centered logo + nav
- **Hero Type:** Image with overlay text
- **Components:** Blog, Cards, Contact Form, Newsletter, CTA
- **Enable WooCommerce:** No
- **Enable Dark Mode:** Yes
- **Enable Preloader:** Yes

This gives you much more control over the exact structure and appearance.

---

## Example Prompts with Image Uploads

When using the GUI, you can upload design mockups or inspiration images:

1. Upload a design mockup (PNG/JPG)
2. Add prompt: "Create a theme matching this design with the same color scheme and layout"
3. WPGen will analyze the image and extract:
   - Color palette
   - Layout patterns
   - Typography style
   - Component arrangement

---

## Tips for Better Results

1. **Be Specific:** Include colors, layout preferences, and key features
2. **Mention Pages:** List the specific pages you need (About, Services, Portfolio, etc.)
3. **Describe Style:** Use descriptive terms (minimal, modern, vintage, brutalist, etc.)
4. **Include Features:** Mention special features (dark mode, WooCommerce, animations, etc.)
5. **Use Examples:** Reference existing sites or themes as inspiration

---

## Testing Generated Themes

After generating a theme:

1. **Validate:**
   ```bash
   wpgen validate output/your-theme-name
   ```

2. **Test Locally:**
   - Copy theme to WordPress `wp-content/themes/`
   - Activate in WordPress admin
   - Test all pages and features

3. **Check Responsiveness:**
   - Test on mobile, tablet, desktop
   - Verify navigation works
   - Check all breakpoints

---

## Common Issues and Solutions

### Issue: Theme crashes WordPress

**Solution:**
```bash
# Validate the theme first
wpgen validate output/your-theme-name

# Use strict mode for more thorough validation
wpgen generate "your prompt" --strict
```

### Issue: Generated theme missing features

**Solution:**
- Be more explicit in your prompt
- Use Guided Mode in GUI for precise control
- Provide reference images

### Issue: Colors don't match expectations

**Solution:**
- Specify exact hex color codes in prompt
- Upload a color palette image
- Use Guided Mode to set exact colors

---

## More Examples

See the [README.md](../README.md) for more examples and documentation.
