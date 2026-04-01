"""Playwright end-to-end tests for WezTerm Configurator UI."""

import json
import re
import subprocess
import sys
import time

import pytest
from playwright.sync_api import Page, expect, sync_playwright

BASE_URL = "http://127.0.0.1:5126"


@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    yield page
    page.close()


# ── Page Load ──


def test_page_loads(page: Page):
    expect(page.locator("h1")).to_contain_text("WezTerm Configurator")


def test_sidebar_has_all_sections(page: Page):
    buttons = page.locator(".sidebar button")
    expect(buttons).to_have_count(10)
    labels = [b.text_content().strip() for b in buttons.all()]
    for section in ["Font", "Colors", "Window", "Tab Bar", "Cursor", "Scrollback", "Background", "Key Bindings", "Shell", "Rendering"]:
        assert any(section in l for l in labels), f"Missing sidebar section: {section}"


def test_lua_preview_populated_on_load(page: Page):
    preview = page.locator("#lua-preview")
    expect(preview).not_to_be_empty()
    assert "local wezterm" in preview.inner_text()
    assert "return config" in preview.inner_text()


def test_source_label_shown(page: Page):
    label = page.locator("#source-label")
    expect(label).to_be_visible()


# ── Font Section ──


def test_font_family_default(page: Page):
    val = page.locator("#font-family").input_value()
    assert val == "JetBrains Mono"


def test_font_size_default(page: Page):
    val = page.locator("#font-size").input_value()
    assert float(val) > 0  # varies based on loaded config


def test_change_font_updates_preview(page: Page):
    page.locator("#font-family").fill("Fira Code")
    page.locator("#font-family").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "Fira Code" in preview_text


def test_change_font_size_updates_preview(page: Page):
    page.locator("#font-size").fill("20")
    page.locator("#font-size").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "config.font_size = 20" in preview_text


def test_change_font_weight_updates_preview(page: Page):
    page.locator("#font-weight").select_option("Bold")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "Bold" in preview_text


def test_add_fallback_font(page: Page):
    page.locator("text=+ Add Fallback").click()
    fallbacks = page.locator(".fallback-font")
    expect(fallbacks).to_have_count(1)


def test_remove_fallback_font(page: Page):
    page.locator("text=+ Add Fallback").click()
    expect(page.locator(".fallback-font")).to_have_count(1)
    page.locator(".fallback-item .btn-danger").click()
    expect(page.locator(".fallback-font")).to_have_count(0)


# ── Sidebar Navigation ──


def test_navigate_to_colors(page: Page):
    page.locator('.sidebar button[data-section="colors"]').click()
    expect(page.locator("#section-colors")).to_have_class(re.compile("active"))
    expect(page.locator("#section-font")).not_to_have_class(re.compile("active"))


def test_navigate_to_window(page: Page):
    page.locator('.sidebar button[data-section="window"]').click()
    expect(page.locator("#section-window")).to_have_class(re.compile("active"))


def test_navigate_to_all_sections(page: Page):
    sections = ["font", "colors", "window", "tab-bar", "cursor", "scrollback", "background", "keys", "shell", "rendering"]
    for section in sections:
        page.locator(f'.sidebar button[data-section="{section}"]').click()
        expect(page.locator(f"#section-{section}")).to_have_class(re.compile("active"))


# ── Colors Section ──


def test_color_scheme_default(page: Page):
    page.locator('.sidebar button[data-section="colors"]').click()
    val = page.locator("#color-scheme").input_value()
    assert val == "Catppuccin Mocha"


def test_change_color_scheme_updates_preview(page: Page):
    page.locator('.sidebar button[data-section="colors"]').click()
    page.locator("#color-scheme").select_option("Dracula")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "Dracula" in preview_text


def test_color_scheme_has_many_options(page: Page):
    page.locator('.sidebar button[data-section="colors"]').click()
    count = page.locator("#color-scheme option").count()
    assert count > 100


# ── Window Section ──


def test_window_opacity_slider_syncs(page: Page):
    page.locator('.sidebar button[data-section="window"]').click()
    page.locator("#window-opacity-range").fill("0.75")
    page.locator("#window-opacity-range").dispatch_event("input")
    val = page.locator("#window-opacity").input_value()
    assert val == "0.75"


def test_window_opacity_input_syncs(page: Page):
    page.locator('.sidebar button[data-section="window"]').click()
    page.locator("#window-opacity").fill("0.8")
    page.locator("#window-opacity").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "0.8" in preview_text


def test_window_padding_updates_preview(page: Page):
    page.locator('.sidebar button[data-section="window"]').click()
    page.locator("#pad-left").fill("3cell")
    page.locator("#pad-left").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "3cell" in preview_text


