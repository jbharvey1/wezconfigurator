"""Unit tests for config_parser and lua_generator."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_parser import get_default_config, parse_config
from lua_generator import generate_config, lua_string, lua_value


# ── lua_generator helpers ──


def test_lua_string_simple():
    assert lua_string("hello") == "'hello'"


def test_lua_string_escapes_quotes():
    assert lua_string("it's") == r"'it\'s'"


def test_lua_string_escapes_backslash():
    assert lua_string("a\\b") == r"'a\\b'"


def test_lua_value_none():
    assert lua_value(None) == "nil"


def test_lua_value_bool():
    assert lua_value(True) == "true"
    assert lua_value(False) == "false"


def test_lua_value_number():
    assert lua_value(42) == "42"
    assert lua_value(3.14) == "3.14"


def test_lua_value_string():
    assert lua_value("foo") == "'foo'"


def test_lua_value_empty_list():
    assert lua_value([]) == "{}"


def test_lua_value_empty_dict():
    assert lua_value({}) == "{}"


# ── generate_config ──


def test_generate_returns_valid_structure():
    config = get_default_config()
    lua = generate_config(config)
    assert lua.startswith("local wezterm = require 'wezterm'")
    assert "return config" in lua


def test_generate_font_family():
    lua = generate_config({"font": {"family": "Fira Code"}})
    assert "Fira Code" in lua
    assert "config.font" in lua


def test_generate_font_with_fallbacks():
    lua = generate_config(
        {"font": {"family": "JetBrains Mono", "fallbacks": ["Noto Sans", "Arial"]}}
    )
    assert "wezterm.font_with_fallback" in lua
    assert "Noto Sans" in lua
    assert "Arial" in lua


def test_generate_font_weight():
    lua = generate_config({"font": {"family": "Mono", "weight": "Bold"}})
    assert "weight = 'Bold'" in lua


def test_generate_font_size():
    lua = generate_config({"font": {"family": "Mono", "size": 16}})
    assert "config.font_size = 16" in lua


def test_generate_line_height():
    lua = generate_config({"font": {"family": "Mono", "line_height": 1.2}})
    assert "config.line_height = 1.2" in lua


def test_generate_color_scheme():
    lua = generate_config({"colors": {"scheme": "Dracula"}})
    assert "config.color_scheme = 'Dracula'" in lua


def test_generate_window_decorations():
    lua = generate_config({"window": {"decorations": "NONE"}})
    assert "config.window_decorations = 'NONE'" in lua


def test_generate_window_opacity():
    lua = generate_config({"window": {"opacity": 0.9}})
    assert "config.window_background_opacity = 0.9" in lua


def test_generate_window_padding():
    lua = generate_config(
        {"window": {"padding": {"left": "2cell", "right": "2cell", "top": "1cell", "bottom": "1cell"}}}
    )
    assert "config.window_padding" in lua
    assert "'2cell'" in lua


def test_generate_initial_size():
    lua = generate_config({"window": {"initial_cols": 200, "initial_rows": 50}})
    assert "config.initial_cols = 200" in lua
    assert "config.initial_rows = 50" in lua


def test_generate_close_confirmation():
    lua = generate_config({"window": {"close_confirmation": "NeverPrompt"}})
    assert "config.window_close_confirmation = 'NeverPrompt'" in lua


def test_generate_tab_bar_bools():
    lua = generate_config(
        {
            "tab_bar": {
                "enable_tab_bar": True,
                "hide_tab_bar_if_only_one_tab": True,
                "tab_bar_at_bottom": True,
                "use_fancy_tab_bar": False,
            }
        }
    )
    assert "config.enable_tab_bar = true" in lua
    assert "config.hide_tab_bar_if_only_one_tab = true" in lua
    assert "config.tab_bar_at_bottom = true" in lua
    assert "config.use_fancy_tab_bar = false" in lua


def test_generate_tab_max_width():
    lua = generate_config({"tab_bar": {"tab_max_width": 40}})
    assert "config.tab_max_width = 40" in lua


def test_generate_cursor_style():
    lua = generate_config({"cursor": {"style": "BlinkingBar"}})
    assert "config.default_cursor_style = 'BlinkingBar'" in lua


def test_generate_cursor_blink_rate():
    lua = generate_config({"cursor": {"blink_rate": 800}})
    assert "config.cursor_blink_rate = 800" in lua


def test_generate_scrollback():
    lua = generate_config({"scrollback": {"lines": 10000, "enable_scroll_bar": True}})
    assert "config.scrollback_lines = 10000" in lua
    assert "config.enable_scroll_bar = true" in lua


def test_generate_shell_default_prog():
    lua = generate_config({"shell": {"default_prog": ["/bin/zsh", "-l"]}})
    assert "config.default_prog" in lua
    assert "'/bin/zsh'" in lua
    assert "'-l'" in lua


def test_generate_shell_exit_behavior():
    lua = generate_config({"shell": {"exit_behavior": "Hold"}})
    assert "config.exit_behavior = 'Hold'" in lua


def test_generate_rendering():
    lua = generate_config({"rendering": {"front_end": "WebGpu", "max_fps": 120, "animation_fps": 30}})
    assert "config.front_end = 'WebGpu'" in lua
    assert "config.max_fps = 120" in lua
    assert "config.animation_fps = 30" in lua


def test_generate_leader_key():
    lua = generate_config({"keys": {"leader": {"key": "a", "mods": "CTRL", "timeout": 2000}}})
    assert "config.leader" in lua
    assert "key = 'a'" in lua
    assert "mods = 'CTRL'" in lua
    assert "timeout_milliseconds = 2000" in lua


def test_generate_key_bindings_simple_action():
    lua = generate_config(
        {"keys": {"bindings": [{"key": "f", "mods": "CTRL", "action": "ToggleFullScreen"}]}}
    )
    assert "config.keys" in lua
    assert "act.ToggleFullScreen" in lua


def test_generate_key_bindings_split():
    lua = generate_config(
        {"keys": {"bindings": [{"key": "d", "mods": "CMD", "action": "SplitHorizontal"}]}}
    )
    assert "act.SplitHorizontal" in lua
    assert "CurrentPaneDomain" in lua


def test_generate_background_image():
    lua = generate_config({"background": {"image": "/tmp/bg.jpg"}})
    assert "config.window_background_image" in lua
    assert "'/tmp/bg.jpg'" in lua


def test_generate_empty_config():
    lua = generate_config({})
    assert "local wezterm = require 'wezterm'" in lua
    assert "return config" in lua


def test_generate_full_defaults():
    """Full default config should produce valid Lua with all sections."""
    lua = generate_config(get_default_config())
    assert "-- Font" in lua
    assert "-- Colors" in lua
    assert "-- Window" in lua
    assert "-- Tab Bar" in lua
    assert "-- Cursor" in lua
    assert "-- Scrollback" in lua
    assert "-- Rendering" in lua
    assert "return config" in lua


# ── config_parser ──


def test_default_config_has_all_sections():
    defaults = get_default_config()
    for key in ["font", "colors", "window", "tab_bar", "cursor", "scrollback", "rendering"]:
        assert key in defaults, f"Missing section: {key}"


def test_parse_empty_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write("")
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result == {}


def test_parse_font_family():
    lua = "config.font = wezterm.font 'Fira Code'\nconfig.font_size = 16\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result["font"]["family"] == "Fira Code"
    assert result["font"]["size"] == 16


def test_parse_color_scheme():
    lua = "config.color_scheme = 'Tokyo Night'\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result["colors"]["scheme"] == "Tokyo Night"


def test_parse_window_settings():
    lua = """config.window_decorations = 'NONE'
