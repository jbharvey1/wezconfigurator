let config = {};
let options = {};
let currentSection = 'font';

async function init() {
  const [cfgResp, optResp] = await Promise.all([
    fetch('/api/config').then(r => r.json()),
    fetch('/api/options').then(r => r.json()),
  ]);
  config = cfgResp.config;
  options = optResp;

  if (cfgResp.source) {
    document.getElementById('source-label').textContent = `Loaded from: ${cfgResp.source}`;
  }

  populateOptions();
  loadConfigToUI();
  updatePreview();

  // Explicitly wire up all selects and inputs for immediate preview updates
  document.querySelectorAll('.main select').forEach(el => {
    el.addEventListener('change', () => updatePreview());
  });
  document.querySelectorAll('.main input').forEach(el => {
    el.addEventListener('input', () => onConfigChange());
  });

  // Sidebar navigation
  document.querySelectorAll('.sidebar button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sidebar button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
      const section = btn.dataset.section;
      document.getElementById(`section-${section}`).classList.add('active');
      currentSection = section;
    });
  });
}

function populateOptions() {
  fillSelect('color-scheme', options.color_schemes);
  fillSelect('cursor-style', options.cursor_styles);
  fillSelect('font-weight', options.font_weights);
  fillSelect('window-decorations', options.window_decorations);
  fillSelect('front-end', options.front_ends);
  fillSelect('key-action', options.key_actions);
}

function fillSelect(id, items) {
  const sel = document.getElementById(id);
  if (!sel) return;
  sel.innerHTML = '';
  items.forEach(item => {
    const opt = document.createElement('option');
    opt.value = item;
    opt.textContent = item;
    sel.appendChild(opt);
  });
}

function loadConfigToUI() {
  const f = config.font || {};
  setVal('font-family', f.family || '');
  setVal('font-weight', f.weight || 'Regular');
  setVal('font-size', f.size || 14);
  setVal('line-height', f.line_height || 1.0);
  setVal('cell-width', f.cell_width || 1.0);
  renderFallbacks(f.fallbacks || []);

  const c = config.colors || {};
  setVal('color-scheme', c.scheme || 'Catppuccin Mocha');

  const w = config.window || {};
  setVal('window-decorations', w.decorations || 'RESIZE');
  setVal('window-opacity', w.opacity != null ? w.opacity : 1.0);
  setVal('window-opacity-range', w.opacity != null ? w.opacity : 1.0);
  setVal('macos-blur', w.macos_blur || 0);
  setVal('initial-cols', w.initial_cols || 120);
  setVal('initial-rows', w.initial_rows || 36);
  const pad = w.padding || {};
  setVal('pad-left', pad.left || '1cell');
  setVal('pad-right', pad.right || '1cell');
  setVal('pad-top', pad.top || '0.5cell');
  setVal('pad-bottom', pad.bottom || '0.5cell');
  setVal('close-confirmation', w.close_confirmation || 'AlwaysPrompt');
  setChecked('adjust-font-window', w.adjust_window_size_when_changing_font_size || false);

  const tb = config.tab_bar || {};
  setChecked('enable-tab-bar', tb.enable_tab_bar !== false);
  setChecked('hide-single-tab', tb.hide_tab_bar_if_only_one_tab || false);
  setChecked('tab-bar-bottom', tb.tab_bar_at_bottom || false);
  setChecked('fancy-tab-bar', tb.use_fancy_tab_bar !== false);
  setChecked('show-tab-index', tb.show_tab_index_in_tab_bar !== false);
  setVal('tab-max-width', tb.tab_max_width || 25);

  const cur = config.cursor || {};
  setVal('cursor-style', cur.style || 'SteadyBlock');
  setVal('cursor-blink-rate', cur.blink_rate != null ? cur.blink_rate : 500);
  setVal('cursor-thickness', cur.thickness || '2px');

  const sb = config.scrollback || {};
  setVal('scrollback-lines', sb.lines != null ? sb.lines : 3500);
  setChecked('scroll-bar', sb.enable_scroll_bar || false);
  setChecked('scroll-to-bottom', sb.scroll_to_bottom_on_input !== false);

  const bg = config.background || {};
  setVal('bg-image', bg.image || '');

  const sh = config.shell || {};
  setVal('default-prog', (sh.default_prog || []).join(' '));
  setVal('default-cwd', sh.default_cwd || '');
  setVal('exit-behavior', sh.exit_behavior || 'Close');
  renderLaunchMenu(sh.launch_menu || []);

  const r = config.rendering || {};
  setVal('front-end', r.front_end || 'OpenGL');
  setVal('max-fps', r.max_fps || 60);
  setVal('animation-fps', r.animation_fps || 10);

  const keys = config.keys || {};
  const leader = keys.leader || {};
  setVal('leader-key', leader.key || '');
  setVal('leader-mods', leader.mods || '');
  setVal('leader-timeout', leader.timeout || 1000);
  renderKeyBindings(keys.bindings || []);
}

