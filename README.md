# WezConfigurator

A web-based GUI for configuring [WezTerm](https://wezfurlong.org/wezterm/), the GPU-accelerated cross-platform terminal emulator. Generate valid `wezterm.lua` configuration files through an intuitive browser interface instead of editing Lua by hand.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
[![Follow on X](https://img.shields.io/badge/follow-%40boschzilla-black.svg?logo=x)](https://x.com/boschzilla)

---

## Features

- **10 Configuration Sections** covering every major area of WezTerm:
  - **Font** -- family, weight, size, line height, cell width, and fallback fonts
  - **Colors** -- 200+ built-in color schemes (Catppuccin, Dracula, Tokyo Night, Gruvbox, Nord, and many more)
  - **Window** -- decorations, opacity, blur, dimensions, padding, and close behavior
  - **Tab Bar** -- visibility, position, fancy mode, index display, and max width
  - **Cursor** -- style (block/underline/bar), blink rate, and thickness
  - **Scrollback** -- buffer size, scroll bar visibility, and scroll-on-input behavior
  - **Background** -- background image path support
  - **Key Bindings** -- leader key configuration and custom key binding editor with 30+ actions
  - **Shell** -- default program, working directory, exit behavior, and launch menu items
  - **Rendering** -- front end (OpenGL/WebGpu/Software), max FPS, and animation FPS

- **Live Lua Preview** -- see your generated `wezterm.lua` update in real time as you change settings
- **Syntax Highlighting** -- the preview panel highlights Lua keywords, strings, numbers, comments, and WezTerm API calls
- **Parse Existing Config** -- automatically loads and parses your existing `wezterm.lua` if one is found
- **Automatic Backup** -- creates a `.bak` backup of your existing config before overwriting
- **Reset to Defaults** -- one-click reset to sensible WezTerm defaults
- **Dark Theme UI** -- clean, modern interface that feels at home alongside your terminal

---

## Screenshots

```
+------------------+---------------------------+--------------------+
|  Font            |  Font Settings            |  Lua Preview       |
|  Colors          |                           |                    |
|  Window          |  Font Family: [JetBrains] |  local wezterm ... |
|  Tab Bar         |  Weight:      [Medium   ] |  local config  ... |
|  Cursor          |  Font Size:   [14       ] |                    |
|  Scrollback      |  Line Height: [1.1      ] |  config.font = ... |
|  Background      |                           |  config.font_s ... |
|  Key Bindings    |  Fallback Fonts           |  config.color_ ... |
|  Shell           |  [Noto Color Emoji    ] x |                    |
|  Rendering       |  + Add Fallback           |  return config     |
+------------------+---------------------------+--------------------+
```

---

## Installation

### Prerequisites

- Python 3.9 or later
- pip (Python package manager)
- WezTerm installed ([installation guide](https://wezfurlong.org/wezterm/installation.html))

### Setup

```bash
# Clone the repository
git clone https://github.com/jbharvey1/wezconfigurator.git
cd wezconfigurator

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Start the App

```bash
source .venv/bin/activate
python app.py
```

The app starts at **http://127.0.0.1:5126** and opens your default browser automatically.

### Workflow

1. **Browse sections** using the sidebar on the left
2. **Adjust settings** using the form controls -- dropdowns, text inputs, sliders, and toggles
3. **Watch the preview** panel on the right update in real time with valid Lua
4. **Save** when ready -- the config is written to `~/.config/wezterm/wezterm.lua`
5. WezTerm **auto-reloads** the config file, so changes take effect immediately

### Config File Locations

WezConfigurator reads from and writes to the standard WezTerm config paths:

| Priority | Path |
|----------|------|
| 1 | `$WEZTERM_CONFIG_FILE` (environment variable) |
| 2 | `$XDG_CONFIG_HOME/wezterm/wezterm.lua` |
| 3 | `~/.config/wezterm/wezterm.lua` |
| 4 | `~/.wezterm.lua` |

When saving, the config is written to `~/.config/wezterm/wezterm.lua` by default.

---

## API Endpoints

WezConfigurator exposes a simple REST API that the frontend consumes:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/config` | Load existing config or return defaults |
| `POST` | `/api/config` | Save config to `wezterm.lua` |
| `POST` | `/api/preview` | Generate Lua preview without saving |
| `GET` | `/api/options` | List available dropdown options (schemes, styles, etc.) |
| `GET` | `/api/config/raw` | Return raw Lua config file content |

### Example: Preview a Config

```bash
curl -X POST http://127.0.0.1:5126/api/preview \
  -H 'Content-Type: application/json' \
  -d '{
    "config": {
      "font": {"family": "Fira Code", "size": 16},
      "colors": {"scheme": "Dracula"}
    }
  }'
```

---

## Project Structure

```
wezconfigurator/
  app.py              # Flask server and API routes
  lua_generator.py    # Converts config dict to valid WezTerm Lua
  config_parser.py    # Parses existing wezterm.lua into Python dicts
  requirements.txt    # Python dependencies
  templates/
    index.html        # Main web UI
  static/
    style.css         # Dark theme styling
    app.js            # Frontend logic and live preview
```

### How It Works

1. **`config_parser.py`** uses regex-based extraction to read an existing `wezterm.lua` file and convert it into a structured Python dictionary. It also provides sensible defaults when no config exists.

2. **`lua_generator.py`** takes the config dictionary and generates syntactically valid Lua code using WezTerm's `config_builder()` pattern. It handles font specs, color schemes, key bindings with action arguments, window settings, and more.

3. **`app.py`** serves the Flask web app and exposes REST endpoints. It bridges the parser and generator, handling config loading, preview generation, and saving with automatic backups.

4. **`app.js`** manages the frontend state, reads form values into a config object, sends it to the preview endpoint, and renders syntax-highlighted Lua in the preview panel. Event delegation ensures live updates on every change.

---

## Supported Configuration Options

### Font
- Font family (any installed font)
- Weight: Thin, ExtraLight, Light, DemiLight, Book, Regular, Medium, DemiBold, Bold, ExtraBold, Black, ExtraBlack
- Font size, line height, cell width
- Unlimited fallback fonts

### Color Schemes (200+)
Includes schemes from iTerm2, base16, Gogh, and terminal.sexy:

`AdventureTime` `Batman` `Catppuccin Mocha` `Dracula` `Gruvbox Dark` `Gruvbox Light` `GitHub Dark` `Kanagawa` `Material` `Nord` `One Dark` `Rose Pine` `Solarized Dark` `Solarized Light` `Tokyo Night` `Tomorrow Night` and many more...

### Cursor Styles
`SteadyBlock` `BlinkingBlock` `SteadyUnderline` `BlinkingUnderline` `SteadyBar` `BlinkingBar`

### Window Decorations
`NONE` `TITLE` `RESIZE` `TITLE | RESIZE`

### Rendering Backends
`OpenGL` (default) `WebGpu` `Software`

### Key Binding Actions
`ToggleFullScreen` `SpawnWindow` `SpawnTab` `CloseCurrentTab` `CloseCurrentPane` `ActivateTab` `ActivateTabRelative` `SplitHorizontal` `SplitVertical` `ActivatePaneDirection` `AdjustPaneSize` `TogglePaneZoomState` `Copy` `Paste` `IncreaseFontSize` `DecreaseFontSize` `ScrollByLine` `ScrollByPage` `ShowDebugOverlay` `ActivateCommandPalette` and more...

---

## Example Generated Config

```lua
local wezterm = require 'wezterm'
local config = wezterm.config_builder()
local act = wezterm.action

-- Font
config.font = wezterm.font_with_fallback {
  { family = 'JetBrains Mono', weight = 'Medium' },
  'Noto Color Emoji',
}
config.font_size = 14.0
config.line_height = 1.1

-- Colors
config.color_scheme = 'Tokyo Night'

-- Window
config.window_decorations = 'RESIZE'
config.window_background_opacity = 0.95
config.macos_window_background_blur = 20
config.window_padding = {
  left = '1cell',
  right = '1cell',
  top = '0.5cell',
  bottom = '0.5cell',
}

-- Tab Bar
config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true
config.tab_bar_at_bottom = true
config.use_fancy_tab_bar = false

-- Cursor
config.default_cursor_style = 'SteadyBar'
config.cursor_blink_rate = 0

-- Scrollback
config.scrollback_lines = 10000

-- Leader Key
config.leader = { key = 'a', mods = 'CTRL', timeout_milliseconds = 1000 }

-- Key Bindings
config.keys = {
  { key = '|', mods = 'LEADER|SHIFT', action = act.SplitHorizontal { domain = 'CurrentPaneDomain' } },
  { key = '-', mods = 'LEADER', action = act.SplitVertical { domain = 'CurrentPaneDomain' } },
  { key = 'h', mods = 'LEADER', action = act.ActivatePaneDirection 'Left' },
  { key = 'l', mods = 'LEADER', action = act.ActivatePaneDirection 'Right' },
}

-- Rendering
config.front_end = 'WebGpu'
config.max_fps = 120

return config
```

---

## Contributing

Contributions are welcome! Some ideas for enhancements:

- **Custom color editor** -- full ANSI palette color pickers for defining custom themes
- **Gradient background builder** -- visual editor for gradient orientations and color stops
- **Key binding presets** -- one-click tmux-like or vim-like key binding profiles
- **Config import/export** -- share configs as JSON or import from community configs
- **Font preview** -- render sample text in the selected font
- **Mouse binding editor** -- configure mouse click and scroll actions
- **SSH/Unix domain editor** -- configure multiplexing domains
- **Config diffing** -- show what changed before saving

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [WezTerm](https://wezfurlong.org/wezterm/) by Wez Furlong
- Built with [Flask](https://flask.palletsprojects.com/)
- Color schemes sourced from iTerm2, base16, Gogh, and terminal.sexy
