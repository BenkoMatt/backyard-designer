# Sprint 17 — Advanced Mode Polish Report (Agent 3)

## Summary

Polished the Advanced Mode of Backyard Designer 3D. Added a Basic/Advanced mode toggle (segmented control), descriptive subtitles on all dock tabs, expanded the command palette to include every feature, and added a comprehensive "What's New" feature guide to the help panel.

## Changes Made

### 1. Mode Toggle (Basic / Advanced Segmented Control)
- Added a segmented control to the topbar (between brand spacer and undo/redo group)
- Two buttons: "Advanced" (active by default) and "Basic"
- CSS uses the same pattern as the existing 3D/Bird's-eye view toggle
- Clicking Basic adds `body.basic-mode` class which hides advanced-only tabs and buttons via CSS
- Clicking Advanced removes the class, showing all features
- Mode preference is persisted to `localStorage` (`byd-mode`)
- Toast message shown on switch:
  - Advanced: "Advanced mode shows all tools. Switch to Basic for a simpler view."
  - Basic: "Basic mode: core tools only. Switch to Advanced for all features."

### 2. Dock Tab Subtitles / Tooltips
Added `.td-subtitle` elements to each dock tab with descriptive labels:
- **Terrain**: "Sun position & shadows" (already existed as Sun & Shadow)
- **Underground**: "View inside the ground"
- **Analyze**: "Slope, contours, drainage"
- **Pro Tools**: "Precision tools"
- **Sun & Shadow**: "Sun position & shadows"
- **Measure**: "Distance measurement"
- **Atmosphere**: "Sky, weather, seasons"

Also updated `title` attributes and `aria-label` attributes to include the subtitle text for tooltip and screen reader support.

### 3. Command Palette Expansion (Ctrl+K)
Expanded from 28 items to 43 items. Added new categories:
- **Planning**: Seasonal Planning, Plant Growth Timeline, Permit Checker, Design Templates, Add Text Label, Print/Export PDF
- **Export**: Export STL, Export OBJ, Export Heightmap PNG, HD Screenshot (4x)
- **Community**: Community Gallery, Time-Lapse Animation, Social Sharing Card
- **Interface**: Switch to Advanced Mode, Switch to Basic Mode

### 4. Help Panel — "What's New" Feature Guide
Added a "What's New — Feature Guide" section to the help modal with:
- Explanation of Basic vs Advanced modes
- **Basic Mode Features** list (11 items): Object Library, 3D View, Bird's-eye, Save/Load, Screenshot, Undo/Redo, Terrain Sculpting, Sun & Shadow, Cost Estimator, Layers, Grid & Scale Bar
- **Advanced Mode Features** list (18 items): Underground/Excavate, Terrain Analysis, Pro Terrain Tools, Atmosphere, Tape Measure, Walk Mode, Seasonal Planning, Plant Growth, Permit Checker, Design Templates, Text Labels, Export, Print/PDF, Community Gallery, Time-Lapse, Social Sharing Card, Share via Link/QR, Command Palette, Multi-Select & Batch, Right-Click Context Menu

### 5. Basic Mode Hiding Logic
When `body.basic-mode` is active, the following are hidden via CSS:
- **Dock tabs**: Underground, Analyze, Pro Tools, Atmosphere, Measure
- **Topbar buttons**: Export, Share, Gallery, Time-Lapse, Card, Season, Growth, Permits, Templates, Label, Print, Walk

In Basic mode, only these dock tabs remain: Terrain, Sun & Shadow
In Basic mode, these topbar buttons remain: Undo, Redo, 3D View, Bird's-eye, Save, Load, Capture, Help, Layers, Cost

## Test Results

### Playwright Test (test_advanced_mode.py)
All 30+ checks passed:
- Mode toggle exists with two buttons (Advanced, Basic) ✓
- Advanced is default ✓
- All 7 dock tabs visible in Advanced mode ✓
- All 5 tab subtitles present and correct ✓
- Basic mode adds `basic-mode` class ✓
- Basic mode hides 5 advanced tabs (only Terrain + Sun & Shadow visible) ✓
- Advanced-only topbar buttons hidden in Basic mode ✓
- Switching back to Advanced restores all tabs ✓
- Command palette opens with Ctrl+K ✓
- Command palette has 43 items across 9 categories ✓
- Keyboard shortcuts all work: V, B, G, R, T, W, 1, 2, [, ], X, Ctrl+Z, Ctrl+Y, Ctrl+A, Ctrl+D ✓
- Help panel has "What's New", "Basic Mode Features", "Advanced Mode Features" ✓
- Zero console errors ✓

### Sprint 16 Quality Gate
31/32 passed (1 failure: FPS=24 in headless mode — pre-existing, not caused by changes)

## Files Modified
- `index.html` — CSS, HTML, and JS changes
- `test_advanced_mode.py` — New Playwright test file