function readConfigFromUI() {
  config.font = {
    family: getVal('font-family'),
    weight: getVal('font-weight'),
    size: parseFloat(getVal('font-size')) || 14,
    line_height: parseFloat(getVal('line-height')) || 1.0,
    cell_width: parseFloat(getVal('cell-width')) || 1.0,
    fallbacks: readFallbacks(),
  };

  config.colors = {
    scheme: getVal('color-scheme'),
    custom: config.colors?.custom || {},
  };

  config.window = {
    decorations: getVal('window-decorations'),
    opacity: parseFloat(getVal('window-opacity')) || 1.0,
    macos_blur: parseInt(getVal('macos-blur')) || 0,
    initial_cols: parseInt(getVal('initial-cols')) || 120,
    initial_rows: parseInt(getVal('initial-rows')) || 36,
    padding: {
      left: getVal('pad-left'),
      right: getVal('pad-right'),
      top: getVal('pad-top'),
      bottom: getVal('pad-bottom'),
    },
    close_confirmation: getVal('close-confirmation'),
    adjust_window_size_when_changing_font_size: getChecked('adjust-font-window'),
  };

  config.tab_bar = {
    enable_tab_bar: getChecked('enable-tab-bar'),
    hide_tab_bar_if_only_one_tab: getChecked('hide-single-tab'),
    tab_bar_at_bottom: getChecked('tab-bar-bottom'),
    use_fancy_tab_bar: getChecked('fancy-tab-bar'),
    show_tab_index_in_tab_bar: getChecked('show-tab-index'),
    tab_max_width: parseInt(getVal('tab-max-width')) || 25,
  };

  config.cursor = {
    style: getVal('cursor-style'),
    blink_rate: parseInt(getVal('cursor-blink-rate')),
    thickness: getVal('cursor-thickness'),
  };

  config.scrollback = {
    lines: parseInt(getVal('scrollback-lines')) || 3500,
    enable_scroll_bar: getChecked('scroll-bar'),
    scroll_to_bottom_on_input: getChecked('scroll-to-bottom'),
  };

  const bgImage = getVal('bg-image');
  config.background = bgImage ? { image: bgImage } : {};

  const progStr = getVal('default-prog').trim();
  config.shell = {};
  if (progStr) config.shell.default_prog = progStr.split(/\s+/);
  const cwd = getVal('default-cwd');
  if (cwd) config.shell.default_cwd = cwd;
  const exitBehavior = getVal('exit-behavior');
  if (exitBehavior) config.shell.exit_behavior = exitBehavior;
  config.shell.launch_menu = readLaunchMenu();

  config.rendering = {
    front_end: getVal('front-end'),
    max_fps: parseInt(getVal('max-fps')) || 60,
    animation_fps: parseInt(getVal('animation-fps')) || 10,
  };

  const leaderKey = getVal('leader-key');
  config.keys = {
    leader: leaderKey ? {
      key: leaderKey,
      mods: getVal('leader-mods'),
      timeout: parseInt(getVal('leader-timeout')) || 1000,
    } : {},
    bindings: readKeyBindings(),
  };

  return config;
}

