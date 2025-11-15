"""
Design Profile System for WPGen
Defines modern design profiles with complete styling specifications
"""

from typing import Dict, Any


class DesignProfile:
    """Base class for design profiles"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.colors = {}
        self.fonts = {}
        self.spacing = {}
        self.layout = {}
        self.components = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for template injection"""
        return {
            'name': self.name,
            'description': self.description,
            'colors': self.colors,
            'fonts': self.fonts,
            'spacing': self.spacing,
            'layout': self.layout,
            'components': self.components,
        }


# Design Profile Definitions

MODERN_STREETWEAR = DesignProfile(
    name="modern_streetwear",
    description="Bold, edgy design with strong typography and urban aesthetics"
)
MODERN_STREETWEAR.colors = {
    'primary': '#000000',
    'secondary': '#FF6B00',
    'accent': '#00FF87',
    'background': '#FFFFFF',
    'surface': '#F5F5F5',
    'text': '#1A1A1A',
    'text_muted': '#666666',
    'border': '#E0E0E0',
    'hover': '#333333',
    'success': '#00FF87',
    'warning': '#FFD600',
    'error': '#FF1744',
}
MODERN_STREETWEAR.fonts = {
    'primary': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    'headings': "'Bebas Neue', 'Impact', sans-serif",
    'mono': "'JetBrains Mono', 'Courier New', monospace",
    'base_size': '16px',
    'scale': '1.25',  # Major third
}
MODERN_STREETWEAR.spacing = {
    'unit': '8px',
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '32px',
    'xl': '64px',
    'xxl': '128px',
    'container_max': '1200px',
    'content_max': '800px',
}
MODERN_STREETWEAR.layout = {
    'density': 'spacious',
    'header_height': '80px',
    'hero_height': '600px',
    'grid_columns': '3',
    'gap': '32px',
    'border_radius': '0px',  # Sharp edges
    'border_width': '2px',
}
MODERN_STREETWEAR.components = {
    'buttons': {
        'style': 'filled',
        'size': 'large',
        'uppercase': True,
        'weight': 'bold',
        'hover_effect': 'slide',
    },
    'cards': {
        'shadow': 'none',
        'border': True,
        'hover_lift': False,
    },
    'navigation': {
        'style': 'horizontal',
        'uppercase': True,
        'weight': 'bold',
    },
}


MINIMALIST = DesignProfile(
    name="minimalist",
    description="Clean, minimal design with subtle accents and plenty of whitespace"
)
MINIMALIST.colors = {
    'primary': '#2D3748',
    'secondary': '#718096',
    'accent': '#4299E1',
    'background': '#FFFFFF',
    'surface': '#F7FAFC',
    'text': '#2D3748',
    'text_muted': '#A0AEC0',
    'border': '#E2E8F0',
    'hover': '#4A5568',
    'success': '#48BB78',
    'warning': '#ED8936',
    'error': '#F56565',
}
MINIMALIST.fonts = {
    'primary': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    'headings': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    'mono': "'IBM Plex Mono', 'Courier New', monospace",
    'base_size': '16px',
    'scale': '1.2',  # Minor third
}
MINIMALIST.spacing = {
    'unit': '8px',
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '32px',
    'xl': '64px',
    'xxl': '96px',
    'container_max': '1140px',
    'content_max': '720px',
}
MINIMALIST.layout = {
    'density': 'airy',
    'header_height': '72px',
    'hero_height': '500px',
    'grid_columns': '3',
    'gap': '24px',
    'border_radius': '8px',
    'border_width': '1px',
}
MINIMALIST.components = {
    'buttons': {
        'style': 'outline',
        'size': 'medium',
        'uppercase': False,
        'weight': 'medium',
        'hover_effect': 'fade',
    },
    'cards': {
        'shadow': 'subtle',
        'border': False,
        'hover_lift': True,
    },
    'navigation': {
        'style': 'horizontal',
        'uppercase': False,
        'weight': 'medium',
    },
}


