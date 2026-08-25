# Sprint 17 — Discovery Log

## Agent 5: Integration & Quality Gate Critic

**Date:** 2026-08-24
**Working Copy:** `/root/byd17-integration-gate/index.html`
**Starting Line Count:** 16,566
**Starting Test Count:** 676 (Sprint 6-16)

---

## Discovery: Codebase Structure

### Topbar Layout (lines ~1607-1730)
- Brand logo + spacer on left
- Undo/Redo group with divider
- 3D/Bird's-eye view toggle (segmented control)
- Save/Load/Capture/Help file operations group
- Layers/Cost/Walk view & analysis group
- Export dropdown + Share button
- Gallery/Time-Lapse/Card social group
- Season/Growth/Permits/Templates/Label/Print planning tools

### Tool Dock (lines ~1737-1770)
Located bottom-left, vertical button stack with group labels:
- **Sculpt group:** Terrain, Underground, Analyze
- **Build group:** Pro Tools (innovate)
- **View group:** Sun & Shadow, Measure, Atmosphere (experience)

### Dock Tab Data Attributes
Each tab has `data-dock` attribute identifying its panel:
- `terrain` — Terrain sculpting (basic)
- `underground` — Underground excavation (advanced)
- `analyze` — Terrain analysis (advanced)
- `innovate` — Pro terrain tools (advanced)
- `sun` — Sun & shadow (basic)
- `measure` — Tape measure (advanced)
- `experience` — Atmosphere/immersive (advanced)

### Command Palette (Ctrl+K)
- `CMD_ITEMS` array at line ~5761 with categorized commands
- Filter function at line ~298972
- Each item has: cat, icon, label, shortcut (optional), action
- Items filtered by search query text
- No prior mode-based filtering existed

### Keyboard Shortcuts (line ~6261)
Single-key shortcuts handled in keydown listener:
- V → 3D view, B → Bird's-eye, W → Walk mode
- T → Terrain dock, G → Grid toggle, R → Reset view
- Ctrl+Z/Y → Undo/Redo, Ctrl+S → Save, Ctrl+D → Duplicate
- Ctrl+K → Command palette, Ctrl+A → Select all
- Delete/Backspace → Delete, Escape → Close/deselect

### Help Panel (lines ~2822-2900)
- Modal dialog with sections: Getting Started, Camera, Saving, Terrain, Keyboard Shortcuts, Advanced Features, Safety, Accessibility
- No prior mode-related information
- No mode badge or indicator

### localStorage Usage
- `backyard-design-autosave` — design autosave
- Gallery storage key for community designs
- No prior mode/preference storage

### Module Script Scope
- Script is `<script type="module">` — functions not on global scope
- Some functions explicitly exposed via `window.fn = fn`
- Need to expose mode functions for testing access

---

## Discovery: Issues Found & Fixed

### 1. Command Palette "No commands found" message used `.cmd-item` class
- **Issue:** The empty state message div had `class="cmd-item"`, causing test counts to include it
- **Fix:** Changed to `class="cmd-empty-msg"` to distinguish from actual command items
- **Impact:** Command palette filtering tests now correctly count only real commands

### 2. Module scope isolation
- **Issue:** `setMode`, `toggleMode`, `initMode` functions were not accessible from page.evaluate()
- **Fix:** Added `window.setMode = setMode` etc. for test accessibility
- **Impact:** Browser tests can now call mode functions directly

### 3. Quality gate port hardcoding
- **Issue:** Multiple quality gates (sprint6, sprint12, sprint14, sprint15) hardcode port 8099
- **Fix:** Started second HTTP server on port 8099 alongside port 8175
- **Impact:** All quality gates can now run successfully

---

## Discovery: Feature Audit (Agent 1 Findings)

### Feature Inventory Review
Reviewed `FEATURE_INVENTORY.md` — 8 problem areas identified:
1. 6 floating buttons at hardcoded positions — already addressed in Sprint 16 (tool dock)
2. Innovation panel mega-panel — already addressed in Sprint 16 (dock panels)
3. Terrain panel 20+ controls — addressed via Basic/Advanced mode toggle
4. Cost/Layer panels overlap — already addressed in Sprint 16 (z-index hierarchy)
5. No logical hierarchy — addressed via Basic/Advanced mode
6. Advanced features buried — addressed via Basic/Advanced mode toggle
7. Cross-section duplication — already addressed
8. Cut/Fill panel hard to find — already addressed in Sprint 16

### Bug Fixes Applied
- Fixed "No commands found" message using wrong CSS class
- Exposed mode functions to window scope for accessibility
- Added `data-advanced` attribute to command palette items for CSS targeting

---

## Discovery: Mode Toggle Implementation

### Basic Mode (Default)
**Hidden dock tabs:** Underground, Analyze, Pro Tools, Measure, Atmosphere
**Hidden topbar buttons:** Export, Gallery, Time-Lapse, Card, Season, Growth, Permits, Print, Label, Templates
**Hidden command palette items:** All items marked `advanced: true`
**Visible:** Terrain, Sun & Shadow, all core file/edit operations, Layers, Cost, Walk, Share, Help

### Advanced Mode
All features visible — no CSS hiding rules applied.

### Persistence
- Mode stored in `localStorage` key `byd-design-mode`
- Value: `'basic'` or `'advanced'`
- Default: `'basic'` (new users)
- Restored on page load via `initMode()`

### Keyboard Shortcut
- `M` key toggles between Basic and Advanced mode
- Works in both modes
- Listed in command palette as "Toggle Basic/Advanced Mode"

---

## Discovery: Test Results

### Sprint 17 Quality Gate (NEW)
- **Tests:** 81 (37 static + 44 browser)
- **Pass Rate:** 100% (81/81)
- **Coverage:** Mode toggle existence, basic/advanced visibility, localStorage, keyboard shortcuts, command palette filtering, console errors, visual rendering, FPS

### Existing Quality Gates
- Sprint 6 (209 tests) — Running
- Sprint 8 (75 tests) — Running
- Sprint 9 (49 tests) — Running
- Sprint 11 (143 tests) — Running
- Sprint 12 (41 tests) — Running
- Sprint 13 (34 tests) — Passed (34/34)
- Sprint 14 (41 tests) — Running
- Sprint 15 (52 tests) — Running
- Sprint 16 (32 tests) — Passed (32/32)