// Fallback fonts
function renderFallbacks(fallbacks) {
  const container = document.getElementById('fallback-list');
  container.innerHTML = '';
  fallbacks.forEach((fb, i) => {
    const name = typeof fb === 'string' ? fb : fb.family || '';
    const div = document.createElement('div');
    div.className = 'fallback-item';
    div.innerHTML = `
      <input type="text" value="${escHtml(name)}" class="fallback-font" data-index="${i}" onchange="onConfigChange()">
      <button class="btn btn-danger btn-sm" onclick="removeFallback(${i})">x</button>
    `;
    container.appendChild(div);
  });
}

function readFallbacks() {
  return Array.from(document.querySelectorAll('.fallback-font'))
    .map(el => el.value.trim())
    .filter(Boolean);
}

function addFallback() {
  const list = readFallbacks();
  list.push('');
  renderFallbacks(list);
}

function removeFallback(i) {
  const list = readFallbacks();
  list.splice(i, 1);
  renderFallbacks(list);
  onConfigChange();
}

// Launch menu
function renderLaunchMenu(items) {
  const container = document.getElementById('launch-menu-list');
  container.innerHTML = '';
  items.forEach((item, i) => {
    const div = document.createElement('div');
    div.className = 'list-item';
    div.innerHTML = `
      <input type="text" placeholder="Label" value="${escHtml(item.label || '')}" class="launch-label" data-index="${i}">
      <input type="text" placeholder="Command args (space-separated)" value="${escHtml((item.args || []).join(' '))}" class="launch-args" data-index="${i}">
      <button class="btn btn-danger btn-sm" onclick="removeLaunchItem(${i})">x</button>
    `;
    container.appendChild(div);
  });
}

function readLaunchMenu() {
  const labels = document.querySelectorAll('.launch-label');
  const argInputs = document.querySelectorAll('.launch-args');
  const items = [];
  labels.forEach((el, i) => {
    const label = el.value.trim();
    const args = argInputs[i].value.trim();
    if (label || args) {
      items.push({
        label: label,
        args: args ? args.split(/\s+/) : [],
      });
    }
  });
  return items;
}

function addLaunchItem() {
  const items = readLaunchMenu();
  items.push({ label: '', args: [] });
  renderLaunchMenu(items);
}

function removeLaunchItem(i) {
  const items = readLaunchMenu();
  items.splice(i, 1);
  renderLaunchMenu(items);
  onConfigChange();
}

// Key bindings
function renderKeyBindings(bindings) {
  const tbody = document.getElementById('keybindings-body');
  tbody.innerHTML = '';
  bindings.forEach((b, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="text" value="${escHtml(b.key || '')}" class="kb-key" data-index="${i}" onchange="onConfigChange()"></td>
      <td><input type="text" value="${escHtml(b.mods || '')}" class="kb-mods" data-index="${i}" placeholder="e.g. CMD|SHIFT" onchange="onConfigChange()"></td>
      <td>
        <select class="kb-action" data-index="${i}" onchange="onConfigChange()">
          ${options.key_actions.map(a => `<option value="${a}" ${a === b.action ? 'selected' : ''}>${a}</option>`).join('')}
        </select>
      </td>
      <td><input type="text" value="${escHtml(b.action_args || '')}" class="kb-args" data-index="${i}" placeholder="optional" onchange="onConfigChange()"></td>
      <td><button class="btn btn-danger btn-sm" onclick="removeKeyBinding(${i})">x</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function readKeyBindings() {
  const keys = document.querySelectorAll('.kb-key');
  const mods = document.querySelectorAll('.kb-mods');
  const actions = document.querySelectorAll('.kb-action');
  const args = document.querySelectorAll('.kb-args');
  const bindings = [];
  keys.forEach((el, i) => {
    const key = el.value.trim();
    if (key) {
      bindings.push({
        key: key,
        mods: mods[i].value.trim(),
        action: actions[i].value,
        action_args: args[i].value.trim() || null,
      });
    }
  });
  return bindings;
}

function addKeyBinding() {
  const bindings = readKeyBindings();
  bindings.push({ key: '', mods: '', action: 'Nop', action_args: null });
  renderKeyBindings(bindings);
}

function removeKeyBinding(i) {
  const bindings = readKeyBindings();
  bindings.splice(i, 1);
  renderKeyBindings(bindings);
  onConfigChange();
}

// Preview
async function updatePreview() {
  try {
    readConfigFromUI();
    const resp = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config }),
    });
    const data = await resp.json();
    document.getElementById('lua-preview').innerHTML = highlightLua(data.lua);
  } catch (err) {
    console.error('Preview update failed:', err);
  }
}

