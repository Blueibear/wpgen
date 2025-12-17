from wpgen.prompts.theme_prompts import get_theme_spec_prompt


def test_theme_prompt_includes_inspiration_and_trends_with_design_profile():
    prompt = get_theme_spec_prompt(
        "Create a bold ecommerce site",
        design_profile={"name": "streetwear_modern", "description": "Bold streetwear look"},
    )

    assert "DESIGN INSPIRATION" in prompt
    assert "MODERN DESIGN TRENDS" in prompt
    assert prompt.index("MODERN DESIGN TRENDS") < prompt.index("## Theme Specification")


def test_theme_prompt_includes_ecommerce_guidance_for_woocommerce():
    prompt = get_theme_spec_prompt(
        "Set up a modern shop",
        woocommerce_enabled=True,
    )

    assert "ECOMMERCE THEME BEST PRACTICES" in prompt
    assert "MODERN DESIGN TRENDS" in prompt
    assert prompt.index("ECOMMERCE THEME BEST PRACTICES") < prompt.index("## Theme Specification")
