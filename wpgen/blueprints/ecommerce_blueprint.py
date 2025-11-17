"""
E-commerce Blueprint for WPGen.

Defines structure and requirements for e-commerce/WooCommerce themes.
This blueprint ensures robust WooCommerce support with product grids,
shop pages, and retail-optimized layouts that work even without products.
"""

from typing import Any


# Retail/ecommerce keywords that trigger this blueprint
RETAIL_KEYWORDS = {
    # General retail
    'shop', 'store', 'ecommerce', 'e-commerce', 'online store', 'retail',
    'marketplace', 'boutique', 'outlet',
    # Products
    'product', 'products', 'item', 'items', 'merchandise', 'goods',
    'catalog', 'catalogue', 'inventory',
    # Shopping actions
    'cart', 'checkout', 'buy', 'purchase', 'sell', 'selling',
    # Apparel/Fashion
    'shirt', 'shirts', 'tee', 'tees', 't-shirt', 't-shirts',
    'apparel', 'clothing', 'clothes', 'fashion', 'wear',
    'dress', 'dresses', 'pants', 'jeans', 'jacket', 'jackets',
    'hoodie', 'hoodies', 'sweater', 'sweaters',
    # Accessories
    'accessory', 'accessories', 'jewelry', 'jewellery', 'watch', 'watches',
    # Other retail categories
    'book', 'books', 'ebook', 'digital downloads',
    'electronics', 'gadget', 'gadgets', 'device', 'devices',
    'furniture', 'home decor', 'decoration',
    'cosmetics', 'beauty', 'makeup',
    'toy', 'toys', 'game', 'games',
    'supply', 'supplies', 'equipment',
}


def is_retail_theme(theme_description: str, features: list[str] = None) -> bool:
    """Detect if theme description indicates retail/ecommerce intent.

    Args:
        theme_description: The theme description or requirements text
        features: Optional list of requested features

    Returns:
        True if retail keywords detected, False otherwise
    """
    if not theme_description:
        return False

    # Convert to lowercase for case-insensitive matching
    description_lower = theme_description.lower()

    # Check description
    for keyword in RETAIL_KEYWORDS:
        if keyword in description_lower:
            return True

    # Check features if provided
    if features:
        features_str = ' '.join(str(f).lower() for f in features)
        for keyword in RETAIL_KEYWORDS:
            if keyword in features_str:
                return True

    return False


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

    def get_product_grid_requirements(self) -> dict[str, str]:
        """Get detailed product grid requirements for generation prompts.

        Returns comprehensive specifications for product grid layouts that work
        even when WooCommerce is not installed or no products exist yet.
        """
        return {
            'layout': '''RESPONSIVE PRODUCT GRID LAYOUT:
- Desktop: 4 columns (25% width each)
- Tablet: 3 columns (33.33% width each)
- Mobile: 2 columns (50% width each)
- Grid gap: 30px between items
- Equal height cards using flexbox or grid
- Smooth hover effects with transform and shadow''',

            'card_structure': '''PRODUCT CARD STRUCTURE:
<div class="product-card">
    <div class="product-image">
        <img src="..." alt="Product name" loading="lazy" />
        <span class="sale-badge">Sale</span>
    </div>
    <div class="product-info">
        <h3 class="product-title">Product Name</h3>
        <div class="product-rating">⭐⭐⭐⭐⭐</div>
        <div class="product-price">
            <span class="regular-price">$99.99</span>
            <span class="sale-price">$79.99</span>
        </div>
        <button class="add-to-cart-btn">Add to Cart</button>
    </div>
</div>''',

            'woocommerce_integration': '''WOOCOMMERCE INTEGRATION (with fallback):
1. Check if WooCommerce is active with is_woocommerce()
2. If active: Use WooCommerce product loop
3. If NOT active: Show placeholder product grid with demo cards
4. Always include product grid CSS (works for both cases)
5. Ensure template never shows blank/empty shop page''',

            'placeholder_products': '''PLACEHOLDER PRODUCT DATA (when WooCommerce not installed):
Display 8-12 demo product cards with:
- Placeholder images (via placeholder.com or solid colors)
- Sample product titles ("Premium T-Shirt", "Classic Jeans", etc.)
- Sample prices ($29.99 - $99.99)
- Sample ratings (4-5 stars)
- "Add to Cart" buttons (disabled or show "WooCommerce Required")
- Call-to-action: "Install WooCommerce to add real products"''',

            'styling': '''PRODUCT CARD STYLING:
- White background with subtle shadow
- Border radius: 8px
- Padding: 20px
- Image aspect ratio: 1:1 (square) or 4:5 (portrait)
- Hover effect: lift with translateY(-4px) and stronger shadow
- Transition: all 0.3s ease
- Price in bold, larger font
- Add to cart button: full width, primary color
- Sale badge: absolute positioned, top-right, bright color''',

            'css_grid_example': '''.products-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 30px;
    margin: 40px 0;
}

@media (max-width: 1024px) {
    .products-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 768px) {
    .products-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }
}

.product-card {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

.product-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

.product-image {
    position: relative;
    aspect-ratio: 1 / 1;
    overflow: hidden;
}

.product-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.product-info {
    padding: 20px;
}

.product-price {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--primary-color);
    margin: 10px 0;
}

.add-to-cart-btn {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 4px;
    background: var(--primary-color);
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

.add-to-cart-btn:hover {
    background: var(--primary-dark);
}''',
        }

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
            'product_grid': self.get_product_grid_requirements(),
        }
