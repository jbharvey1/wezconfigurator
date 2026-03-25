"""Generates valid WezTerm Lua configuration from a Python dict."""


def lua_string(s):
    """Escape and quote a string for Lua."""
    escaped = s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    return f"'{escaped}'"


def lua_value(val, indent=0):
    """Convert a Python value to a Lua literal."""
    prefix = "  " * indent
    if val is None:
        return "nil"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        return lua_string(val)
    if isinstance(val, list):
        if not val:
            return "{}"
        items = []
        for v in val:
            items.append(f"{prefix}  {lua_value(v, indent + 1)},")
        return "{\n" + "\n".join(items) + f"\n{prefix}}}"
    if isinstance(val, dict):
        if not val:
            return "{}"
        items = []
        for k, v in val.items():
            lv = lua_value(v, indent + 1)
            if k.isidentifier() and not k.startswith("_"):
                items.append(f"{prefix}  {k} = {lv},")
            else:
                items.append(f"{prefix}  [{lua_string(k)}] = {lv},")
        return "{\n" + "\n".join(items) + f"\n{prefix}}}"
    return str(val)


class LuaRaw:
    """Represents a raw Lua expression that should not be quoted."""

    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return self.expr


def generate_config(config):
    """Generate a complete wezterm.lua from a config dict.

    Args:
        config: dict with keys matching WezTerm config sections:
            font, colors, window, tab_bar, cursor, scrollback,
            background, keys, shell, rendering
    Returns:
        str: valid Lua config file content
    """
    lines = [
        "local wezterm = require 'wezterm'",
        "local config = wezterm.config_builder()",
        "local act = wezterm.action",
        "",
    ]

    font_cfg = config.get("font", {})
    colors_cfg = config.get("colors", {})
    window_cfg = config.get("window", {})
    tab_bar_cfg = config.get("tab_bar", {})
    cursor_cfg = config.get("cursor", {})
    scrollback_cfg = config.get("scrollback", {})
    background_cfg = config.get("background", {})
    keys_cfg = config.get("keys", {})
    shell_cfg = config.get("shell", {})
    rendering_cfg = config.get("rendering", {})

    # -- Font --
    if font_cfg:
        lines.append("-- Font")
        family = font_cfg.get("family", "")
        fallbacks = font_cfg.get("fallbacks", [])
        weight = font_cfg.get("weight", "Regular")
        style = font_cfg.get("style", "Normal")
        harfbuzz = font_cfg.get("harfbuzz_features", [])

        font_spec = _build_font_spec(family, weight, style, harfbuzz)

        if fallbacks:
            fallback_entries = [font_spec]
            for fb in fallbacks:
                if isinstance(fb, str):
                    fallback_entries.append(f"  '{fb}',")
                elif isinstance(fb, dict):
                    fallback_entries.append(
                        _build_font_spec(
                            fb.get("family", ""),
                            fb.get("weight", "Regular"),
                            fb.get("style", "Normal"),
                            fb.get("harfbuzz_features", []),
                        )
                    )
            lines.append("config.font = wezterm.font_with_fallback {")
            for entry in fallback_entries:
                lines.append(f"  {entry}")
            lines.append("}")
        elif family:
            # Remove trailing comma for standalone font spec
            standalone = font_spec.rstrip(",").rstrip()
            lines.append(f"config.font = wezterm.font {standalone}")

        if font_cfg.get("size"):
            lines.append(f"config.font_size = {font_cfg['size']}")
        if font_cfg.get("line_height"):
            lines.append(f"config.line_height = {font_cfg['line_height']}")
        if font_cfg.get("cell_width"):
            lines.append(f"config.cell_width = {font_cfg['cell_width']}")
        lines.append("")

    # -- Color Scheme --
    if colors_cfg:
        lines.append("-- Colors")
        scheme = colors_cfg.get("scheme", "")
        if scheme:
            lines.append(f"config.color_scheme = {lua_string(scheme)}")

        custom = colors_cfg.get("custom", {})
        if custom:
            lines.append("config.colors = {")
            for key in [
                "foreground",
                "background",
                "cursor_bg",
                "cursor_fg",
                "cursor_border",
                "selection_fg",
                "selection_bg",
                "scrollbar_thumb",
                "split",
            ]:
                if custom.get(key):
                    lines.append(f"  {key} = {lua_string(custom[key])},")

            ansi = custom.get("ansi", [])
            if ansi and len(ansi) == 8:
                lines.append("  ansi = {")
                names = [
                    "black",
                    "red",
                    "green",
                    "yellow",
                    "blue",
                    "magenta",
                    "cyan",
                    "white",
                ]
                for i, color in enumerate(ansi):
                    lines.append(f"    {lua_string(color)},  -- {names[i]}")
                lines.append("  },")

            brights = custom.get("brights", [])
            if brights and len(brights) == 8:
                lines.append("  brights = {")
                names = [
                    "bright black",
                    "bright red",
                    "bright green",
                    "bright yellow",
                    "bright blue",
                    "bright magenta",
                    "bright cyan",
                    "bright white",
                ]
                for i, color in enumerate(brights):
                    lines.append(f"    {lua_string(color)},  -- {names[i]}")
                lines.append("  },")

            # Tab bar colors
            tab_colors = custom.get("tab_bar", {})
            if tab_colors:
                lines.append("  tab_bar = {")
                if tab_colors.get("background"):
                    lines.append(
                        f"    background = {lua_string(tab_colors['background'])},"
                    )
                for tab_type in [
                    "active_tab",
                    "inactive_tab",
                    "inactive_tab_hover",
                    "new_tab",
                    "new_tab_hover",
                ]:
                    t = tab_colors.get(tab_type, {})
                    if t:
                        lines.append(f"    {tab_type} = {{")
                        if t.get("bg_color"):
                            lines.append(
                                f"      bg_color = {lua_string(t['bg_color'])},"
                            )
                        if t.get("fg_color"):
                            lines.append(
                                f"      fg_color = {lua_string(t['fg_color'])},"
                            )
                        if t.get("intensity"):
                            lines.append(
                                f"      intensity = {lua_string(t['intensity'])},"
                            )
                        if t.get("italic") is not None:
                            lines.append(
                                f"      italic = {'true' if t['italic'] else 'false'},"
                            )
                        lines.append(f"    }},")
                lines.append("  },")

            lines.append("}")
        lines.append("")

    # -- Window --
    if window_cfg:
        lines.append("-- Window")
        if window_cfg.get("decorations"):
            lines.append(
                f"config.window_decorations = {lua_string(window_cfg['decorations'])}"
            )
        if window_cfg.get("opacity") is not None:
            lines.append(
                f"config.window_background_opacity = {window_cfg['opacity']}"
            )
        if window_cfg.get("macos_blur") is not None:
            lines.append(
                f"config.macos_window_background_blur = {window_cfg['macos_blur']}"
            )
        if window_cfg.get("initial_cols"):
            lines.append(f"config.initial_cols = {window_cfg['initial_cols']}")
        if window_cfg.get("initial_rows"):
            lines.append(f"config.initial_rows = {window_cfg['initial_rows']}")

        padding = window_cfg.get("padding", {})
        if padding:
            lines.append("config.window_padding = {")
            for side in ["left", "right", "top", "bottom"]:
                if padding.get(side):
                    lines.append(f"  {side} = {lua_string(padding[side])},")
            lines.append("}")

        if window_cfg.get("close_confirmation"):
            lines.append(
                f"config.window_close_confirmation = {lua_string(window_cfg['close_confirmation'])}"
            )
        if window_cfg.get("adjust_window_size_when_changing_font_size") is not None:
            val = (
                "true"
                if window_cfg["adjust_window_size_when_changing_font_size"]
                else "false"
            )
            lines.append(
                f"config.adjust_window_size_when_changing_font_size = {val}"
            )
        if window_cfg.get("native_macos_fullscreen_mode") is not None:
            val = (
                "true" if window_cfg["native_macos_fullscreen_mode"] else "false"
            )
            lines.append(f"config.native_macos_fullscreen_mode = {val}")

        inactive_pane = window_cfg.get("inactive_pane_hsb", {})
        if inactive_pane:
            lines.append("config.inactive_pane_hsb = {")
            for k in ["hue", "saturation", "brightness"]:
                if inactive_pane.get(k) is not None:
                    lines.append(f"  {k} = {inactive_pane[k]},")
            lines.append("}")
        lines.append("")

    # -- Tab Bar --
    if tab_bar_cfg:
        lines.append("-- Tab Bar")
        bool_opts = [
            "enable_tab_bar",
            "hide_tab_bar_if_only_one_tab",
            "tab_bar_at_bottom",
            "use_fancy_tab_bar",
            "show_tabs_in_tab_bar",
            "show_new_tab_button_in_tab_bar",
            "show_close_tab_button_in_tabs",
            "show_tab_index_in_tab_bar",
        ]
        for opt in bool_opts:
            if tab_bar_cfg.get(opt) is not None:
                val = "true" if tab_bar_cfg[opt] else "false"
                lines.append(f"config.{opt} = {val}")
        if tab_bar_cfg.get("tab_max_width"):
            lines.append(f"config.tab_max_width = {tab_bar_cfg['tab_max_width']}")

        frame = tab_bar_cfg.get("window_frame", {})
        if frame:
            lines.append("config.window_frame = {")
            if frame.get("font_family"):
                lines.append(
                    f"  font = wezterm.font {{ family = {lua_string(frame['font_family'])}, weight = {lua_string(frame.get('font_weight', 'Bold'))} }},"
                )
            if frame.get("font_size"):
                lines.append(f"  font_size = {frame['font_size']},")
            if frame.get("active_titlebar_bg"):
                lines.append(
                    f"  active_titlebar_bg = {lua_string(frame['active_titlebar_bg'])},"
                )
            if frame.get("inactive_titlebar_bg"):
                lines.append(
                    f"  inactive_titlebar_bg = {lua_string(frame['inactive_titlebar_bg'])},"
                )
            lines.append("}")
        lines.append("")

    # -- Cursor --
    if cursor_cfg:
        lines.append("-- Cursor")
        if cursor_cfg.get("style"):
            lines.append(
                f"config.default_cursor_style = {lua_string(cursor_cfg['style'])}"
            )
        if cursor_cfg.get("blink_rate") is not None:
            lines.append(f"config.cursor_blink_rate = {cursor_cfg['blink_rate']}")
        if cursor_cfg.get("thickness"):
            lines.append(
                f"config.cursor_thickness = {lua_string(cursor_cfg['thickness'])}"
            )
        if cursor_cfg.get("force_reverse_video") is not None:
            val = "true" if cursor_cfg["force_reverse_video"] else "false"
            lines.append(f"config.force_reverse_video_cursor = {val}")
        lines.append("")

    # -- Scrollback --
    if scrollback_cfg:
        lines.append("-- Scrollback")
        if scrollback_cfg.get("lines") is not None:
            lines.append(f"config.scrollback_lines = {scrollback_cfg['lines']}")
        if scrollback_cfg.get("enable_scroll_bar") is not None:
            val = "true" if scrollback_cfg["enable_scroll_bar"] else "false"
            lines.append(f"config.enable_scroll_bar = {val}")
        if scrollback_cfg.get("scroll_to_bottom_on_input") is not None:
            val = (
                "true" if scrollback_cfg["scroll_to_bottom_on_input"] else "false"
            )
            lines.append(f"config.scroll_to_bottom_on_input = {val}")
        lines.append("")

    # -- Background --
    if background_cfg:
        lines.append("-- Background")
        if background_cfg.get("image"):
            lines.append(
                f"config.window_background_image = {lua_string(background_cfg['image'])}"
            )
            hsb = background_cfg.get("image_hsb", {})
            if hsb:
                lines.append("config.window_background_image_hsb = {")
                for k in ["brightness", "hue", "saturation"]:
                    if hsb.get(k) is not None:
                        lines.append(f"  {k} = {hsb[k]},")
                lines.append("}")

        gradient = background_cfg.get("gradient", {})
        if gradient:
            lines.append("config.window_background_gradient = {")
            if gradient.get("orientation"):
                lines.append(
                    f"  orientation = {lua_string(gradient['orientation'])},"
                )
            colors = gradient.get("colors", [])
            if colors:
                lines.append("  colors = {")
                for c in colors:
                    lines.append(f"    {lua_string(c)},")
                lines.append("  },")
            if gradient.get("interpolation"):
                lines.append(
                    f"  interpolation = {lua_string(gradient['interpolation'])},"
                )
            if gradient.get("blend"):
                lines.append(f"  blend = {lua_string(gradient['blend'])},")
            if gradient.get("noise") is not None:
                lines.append(f"  noise = {gradient['noise']},")
            lines.append("}")
        lines.append("")

    # -- Keys --
    if keys_cfg:
        leader = keys_cfg.get("leader", {})
        bindings = keys_cfg.get("bindings", [])

        if leader:
            lines.append("-- Leader Key")
            parts = [f"key = {lua_string(leader['key'])}"]
            if leader.get("mods"):
                parts.append(f"mods = {lua_string(leader['mods'])}")
            parts.append(
                f"timeout_milliseconds = {leader.get('timeout', 1000)}"
            )
            lines.append("config.leader = { " + ", ".join(parts) + " }")
            lines.append("")

        if bindings:
            lines.append("-- Key Bindings")
            lines.append("config.keys = {")
            for b in bindings:
                action_str = _build_action(b.get("action", ""), b.get("action_args"))
                parts = [f"key = {lua_string(b['key'])}"]
                if b.get("mods"):
                    parts.append(f"mods = {lua_string(b['mods'])}")
                parts.append(f"action = {action_str}")
                lines.append("  { " + ", ".join(parts) + " },")
            lines.append("}")
            lines.append("")

    # -- Shell --
    if shell_cfg:
        lines.append("-- Shell / Launch")
        if shell_cfg.get("default_prog"):
            prog = shell_cfg["default_prog"]
            if isinstance(prog, str):
                prog = [prog]
            items = ", ".join(lua_string(p) for p in prog)
            lines.append(f"config.default_prog = {{ {items} }}")
        if shell_cfg.get("default_cwd"):
            lines.append(
                f"config.default_cwd = {lua_string(shell_cfg['default_cwd'])}"
            )
        if shell_cfg.get("exit_behavior"):
            lines.append(
                f"config.exit_behavior = {lua_string(shell_cfg['exit_behavior'])}"
            )

        env_vars = shell_cfg.get("environment", {})
        if env_vars:
            lines.append("config.set_environment_variables = {")
            for k, v in env_vars.items():
                lines.append(f"  {k} = {lua_string(v)},")
            lines.append("}")

        launch_menu = shell_cfg.get("launch_menu", [])
        if launch_menu:
            lines.append("config.launch_menu = {")
            for item in launch_menu:
                lines.append("  {")
                if item.get("label"):
                    lines.append(f"    label = {lua_string(item['label'])},")
                if item.get("args"):
                    args = ", ".join(lua_string(a) for a in item["args"])
                    lines.append(f"    args = {{ {args} }},")
                if item.get("cwd"):
                    lines.append(f"    cwd = {lua_string(item['cwd'])},")
                lines.append("  },")
            lines.append("}")
        lines.append("")

    # -- Rendering --
    if rendering_cfg:
        lines.append("-- Rendering")
        if rendering_cfg.get("front_end"):
            lines.append(
                f"config.front_end = {lua_string(rendering_cfg['front_end'])}"
            )
        if rendering_cfg.get("max_fps"):
            lines.append(f"config.max_fps = {rendering_cfg['max_fps']}")
        if rendering_cfg.get("animation_fps"):
            lines.append(f"config.animation_fps = {rendering_cfg['animation_fps']}")
        if rendering_cfg.get("webgpu_power_preference"):
            lines.append(
                f"config.webgpu_power_preference = {lua_string(rendering_cfg['webgpu_power_preference'])}"
            )
        if rendering_cfg.get("enable_wayland") is not None:
            val = "true" if rendering_cfg["enable_wayland"] else "false"
            lines.append(f"config.enable_wayland = {val}")
        if rendering_cfg.get("bold_brightens_ansi_colors"):
            lines.append(
                f"config.bold_brightens_ansi_colors = {lua_string(rendering_cfg['bold_brightens_ansi_colors'])}"
            )
        lines.append("")

    lines.append("return config")
    lines.append("")

    return "\n".join(lines)


