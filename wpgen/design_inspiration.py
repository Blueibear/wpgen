"""
Design Inspiration Configuration for WPGen
Non-code inspiration references for modern ecommerce theme generation
"""

from typing import Dict, List, Any


# Inspiration brand references (non-scraping, style guidance only)
INSPIRATION_BRANDS = {
    'streetwear_modern': {
        'brands': ['Palace', 'Supreme', 'Kith', 'ASOS', 'Fear of God', 'Stussy'],
        'style_keywords': [
            'bold typography',
            'generous whitespace',
            'strong product cards',
            'minimal navigation',
            'high-contrast imagery',
            'clean grid layouts',
            'large hero images',
            'simple checkout flow'
        ],
        'layout_characteristics': [
            'Full-width hero sections',
            'Product grids with 3-4 columns',
            'Sticky header navigation',
            'Large, tappable CTAs',
            'Image-first design',
            'Minimal text, maximum impact'
        ]
    },
    'minimal_clean': {
        'brands': ['Apple', 'Everlane', 'Muji', 'COS', 'APC'],
        'style_keywords': [
            'subtle colors',
            'generous whitespace',
            'refined typography',
            'soft shadows',
            'clean lines',
            'understated elegance'
        ],
        'layout_characteristics': [
            'Breathing room around elements',
            'Simple grid structures',
            'Soft color palettes',
            'Serif or sans-serif typography',
            'Minimal borders'
        ]
    },
    'bold_neon': {
        'brands': ['Cyberpunk aesthetics', 'Tech startups', 'Gaming brands'],
        'style_keywords': [
            'neon accents',
            'dark backgrounds',
            'high contrast',
            'electric colors',
            'futuristic vibes',
            'glow effects'
        ],
        'layout_characteristics': [
            'Dark mode first',
            'Glowing CTAs',
            'Neon borders',
            'Tech-inspired typography',
            'High energy design'
        ]
    },
    'dark_mode': {
        'brands': ['Spotify', 'Twitter', 'Discord', 'GitHub'],
        'style_keywords': [
            'sophisticated dark theme',
            'excellent readability',
            'subtle accents',
            'reduced eye strain',
            'modern interface'
        ],
        'layout_characteristics': [
            'Dark background (#0F172A)',
            'Light text (#F1F5F9)',
            'Subtle borders',
            'Elevated cards',
            'Blue/purple accents'
        ]
    }
}


def get_inspiration_context(profile_name: str) -> str:
    """
    Get inspiration context for a design profile

    Args:
        profile_name: Name of the design profile

    Returns:
        String description for LLM context
    """
    inspiration = INSPIRATION_BRANDS.get(profile_name, {})

    if not inspiration:
        return ""

    context = f"""
DESIGN INSPIRATION (Style Reference Only - Do Not Copy Code):

Reference Brands for {profile_name.replace('_', ' ').title()} Style:
{', '.join(inspiration.get('brands', []))}

Style Keywords:
{chr(10).join(f'- {keyword}' for keyword in inspiration.get('style_keywords', []))}

Layout Characteristics to Emulate:
{chr(10).join(f'- {char}' for char in inspiration.get('layout_characteristics', []))}

IMPORTANT: Use these as INSPIRATION for layout style and visual approach only.
DO NOT copy any code, text, or assets from these brands.
Create original implementations following these aesthetic principles.
"""
    return context.strip()


def get_ecommerce_best_practices() -> str:
    """
    Get ecommerce best practices for theme generation

    Returns:
        String with ecommerce UX guidelines
    """
    return """
ECOMMERCE THEME BEST PRACTICES:

1. NAVIGATION:
   - Clear, minimal top navigation
   - Sticky header with shopping cart icon
   - Search functionality prominent
   - Mobile: hamburger menu with full-screen overlay

2. PRODUCT DISPLAY:
   - Large, high-quality product images
   - Clear pricing (large, bold font)
   - Prominent "Add to Cart" buttons
   - Product grids: 3-4 columns on desktop, 2 on tablet, 1 on mobile
   - Quick view option for products

3. HOMEPAGE LAYOUT:
   - Hero section with main collection or promotion
   - Featured products section
   - Category highlights
   - Social proof (testimonials, reviews)
   - Newsletter signup
   - Trust indicators (free shipping, returns, etc.)

4. CALLS TO ACTION:
   - High contrast CTA buttons
   - Generous button sizing (min 44px tap target)
   - Clear, action-oriented copy ("Shop Now", "Add to Cart", "View Collection")

5. TRUST & CONVERSION:
   - Visible security badges
   - Customer testimonials
   - Clear return policy
   - Free shipping messaging
   - Product reviews

6. MOBILE OPTIMIZATION:
   - Touch-friendly interface (44px+ tap targets)
   - Simplified mobile navigation
   - Optimized product images
   - Easy checkout process
   - Sticky "Add to Cart" on product pages

7. PERFORMANCE:
   - Lazy load images
   - Optimized asset loading
   - Minimal JavaScript
   - Fast page transitions
"""


def get_modern_design_trends() -> str:
    """
    Get current design trends for modern themes

    Returns:
        String with design trend guidance
    """
    return """
MODERN DESIGN TRENDS (2024-2025):

1. VISUAL HIERARCHY:
   - Bold, oversized typography
   - Clear content hierarchy
   - Generous whitespace
   - Strategic use of color

2. MICRO-INTERACTIONS:
   - Smooth transitions (0.2-0.3s)
   - Hover effects (lift, scale, color change)
   - Loading states
   - Focus indicators

3. LAYOUT:
   - Asymmetric layouts for visual interest
   - Grid-based structure
   - Full-width sections
   - Card-based components

4. COLOR:
   - High contrast for readability
   - Bold accent colors
   - Monochromatic schemes
   - Dark mode support

5. TYPOGRAPHY:
   - Large headings (48px+)
   - Readable body text (16-18px)
   - Clear hierarchy
   - Web-safe font stacks with modern alternatives

6. IMAGERY:
   - Full-width hero images
   - Proper aspect ratios
   - Lazy loading
   - WebP format support

7. COMPONENTS:
   - Card-based layouts
   - Floating CTAs
   - Sticky headers
   - Modal overlays
   - Toast notifications
"""