CORPORATE = DesignProfile(
    name="corporate",
    description="Professional, trustworthy design for business and enterprise"
)
CORPORATE.colors = {
    'primary': '#1E3A8A',
    'secondary': '#3B82F6',
    'accent': '#60A5FA',
    'background': '#FFFFFF',
    'surface': '#F8FAFC',
    'text': '#1E293B',
    'text_muted': '#64748B',
    'border': '#CBD5E1',
    'hover': '#1E40AF',
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
}
CORPORATE.fonts = {
    'primary': "'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    'headings': "'Montserrat', 'Helvetica Neue', sans-serif",
    'mono': "'Roboto Mono', 'Courier New', monospace",
    'base_size': '16px',
    'scale': '1.25',
}
CORPORATE.spacing = {
    'unit': '8px',
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '24px',
    'xl': '48px',
    'xxl': '72px',
    'container_max': '1280px',
    'content_max': '900px',
}
CORPORATE.layout = {
    'density': 'comfortable',
    'header_height': '88px',
    'hero_height': '480px',
    'grid_columns': '4',
    'gap': '24px',
    'border_radius': '4px',
    'border_width': '1px',
}
CORPORATE.components = {
    'buttons': {
        'style': 'filled',
        'size': 'medium',
        'uppercase': False,
        'weight': 'semibold',
        'hover_effect': 'darken',
    },
    'cards': {
        'shadow': 'medium',
        'border': True,
        'hover_lift': False,
    },
    'navigation': {
        'style': 'horizontal',
        'uppercase': False,
        'weight': 'semibold',
    },
}


VIBRANT_BOLD = DesignProfile(
    name="vibrant_bold",
    description="Energetic, colorful design with bold contrasts and dynamic elements"
)
VIBRANT_BOLD.colors = {
    'primary': '#8B5CF6',
    'secondary': '#EC4899',
    'accent': '#F59E0B',
    'background': '#FFFFFF',
    'surface': '#FAF5FF',
    'text': '#1F2937',
    'text_muted': '#6B7280',
    'border': '#E5E7EB',
    'hover': '#7C3AED',
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
}
VIBRANT_BOLD.fonts = {
    'primary': "'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    'headings': "'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    'mono': "'Fira Code', 'Courier New', monospace",
    'base_size': '16px',
    'scale': '1.333',  # Perfect fourth
}
VIBRANT_BOLD.spacing = {
    'unit': '8px',
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '32px',
    'xl': '64px',
    'xxl': '96px',
    'container_max': '1200px',
    'content_max': '800px',
}
VIBRANT_BOLD.layout = {
    'density': 'compact',
    'header_height': '76px',
    'hero_height': '550px',
    'grid_columns': '3',
    'gap': '28px',
    'border_radius': '12px',
    'border_width': '2px',
}
VIBRANT_BOLD.components = {
    'buttons': {
        'style': 'gradient',
        'size': 'large',
        'uppercase': False,
        'weight': 'bold',
        'hover_effect': 'scale',
    },
    'cards': {
        'shadow': 'bold',
        'border': False,
        'hover_lift': True,
    },
    'navigation': {
        'style': 'horizontal',
        'uppercase': False,
        'weight': 'bold',
    },
}


EARTHY_NATURAL = DesignProfile(
    name="earthy_natural",
    description="Warm, organic design inspired by nature with earthy tones"
)
EARTHY_NATURAL.colors = {
    'primary': '#78350F',
    'secondary': '#92400E',
    'accent': '#059669',
    'background': '#FFFBEB',
    'surface': '#FEF3C7',
    'text': '#292524',
    'text_muted': '#78716C',
    'border': '#D6D3D1',
    'hover': '#92400E',
    'success': '#059669',
    'warning': '#D97706',
    'error': '#DC2626',
}
EARTHY_NATURAL.fonts = {
    'primary': "'Lora', Georgia, serif",
    'headings': "'Merriweather', Georgia, serif",
    'mono': "'Source Code Pro', 'Courier New', monospace",
    'base_size': '17px',
    'scale': '1.2',
}
EARTHY_NATURAL.spacing = {
    'unit': '8px',
    'xs': '4px',
    'sm': '8px',
    'md': '16px',
    'lg': '32px',
    'xl': '56px',
    'xxl': '88px',
    'container_max': '1100px',
    'content_max': '750px',
}
EARTHY_NATURAL.layout = {
    'density': 'relaxed',
    'header_height': '80px',
    'hero_height': '520px',
    'grid_columns': '3',
    'gap': '32px',
    'border_radius': '16px',
    'border_width': '1px',
}
EARTHY_NATURAL.components = {
    'buttons': {
        'style': 'filled',
        'size': 'medium',
        'uppercase': False,
        'weight': 'medium',
        'hover_effect': 'fade',
    },
    'cards': {
        'shadow': 'soft',
        'border': True,
        'hover_lift': False,
    },
    'navigation': {
        'style': 'horizontal',
        'uppercase': False,
        'weight': 'medium',
    },
}