def _build_font_spec(family, weight="Regular", style="Normal", harfbuzz=None):
    """Build a Lua font specification string."""
    if not family:
        return "''"
    parts = [f"family = {lua_string(family)}"]
    if weight and weight != "Regular":
        parts.append(f"weight = {lua_string(weight)}")
    if style and style != "Normal":
        parts.append(f"style = {lua_string(style)}")
    if harfbuzz:
        hb_items = ", ".join(lua_string(h) for h in harfbuzz)
        parts.append(f"harfbuzz_features = {{ {hb_items} }}")
    return "{ " + ", ".join(parts) + " },"


def _build_action(action_name, args=None):
    """Build a Lua action expression."""
    if not action_name:
        return "act.Nop"

    simple_actions = {
        "ToggleFullScreen",
        "SpawnWindow",
        "IncreaseFontSize",
        "DecreaseFontSize",
        "ResetFontSize",
        "ResetFontAndWindowSize",
        "TogglePaneZoomState",
        "ScrollToTop",
        "ScrollToBottom",
        "ReloadConfiguration",
        "ShowDebugOverlay",
        "ActivateCommandPalette",
        "ActivateCopyMode",
        "ActivateLastTab",
        "QuickSelect",
        "ShowTabNavigator",
        "Nop",
        "QuitApplication",
        "PaneSelect",
        "Copy",
        "Paste",
    }

    if action_name in simple_actions:
        return f"act.{action_name}"

    string_arg_actions = {
        "CopyTo",
        "PasteFrom",
        "ActivatePaneDirection",
        "SendString",
    }
    if action_name in string_arg_actions and args:
        return f"act.{action_name} {lua_string(args)}"

    int_arg_actions = {
        "ActivateTab",
        "ActivateTabRelative",
        "ActivateTabRelativeNoWrap",
        "MoveTab",
        "MoveTabRelative",
        "ScrollByLine",
        "ScrollByPage",
        "ScrollToPrompt",
        "ActivateWindow",
        "ActivateWindowRelative",
        "ActivatePaneByIndex",
        "SwitchWorkspaceRelative",
    }
    if action_name in int_arg_actions and args is not None:
        return f"act.{action_name}({args})"

    if action_name == "SplitHorizontal":
        domain = args if args else "CurrentPaneDomain"
        return f"act.SplitHorizontal {{ domain = {lua_string(domain)} }}"

    if action_name == "SplitVertical":
        domain = args if args else "CurrentPaneDomain"
        return f"act.SplitVertical {{ domain = {lua_string(domain)} }}"

    if action_name == "SpawnTab":
        domain = args if args else "CurrentPaneDomain"
        return f"act.SpawnTab {lua_string(domain)}"

    if action_name == "CloseCurrentTab":
        return "act.CloseCurrentTab { confirm = true }"

    if action_name == "CloseCurrentPane":
        return "act.CloseCurrentPane { confirm = true }"

    if action_name == "SendKey" and args:
        if isinstance(args, dict):
            parts = [f"key = {lua_string(args['key'])}"]
            if args.get("mods"):
                parts.append(f"mods = {lua_string(args['mods'])}")
            return "act.SendKey { " + ", ".join(parts) + " }"
        return f"act.SendKey {{ key = {lua_string(args)} }}"

    if action_name == "AdjustPaneSize" and args:
        if isinstance(args, dict):
            return f"act.AdjustPaneSize {{ {lua_string(args.get('direction', 'Right'))}, {args.get('amount', 1)} }}"
        return f"act.AdjustPaneSize {{ 'Right', 1 }}"

    if action_name == "RotatePanes":
        direction = args if args else "Clockwise"
        return f"act.RotatePanes {lua_string(direction)}"

    if action_name == "DisableDefaultAssignment":
        return "act.DisableDefaultAssignment"

    if action_name == "ShowLauncher":
        return "act.ShowLauncher"

    return f"act.{action_name}"