function highlightLua(code) {
  return code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/(--[^\n]*)/g, '<span class="lua-comment">$1</span>')
    .replace(/('[^']*')/g, '<span class="lua-string">$1</span>')
    .replace(/\b(local|return|require|true|false|nil)\b/g, '<span class="lua-keyword">$1</span>')
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="lua-number">$1</span>')
    .replace(/\b(wezterm\.\w+|act\.\w+)/g, '<span class="lua-func">$1</span>')
    .replace(/(config\.\w+)/g, '<span class="lua-field">$1</span>');
}

// Save
async function saveConfig() {
  readConfigFromUI();
  const resp = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ config }),
  });
  const data = await resp.json();
  if (data.success) {
    showToast(`Saved to ${data.path}`, 'success');
    document.getElementById('source-label').textContent = `Loaded from: ${data.path}`;
  } else {
    showToast('Failed to save config', 'error');
  }
}

// Helpers
function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function getVal(id) {
  const el = document.getElementById(id);
  return el ? el.value : '';
}

function setChecked(id, val) {
  const el = document.getElementById(id);
  if (el) el.checked = val;
}

function getChecked(id) {
  const el = document.getElementById(id);
  return el ? el.checked : false;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

let previewTimeout;
function onConfigChange() {
  clearTimeout(previewTimeout);
  previewTimeout = setTimeout(updatePreview, 150);
}

function showToast(msg, type) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// Sync opacity slider and input
function syncOpacity(source) {
  if (source === 'range') {
    document.getElementById('window-opacity').value = document.getElementById('window-opacity-range').value;
  } else {
    document.getElementById('window-opacity-range').value = document.getElementById('window-opacity').value;
  }
  onConfigChange();
}

// Reset to defaults
async function resetDefaults() {
  const resp = await fetch('/api/config').then(r => r.json());
  // Use fresh defaults, not parsed config
  config = {
    font: { family: 'JetBrains Mono', weight: 'Regular', size: 14, line_height: 1.0, fallbacks: [] },
    colors: { scheme: 'Catppuccin Mocha', custom: {} },
    window: { decorations: 'RESIZE', opacity: 1.0, macos_blur: 0, initial_cols: 120, initial_rows: 36,
              padding: { left: '1cell', right: '1cell', top: '0.5cell', bottom: '0.5cell' },
              close_confirmation: 'AlwaysPrompt', adjust_window_size_when_changing_font_size: false },
    tab_bar: { enable_tab_bar: true, hide_tab_bar_if_only_one_tab: false, tab_bar_at_bottom: false,
               use_fancy_tab_bar: true, show_tab_index_in_tab_bar: true, tab_max_width: 25 },
    cursor: { style: 'SteadyBlock', blink_rate: 500, thickness: '2px' },
    scrollback: { lines: 3500, enable_scroll_bar: false, scroll_to_bottom_on_input: true },
    background: {},
    keys: { leader: {}, bindings: [] },
    shell: {},
    rendering: { front_end: 'OpenGL', max_fps: 60, animation_fps: 10 },
  };
  loadConfigToUI();
  updatePreview();
  showToast('Reset to defaults', 'success');
}

document.addEventListener('DOMContentLoaded', () => {
  init();

  // Global event delegation: update preview on any input/change in the main area
  const main = document.querySelector('.main');
  main.addEventListener('input', onConfigChange);
  main.addEventListener('change', onConfigChange);
});