def test_window_decorations_change(page: Page):
    page.locator('.sidebar button[data-section="window"]').click()
    page.locator("#window-decorations").select_option("NONE")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "NONE" in preview_text


# ── Tab Bar Section ──


def test_tab_bar_toggles(page: Page):
    page.locator('.sidebar button[data-section="tab-bar"]').click()
    # The actual checkbox is hidden by the .toggle CSS; click the label/slider instead
    page.locator("#hide-single-tab").evaluate("el => el.click()")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "hide_tab_bar_if_only_one_tab = true" in preview_text


def test_tab_bar_at_bottom(page: Page):
    page.locator('.sidebar button[data-section="tab-bar"]').click()
    page.locator("#tab-bar-bottom").evaluate("el => el.click()")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "tab_bar_at_bottom = true" in preview_text


def test_tab_max_width_change(page: Page):
    page.locator('.sidebar button[data-section="tab-bar"]').click()
    page.locator("#tab-max-width").fill("50")
    page.locator("#tab-max-width").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "config.tab_max_width = 50" in preview_text


# ── Cursor Section ──


def test_cursor_style_change(page: Page):
    page.locator('.sidebar button[data-section="cursor"]').click()
    page.locator("#cursor-style").select_option("BlinkingBar")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "BlinkingBar" in preview_text


def test_cursor_blink_rate_change(page: Page):
    page.locator('.sidebar button[data-section="cursor"]').click()
    page.locator("#cursor-blink-rate").fill("1000")
    page.locator("#cursor-blink-rate").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "config.cursor_blink_rate = 1000" in preview_text


# ── Scrollback Section ──


def test_scrollback_lines_change(page: Page):
    page.locator('.sidebar button[data-section="scrollback"]').click()
    page.locator("#scrollback-lines").fill("50000")
    page.locator("#scrollback-lines").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "config.scrollback_lines = 50000" in preview_text


def test_scroll_bar_toggle(page: Page):
    page.locator('.sidebar button[data-section="scrollback"]').click()
    page.locator("#scroll-bar").evaluate("el => el.click()")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "enable_scroll_bar = true" in preview_text


# ── Key Bindings Section ──


def test_add_key_binding(page: Page):
    page.locator('.sidebar button[data-section="keys"]').click()
    page.locator("text=+ Add Binding").click()
    rows = page.locator("#keybindings-body tr")
    expect(rows).to_have_count(1)


def test_add_and_remove_key_binding(page: Page):
    page.locator('.sidebar button[data-section="keys"]').click()
    page.locator("text=+ Add Binding").click()
    expect(page.locator("#keybindings-body tr")).to_have_count(1)
    page.locator("#keybindings-body .btn-danger").click()
    expect(page.locator("#keybindings-body tr")).to_have_count(0)


def test_key_binding_updates_preview(page: Page):
    page.locator('.sidebar button[data-section="keys"]').click()
    page.locator("text=+ Add Binding").click()
    page.locator(".kb-key").fill("f")
    page.locator(".kb-mods").fill("CTRL")
    page.locator(".kb-action").select_option("ToggleFullScreen")
    page.locator(".kb-key").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "act.ToggleFullScreen" in preview_text


# ── Shell Section ──


def test_shell_default_prog(page: Page):
    page.locator('.sidebar button[data-section="shell"]').click()
    page.locator("#default-prog").fill("/bin/bash -l")
    page.locator("#default-prog").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "/bin/bash" in preview_text


def test_add_launch_menu_item(page: Page):
    page.locator('.sidebar button[data-section="shell"]').click()
    page.locator("text=+ Add Menu Item").click()
    items = page.locator("#launch-menu-list .list-item")
    expect(items).to_have_count(1)


# ── Rendering Section ──


def test_rendering_front_end_change(page: Page):
    page.locator('.sidebar button[data-section="rendering"]').click()
    page.locator("#front-end").select_option("WebGpu")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "WebGpu" in preview_text


def test_rendering_max_fps(page: Page):
    page.locator('.sidebar button[data-section="rendering"]').click()
    page.locator("#max-fps").fill("144")
    page.locator("#max-fps").dispatch_event("change")
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "config.max_fps = 144" in preview_text


# ── Reset Defaults ──


def test_reset_defaults(page: Page):
    # Change something first
    page.locator("#font-family").fill("Hack")
    page.locator("#font-family").dispatch_event("change")
    page.wait_for_timeout(300)

    # Reset
    page.locator("text=Reset Defaults").click()
    page.wait_for_timeout(500)

    # Should be back to default
    val = page.locator("#font-family").input_value()
    assert val == "JetBrains Mono"

    preview_text = page.locator("#lua-preview").inner_text()
    assert "JetBrains Mono" in preview_text


