# Sprint 17 — Agent 3 Discovery Log

## Initial State Discovery
- Working copy: /root/byd17-advanced-mode/index.html (16,566 lines)
- Git: main branch, 1 commit (baseline from Sprint 16)
- Three.js v0.160.0, single self-contained HTML file
- 676 tests passing (Sprint 16)

## Key Code Locations Found

### Topbar HTML (line ~1607)
- Brand div, spacer, then toolbar groups for Undo/Redo, View toggle, File ops, View/Analysis, Export/Share, Community, Planning
- Mode toggle inserted between spacer and Undo/Redo group

### Tool Dock HTML (line ~1737)
- 7 dock tabs: Terrain, Underground, Analyze, Pro Tools, Sun & Shadow, Measure, Atmosphere
- Group labels: "Sculpt", "Build", "View"
- Each tab is a `.td-tab` button with `.td-label` span

### CSS Variables (lines ~40-105)
- `--topbar-h: 52px`, `--radius-sm`, `--primary`, `--hover-bg`, etc.
- `.view-toggle` is the existing segmented control pattern (used as model for mode toggle)

### Command Palette (line ~5760)
- `CMD_ITEMS` array with `{cat, icon, label, shortcut?, action}` objects
- `openCommandPalette()` / `closeCommandPalette()` / `renderCommandPalette()` functions
- Originally 28 items across 5 categories: View, Edit, File, Tools, Help

### Keyboard Shortcuts (lines ~6261, ~16470)
- Main handler: `document.addEventListener('keydown', ...)` at line 6261
  - Ctrl+Z/Y/S/D/K/A, Delete, Escape, Tab, Arrows, V, B, W, T, G, R
- Terrain shortcuts: separate IIFE at line 16470
  - 1-6 (brush modes), [ ] (brush size), X (terrain toggle)

### Help Panel (line ~2822)
- `#help-modal` with `.help-panel` div
- Sections: Getting Started, Camera Controls, Saving & Sharing, Terrain & Measuring, Keyboard Shortcuts, Advanced Features, Safety Reminders, Accessibility Tips
- Close button: `#help-close-btn`

### Mode State
- No existing Basic/Advanced mode toggle
- `body.basic-mode` class did not exist before
- No localStorage mode preference

### Dock Panel System
- `window._dockClosePanel` and `window._dockActiveTab` exposed at line ~12664
- `activeDockTab` variable tracks current open tab
- `closeDockPanel()` function closes the active panel

## Changes Applied
1. CSS: Added `.mode-toggle`, `.td-subtitle`, `body.basic-mode` hiding rules (line ~180)
2. HTML: Mode toggle inserted in topbar (line ~1639)
3. HTML: Subtitles added to all 7 dock tabs (lines ~1771-1800)
4. JS: `setMode()` function, `initModeToggle()`, localStorage persistence (line ~6286)
5. JS: CMD_ITEMS expanded from 28 to 43 items (line ~5822)
6. HTML: "What's New" section added to help panel (line ~2935)

## Issues Found
- None blocking. All features work as expected.
- FPS test in Sprint 16 quality gate fails at 24 FPS in headless mode — pre-existing, not caused by changes.