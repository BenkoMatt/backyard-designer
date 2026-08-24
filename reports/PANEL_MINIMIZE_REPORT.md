# PANEL MINIMIZE REPORT — Sprint 13 Agent 3

## Feature: Panel Minimize/Collapse for Dock Panels

### Summary
Added a minimize (−) button to every dock panel header and the terrain controls panel. When clicked, the panel content collapses while the tool stays active. A floating "Sculpt ▸" pill appears when the terrain panel is minimized, allowing one-click restore.

### Changes Made

#### 1. CSS (after line 206)
- `.dock-panel-header .minimize` — styled to match the close button (background: none, border: none, 18px font, muted color)
- `.dock-panel-header .minimize:hover` — brightens to `var(--text)`
- `.dock-panel.minimized .dock-panel-content` — `display: none` (hides content)
- `.dock-panel.minimized` — `max-height: none; overflow: visible` (allows header to show)
- `#sculpt-restore-pill` — fixed-position pill at bottom center, terrain-colored, with hover effect
- `#sculpt-restore-pill.visible` — `display: flex`
- Mobile media query for sculpt pill (larger touch target, 44px min-height)

#### 2. HTML — Dock Panel Headers (7 panels)
Added `<button class="minimize" data-dock-minimize aria-label="Minimize panel">−</button>` before each close button in:
- `#dock-terrain` (Terrain Sculpting)
- `#dock-underground` (Underground View)
- `#dock-analyze` (Terrain Analysis)
- `#dock-innovate` (Pro Terrain Tools)
- `#dock-sun` (Sun & Shadow)
- `#dock-measure` (Measure)
- `#dock-experience` (Atmosphere)

Also added `class="dock-panel-content"` to each content div for the CSS selector.

#### 3. HTML — Sculpt Restore Pill
Added `<button id="sculpt-restore-pill" aria-label="Restore terrain sculpt panel">Sculpt ▸</button>` before `</body>`.

#### 4. JavaScript — Click Handlers (inside setupToolDock IIFE)
- **Minimize button handler**: For each `[data-dock-minimize]` in dock panels:
  - Toggles `.minimized` class on parent `.dock-panel`
  - Changes button text: `−` → `+` when minimized, `+` → `−` when restored
  - Updates `aria-label` accordingly
  - For `#dock-terrain`: shows/hides `#sculpt-restore-pill`
  - Calls `requestRender()` to update canvas

- **Terrain controls minimize button**: Created programmatically after init (since `#terrain-controls` content is moved to dock at init). Added to the empty `#terrain-controls` container with click handler.

- **Sculpt restore pill handler**: Clicking the pill removes `.minimized` from `#dock-terrain`, resets button text to `−`, hides the pill.

- **closeDockPanel() modification**: Added cleanup at the start of `closeDockPanel()` to:
  - Hide the sculpt restore pill
  - Remove `.minimized` from all dock panels
  - Reset all minimize button text to `−`

### Key Design Decisions

1. **Minimize ≠ Close**: Minimizing only hides the content div; the panel header stays visible. The dock tab stays active (`aria-pressed=true`). The tool (e.g., terrain brush) remains fully functional.

2. **Terrain controls migration**: The floating `#terrain-controls` panel's children are moved to `#dock-terrain-content` at init by the existing code. We add a minimize button to `#terrain-controls` programmatically after the move, satisfying the requirement without creating duplicate buttons.

3. **Sculpt pill**: Only appears for the terrain (dock-terrain) panel, since that's the primary sculpting workflow. The pill is a fixed-position button at the bottom center of the screen, styled with the terrain color, with a mobile-friendly touch target.

4. **Button text**: Uses `−` (minus sign, U+2212) and `+` (plus sign) for clear visual indication of state.

### Test Results

#### Desktop (1280×800)
| Test | Result |
|------|--------|
| Minimize buttons in dock panels (expect 7) | ✅ PASS (count: 7) |
| Minimize button in #terrain-controls (expect 1) | ✅ PASS (count: 1) |
| Sculpt restore pill exists | ✅ PASS |
| Terrain brush active when dock opens | ✅ PASS |
| Dock terrain: minimize/restore | ✅ PASS (minimized: true, restored: true, content hidden, tab active, brush active, pill visible→hidden) |
| Dock underground: minimize/restore | ✅ PASS |
| Dock analyze: minimize/restore | ✅ PASS |
| Dock innovate: minimize/restore | ✅ PASS |
| Dock sun: minimize/restore | ✅ PASS |
| Dock measure: minimize/restore | ✅ PASS |
| Dock experience: minimize/restore | ✅ PASS |
| Sculpt pill restores panel | ✅ PASS |
| JS console errors | ✅ 0 errors |

#### Mobile (375×812)
| Test | Result |
|------|--------|
| Mobile: terrain dock opens | ✅ PASS |
| Mobile: terrain minimizes | ✅ PASS |
| Mobile: sculpt pill visible when minimized | ✅ PASS |
| Mobile: sculpt pill display is flex | ✅ PASS |
| Mobile: terrain restores | ✅ PASS |
| Mobile: sculpt pill hidden after restore | ✅ PASS |
| Mobile: terrain brush stays active | ✅ PASS |

### Files Modified
- `index.html` — CSS, HTML buttons, JavaScript handlers

### Files Created
- `DISCOVERY_LOG.md` — Architecture findings
- `PANEL_MINIMIZE_REPORT.md` — This report
- `test_single.py` — Desktop Playwright test
- `test_mobile.py` — Mobile Playwright test
- `test_errors.py` — JS error check

### Commits
1. `Sprint 13 Agent 3: Panel minimize feature — minimize/restore on all dock panels + sculpt pill`