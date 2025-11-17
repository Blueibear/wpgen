"""
E-commerce Blueprint for WPGen.

Defines structure and requirements for e-commerce/WooCommerce themes.
"""

from typing import Any


class EcommerceBlueprint:
    """Blueprint for e-commerce themes with WooCommerce support."""

    def __init__(self):
        """Initialize the e-commerce blueprint."""
        self.name = "ecommerce"
        self.display_name = "E-commerce / WooCommerce"
        self.description = "Professional online store with WooCommerce integration"

    def get_required_templates(self) -> list[str]:
        """Get list of required template files."""
        return [
            'style.css',
            'index.php',
            'header.php',
            'footer.php',
            'functions.php',
            'front-page.php',
            'page.php',
            'single.php',
            'archive.php',
            'search.php',
            'sidebar.php',
            '404.php',
            'woocommerce.php',
            'woocommerce/archive-product.php',
            'woocommerce/single-product.php',
        ]

    def get_optional_templates(self) -> list[str]:
        """Get list of optional template files."""
        return [
            'woocommerce/cart.php',
            'woocommerce/checkout.php',
            'woocommerce/content-product.php',
            'woocommerce/content-single-product.php',
            'page-shop.php',
            'taxonomy-product_cat.php',
            'taxonomy-product_tag.php',
        ]

    def get_template_structure(self) -> dict[str, str]:
        """Get template structure requirements."""
        return {
            'header.php': '''Must contain:
- <!DOCTYPE html> and <html> tag
- <head> with wp_head()
- <body> with body_class()
- <header> tag with site branding
- Navigation menu with wp_nav_menu()
- Opening <main id="content"> tag
- Shopping cart icon with item count
Must NOT close </main> tag''',

            'footer.php': '''Must contain:
- Closing </main> tag
- <footer> tag with widgets
- Footer menu and social links
- Copyright notice
- wp_footer() before </body>
- Closing </body> and </html> tags''',

            'index.php': '''Must contain:
- get_header() call
- WordPress loop with have_posts()
- Post content display
- Pagination
- get_sidebar() call
- get_footer() call''',

            'front-page.php': '''Must contain:
- get_header()
- Hero section with shop CTA
- Featured products section
- Product categories grid
- Promotional banners
- Testimonials/trust badges
- Newsletter signup
- get_footer()''',

            'woocommerce.php': '''Must contain:
- get_header()
- woocommerce_content() call
- get_footer()''',

            'woocommerce/archive-product.php': '''Must contain:
- woocommerce_before_shop_loop hook
- Product grid/loop
- woocommerce_after_shop_loop hook
- Pagination
- Category filtering
- Product sorting''',

            'woocommerce/single-product.php': '''Must contain:
- woocommerce_before_single_product hook
- Product gallery
- Product details and meta
- Add to cart form
- Product tabs (description, reviews, etc)
- Related products
- woocommerce_after_single_product hook''',
        }

    def get_css_sections(self) -> list[str]:
        """Get required CSS sections."""
        return [
            'CSS Variables (colors, spacing, typography)',
            'Reset and Base Styles',
            'Typography',
            'Layout and Grid',
            'Header and Navigation',
            'Hero Section',
            'Product Grid',
            'Product Cards',
            'Shopping Cart Widget',
            'WooCommerce Core Styles',
            'WooCommerce Product Pages',
            'WooCommerce Cart & Checkout',
            'Forms and Buttons',
            'Footer',
            'Responsive Media Queries',
            'Animations and Transitions',
        ]

    def get_layout_defaults(self) -> dict[str, Any]:
        """Get default layout configuration."""
        return {
            'container_width': '1200px',
            'content_width': '100%',
            'grid_columns': 4,
            'grid_gap': '30px',
            'mobile_columns': 2,
            'tablet_columns': 3,
            'sidebar_position': 'none',  # Full width for shop
            'header_layout': 'traditional',  # Logo, nav, cart
            'footer_columns': 4,
        }

    def get_color_scheme(self) -> dict[str, str]:
        """Get default color scheme for e-commerce."""
        return {
            'primary': '#2563eb',      # Trust-building blue
            'secondary': '#10b981',    # Success green
            'accent': '#f59e0b',       # Sale/CTA orange
            'background': '#ffffff',
            'surface': '#f9fafb',
            'text': '#1f2937',
            'text_light': '#6b7280',
            'border': '#e5e7eb',
            'error': '#ef4444',
            'success': '#10b981',
        }

    def get_woocommerce_support(self) -> dict[str, Any]:
        """Get WooCommerce-specific requirements."""
        return {
            'theme_support': [
                'woocommerce',
                'wc-product-gallery-zoom',
                'wc-product-gallery-lightbox',
                'wc-product-gallery-slider',
            ],
            'image_sizes': {
                'thumbnail': [150, 150],
                'catalog': [300, 300],
                'single': [600, 600],
            },
            'hooks': [
                'woocommerce_before_main_content',
                'woocommerce_after_main_content',
                'woocommerce_sidebar',
                'woocommerce_before_shop_loop',
                'woocommerce_after_shop_loop',
                'woocommerce_before_shop_loop_item',
                'woocommerce_after_shop_loop_item',
                'woocommerce_before_single_product',
                'woocommerce_after_single_product',
                'woocommerce_before_add_to_cart_form',
                'woocommerce_after_add_to_cart_form',
            ],
            'products_per_page': 12,
            'thumbnail_position': 'left',
            'gallery_thumbnail_columns': 4,
        }

    def get_ux_elements(self) -> list[str]:
        """Get required UX elements."""
        return [
            'Prominent "Shop Now" CTA in hero',
            'Shopping cart icon with live item count',
            'Product quick view modal',
            'Product image zoom and gallery',
            'Add to cart with loading state',
            'Product filtering (category, price, rating)',
            'Product sorting (price, popularity, rating)',
            'Product search with autocomplete',
            'Wishlist/favorites functionality',
            'Customer review display and submission',
            'Related products carousel',
            'Cross-sell and upsell sections',
            'Trust badges and security icons',
            'Free shipping threshold indicator',
            'Sale/discount badges',
            'Stock availability indicator',
            'Size/variation selector',
            'Product image thumbnails',
            'Breadcrumb navigation',
            'Category navigation menu',
            'Newsletter signup form',
            'Social proof (reviews, testimonials)',
            'Mobile-friendly cart drawer',
        ]

    def get_homepage_sections(self) -> list[dict[str, str]]:
        """Get homepage section structure."""
        return [
            {
                'name': 'hero',
                'description': 'Eye-catching hero with headline, subtitle, and Shop CTA',
                'required': True,
            },
            {
                'name': 'featured_products',
                'description': 'Showcase featured or best-selling products',
                'required': True,
            },
            {
                'name': 'categories',
                'description': 'Product category grid with images',
                'required': True,
            },
            {
                'name': 'promotional_banner',
                'description': 'Sale or promotional content area',
                'required': False,
            },
            {
                'name': 'testimonials',
                'description': 'Customer reviews and social proof',
                'required': True,
            },
            {
                'name': 'trust_badges',
                'description': 'Security, shipping, guarantee badges',
                'required': True,
            },
            {
                'name': 'newsletter',
                'description': 'Email signup form',
                'required': True,
            },
        ]

    def get_functions_php_requirements(self) -> list[str]:
        """Get functions.php requirements."""
        return [
            'Theme setup function with after_setup_theme hook',
            'WooCommerce theme support declarations',
            'Register navigation menus (primary, footer)',
            'Register widget areas (sidebar, footer columns)',
            'Enqueue styles (main, WooCommerce overrides)',
            'Enqueue scripts (main.js, cart functionality)',
            'Custom WooCommerce hooks and filters',
            'Adjust products per page',
            'Customize product gallery settings',
            'Add cart item count to header',
            'Custom breadcrumb function',
            'Product search customization',
            'Plugin compatibility layer',
            'Translation support setup',
        ]

    def get_javascript_features(self) -> list[str]:
        """Get JavaScript functionality requirements."""
        return [
            'Mobile menu toggle',
            'Cart drawer toggle',
            'Product quick view modal',
            'Product image gallery/lightbox',
            'Add to cart AJAX functionality',
            'Cart update without page reload',
            'Product filtering AJAX',
            'Newsletter form validation',
            'Sticky header on scroll',
            'Back to top button',
            'Product quantity increment/decrement',
            'Wishlist toggle',
            'Product image zoom',
            'Smooth scroll to sections',
            'Loading states and animations',
        ]

    def get_markup_structure(self) -> dict[str, str]:
        """Get semantic HTML structure requirements."""
        return {
            'header': '<header class="site-header"><div class="header-inner"><div class="site-branding">...</div><nav class="main-navigation">...</nav><div class="header-cart">...</div></div></header>',
            'hero': '<section class="hero"><div class="hero-content"><h1>...</h1><p>...</p><a class="cta-button">...</a></div><div class="hero-image">...</div></section>',
            'product_grid': '<div class="products-grid"><div class="product-card"><img /><h3>...</h3><span class="price">...</span><button class="add-to-cart">...</button></div></div>',
            'footer': '<footer class="site-footer"><div class="footer-widgets"><div class="footer-column">...</div></div><div class="footer-bottom"><p class="copyright">...</p></div></footer>',
        }

    def get_accessibility_requirements(self) -> list[str]:
        """Get accessibility requirements."""
        return [
            'ARIA labels for cart and navigation',
            'Keyboard navigation support',
            'Focus indicators on interactive elements',
            'Alt text for product images',
            'Proper heading hierarchy',
            'Color contrast compliance (WCAG AA)',
            'Skip to content link',
            'Screen reader text for icons',
            'Form labels and error messages',
            'Accessible modals and dropdowns',
        ]

    def get_full_requirements(self) -> dict[str, Any]:
        """Get all blueprint requirements in one dict."""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'required_templates': self.get_required_templates(),
            'optional_templates': self.get_optional_templates(),
            'template_structure': self.get_template_structure(),
            'css_sections': self.get_css_sections(),
            'layout_defaults': self.get_layout_defaults(),
            'color_scheme': self.get_color_scheme(),
            'woocommerce': self.get_woocommerce_support(),
            'ux_elements': self.get_ux_elements(),
            'homepage_sections': self.get_homepage_sections(),
            'functions_php': self.get_functions_php_requirements(),
            'javascript': self.get_javascript_features(),
            'markup': self.get_markup_structure(),
            'accessibility': self.get_accessibility_requirements(),
        }