# Profile Registry
DESIGN_PROFILES = {
    'modern_streetwear': MODERN_STREETWEAR,
    'minimalist': MINIMALIST,
    'corporate': CORPORATE,
    'vibrant_bold': VIBRANT_BOLD,
    'earthy_natural': EARTHY_NATURAL,
}


def get_design_profile(profile_name: str = None) -> DesignProfile:
    """
    Get a design profile by name. Defaults to minimalist if not specified.

    Args:
        profile_name: Name of the design profile

    Returns:
        DesignProfile object
    """
    if profile_name and profile_name in DESIGN_PROFILES:
        return DESIGN_PROFILES[profile_name]
    return MINIMALIST  # Default profile


def get_profile_names() -> list:
    """Get list of available profile names"""
    return list(DESIGN_PROFILES.keys())


def profile_to_css_variables(profile: DesignProfile) -> str:
    """
    Convert design profile to CSS custom properties

    Args:
        profile: DesignProfile object

    Returns:
        CSS string with custom properties
    """
    css_vars = [':root {']

    # Colors
    for key, value in profile.colors.items():
        css_vars.append(f'  --color-{key.replace("_", "-")}: {value};')

    # Fonts
    css_vars.append(f'  --font-primary: {profile.fonts["primary"]};')
    css_vars.append(f'  --font-headings: {profile.fonts["headings"]};')
    css_vars.append(f'  --font-mono: {profile.fonts["mono"]};')
    css_vars.append(f'  --font-base-size: {profile.fonts["base_size"]};')

    # Spacing
    for key, value in profile.spacing.items():
        css_vars.append(f'  --spacing-{key.replace("_", "-")}: {value};')

    # Layout
    for key, value in profile.layout.items():
        css_vars.append(f'  --layout-{key.replace("_", "-")}: {value};')

    css_vars.append('}')
    return '\n'.join(css_vars)


def profile_to_prompt_context(profile: DesignProfile) -> str:
    """
    Convert design profile to natural language context for LLM prompts

    Args:
        profile: DesignProfile object

    Returns:
        String description for LLM context
    """
    context = f"""
Design Profile: {profile.name.replace('_', ' ').title()}
{profile.description}

Color Palette:
- Primary: {profile.colors['primary']} (main brand color)
- Secondary: {profile.colors['secondary']} (supporting color)
- Accent: {profile.colors['accent']} (highlights and CTAs)
- Background: {profile.colors['background']}
- Text: {profile.colors['text']} (main text color)
- Text Muted: {profile.colors['text_muted']} (secondary text)

Typography:
- Primary Font: {profile.fonts['primary']}
- Headings Font: {profile.fonts['headings']}
- Base Size: {profile.fonts['base_size']}
- Type Scale: {profile.fonts['scale']}

Spacing System:
- Base Unit: {profile.spacing['unit']}
- Container Max Width: {profile.spacing['container_max']}
- Content Max Width: {profile.spacing['content_max']}

Layout:
- Density: {profile.layout['density']}
- Header Height: {profile.layout['header_height']}
- Hero Height: {profile.layout['hero_height']}
- Grid Columns: {profile.layout['grid_columns']}
- Grid Gap: {profile.layout['gap']}
- Border Radius: {profile.layout['border_radius']}

Component Styles:
- Buttons: {profile.components['buttons']['style']}, {profile.components['buttons']['size']}, {profile.components['buttons']['hover_effect']} hover
- Cards: {'with shadow' if profile.components['cards']['shadow'] != 'none' else 'flat'}, {'with border' if profile.components['cards']['border'] else 'borderless'}
- Navigation: {profile.components['navigation']['style']}, {profile.components['navigation']['weight']} weight
"""
    return context.strip()