config.window_background_opacity = 0.85
config.initial_cols = 160
config.initial_rows = 48
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result["window"]["decorations"] == "NONE"
    assert result["window"]["opacity"] == 0.85
    assert result["window"]["initial_cols"] == 160
    assert result["window"]["initial_rows"] == 48


def test_parse_tab_bar_bools():
    lua = """config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true
config.tab_bar_at_bottom = false
config.use_fancy_tab_bar = false
config.tab_max_width = 30
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result["tab_bar"]["enable_tab_bar"] is True
    assert result["tab_bar"]["hide_tab_bar_if_only_one_tab"] is True
    assert result["tab_bar"]["use_fancy_tab_bar"] is False
    assert result["tab_bar"]["tab_max_width"] == 30


def test_parse_cursor():
    lua = """config.default_cursor_style = 'BlinkingBar'
config.cursor_blink_rate = 750
config.cursor_thickness = '3px'
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result["cursor"]["style"] == "BlinkingBar"
    assert result["cursor"]["blink_rate"] == 750
    assert result["cursor"]["thickness"] == "3px"


def test_parse_scrollback():
    lua = "config.scrollback_lines = 10000\nconfig.enable_scroll_bar = true\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result["scrollback"]["lines"] == 10000
    assert result["scrollback"]["enable_scroll_bar"] is True


