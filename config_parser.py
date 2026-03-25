"""Parses an existing WezTerm Lua config file into a Python dict.

This is a best-effort parser that handles the most common config patterns.
It uses regex-based extraction rather than a full Lua parser.
"""

import re
import os

CONFIG_PATHS = [
    os.path.expanduser("~/.config/wezterm/wezterm.lua"),
    os.path.expanduser("~/.wezterm.lua"),
]


def find_config_file():
    """Find the first existing WezTerm config file."""
    env_path = os.environ.get("WEZTERM_CONFIG_FILE")
    if env_path and os.path.isfile(env_path):
        return env_path
    for path in CONFIG_PATHS:
        if os.path.isfile(path):
            return path
    return None


def _extract_string(lua, pattern):
    """Extract a string value from a Lua assignment."""
    m = re.search(pattern, lua)
    if m:
        return m.group(1)
    return None


def _extract_number(lua, pattern):
    """Extract a numeric value from a Lua assignment."""
    m = re.search(pattern, lua)
    if m:
        try:
            val = m.group(1)
            return float(val) if "." in val else int(val)
        except ValueError:
            return None
    return None


def _extract_bool(lua, pattern):
    """Extract a boolean value from a Lua assignment."""
    m = re.search(pattern, lua)
    if m:
        return m.group(1) == "true"
    return None


def _extract_string_list(lua, var_name):
    """Extract a list of strings from a Lua table assignment."""
    pattern = rf"{var_name}\s*=\s*\{{([^}}]*)\}}"
    m = re.search(pattern, lua, re.DOTALL)
    if m:
        content = m.group(1)
        return re.findall(r"['\"]([^'\"]+)['\"]", content)
    return []


