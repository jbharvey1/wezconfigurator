#!/usr/bin/env python3
"""WezTerm Configurator - A web-based GUI for configuring WezTerm."""

import json
import os
import webbrowser
from threading import Timer

from flask import Flask, jsonify, render_template, request

from config_parser import find_config_file, get_default_config, parse_config
from lua_generator import generate_config

app = Flask(__name__)

CONFIG_DIR = os.path.expanduser("~/.config/wezterm")
CONFIG_FILE = os.path.join(CONFIG_DIR, "wezterm.lua")

COLOR_SCHEMES = [
    "AdventureTime", "Afterglow", "Alabaster", "AlienBlood",
    "Alucard", "Argonaut", "Arthur", "AtelierSulphurpool",
    "Atom", "AtomOneLight", "ayu", "ayu_light",
    "Batman", "Belafonte Day", "Belafonte Night", "Blazer",
    "BlueBerryPie", "BlueDolphin", "BlulocoDark", "BlulocoLight",
    "Borland", "Breeze", "Broadcast", "Brogrammer",
    "BuiltinDark", "BuiltinLight", "BuiltinPassthrough", "BuiltinSolarizedDark",
    "BuiltinSolarizedLight", "BuiltinTangoDark", "BuiltinTangoLight",
    "C64", "Calamity", "catppuccin-frappe", "catppuccin-latte",
    "catppuccin-macchiato", "Catppuccin Mocha", "Chalk", "Chalkboard",
    "ChallengerDeep", "Chester", "Ciapre", "CLRS",
    "Cobalt2", "CobaltNeon", "Cobalt Neon", "ColdarkCold",
    "ColdarkDark", "cyberpunk", "DanQing", "Dark+",
    "darkermatrix", "DarkMoss", "DarkOcean", "DarkPastel",
    "Darkside", "deep", "Desert", "DimmedMonokai",
    "Django", "DjangoRebornAgain", "DjangoSmooth", "DoomOne",
    "DoomPeacock", "Dot Gov", "Dracula", "Dracula+",
    "DuotoneDark", "Earthsong", "Ef-Autumn", "Elemental",
    "Elementary", "ENCOM", "Espresso", "Espresso Libre",
    "Everblush", "Everforest Dark (Gogh)", "Everforest Light (Gogh)",
    "Fahrenheit", "Fairy Floss", "FarSide", "Firefly Traditional",
    "Firenze", "FishTank", "Flat", "Flatland",
    "FlexibleMinimal", "Floraverse", "ForestBlue", "Foxnightly",
    "FrontEndDelight", "Galaxy", "Github", "GitHub Dark",
    "Glacier", "Grape", "Grass", "Gruvbox Dark",
    "Gruvbox dark, hard (base16)", "Gruvbox dark, medium (base16)",
    "Gruvbox dark, pale (base16)", "Gruvbox dark, soft (base16)",
    "Gruvbox Light", "Guezwhoz", "Hacktober", "Hardcore",
    "Harper", "Hax0r_B", "Hax0r_GR", "Hax0r_R",
    "Highway", "Hipster Green", "Homebrew", "Hopscotch",
    "Horizon Dark (Gogh)", "Horizon Light (Gogh)", "HubsterPony",
    "Hurtado", "Hybrid", "IC_Green_PPL", "IC_Orange_PPL",
    "iceberg-dark", "iceberg-light", "idea", "Ifrit",
    "IR_Black", "Jackie Brown", "Japanesque", "Jellybeans",
    "JetBrains Darcula", "Joy", "Kanagawa (Gogh)",
    "Kanagawa Dragon (Gogh)", "Kibble", "Kolorit",
    "Konsolas", "Laser", "Later This Evening", "Lavandula",
    "LiquidCarbon", "LiquidCarbonTransparent", "lovelace", "Man Page",
    "Mariana", "Material", "MaterialDark", "MaterialDesignColors",
    "MaterialOcean", "Mathias", "Medallion", "midnight-in-mojave",
    "Mirage", "Miu", "Molokai", "MonaLisa",
    "Monokai (Gogh)", "Monokai Pro (Gogh)", "Monokai Remastered",
    "Monokai Soda", "Monokai Vivid", "N0tch2k", "Neon",
    "Neutron", "NightLion v1", "NightLion v2", "nightfox",
    "Night Owl", "Night Owlish Light", "nord", "Nord (Gogh)",
    "Novel", "Obsidian", "Ocean", "OceanicMaterial",
    "Ollie", "One Dark (Gogh)", "One Half Black (Gogh)",
    "OneHalfDark", "OneHalfLight", "One Light (Gogh)",
    "Operator Mono Dark", "Overnight Slumber", "Oxocarbon Dark (Gogh)",
    "PaleNightHC", "Pandora", "Paraiso Dark (Gogh)",
    "PaperColor Dark (base16)", "PaperColor Light (base16)",
    "Pencil Dark", "Pencil Light", "Peppermint",
    "Piatto Light", "Pnevma", "PoppingAndLocking",
    "primary", "Pro", "Pro Light", "purplepeter",
    "Rapture", "Raycast_Dark", "Raycast_Light",
    "Rebecca", "Red Alert", "Red Planet", "Red Sands",
    "Relaxed", "Retro", "Rippedcasts", "rose-pine",
    "rose-pine-dawn", "rose-pine-moon", "Royal",
    "Ryuuko", "Sakura", "Scarlet Protocol",
    "Seafoam Pastel", "SeaShells", "Seti", "shades-of-purple",
    "Slate", "SleepyHollow", "Smyck", "Snazzy",
    "SoftServer", "Solarized (dark) (terminal.sexy)",
    "Solarized (light) (terminal.sexy)", "Solarized Dark - Patched",
    "Solarized Dark Higher Contrast", "Solarized Darcula",
    "Solarized Dark (Gogh)", "Solarized Light (Gogh)",
    "SpaceGray", "SpaceGray Eighties", "SpaceGray Eighties Dull",
    "Spacemacs", "Spiderman", "Spring", "Square",
    "Sublette", "Subliminal", "Sundried", "Symfonic",
    "Synthwave (Gogh)", "Synthwave Alpha (Gogh)",
    "Tango (terminal.sexy)", "Tango Adapted", "Tango Half Adapted",
    "Terminal Basic", "Terminix Dark", "TerraformPlan",
    "Thayer Bright", "The Hulk", "Tinacious Design (Dark)",
    "Tinacious Design (Light)", "Tokyo Night", "Tokyo Night Moon",
    "Tokyo Night Storm", "Tokyo Night Day",
    "Tomorrow", "Tomorrow Night", "Tomorrow Night Blue",
    "Tomorrow Night Bright", "Tomorrow Night Burns",
    "Tomorrow Night Eighties", "tokyonight",
    "tokyonight_day", "tokyonight_moon", "tokyonight_storm",
    "Treehouse", "Twilight", "Ubuntu", "UltraDark",
    "UltraViolent", "UnderTheSea", "Unikitty",
    "Urple", "Vaughn", "VibrantInk", "vimbones",
    "Violet Dark", "Violet Light", "WarmNeon",
    "Wez", "Whimsy", "WildCherry", "wilmersdorf",
    "Wombat", "Wryan", "Zenburn", "zenbones",
    "zenbones_dark", "zenbones_light",
]