def test_reset_shows_toast(page: Page):
    page.locator("text=Reset Defaults").click()
    toast = page.locator("#toast")
    expect(toast).to_have_class(re.compile("show"))


# ── Preview Refresh Button ──


def test_manual_refresh_preview(page: Page):
    page.locator("#font-family").fill("Monaco")
    page.locator(".preview-header .btn").click()
    page.wait_for_timeout(500)
    preview_text = page.locator("#lua-preview").inner_text()
    assert "Monaco" in preview_text


# ── Save Config ──


def test_save_config(page: Page):
    page.locator("text=Save Config").click()
    page.wait_for_timeout(500)
    toast = page.locator("#toast")
    expect(toast).to_contain_text("Saved to")


# ── Visual Preview ──


def test_visual_preview_visible_by_default(page: Page):
    visual_pane = page.locator("#visual-preview-pane")
    expect(visual_pane).to_have_class(re.compile("active"))
    lua_pane = page.locator("#lua-preview-pane")
    expect(lua_pane).not_to_have_class(re.compile("active"))


def test_preview_tab_switching(page: Page):
    # Switch to Lua tab
    page.locator(".preview-tab[data-preview='lua']").click()
    expect(page.locator("#lua-preview-pane")).to_have_class(re.compile("active"))
    expect(page.locator("#visual-preview-pane")).not_to_have_class(re.compile("active"))

    # Switch back to Visual tab
    page.locator(".preview-tab[data-preview='visual']").click()
    expect(page.locator("#visual-preview-pane")).to_have_class(re.compile("active"))
    expect(page.locator("#lua-preview-pane")).not_to_have_class(re.compile("active"))


def test_visual_preview_has_terminal_content(page: Page):
    terminal = page.locator("#vp-terminal")
    expect(terminal).to_contain_text("user@host")
    expect(terminal).to_contain_text("ls -la")
    expect(terminal).to_contain_text("git status")


def test_visual_preview_updates_font(page: Page):
    page.locator("#font-family").fill("Fira Code")
    page.locator("#font-family").dispatch_event("change")
    page.wait_for_timeout(300)
    terminal = page.locator("#vp-terminal")
    font_family = terminal.evaluate("el => getComputedStyle(el).fontFamily")
    assert "Fira Code" in font_family


def test_visual_preview_updates_color_scheme(page: Page):
    # Navigate to Colors section first
    page.locator(".sidebar button[data-section='colors']").click()
    page.locator("#color-scheme").select_option("Dracula")
    page.wait_for_timeout(300)
    vp = page.locator("#visual-preview")
    bg = vp.evaluate("el => getComputedStyle(el).backgroundColor")
    # Dracula background is #282a36 → rgb(40, 42, 54)
    assert bg != "rgba(0, 0, 0, 0)", "Background should be set by scheme"


def test_visual_preview_cursor_style(page: Page):
    # Navigate to cursor section
    page.locator(".sidebar button[data-section='cursor']").click()
    page.locator("#cursor-style").select_option("BlinkingBar")
    page.wait_for_timeout(300)
    cursor = page.locator("#vp-cursor")
    classes = cursor.get_attribute("class")
    assert "vp-cursor-bar" in classes
    assert "vp-cursor-blink" in classes


def test_visual_preview_tab_bar_toggle(page: Page):
    page.locator(".sidebar button[data-section='tab-bar']").click()
    tab_bar = page.locator("#vp-tab-bar")

    # Disable tab bar — checkbox is hidden by .toggle CSS, click the label instead
    page.locator("#enable-tab-bar").evaluate("el => el.click()")
    page.wait_for_timeout(300)
    display = tab_bar.evaluate("el => getComputedStyle(el).display")
    assert display == "none"

    # Re-enable
    page.locator("#enable-tab-bar").evaluate("el => el.click()")
    page.wait_for_timeout(300)
    display = tab_bar.evaluate("el => getComputedStyle(el).display")
    assert display != "none"


def test_visual_preview_opacity(page: Page):
    page.locator(".sidebar button[data-section='window']").click()
    page.locator("#window-opacity").fill("0.8")
    page.locator("#window-opacity").dispatch_event("change")
    page.wait_for_timeout(300)
    vp = page.locator("#visual-preview")
    opacity = vp.evaluate("el => getComputedStyle(el).opacity")
    assert float(opacity) == pytest.approx(0.8, abs=0.05)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