def test_parse_rendering():
    lua = "config.front_end = 'WebGpu'\nconfig.max_fps = 144\nconfig.animation_fps = 20\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result["rendering"]["front_end"] == "WebGpu"
    assert result["rendering"]["max_fps"] == 144
    assert result["rendering"]["animation_fps"] == 20


def test_parse_window_padding():
    lua = """config.window_padding = {
  left = '2cell',
  right = '2cell',
  top = '1cell',
  bottom = '1cell',
}
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        result = parse_config(f.name)
    os.unlink(f.name)
    assert result["window"]["padding"]["left"] == "2cell"
    assert result["window"]["padding"]["bottom"] == "1cell"


def test_roundtrip_defaults():
    """Generate Lua from defaults, parse it back, verify key fields survive."""
    defaults = get_default_config()
    lua = generate_config(defaults)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lua", delete=False) as f:
        f.write(lua)
        f.flush()
        parsed = parse_config(f.name)
    os.unlink(f.name)
    assert parsed["font"]["family"] == defaults["font"]["family"]
    assert parsed["colors"]["scheme"] == defaults["colors"]["scheme"]
    assert parsed["window"]["decorations"] == defaults["window"]["decorations"]
    assert parsed["cursor"]["style"] == defaults["cursor"]["style"]
    assert parsed["rendering"]["front_end"] == defaults["rendering"]["front_end"]


# ── Flask API ──


def test_api_health():
    from app import app
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200


def test_api_get_config():
    from app import app
    client = app.test_client()
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "config" in data
    assert "font" in data["config"]


def test_api_get_options():
    from app import app
    client = app.test_client()
    resp = client.get("/api/options")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "color_schemes" in data
    assert "cursor_styles" in data
    assert len(data["color_schemes"]) > 50


def test_api_preview():
    from app import app
    client = app.test_client()
    config = get_default_config()
    resp = client.post(
        "/api/preview",
        data=json.dumps({"config": config}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "lua" in data
    assert "return config" in data["lua"]


def test_api_preview_with_changes():
    from app import app
    client = app.test_client()
    config = get_default_config()
    config["font"]["family"] = "Hack"
    config["colors"]["scheme"] = "Dracula"
    resp = client.post(
        "/api/preview",
        data=json.dumps({"config": config}),
        content_type="application/json",
    )
    data = resp.get_json()
    assert "Hack" in data["lua"]
    assert "Dracula" in data["lua"]


def test_api_save_config():
    from app import app
    client = app.test_client()
    config = get_default_config()
    resp = client.post(
        "/api/config",
        data=json.dumps({"config": config}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "lua" in data


def test_api_get_color_schemes():
    from app import app
    client = app.test_client()
    resp = client.get("/api/color-schemes")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert len(data) > 100  # Should have 200+ schemes
    # Verify Catppuccin Mocha has expected structure
    assert "Catppuccin Mocha" in data
    scheme = data["Catppuccin Mocha"]
    assert "foreground" in scheme
    assert "background" in scheme
    assert "ansi" in scheme
    assert len(scheme["ansi"]) == 8
    assert "brights" in scheme
    assert len(scheme["brights"]) == 8
    # Verify hex color format
    assert scheme["foreground"].startswith("#")
    assert scheme["background"].startswith("#")


def test_api_color_schemes_dracula():
    from app import app
    client = app.test_client()
    resp = client.get("/api/color-schemes")
    data = resp.get_json()
    assert "Dracula" in data or "Dracula+" in data


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
