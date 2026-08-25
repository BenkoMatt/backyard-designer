# Discovery Log — Sprint 17: Basic Mode

## Date: 2026-08-24
## Agent: Agent 2 (Basic Mode)
## Working Copy: /root/byd17-basic-mode/index.html (16,831 lines after edits)

---

## 1. File Structure Overview

The app is a single `index.html` file (~16,566 lines originally) containing:
- **CSS** (lines 1–1554): All styles in a single `<style>` block
- **HTML body** (lines 1581–16,835): Markup for topbar, sidebar, viewport, tool dock, dock panels, terrain controls, modals
- **JavaScript** (inline `<script>` blocks throughout): All app logic

### Key UI Elements Discovered

#### Topbar (`#topbar`, line 1607)
- Brand area: `div.topbar-brand`
- Undo/Redo group: `div.topbar-group[aria-label="Undo/Redo"]` (keep)
- View toggle: `div#view-toggle` (3D / Bird's-eye) (keep)
- File operations group: Save, Load, Screenshot, Help (keep)
- View and analysis group: Layers (#btn-layers), Cost (#btn-cost), Walk (#btn-walk) (hide)
- Export and share group: Export dropdown (.tb-export-wrap), Share (#btn-share) (hide)
- Community and sharing group: Gallery (#btn-gallery), Time-Lapse (#btn-timelapse), Card (#btn-socialcard) (hide)
- Planning tools group: Season, Growth, Permits, Templates, Label, Print (hide)

#### Tool Dock (`#tool-dock`, line 1737)
- "Sculpt" group label
- Terrain tab: `.td-tab[data-dock="terrain"]` (keep)
- Underground tab: `.td-tab[data-dock="underground"]` (hide)
- Analyze tab: `.td-tab[data-dock="analyze"]` (hide)
- "Build" group label (2nd `.td-group-label`)
- Pro Tools tab: `.td-tab[data-dock="innovate"]` (hide)
- "View" group label (3rd `.td-group-label`)
- Sun & Shadow tab: `.td-tab[data-dock="sun"]` (keep)
- Measure tab: `.td-tab[data-dock="measure"]` (hide)
- Atmosphere tab: `.td-tab[data-dock="experience"]` (hide)

#### Dock Panels (line 1770+)
- `#dock-terrain`, `#dock-underground`, `#dock-analyze`, `#dock-innovate`, `#dock-measure`, `#dock-experience`
- Each has a `dock-panel-header` and `dock-panel-body`

#### Terrain Controls (`#terrain-controls`, line 1969)
- Initially `display: none`, gets `.visible` class when terrain tab is clicked
- Content is moved to `#dock-terrain-content` at runtime (line 6613)
- **Terrain mode buttons** (line 1977-1985):
  - `.terrain-mode-btn[data-tmode="raise"]` (keep)
  - `.terrain-mode-btn[data-tmode="lower"]` (keep)
  - `.terrain-mode-btn[data-tmode="smooth"]` (keep)
  - `.terrain-mode-btn[data-tmode="erode"]` (hide)
  - `.terrain-mode-btn[data-tmode="flatten"]` (keep)
  - `.terrain-mode-btn[data-tmode="dig"]` (keep)
  - `.terrain-mode-btn[data-tmode="fill"]` (keep)
- **Terrain presets** (line 2114-2121): `.terrain-presets` with buttons: Flat, Gentle Slope, Hill, Valley, Terraced, Pool Slope (hide)
- **Terrain overlays** (line 2125-2130): Height Colors, Drainage, Flatten All Terrain, Smooth Terrain (hide)
- **Precision mode** (line 2008-2015): toggle + hint (hide)
- **Grid level section** (line 2020+): slider + hint (hide)
- **Carving section** (line 2049+): shape buttons, commit/clear buttons (hide)

#### Status Bar (`#status-bar`, line 1591)
- 4 items: Tool, Brush, Height, FPS (separated by `.sb-sep` dividers)
- In basic mode: show only first item (Tool)

#### Command Palette (`#cmd-palette-overlay`, line 875)
- CSS: `display: none` by default, `.visible` class shows it
- Opened via `openCommandPalette()` function (line 5801)
- Triggered by Ctrl+K (line 6274) or 'K' key (line 6274)
- Feature usage tracking also listens for Ctrl+K (line 16000)

#### Wizard Overlay (`#wizard`, line 2833)
- Full-screen overlay shown on first visit
- Contains "Skip — use default yard" button (#wizard-skip)
- **IMPORTANT**: The wizard div intercepts pointer events, making it impossible to click elements behind it with Playwright's normal click. Must use `force: true` or JS `element.click()` to bypass.

---

## 2. Implementation Decisions

### CSS-Driven Approach
Used `body.byd-basic-mode` and `body.byd-advanced-mode` classes to drive all show/hide via CSS. This is cleaner than JS DOM manipulation and avoids timing issues.

### Default Mode
Default to "basic" on first visit (when no localStorage entry exists). This ensures beginners see the simplified interface first.

### What Gets Hidden in Basic Mode

**Tool Dock Tabs:**
- Underground, Analyze, Pro Tools (innovate), Atmosphere (experience), Measure

**Dock Panels:**
- #dock-underground, #dock-analyze, #dock-innovate, #dock-measure, #dock-experience

**Terrain Panel:**
- Erode brush button
- Terrain presets (Flat, Hill, Valley, etc.)
- Terrain overlays (Height Colors, Drainage)
- Flatten All Terrain button
- Smooth Terrain button
- Precision mode toggle + hint
- Grid level section
- Carving section (shape buttons, commit/clear)

**Topbar Buttons:**
- Layers, Cost, Walk, Share
- Export dropdown
- Gallery, Time-Lapse, Social Card
- Season, Growth, Permits, Templates, Label, Print

**Topbar Groups (entire groups including dividers):**
- "View and analysis" group
- "Export and share" group
- "Community and sharing" group
- "Planning tools" group

**Other:**
- Status bar: only show first item (current tool)
- Command palette overlay: hidden
- Terrain height legend: hidden
- "Build" group label in tool dock (only Pro Tools was under it)

### What Stays Visible in Basic Mode
- Mode toggle (Basic/Advanced)
- Undo, Redo
- 3D/Bird's-eye view toggle
- Save, Load, Screenshot, Help
- Terrain tab + panel (with Raise, Lower, Smooth, Dig, Fill, Flatten brushes)
- Sun & Shadow tab + panel
- Object sidebar
- Properties panel
- Status bar (simplified to show only current tool)

### JS Safeguards
- `setMode()` validates mode parameter, defaults to 'basic' if invalid
- When switching to basic mode, if an advanced dock tab is currently active, auto-switches to terrain tab
- When switching to basic mode, closes any open advanced panels (cost, layers, share, season, growth, permit)
- Ctrl+K is blocked in basic mode via capture-phase event listener
- localStorage key: `byd-mode`, values: `'basic'` or `'advanced'`

---

## 3. Testing Approach

Used Playwright with headless Chromium. 22 tests covering:
1. Default to Basic mode on first visit
2. Mode toggle buttons exist
3. Advanced dock tabs hidden in Basic mode (underground, analyze, innovate, experience, measure)
4. Terrain & Sun tabs visible in Basic mode
5. Erode brush hidden in Basic mode
6. Required terrain brushes visible (raise, lower, smooth, dig, fill, flatten)
7. Advanced topbar buttons hidden (Layers, Cost, Walk, Share)
8. Essential topbar buttons visible (Undo, Redo, Save, Load, Screenshot, Help)
9. View toggle visible
10. Status bar simplified (only 1 item visible)
11. Command palette hidden
12. Switch to Advanced mode
13. All dock tabs visible in Advanced mode
14. Advanced buttons visible in Advanced mode
15. Erode brush visible in Advanced mode
16. localStorage persistence (advanced)
17. Mode persists on reload
18. Switch to Basic and verify localStorage (basic)
19. Ctrl+K blocked in basic mode
20. window.setMode function exists
21. No JS errors on page load
22. Mode toggle button click works

All 22 tests pass.

---

## 4. Issues Encountered

1. **Wizard overlay intercepts clicks**: The `#wizard` div intercepts pointer events in Playwright. Solved by using `page.evaluate()` with JS `element.click()` instead of Playwright's `page.click()`.

2. **Terrain panel initially hidden**: The `#terrain-controls` panel starts with `display: none` and only becomes visible when the Terrain tab is clicked. Tests that check brush visibility must click the terrain tab first.

3. **`.terrain-row:has(> label:only-child)` CSS selector**: Initially used `:has()` pseudo-class which could match too broadly. Changed to `.terrain-row > label:only-child` to only hide the label element (Presets, Overlays labels) rather than the entire row.

4. **Mode toggle click after terrain panel open**: Clicking the terrain tab when it's already active toggles the panel closed. Tests must check if the panel is already open before clicking.

---

## 5. Lines Changed

- **CSS added** (after line 1553): ~165 lines of basic mode CSS rules
- **HTML added** (after line 1772): 4 lines for mode toggle UI
- **JS added** (before line 16836): ~96 lines for setMode function and event handlers
- **Total new lines**: ~265 lines