CURSOR_STYLES = [
    "SteadyBlock",
    "BlinkingBlock",
    "SteadyUnderline",
    "BlinkingUnderline",
    "SteadyBar",
    "BlinkingBar",
]

FONT_WEIGHTS = [
    "Thin",
    "ExtraLight",
    "Light",
    "DemiLight",
    "Book",
    "Regular",
    "Medium",
    "DemiBold",
    "Bold",
    "ExtraBold",
    "Black",
    "ExtraBlack",
]

WINDOW_DECORATIONS = [
    "NONE",
    "TITLE",
    "RESIZE",
    "TITLE | RESIZE",
]

FRONT_ENDS = ["OpenGL", "WebGpu", "Software"]

KEY_ACTIONS = [
    "ToggleFullScreen",
    "SpawnWindow",
    "SpawnTab",
    "CloseCurrentTab",
    "CloseCurrentPane",
    "ActivateTab",
    "ActivateTabRelative",
    "ActivateLastTab",
    "MoveTabRelative",
    "SplitHorizontal",
    "SplitVertical",
    "ActivatePaneDirection",
    "AdjustPaneSize",
    "TogglePaneZoomState",
    "RotatePanes",
    "PaneSelect",
    "Copy",
    "Paste",
    "CopyTo",
    "PasteFrom",
    "ActivateCopyMode",
    "QuickSelect",
    "IncreaseFontSize",
    "DecreaseFontSize",
    "ResetFontSize",
    "ScrollByLine",
    "ScrollByPage",
    "ScrollToTop",
    "ScrollToBottom",
    "ShowDebugOverlay",
    "ShowTabNavigator",
    "ShowLauncher",
    "ActivateCommandPalette",
    "ReloadConfiguration",
    "SendString",
    "Nop",
    "DisableDefaultAssignment",
    "QuitApplication",
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    """Load existing config or return defaults."""
    existing = find_config_file()
    if existing:
        parsed = parse_config(existing)
        defaults = get_default_config()
        merged = _deep_merge(defaults, parsed)
        return jsonify({"config": merged, "source": existing})
    return jsonify({"config": get_default_config(), "source": None})


@app.route("/api/config", methods=["POST"])
def save_config():
    """Save config to wezterm.lua."""
    data = request.get_json()
    config = data.get("config", {})

    lua_content = generate_config(config)

    os.makedirs(CONFIG_DIR, exist_ok=True)

    # Backup existing config
    if os.path.isfile(CONFIG_FILE):
        backup = CONFIG_FILE + ".bak"
        with open(CONFIG_FILE) as f:
            with open(backup, "w") as bf:
                bf.write(f.read())

    with open(CONFIG_FILE, "w") as f:
        f.write(lua_content)

    return jsonify({"success": True, "path": CONFIG_FILE, "lua": lua_content})


@app.route("/api/preview", methods=["POST"])
def preview_config():
    """Generate Lua preview without saving."""
    data = request.get_json()
    config = data.get("config", {})
    lua_content = generate_config(config)
    return jsonify({"lua": lua_content})


@app.route("/api/options", methods=["GET"])
def get_options():
    """Return available options for dropdowns."""
    return jsonify(
        {
            "color_schemes": COLOR_SCHEMES,
            "cursor_styles": CURSOR_STYLES,
            "font_weights": FONT_WEIGHTS,
            "window_decorations": WINDOW_DECORATIONS,
            "front_ends": FRONT_ENDS,
            "key_actions": KEY_ACTIONS,
        }
    )


@app.route("/api/color-schemes", methods=["GET"])
def get_color_schemes():
    """Return color scheme hex data for visual preview."""
    schemes_file = os.path.join(app.static_folder, "color_schemes.json")
    if os.path.isfile(schemes_file):
        with open(schemes_file) as f:
            return jsonify(json.load(f))
    return jsonify({})


@app.route("/api/config/raw", methods=["GET"])
def get_raw_config():
    """Return the raw Lua config file content."""
    existing = find_config_file()
    if existing and os.path.isfile(existing):
        with open(existing) as f:
            return jsonify({"content": f.read(), "path": existing})
    return jsonify({"content": None, "path": None})


def _deep_merge(base, override):
    """Deep merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def open_browser():
    webbrowser.open("https://127.0.0.1:5126")


if __name__ == "__main__":
    ssl_cert = "c:/ai/procman/certs/server.pem"
    ssl_key = "c:/ai/procman/certs/server-key.pem"
    Timer(1.0, open_browser).start()
    print("\n  WezTerm Configurator running at https://127.0.0.1:5126\n")
    app.run(host="127.0.0.1", port=5126, debug=False,
            ssl_context=(ssl_cert, ssl_key))