def parse_config(filepath=None):
    """Parse a WezTerm Lua config file into a Python dict.

    Returns a dict with the same structure expected by lua_generator.generate_config().
    """
    if filepath is None:
        filepath = find_config_file()
    if filepath is None or not os.path.isfile(filepath):
        return {}

    with open(filepath) as f:
        lua = f.read()

    config = {}

    # -- Font --
    font = {}
    # font family from wezterm.font or font_with_fallback
    m = re.search(
        r"config\.font\s*=\s*wezterm\.font\s*\{?\s*['\"]([^'\"]+)['\"]", lua
    )
    if not m:
        m = re.search(
            r"config\.font\s*=\s*wezterm\.font\s*\{[^}]*family\s*=\s*['\"]([^'\"]+)['\"]",
            lua,
        )
    if m:
        font["family"] = m.group(1)

    # weight
    m = re.search(r"weight\s*=\s*['\"]([^'\"]+)['\"]", lua)
    if m:
        font["weight"] = m.group(1)

    val = _extract_number(lua, r"config\.font_size\s*=\s*([\d.]+)")
    if val is not None:
        font["size"] = val
    val = _extract_number(lua, r"config\.line_height\s*=\s*([\d.]+)")
    if val is not None:
        font["line_height"] = val
    val = _extract_number(lua, r"config\.cell_width\s*=\s*([\d.]+)")
    if val is not None:
        font["cell_width"] = val

    # fallback fonts
    m = re.search(r"wezterm\.font_with_fallback\s*\{(.+?)\}\s*\n", lua, re.DOTALL)
    if m:
        fallback_block = m.group(1)
        fallbacks = re.findall(r"['\"]([^'\"]+)['\"]", fallback_block)
        if fallbacks and font.get("family"):
            fallbacks = [f for f in fallbacks if f != font["family"]]
        font["fallbacks"] = fallbacks

    if font:
        config["font"] = font

    # -- Colors --
    colors = {}
    scheme = _extract_string(lua, r"config\.color_scheme\s*=\s*['\"]([^'\"]+)['\"]")
    if scheme:
        colors["scheme"] = scheme

    if colors:
        config["colors"] = colors

    # -- Window --
    window = {}
    val = _extract_string(lua, r"config\.window_decorations\s*=\s*['\"]([^'\"]+)['\"]")
    if val:
        window["decorations"] = val
    val = _extract_number(lua, r"config\.window_background_opacity\s*=\s*([\d.]+)")
    if val is not None:
        window["opacity"] = val
    val = _extract_number(lua, r"config\.macos_window_background_blur\s*=\s*(\d+)")
    if val is not None:
        window["macos_blur"] = val
    val = _extract_number(lua, r"config\.initial_cols\s*=\s*(\d+)")
    if val is not None:
        window["initial_cols"] = val
    val = _extract_number(lua, r"config\.initial_rows\s*=\s*(\d+)")
    if val is not None:
        window["initial_rows"] = val
    val = _extract_string(
        lua, r"config\.window_close_confirmation\s*=\s*['\"]([^'\"]+)['\"]"
    )
    if val:
        window["close_confirmation"] = val
    val = _extract_bool(
        lua,
        r"config\.adjust_window_size_when_changing_font_size\s*=\s*(true|false)",
    )
    if val is not None:
        window["adjust_window_size_when_changing_font_size"] = val

    # padding
    m = re.search(r"config\.window_padding\s*=\s*\{(.+?)\}", lua, re.DOTALL)
    if m:
        pad_block = m.group(1)
        padding = {}
        for side in ["left", "right", "top", "bottom"]:
            pm = re.search(rf"{side}\s*=\s*['\"]([^'\"]+)['\"]", pad_block)
            if pm:
                padding[side] = pm.group(1)
        if padding:
            window["padding"] = padding

    if window:
        config["window"] = window

    # -- Tab Bar --
    tab_bar = {}
    for opt in [
        "enable_tab_bar",
        "hide_tab_bar_if_only_one_tab",
        "tab_bar_at_bottom",
        "use_fancy_tab_bar",
        "show_tab_index_in_tab_bar",
    ]:
        val = _extract_bool(lua, rf"config\.{opt}\s*=\s*(true|false)")
        if val is not None:
            tab_bar[opt] = val
    val = _extract_number(lua, r"config\.tab_max_width\s*=\s*(\d+)")
    if val is not None:
        tab_bar["tab_max_width"] = val
    if tab_bar:
        config["tab_bar"] = tab_bar

    # -- Cursor --
    cursor = {}
    val = _extract_string(
        lua, r"config\.default_cursor_style\s*=\s*['\"]([^'\"]+)['\"]"
    )
    if val:
        cursor["style"] = val
    val = _extract_number(lua, r"config\.cursor_blink_rate\s*=\s*(\d+)")
    if val is not None:
        cursor["blink_rate"] = val
    val = _extract_string(lua, r"config\.cursor_thickness\s*=\s*['\"]([^'\"]+)['\"]")
    if val:
        cursor["thickness"] = val
    if cursor:
        config["cursor"] = cursor

    # -- Scrollback --
    scrollback = {}
    val = _extract_number(lua, r"config\.scrollback_lines\s*=\s*(\d+)")
    if val is not None:
        scrollback["lines"] = val
    val = _extract_bool(lua, r"config\.enable_scroll_bar\s*=\s*(true|false)")
    if val is not None:
        scrollback["enable_scroll_bar"] = val
    if scrollback:
        config["scrollback"] = scrollback

    # -- Shell --
    shell = {}
    val = _extract_string(lua, r"config\.default_cwd\s*=\s*['\"]([^'\"]+)['\"]")
    if val:
        shell["default_cwd"] = val
    val = _extract_string(lua, r"config\.exit_behavior\s*=\s*['\"]([^'\"]+)['\"]")
    if val:
        shell["exit_behavior"] = val
    prog = _extract_string_list(lua, r"config\.default_prog")
    if prog:
        shell["default_prog"] = prog
    if shell:
        config["shell"] = shell

    # -- Rendering --
    rendering = {}
    val = _extract_string(lua, r"config\.front_end\s*=\s*['\"]([^'\"]+)['\"]")
    if val:
        rendering["front_end"] = val
    val = _extract_number(lua, r"config\.max_fps\s*=\s*(\d+)")
    if val is not None:
        rendering["max_fps"] = val
    val = _extract_number(lua, r"config\.animation_fps\s*=\s*(\d+)")
    if val is not None:
        rendering["animation_fps"] = val
    if rendering:
        config["rendering"] = rendering

    return config


def get_default_config():
    """Return a sensible default config dict."""
    return {
        "font": {
            "family": "JetBrains Mono",
            "weight": "Regular",
            "style": "Normal",
            "size": 14.0,
            "line_height": 1.0,
            "fallbacks": [],
        },
        "colors": {"scheme": "Catppuccin Mocha", "custom": {}},
        "window": {
            "decorations": "RESIZE",
            "opacity": 1.0,
            "macos_blur": 0,
            "initial_cols": 120,
            "initial_rows": 36,
            "padding": {
                "left": "1cell",
                "right": "1cell",
                "top": "0.5cell",
                "bottom": "0.5cell",
            },
            "close_confirmation": "AlwaysPrompt",
            "adjust_window_size_when_changing_font_size": False,
        },
        "tab_bar": {
            "enable_tab_bar": True,
            "hide_tab_bar_if_only_one_tab": False,
            "tab_bar_at_bottom": False,
            "use_fancy_tab_bar": True,
            "show_tab_index_in_tab_bar": True,
            "tab_max_width": 25,
        },
        "cursor": {
            "style": "SteadyBlock",
            "blink_rate": 500,
            "thickness": "2px",
        },
        "scrollback": {
            "lines": 3500,
            "enable_scroll_bar": False,
            "scroll_to_bottom_on_input": True,
        },
        "background": {},
        "keys": {"leader": {}, "bindings": []},
        "shell": {},
        "rendering": {
            "front_end": "OpenGL",
            "max_fps": 60,
            "animation_fps": 10,
        },
    }
