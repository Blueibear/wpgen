"""
Pattern and Component Library for WPGen
Provides reusable design patterns for modern WordPress themes
"""

from typing import Dict, Any
import json
from pathlib import Path


class PatternLibrary:
    """Central registry for design patterns and components"""

    def __init__(self):
        self.patterns_dir = Path(__file__).parent
        self._patterns = {}
        self._load_patterns()

    def _load_patterns(self):
        """Load all pattern definitions"""
        # Patterns will be loaded from JSON files or defined here
        pass

    def get_pattern(self, pattern_name: str) -> Dict[str, Any]:
        """Get a specific pattern by name"""
        return self._patterns.get(pattern_name, {})

    def get_all_patterns(self) -> Dict[str, Any]:
        """Get all available patterns"""
        return self._patterns


# Pattern definitions for modern ecommerce themes
PATTERNS = {
    'header': {
        'name': 'Modern Header',
        'description': 'Responsive header with logo, navigation, and mobile menu',
        'structure': '''
<header class="site-header">
    <div class="header-inner container">
        <div class="site-branding">
            [LOGO]
            <div class="site-title-group">
                [SITE_TITLE]
                [SITE_DESCRIPTION]
            </div>
        </div>

        <button class="mobile-menu-toggle" aria-label="Toggle mobile menu">
            <span class="menu-icon"></span>
        </button>

        <nav class="main-navigation">
            [PRIMARY_MENU]
        </nav>
    </div>
</header>
        ''',
        'classes': [
            'site-header', 'header-inner', 'container', 'site-branding',
            'site-title-group', 'mobile-menu-toggle', 'main-navigation'
        ],
        'css_requirements': [
            'Flexbox layout for logo and nav',
            'Sticky/fixed positioning option',
            'Mobile hamburger menu styles',
            'Responsive breakpoints'
        ]
    },

    'hero': {
        'name': 'Hero Section',
        'description': 'Full-width hero banner with background, headline, and CTA',
        'structure': '''
<section class="hero-section">
    <div class="hero-overlay"></div>
    <div class="hero-content container">
        <h1 class="hero-title">[HEADLINE]</h1>
        <p class="hero-subtitle">[SUBHEADLINE]</p>
        <div class="hero-cta">
            <a href="[CTA_URL]" class="btn btn-primary btn-lg">[CTA_TEXT]</a>
            <a href="[SECONDARY_URL]" class="btn btn-outline btn-lg">[SECONDARY_TEXT]</a>
        </div>
    </div>
</section>
        ''',
        'classes': [
            'hero-section', 'hero-overlay', 'hero-content', 'hero-title',
            'hero-subtitle', 'hero-cta', 'btn', 'btn-primary', 'btn-outline', 'btn-lg'
        ],
        'css_requirements': [
            'Background image with overlay',
            'Centered content',
            'Min height 500-700px',
            'Responsive typography',
            'Strong button styling'
        ]
    },

    'product_grid': {
        'name': 'Product Grid',
        'description': '3-4 column grid for products or content cards',
        'structure': '''
<section class="products-section section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title">[SECTION_TITLE]</h2>
            <p class="section-subtitle">[SECTION_SUBTITLE]</p>
        </div>

        <div class="products-grid grid grid-3">
            <article class="product-card">
                <div class="product-image">
                    <img src="[IMAGE_URL]" alt="[PRODUCT_NAME]">
                    <span class="product-badge">New</span>
                </div>
                <div class="product-content">
                    <h3 class="product-title">[PRODUCT_NAME]</h3>
                    <p class="product-description">[PRODUCT_DESCRIPTION]</p>
                    <div class="product-meta">
                        <span class="product-price">$[PRICE]</span>
                        <a href="[PRODUCT_URL]" class="btn btn-primary">Shop Now</a>
                    </div>
                </div>
            </article>
            <!-- Repeat for 3-6 products -->
        </div>
    </div>
</section>
        ''',
        'classes': [
            'products-section', 'section', 'section-header', 'section-title',
            'section-subtitle', 'products-grid', 'grid', 'grid-3', 'product-card',
            'product-image', 'product-badge', 'product-content', 'product-title',
            'product-description', 'product-meta', 'product-price'
        ],
        'css_requirements': [
            'CSS Grid layout (3-4 columns)',
            'Card styling with shadows/borders',
            'Hover effects (lift, scale)',
            'Responsive: stack on mobile',
            'Image aspect ratio control'
        ]
    },

    'feature_strip': {
        'name': 'Feature Strip',
        'description': 'Horizontal feature highlights or USPs',
        'structure': '''
<section class="features-section section bg-light">
    <div class="container">
        <div class="features-grid grid grid-3">
            <div class="feature-item">
                <div class="feature-icon">[ICON]</div>
                <h3 class="feature-title">[FEATURE_TITLE]</h3>
                <p class="feature-description">[FEATURE_DESCRIPTION]</p>
            </div>
            <!-- Repeat for 3-4 features -->
        </div>
    </div>
</section>
        ''',
        'classes': [
            'features-section', 'section', 'bg-light', 'features-grid',
            'feature-item', 'feature-icon', 'feature-title', 'feature-description'
        ],
        'css_requirements': [
            'Grid or flexbox layout',
            'Icon styling',
            'Subtle background color',
            'Generous spacing'
        ]
    },

    'cta_strip': {
        'name': 'CTA Strip',
        'description': 'Full-width call-to-action banner',
        'structure': '''
<section class="cta-section section bg-primary">
    <div class="container">
        <div class="cta-content">
            <h2 class="cta-title">[CTA_HEADLINE]</h2>
            <p class="cta-subtitle">[CTA_SUBTITLE]</p>
            <a href="[CTA_URL]" class="btn btn-lg btn-secondary">[CTA_BUTTON_TEXT]</a>
        </div>
    </div>
</section>
        ''',
        'classes': [
            'cta-section', 'section', 'bg-primary', 'cta-content',
            'cta-title', 'cta-subtitle'
        ],
        'css_requirements': [
            'Full-width background color',
            'Centered text',
            'Contrasting button',
            'Padding top/bottom'
        ]
    },

    'footer': {
        'name': 'Multi-Column Footer',
        'description': 'Footer with columns, menus, and copyright bar',
        'structure': '''
<footer class="site-footer">
    <div class="footer-main">
        <div class="container">
            <div class="footer-columns grid grid-4">
                <div class="footer-column">
                    <h3 class="footer-heading">[COLUMN_TITLE]</h3>
                    [WIDGET_AREA_1]
                </div>
                <div class="footer-column">
                    <h3 class="footer-heading">[COLUMN_TITLE]</h3>
                    [WIDGET_AREA_2]
                </div>
                <div class="footer-column">
                    <h3 class="footer-heading">[COLUMN_TITLE]</h3>
                    [WIDGET_AREA_3]
                </div>
                <div class="footer-column">
                    <h3 class="footer-heading">[COLUMN_TITLE]</h3>
                    [WIDGET_AREA_4]
                </div>
            </div>
        </div>
    </div>

    <div class="footer-bottom">
        <div class="container">
            <div class="footer-bottom-inner">
                <p class="copyright">[COPYRIGHT_TEXT]</p>
                <nav class="footer-menu">
                    [FOOTER_MENU]
                </nav>
            </div>
        </div>
    </div>
</footer>
        ''',
        'classes': [
            'site-footer', 'footer-main', 'footer-columns', 'footer-column',
            'footer-heading', 'footer-bottom', 'footer-bottom-inner',
            'copyright', 'footer-menu'
        ],
        'css_requirements': [
            'Multi-column grid layout',
            'Background color distinction',
            'Bottom bar with flex layout',
            'Responsive: stack on mobile',
            'Typography hierarchy'
        ]
    },

    'testimonial_section': {
        'name': 'Testimonials',
        'description': 'Customer testimonials or reviews grid',
        'structure': '''
<section class="testimonials-section section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title">What Our Customers Say</h2>
        </div>

        <div class="testimonials-grid grid grid-3">
            <div class="testimonial-card">
                <div class="testimonial-content">
                    <p class="testimonial-text">"[TESTIMONIAL_TEXT]"</p>
                </div>
                <div class="testimonial-author">
                    <img src="[AVATAR_URL]" alt="[AUTHOR_NAME]" class="author-avatar">
                    <div class="author-info">
                        <p class="author-name">[AUTHOR_NAME]</p>
                        <p class="author-title">[AUTHOR_TITLE]</p>
                    </div>
                </div>
            </div>
            <!-- Repeat for 3 testimonials -->
        </div>
    </div>
</section>
        ''',
        'classes': [
            'testimonials-section', 'testimonials-grid', 'testimonial-card',
            'testimonial-content', 'testimonial-text', 'testimonial-author',
            'author-avatar', 'author-info', 'author-name', 'author-title'
        ],
        'css_requirements': [
            'Card styling',
            'Avatar sizing (circular)',
            'Quote styling',
            'Grid layout'
        ]
    }
}


def get_pattern(pattern_name: str) -> Dict[str, Any]:
    """
    Get a pattern definition by name

    Args:
        pattern_name: Name of the pattern

    Returns:
        Pattern definition dict
    """
    return PATTERNS.get(pattern_name, {})


def get_all_patterns() -> Dict[str, Any]:
    """Get all available patterns"""
    return PATTERNS


def get_pattern_names() -> list:
    """Get list of all pattern names"""
    return list(PATTERNS.keys())


def pattern_to_prompt_context(pattern_name: str) -> str:
    """
    Convert a pattern to natural language context for LLM prompts

    Args:
        pattern_name: Name of the pattern

    Returns:
        String description for LLM context
    """
    pattern = get_pattern(pattern_name)
    if not pattern:
        return ""

    context = f"""
Pattern: {pattern['name']}
{pattern['description']}

HTML Structure:
{pattern['structure']}

Required CSS Classes: {', '.join(pattern['classes'])}

CSS Requirements:
{chr(10).join(f'- {req}' for req in pattern['css_requirements'])}
"""
    return context.strip()
