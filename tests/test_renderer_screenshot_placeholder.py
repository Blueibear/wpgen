from pathlib import Path

from PIL import Image

from wpgen.schema import get_default_theme_spec
from wpgen.templates.renderer import ThemeRenderer


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def test_placeholder_screenshot_uses_theme_palette(tmp_path: Path) -> None:
    spec = get_default_theme_spec()
    spec.theme_name = "palette-preview"
    spec.colors.primary = "#103754"
    spec.colors.secondary = "#0f7f8c"
    spec.colors.accent = "#f97316"
    spec.colors.background = "#f3f4f6"
    spec.colors.surface = "#ffffff"

    renderer = ThemeRenderer(tmp_path)
    renderer.render(spec, images=None)

    screenshot = tmp_path / spec.theme_name / "screenshot.png"
    assert screenshot.exists()

    with Image.open(screenshot) as img:
        assert img.size == (1200, 900)
        pixels = img.convert("RGB")

        accent_rgb = _hex_to_rgb(spec.colors.accent)
        background_rgb = _hex_to_rgb(spec.colors.background)
        surface_rgb = _hex_to_rgb(spec.colors.surface)

        cta_width = 280
        cta_height = 64
        cta_x = (1200 - cta_width) // 2
        cta_y = 260

        assert pixels.getpixel((cta_x + 12, cta_y + cta_height // 2)) == accent_rgb
        assert pixels.getpixel((50, 850)) == background_rgb

        card_width = 320
        card_height = 200
        gap = 60
        start_x = (1200 - (3 * card_width + 2 * gap)) // 2
        card_center = (start_x + card_width // 2, 360 + 30 + card_height // 2)
        assert pixels.getpixel(card_center) == surface_rgb
