"""
Prompt Optimizer for WPGen.

This module takes raw user prompts and rewrites them into structured,
technical, explicit instructions for the LLM to generate high-quality themes.
It detects domain-specific intent and automatically applies appropriate blueprints.
"""

import re
from typing import Any
from dataclasses import dataclass


@dataclass
class OptimizedPrompt:
    """Container for optimized prompt data."""

    original_prompt: str
    optimized_prompt: str
    detected_domain: str
    blueprint_name: str | None
    injected_requirements: dict[str, Any]
    woocommerce_detected: bool


class PromptOptimizer:
    """
    Optimizes user prompts for better theme generation.

    Responsibilities:
    - Detect domain-specific intent (ecommerce, blog, portfolio, magazine, photography)
    - Detect store/WooCommerce keywords
    - Rewrite vague prompts into structured technical instructions
    - Inject blueprint requirements automatically
    """

    # Keywords for domain detection
    ECOMMERCE_KEYWORDS = {
        'store', 'shop', 'ecommerce', 'woocommerce', 'sell', 'product', 'products',
        'cart', 'checkout', 'payment', 'merch', 'merchandise', 'clothing', 'apparel',
        'shirts', 'tees', 't-shirts', 'fashion', 'boutique', 'retail', 'purchase',
        'buy', 'sale', 'catalog', 'inventory'
    }

    BLOG_KEYWORDS = {
        'blog', 'article', 'posts', 'writing', 'journal', 'news', 'magazine',
        'publication', 'editorial', 'content', 'stories', 'author', 'blogger'
    }

    PORTFOLIO_KEYWORDS = {
        'portfolio', 'showcase', 'gallery', 'work', 'projects', 'creative',
        'designer', 'developer', 'artist', 'photographer', 'freelancer',
        'agency', 'studio', 'case studies', 'examples'
    }

    MAGAZINE_KEYWORDS = {
        'magazine', 'news', 'publication', 'editorial', 'articles', 'journal',
        'media', 'press', 'stories', 'featured', 'trending', 'latest'
    }

    PHOTOGRAPHY_KEYWORDS = {
        'photography', 'photo', 'photos', 'images', 'photographer', 'camera',
        'portrait', 'wedding', 'event', 'visual', 'shoot', 'picture'
    }

    def __init__(self):
        """Initialize the prompt optimizer."""
        pass

    def optimize(self, raw_prompt: str, additional_context: dict[str, Any] | None = None) -> OptimizedPrompt:
        """
        Optimize a raw user prompt into a structured technical instruction.

        Args:
            raw_prompt: The original user prompt
            additional_context: Optional additional context (images, files, etc.)

        Returns:
            OptimizedPrompt object with all optimization data
        """
        raw_prompt_lower = raw_prompt.lower()

        # Detect domain and WooCommerce intent
        detected_domain = self._detect_domain(raw_prompt_lower)
        woocommerce_detected = self._detect_woocommerce(raw_prompt_lower)

        # Override domain if WooCommerce detected
        if woocommerce_detected:
            detected_domain = 'ecommerce'

        # Select appropriate blueprint
        blueprint_name = self._select_blueprint(detected_domain)

        # Generate injected requirements based on domain
        injected_requirements = self._generate_requirements(detected_domain, woocommerce_detected)

        # Rewrite the prompt
        optimized_prompt = self._rewrite_prompt(
            raw_prompt,
            detected_domain,
            woocommerce_detected,
            injected_requirements
        )

        return OptimizedPrompt(
            original_prompt=raw_prompt,
            optimized_prompt=optimized_prompt,
            detected_domain=detected_domain,
            blueprint_name=blueprint_name,
            injected_requirements=injected_requirements,
            woocommerce_detected=woocommerce_detected
        )

    def _detect_domain(self, prompt_lower: str) -> str:
        """
        Detect the primary domain/intent from the prompt.

        Returns: 'ecommerce', 'blog', 'portfolio', 'magazine', 'photography', or 'general'
        """
        scores = {
            'ecommerce': self._count_keywords(prompt_lower, self.ECOMMERCE_KEYWORDS),
            'blog': self._count_keywords(prompt_lower, self.BLOG_KEYWORDS),
            'portfolio': self._count_keywords(prompt_lower, self.PORTFOLIO_KEYWORDS),
            'magazine': self._count_keywords(prompt_lower, self.MAGAZINE_KEYWORDS),
            'photography': self._count_keywords(prompt_lower, self.PHOTOGRAPHY_KEYWORDS),
        }

        # Return domain with highest score, or 'general' if no clear winner
        max_score = max(scores.values())
        if max_score == 0:
            return 'general'

        return max(scores, key=scores.get)

    def _detect_woocommerce(self, prompt_lower: str) -> bool:
        """Detect if WooCommerce functionality is needed."""
        return any(keyword in prompt_lower for keyword in self.ECOMMERCE_KEYWORDS)

    def _count_keywords(self, text: str, keywords: set[str]) -> int:
        """Count how many keywords from a set appear in text."""
        count = 0
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                count += 1
        return count

    def _select_blueprint(self, domain: str) -> str | None:
        """Select the appropriate blueprint based on detected domain."""
        blueprint_map = {
            'ecommerce': 'ecommerce_blueprint',
            'blog': 'blog_blueprint',
            'portfolio': 'portfolio_blueprint',
            'magazine': 'magazine_blueprint',
            'photography': 'portfolio_blueprint',  # Use portfolio blueprint for photography
            'general': None
        }
        return blueprint_map.get(domain)

    def _generate_requirements(self, domain: str, woocommerce: bool) -> dict[str, Any]:
        """Generate structured requirements based on domain and WooCommerce detection."""
        requirements = {
            'domain': domain,
            'visual_requirements': self._get_visual_requirements(domain),
            'template_requirements': self._get_template_requirements(domain, woocommerce),
            'css_requirements': self._get_css_requirements(domain),
            'layout_defaults': self._get_layout_defaults(domain),
            'ux_elements': self._get_ux_elements(domain)
        }

        if woocommerce:
            requirements['woocommerce'] = self._get_woocommerce_requirements()

        return requirements

    def _get_visual_requirements(self, domain: str) -> list[str]:
        """Get visual requirements based on domain."""
        base_requirements = [
            'Hero section on homepage with compelling headline and CTA',
            'Professional header with logo/branding and navigation menu',
            'Footer with widgets, social links, and copyright',
            'Visual hierarchy with proper heading structure (H1, H2, H3)',
            'CSS custom properties for theme colors and typography',
            'Responsive grid and flexbox layouts',
            'Professional spacing and whitespace',
            'Modern typography with proper font pairing'
        ]

        domain_specific = {
            'ecommerce': [
                'Product grid layout with hover effects',
                'Featured products section on homepage',
                'Category navigation and filtering UI',
                'Shopping cart icon in header',
                'Trust badges and testimonials section',
                'Promotional banner area'
            ],
            'blog': [
                'Featured posts section with thumbnails',
                'Article grid/list with excerpts',
                'Sidebar with widgets (categories, recent posts, search)',
                'Author bio section',
                'Social sharing buttons',
                'Comment section styling'
            ],
            'portfolio': [
                'Project showcase grid with image previews',
                'Case study layout with before/after sections',
                'Skills and services section',
                'Client testimonials carousel',
                'Contact form with professional styling',
                'About section with profile image'
            ],
            'magazine': [
                'Featured story hero with large image',
                'Multi-column article layout',
                'Category sections with horizontal scrolling',
                'Trending/popular articles widget',
                'Newsletter signup form',
                'Advertisement placeholder areas'
            ]
        }

        return base_requirements + domain_specific.get(domain, [])

    def _get_template_requirements(self, domain: str, woocommerce: bool) -> list[str]:
        """Get template file requirements based on domain."""
        base_templates = [
            'header.php: Must contain <header> tag, site-branding div, nav menu, and opening <main id="content">',
            'footer.php: Must contain closing </main> tag, <footer> tag, and wp_footer() call',
            'index.php: Must contain the WordPress loop with get_header() and get_footer()',
            'functions.php: Theme setup, widget areas, enqueue scripts/styles',
            'style.css: WordPress theme header with proper metadata',
            'front-page.php: Custom homepage with hero and feature sections',
            'page.php: Single page template',
            'single.php: Single post template with navigation',
            'archive.php: Archive template with post loop',
            'search.php: Search results template',
            'sidebar.php: Sidebar with widget areas',
            '404.php: Custom 404 error page'
        ]

        if woocommerce:
            base_templates.extend([
                'woocommerce.php: WooCommerce compatibility template',
                'woocommerce/archive-product.php: Product archive/shop page',
                'woocommerce/single-product.php: Single product page',
                'woocommerce/cart.php: Shopping cart template (optional override)',
                'woocommerce/checkout.php: Checkout template (optional override)'
            ])

        domain_specific = {
            'blog': [
                'home.php: Blog index page',
                'category.php: Category archive',
                'tag.php: Tag archive',
                'author.php: Author archive'
            ],
            'portfolio': [
                'archive-portfolio.php: Portfolio archive',
                'single-portfolio.php: Single portfolio item',
                'page-portfolio.php: Portfolio landing page template'
            ],
            'magazine': [
                'home.php: Magazine-style homepage with sections',
                'category.php: Category pages with featured posts',
                'single.php: Article template with related posts'
            ]
        }

        return base_templates + domain_specific.get(domain, [])

    def _get_css_requirements(self, domain: str) -> list[str]:
        """Get CSS structure requirements."""
        return [
            'CSS custom properties (variables) for colors, spacing, and typography',
            'Mobile-first responsive design with breakpoints',
            'Flexbox and CSS Grid for layouts',
            'Consistent spacing scale using CSS variables',
            'Typography scale with proper hierarchy',
            'Component-based CSS organization',
            'Hover and focus states for interactive elements',
            'Smooth transitions and animations',
            'Accessibility: proper contrast ratios, focus indicators',
            'Print stylesheet considerations'
        ]

    def _get_layout_defaults(self, domain: str) -> dict[str, str]:
        """Get layout defaults based on domain."""
        layouts = {
            'ecommerce': 'full-width with sidebar on product pages',
            'blog': 'sidebar-right for posts, full-width for pages',
            'portfolio': 'full-width with grid layouts',
            'magazine': 'multi-column with featured areas',
            'general': 'responsive with optional sidebar'
        }

        return {
            'primary_layout': layouts.get(domain, layouts['general']),
            'container_width': '1200px',
            'content_width': '800px',
            'sidebar_width': '300px',
            'grid_columns': '3' if domain == 'ecommerce' else '2',
            'mobile_breakpoint': '768px',
            'tablet_breakpoint': '992px',
            'desktop_breakpoint': '1200px'
        }

    def _get_ux_elements(self, domain: str) -> list[str]:
        """Get UX element requirements."""
        base_elements = [
            'Hero section with headline, subheadline, and CTA button',
            'Clear navigation menu with dropdown support',
            'Mobile-responsive hamburger menu',
            'Breadcrumbs for navigation context',
            'Search functionality',
            'Social media links',
            'Contact information in footer',
            'Back to top button for long pages',
            'Loading states and transitions',
            'Form validation feedback'
        ]

        domain_specific = {
            'ecommerce': [
                'Add to cart buttons',
                'Product quick view',
                'Shopping cart widget',
                'Wishlist functionality',
                'Product filtering and sorting',
                'Customer reviews section',
                'Related products carousel'
            ],
            'blog': [
                'Post navigation (prev/next)',
                'Category and tag filters',
                'Author bio box',
                'Social sharing buttons',
                'Comment form',
                'Related posts section',
                'Newsletter signup'
            ],
            'portfolio': [
                'Project showcase grid',
                'Lightbox/modal for images',
                'Case study navigation',
                'Contact form',
                'Skills/services list',
                'Client logo grid',
                'Testimonials carousel'
            ]
        }

        return base_elements + domain_specific.get(domain, [])

    def _get_woocommerce_requirements(self) -> dict[str, Any]:
        """Get WooCommerce-specific requirements."""
        return {
            'theme_support': [
                'woocommerce',
                'wc-product-gallery-zoom',
                'wc-product-gallery-lightbox',
                'wc-product-gallery-slider'
            ],
            'templates': [
                'archive-product.php',
                'single-product.php',
                'woocommerce.php'
            ],
            'hooks': [
                'woocommerce_before_main_content',
                'woocommerce_after_main_content',
                'woocommerce_sidebar',
                'woocommerce_before_shop_loop',
                'woocommerce_after_shop_loop',
                'woocommerce_before_single_product',
                'woocommerce_after_single_product'
            ],
            'css_selectors': [
                '.woocommerce',
                '.woocommerce-page',
                '.products',
                '.product',
                '.cart',
                '.checkout',
                '.woocommerce-cart',
                '.woocommerce-checkout'
            ],
            'features': [
                'Product grid with responsive columns',
                'Product image gallery',
                'Add to cart button styling',
                'Cart icon in header with item count',
                'Product categories widget',
                'Price display formatting',
                'Sale badge styling',
                'Product pagination',
                'Breadcrumb navigation',
                'Product search widget'
            ]
        }

    def _rewrite_prompt(
        self,
        raw_prompt: str,
        domain: str,
        woocommerce: bool,
        requirements: dict[str, Any]
    ) -> str:
        """
        Rewrite the user's prompt into a structured, technical instruction.

        This creates a comprehensive prompt that the LLM can use to generate
        high-quality, complete WordPress themes.
        """
        # Build the optimized prompt
        sections = []

        # Introduction
        sections.append("=== WORDPRESS THEME GENERATION INSTRUCTIONS ===\n")
        sections.append(f"USER REQUEST: {raw_prompt}\n")
        sections.append(f"DETECTED DOMAIN: {domain.upper()}\n")
        if woocommerce:
            sections.append("WOOCOMMERCE: REQUIRED\n")

        # Visual requirements
        sections.append("\n--- VISUAL DESIGN REQUIREMENTS ---")
        for req in requirements['visual_requirements']:
            sections.append(f"• {req}")

        # Template requirements
        sections.append("\n--- REQUIRED TEMPLATE FILES ---")
        for template in requirements['template_requirements']:
            sections.append(f"• {template}")

        # CSS requirements
        sections.append("\n--- CSS ARCHITECTURE ---")
        for css_req in requirements['css_requirements']:
            sections.append(f"• {css_req}")

        # Layout defaults
        sections.append("\n--- LAYOUT CONFIGURATION ---")
        for key, value in requirements['layout_defaults'].items():
            sections.append(f"• {key}: {value}")

        # UX elements
        sections.append("\n--- USER EXPERIENCE ELEMENTS ---")
        for ux_elem in requirements['ux_elements']:
            sections.append(f"• {ux_elem}")

        # WooCommerce specifics
        if woocommerce:
            sections.append("\n--- WOOCOMMERCE INTEGRATION ---")
            wc_reqs = requirements['woocommerce']

            sections.append("\nTheme Support:")
            for support in wc_reqs['theme_support']:
                sections.append(f"  • add_theme_support('{support}');")

            sections.append("\nRequired Templates:")
            for template in wc_reqs['templates']:
                sections.append(f"  • {template}")

            sections.append("\nWooCommerce Hooks to Use:")
            for hook in wc_reqs['hooks']:
                sections.append(f"  • {hook}")

            sections.append("\nFeatures to Implement:")
            for feature in wc_reqs['features']:
                sections.append(f"  • {feature}")

        # Code quality requirements - CRITICAL for preventing theme breakage
        sections.append("\n--- CRITICAL CODE QUALITY STANDARDS ---")
        sections.append("⚠️  ABSOLUTELY REQUIRED - Theme WILL BREAK if these are violated:")
        sections.append("")
        sections.append("PHP SYNTAX RULES:")
        sections.append("  • NEVER output invalid PHP syntax")
        sections.append("  • NEVER leave PHP blocks unclosed (<?php must have matching ?>)")
        sections.append("  • NEVER output unmatched braces { or }")
        sections.append("  • ALWAYS ensure every opening brace { has a closing brace }")
        sections.append("  • NEVER insert invisible Unicode characters (zero-width spaces, etc.)")
        sections.append("  • NEVER include markdown code fences (```) in generated code")
        sections.append("  • NEVER include explanatory text before code (start with <?php or <!DOCTYPE)")
        sections.append("")
        sections.append("REQUIRED WORDPRESS TEMPLATE TAGS:")
        sections.append("  • header.php MUST include wp_head() before </head>")
        sections.append("  • header.php MUST include <!DOCTYPE html>, <meta charset>, <meta viewport>")
        sections.append("  • header.php MUST open <main id=\"content\"> but NOT close it")
        sections.append("  • footer.php MUST close </main> and include wp_footer() before </body>")
        sections.append("  • footer.php MUST include closing </body> and </html> tags")
        sections.append("  • All page templates MUST call get_header() and get_footer()")
        sections.append("")
        sections.append("DEPRECATED FUNCTIONS - NEVER USE:")
        sections.append("  • NEVER use post_loop() - use have_posts() and the_post() instead")
        sections.append("  • NEVER use the_category_list() - use the_category() instead")
        sections.append("  • NEVER use bloginfo('url') - use home_url() instead")
        sections.append("  • NEVER call wp_pagenavi() without function_exists() check")
        sections.append("")
        sections.append("REQUIRED WORDPRESS PRACTICES:")
        sections.append("  • Use proper WordPress loop: if (have_posts()) : while (have_posts()) : the_post()")
        sections.append("  • Escape ALL output: esc_html(), esc_url(), esc_attr()")
        sections.append("  • Use get_template_part() ONLY for files that will exist")
        sections.append("  • Wrap plugin functions in function_exists() checks")
        sections.append("  • Use translation functions: __(), _e(), esc_html__(), esc_html_e()")
        sections.append("  • Enqueue scripts/styles via wp_enqueue_style() and wp_enqueue_script()")
        sections.append("  • Include proper WordPress theme header in style.css")
        sections.append("  • Follow WordPress coding standards (spaces, braces, naming)")
        sections.append("")
        sections.append("TEMPLATE STRUCTURE:")
        sections.append("  • Every template that displays content needs get_header() + get_footer()")
        sections.append("  • Templates MUST NOT have trailing commas in get_template_part() calls")
        sections.append("  • Use semantic HTML5: <header>, <main>, <footer>, <article>, <section>")
        sections.append("  • Add proper classes: .site-header, .site-main, .site-footer")
        sections.append("  • Ensure proper DOM structure: header -> main -> footer")

        # Final instruction
        sections.append("\n--- GENERATION INSTRUCTIONS ---")
        sections.append("Generate a complete, production-ready WordPress theme that:")
        sections.append("1. Fully implements ALL requirements listed above")
        sections.append("2. Has professional, modern visual design")
        sections.append("3. Is mobile-responsive and accessible")
        sections.append("4. Uses semantic HTML5 markup")
        sections.append("5. Has no syntax errors or broken code")
        sections.append("6. Includes comprehensive CSS styling")
        sections.append("7. Has interactive JavaScript where appropriate")
        sections.append(f"8. Is optimized for the {domain} domain")
        if woocommerce:
            sections.append("9. Is fully compatible with WooCommerce")
        sections.append("\nThe theme must be immediately usable in WordPress without errors.")

        return "\n".join(sections)

    def get_blueprint_requirements(self, blueprint_name: str) -> dict[str, Any] | None:
        """
        Get requirements for a specific blueprint.
        This is a convenience method for external modules.
        """
        if blueprint_name == 'ecommerce_blueprint':
            return self._generate_requirements('ecommerce', woocommerce=True)
        elif blueprint_name == 'blog_blueprint':
            return self._generate_requirements('blog', woocommerce=False)
        elif blueprint_name == 'portfolio_blueprint':
            return self._generate_requirements('portfolio', woocommerce=False)
        elif blueprint_name == 'magazine_blueprint':
            return self._generate_requirements('magazine', woocommerce=False)
        else:
            return None
