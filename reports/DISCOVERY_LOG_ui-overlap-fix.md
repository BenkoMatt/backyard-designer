# DISCOVERY LOG — UI Overlap Audit (Sprint 16, Agent 2)

## Audit Date: 2026-08-24
## File: index.html (16,772 lines)
## Auditor: Agent 2

---

## 1. Z-INDEX INVENTORY (Before Fix)

### CSS :root variables
- `--modal-z: 200` (line 62)
- `--z-overlay: 10` (line 42) — unused
- `--z-panel: 20` (line 43) — unused
- `--z-modal: 30` (line 44) — unused
- `--z-toast: 40` (line 45) — unused

### All z-index declarations in CSS (sorted by z-value)

| Line | Selector/Context | Position | z-index | Top | Right | Bottom | Left |
|------|-----------------|----------|---------|-----|-------|--------|------|
| 1012 | `#sky-dome` | absolute | 0 | 0 | - | - | 0 |
| 865 | `#topbar::after` (mobile) | absolute | 1 | 0 | 0 | 3px | — |
| 125 | `.viewport-overlay` | absolute | 10 | — | — | — | — |
| 379 | `#excavate-btn` | absolute | 10 | — | — | 16px | 460px |
| 693 | `#sun-btn` | absolute | 10 | — | — | 16px | 410px |
| 697 | `#sun-panel` | absolute | 10 | — | — | 56px | 410px |
| 740 | `#innovation-btn` | absolute | 10 | — | — | 16px | 530px |
| 262 | `#terrain-analysis-btn` | absolute | 11 | — | — | 16px | 480px |
| 383 | `#excavate-panel` | absolute | 11 | — | — | 56px | 460px |
| 744 | `#innovation-panel` | absolute | 11 | — | — | 56px | 530px |
| 1036 | `#atmosphere-badge` | absolute | 12 | 8px | — | — | 50% |
| 134 | `#scale-bar` | absolute | 15 | — | — | 16px | 16px |
| 218 | `#sculpt-restore-pill` | fixed | 25 | — | — | 16px | 50% |
| 182 | `#dock-panel-container` | absolute | 19 | — | — | 16px | 90px |
| 158 | `#tool-dock` | absolute | 20 | — | — | 16px | 16px |
| 334 | `#terrain-height-legend` | absolute | 45 | 16px | — | — | 16px |
| 781 | `#grid-level-badge` | absolute | 46 | 16px | — | — | 50% |
| 812 | `#depth-gauge-overlay` | absolute | 47 | 16px | 16px | — | — |
| 908 | `#season-panel` | absolute | 48 | 200px | 16px | — | — |
| 957 | `#growth-panel` | absolute | 48 | 380px | 16px | — | — |
| 665 | `#layer-panel` | absolute | 49 | 200px | 16px | — | — |
| 365 | `#measure-readout` | absolute | 50 | — | — | — | — |
| 516 | `#properties` (mobile) | absolute | 50 | 0 | 0 | 0 | — |
| 644 | `#cost-panel` | absolute | 50 | 16px | 16px | — | — |
| 981 | `#permit-panel` | absolute | 50 | 200px | 340px | — | — |
| 1070 | `#compass-indicator` | absolute | 50 | 60px→120px | 16px | — | — |
| 1406 | `.discovery-badge` | absolute | 50 | -6px | -6px | — | — |
| 414 | `#cross-section-panel` | absolute | 51 | 16px | 340px | — | — |
| 295 | `#cut-fill-panel` | absolute | 52 | 16px | 340px | — | — |
| 499 | `#sidebar` (mobile) | absolute | 55 | — | — | — | — |
| 11392 | `#innov-stats-overlay` (JS) | absolute | 55 | 60px | 16px | — | — |
| 266 | `#terrain-analysis-panel` | absolute | 60 | — | — | 56px | 480px |
| 504 | `#mobile-lib-toggle` (mobile) | fixed | 60 | — | 16px | 200px | — |
| 345 | `#terrain-controls` (mobile) | fixed | 65 | 60px | 0 | 0 | 0 |
| 285 | `#ta-cross-section-overlay` | absolute | 70 | — | — | 16px | 50% |
| 544 | `#mobile-props-sheet` (mobile) | fixed | 70 | — | 0 | 0 | 0 |
| 90 | `#topbar` | relative | 100 | — | — | 1px | — |
| 1224 | `#batch-bar` | fixed | 100 | — | — | 60px | 50% |
| 1432 | `#onboarding-restart-btn` | fixed | 100 | — | 200px | 16px | — |
| 483 | `#toast` | fixed | 150 | — | — | 70px | 50% |
| 728 | `#walk-controls` | absolute | 150 | — | — | — | — |
| 730 | `#walk-exit` | absolute | 201 | 16px | 16px | — | — |
| 954 | `.print-overlay-btn` | fixed | 210 | 20px | 20px | — | — |
| 1418 | `#progressive-hint` | fixed | 220 | — | — | 80px | 50% |
| 1391 | `#ctx-tooltip` | fixed | 230 | — | — | — | — |
| 1350 | `#tour-overlay` | fixed | 240 | — | — | — | — |
| 1358 | `#tour-spotlight` | fixed | 241 | — | — | — | — |
| 1364 | `#tour-bubble` | fixed | 242 | — | — | — | — |
| 1176 | `#ctx-menu` | fixed | 250 | — | — | — | — |
| 1925 | `#export-menu` (inline) | absolute | 200 | 100% | 0 | — | — |
| 458+ | Modals (wizard, help, share, templates, etc.) | fixed | var(--modal-z)=200 | — | — | — | — |
| 1264 | `.skip-link` | absolute | 9999 | 0 | — | — | -9999px |
| 1814 | `.mi-progress` | fixed | 9999 | 0 | — | — | 0 |
| 4280 | `#webgl-error-overlay` (JS) | absolute | 9999 | — | — | — | — |
| 1633 | `.mi-spinner-overlay` | absolute | 500 | — | — | — | — |
| 5123 | `#mobile-ctx-menu` (JS) | fixed | 300 | — | — | — | — |
| 15164 | `#perf-panel` (JS) | fixed | 500 | 60px | 16px | — | — |

---

## 2. Z-INDEX CONFLICTS IDENTIFIED

### Conflict Group A: z-index:50 (7 elements)
- `#measure-readout` — floating measurement tooltip
- `#properties` (mobile) — properties panel
- `#cost-panel` — top-right cost panel (top:16px, right:16px)
- `#permit-panel` — top:200px, right:340px
- `#compass-indicator` — top:120px, right:16px (56x56px)
- `.discovery-badge` — badge on parent element
- `#walk-exit` also at 201, not 50 — ok

**Issue**: `#cost-panel` (top:16px, right:16px) and `#compass-indicator` (top:120px, right:16px) both at z-index:50. They don't visually overlap because compass is at top:120px and cost-panel starts at top:16px. But the cost-panel can extend down past 120px depending on content. The compass is below the cost panel and could be hidden by it.

### Conflict Group B: z-index:10 (5 elements)
- `.viewport-overlay` (base class for dim-readout, view-controls, context-hint, safety-warnings)
- `#excavate-btn` — bottom:16px, left:460px
- `#sun-btn` — bottom:16px, left:410px
- `#sun-panel` — bottom:56px, left:410px
- `#innovation-btn` — bottom:16px, left:530px

**Issue**: These buttons share the same z-index as the `.viewport-overlay` base class. The buttons should be at a higher layer.

### Conflict Group C: z-index:11 (3 elements)
- `#terrain-analysis-btn` — bottom:16px, left:480px
- `#excavate-panel` — bottom:56px, left:460px
- `#innovation-panel` — bottom:56px, left:530px

**Issue**: Panels at z-index:11 are LOWER than dock-panel-container at z-index:19. These panels could be hidden behind the dock.

### Conflict Group D: z-index:48 (2 elements)
- `#season-panel` — top:200px, right:16px
- `#growth-panel` — top:380px, right:16px

**Issue**: Both at right:16px. Season at top:200px, Growth at top:380px. If season panel is tall enough it could overlap growth panel.

### Conflict Group E: z-index:70 (3 elements)
- `#ta-cross-section-overlay` — bottom:16px, center
- `#mobile-props-sheet` (mobile) — bottom sheet
- `#mobile-props-sheet` (is-mobile) — bottom sheet (duplicate rule)

### Conflict Group F: z-index:60 (3 elements)
- `#terrain-analysis-panel` — bottom:56px, left:480px
- `#mobile-lib-toggle` (mobile) — bottom:200px, right:16px
- `#mobile-lib-toggle` (is-mobile) — duplicate

### Conflict Group G: z-index:100 (3 elements)
- `#topbar` — relative, not absolute
- `#batch-bar` — fixed, bottom:60px, center
- `#onboarding-restart-btn` — fixed, bottom:16px, right:200px

### Conflict Group H: z-index:200 (2+ elements)
- `#export-menu` (inline style) — absolute, top:100%, right:0
- All modals via `--modal-z: 200`

---

## 3. POSITIONING OVERLAPS IDENTIFIED

### 3a. Bottom-Left Button Cluster (bottom:16px)
All these buttons are at `bottom: 16px`:

| Button | Left | Approx Width | Right Edge |
|--------|------|-------------|-----------|
| `#scale-bar` | 16px | ~120px | ~136px |
| `#tool-dock` | 16px | ~70px | ~86px |
| `#tape-measure-btn` | 200px | ~110px | ~310px |
| `#terrain-btn` | 330px | ~100px | ~430px |
| `#sun-btn` | 410px | ~90px | ~500px |
| `#excavate-btn` | 460px | ~100px | ~560px |
| `#terrain-analysis-btn` | 480px | ~130px | ~610px |
| `#innovation-btn` | 530px | ~120px | ~650px |

**OVERLAPS FOUND**:
1. `#terrain-btn` (left:330px, ~100px wide → ends ~430px) overlaps `#sun-btn` (left:410px) — **20px overlap**
2. `#sun-btn` (left:410px, ~90px wide → ends ~500px) overlaps `#excavate-btn` (left:460px) — **40px overlap**
3. `#excavate-btn` (left:460px, ~100px wide → ends ~560px) overlaps `#terrain-analysis-btn` (left:480px) — **80px overlap**
4. `#terrain-analysis-btn` (left:480px, ~130px wide → ends ~610px) overlaps `#innovation-btn` (left:530px) — **80px overlap**
5. `#tool-dock` (left:16px) overlaps `#scale-bar` (left:16px) — both at same position. Tool-dock has z-index:20, scale-bar z-index:15, so tool-dock is on top.

**NOTE**: Many of these buttons are hidden via `display: none !important` (lines 255-260). The visible bottom-left controls are `#tool-dock` and `#scale-bar`. But when tool-dock is collapsed/hidden, the standalone buttons may become visible.

### 3b. Top-Right Panel Cluster

| Panel | Top | Right | z-index |
|-------|-----|-------|---------|
| `#cost-panel` | 16px | 16px (or 280px shifted) | 50 |
| `#compass-indicator` | 120px | 16px | 50 |
| `#cut-fill-panel` | 16px | 340px | 52 |
| `#cross-section-panel` | 16px | 340px | 51 |
| `#permit-panel` | 200px | 340px | 50 |
| `#layer-panel` | 200px | 16px | 49 |
| `#season-panel` | 200px | 16px | 48 |
| `#growth-panel` | 380px | 16px | 48 |
| `#depth-gauge-overlay` | 16px | 16px | 47 |

**OVERLAPS FOUND**:
1. `#cost-panel` (top:16px, right:16px) and `#depth-gauge-overlay` (top:16px, right:16px) — **same position**, but cost-panel z-index:50 > depth-gauge z-index:47. Depth gauge hidden behind cost panel.
2. `#cost-panel` and `#compass-indicator` — cost-panel starts at top:16px, compass at top:120px. Cost panel could extend down past 120px and overlap compass.
3. `#layer-panel` (top:200px, right:16px) and `#season-panel` (top:200px, right:16px) — **same position**, z-index 49 vs 48. Only one visible at a time typically.
4. `#cut-fill-panel` (top:16px, right:340px) and `#cross-section-panel` (top:16px, right:340px) — **same position**, z-index 52 vs 51. Only one visible at a time typically.
5. `#permit-panel` (top:200px, right:340px) and `#layer-panel` (top:200px, right:16px) — different right values, no overlap.
6. `#growth-panel` (top:380px, right:16px) could overlap `#layer-panel` (top:200px, right:16px) if layer-panel extends past 380px.
7. `#innov-stats-overlay` (JS, top:60px, right:16px, z-index:55) overlaps `#compass-indicator` (top:120px, right:16px, z-index:50) — innov-stats at top:60px extends down, compass at top:120px.
8. `#perf-panel` (JS, top:60px, right:16px, z-index:500) overlaps everything in top-right at z-index:500.

### 3c. Onboarding Restart Button
- `#onboarding-restart-btn` — fixed, bottom:16px, right:200px, z-index:100
- `#view-controls` — bottom:16px, right:16px (flex column, ~40px wide each, ~4-5 buttons → ~200px tall)
- At right:200px, onboarding button is 184px from view-controls (right:16px → right edge at viewport-16px, view-controls width ~40px, so view-controls occupies right:16px to right:56px). Onboarding at right:200px starts at viewport-200px. Gap is 200-56=144px. **No overlap** but close.

### 3d. Context Menu z-index
- `#ctx-menu` z-index:250 — context menu
- `#ctx-tooltip` z-index:230 — tooltip
- `#tour-overlay` z-index:240, `#tour-spotlight` z-index:241, `#tour-bubble` z-index:242
- `#mobile-ctx-menu` (JS) z-index:300

**Issue**: ctx-tooltip at 230 is below tour-overlay at 240. Tooltip should be above tour? Actually tooltips are contextual and may need to be above tour overlays — or not, depending on design. The spec says tooltips at z-index:40, which is below panels. This is wrong — tooltips need to be visible above content.

### 3e. Walk-mode overlay
- `#walk-controls` z-index:150 — covers entire viewport
- `#walk-exit` z-index:201 — exit button on top of walk controls
- `#toast` z-index:150 — same as walk-controls, could conflict

---

## 4. TARGET Z-INDEX HIERARCHY (per spec)

| Layer | z-index | Elements |
|-------|---------|----------|
| Canvas/viewport | 1 | `#sky-dome`, `#viewport canvas` |
| Overlay info | 10 | `#scale-bar`, `#dim-readout`, `#atmosphere-badge` |
| Tool dock / bottom-left buttons | 15 | `#tool-dock`, `#tape-measure-btn`, `#terrain-btn`, `#excavate-btn`, `#terrain-analysis-btn`, `#sun-btn`, `#innovation-btn` |
| Dock panel container | 19 | `#dock-panel-container` |
| Sidebar / properties | 20 | `#sidebar` (mobile), `#properties` |
| Floating panels | 25 | `#sun-panel`, `#terrain-analysis-panel`, `#excavate-panel`, `#innovation-panel`, `#sculpt-restore-pill`, `#terrain-controls` |
| Cost / cut-fill / layer / cross-section | 30 | `#cost-panel`, `#cut-fill-panel`, `#cross-section-panel`, `#layer-panel`, `#permit-panel`, `#season-panel`, `#growth-panel`, `#terrain-height-legend`, `#grid-level-badge`, `#depth-gauge-overlay`, `#innov-stats-overlay` |
| Context menus / tooltips | 40 | `#ctx-menu`, `#ctx-tooltip`, `#mobile-ctx-menu`, `#measure-readout` |
| Modal overlays | 50 | `#help-modal`, `#walk-controls`, `#wizard`, `#share-modal`, `#templates-modal`, `#label-edit-modal`, `#gallery-modal`, `#timelapse-modal`, `#socialcard-modal`, `#cmd-palette-overlay`, `#welcome-prompt`, `#confirm-dialog`, `#walk-exit` |
| Topbar | 100 | `#topbar`, `#batch-bar`, `#onboarding-restart-btn` |
| Toast | 150 | `#toast` |
| Tour overlay / backdrop | 200 | `#tour-overlay`, `#tour-spotlight`, `#tour-bubble`, `#tour-backdrop`, `#export-menu` |
| Command palette | 500 | `#cmd-palette-overlay` (but this is a modal...), `#perf-panel`, `.mi-spinner-overlay` |
| Desktop gate / highest | 9999 | `.skip-link`, `.mi-progress`, `#webgl-error-overlay` |

**IMPORTANT NOTE**: `--modal-z` is 200. Modals use `var(--modal-z)`. The spec says modals should be z-index:50, but the current value is 200. Changing `--modal-z` to 50 would put modals BELOW the topbar (100) and toast (150). This would be wrong — modals must be above everything. The spec's z-index:50 for "modal overlays" appears to be in conflict with z-index:100 for topbar. 

**RESOLUTION**: The spec says modal overlays at z-index:50, but also says topbar at 100 and toast at 150. A modal at z-index:50 would appear BEHIND the topbar. This is clearly wrong for full-screen modals with backdrop. We will set `--modal-z` to 300 (above topbar:100, toast:150, tour:200) but below the highest-priority elements (skip-link, progress, webgl-error at 9999). The spec's z-index:50 likely refers to panel-style "overlays" like help-panel, not full-screen modals. However, the spec explicitly says "help-panel" at z-index:50. We'll interpret this as: non-fullscreen help panels at 50, but full-screen modal backdrops remain higher. We'll set `--modal-z` to 300.

Actually, re-reading the spec: "z-index: 50 — modal overlays (help-panel, walk-mode overlay)". These are NOT the same as full-screen modals (wizard, share-modal, etc.). The help-modal IS a full-screen modal with backdrop. Setting it to z-index:50 would put it behind the topbar.

**FINAL RESOLUTION**: Set `--modal-z` to 300. This puts all full-screen modals above topbar(100), toast(150), tour(200). The spec's z-index:50 layer is for walk-controls and similar overlay panels. We'll set `#walk-controls` to 50 (it's a viewport overlay, not a full-page modal). But walk-exit needs to be above walk-controls, so it should also be at 50+ or higher. Actually the spec says "walk-mode overlay" at z-index:50 — that includes walk-controls. We'll follow the spec: walk-controls at 50, walk-exit at 51 or 100.

For modals, we need them above everything except the desktop gate. Setting `--modal-z` to 300 is the correct approach.

---

## 5. BOTTOM-LEFT BUTTON REPOSITIONING PLAN

Current (hidden by `display:none !important`, but may be shown when tool-dock is collapsed):
- `#tape-measure-btn` left:200px
- `#terrain-btn` left:330px
- `#sun-btn` left:410px
- `#excavate-btn` left:460px
- `#terrain-analysis-btn` left:480px
- `#innovation-btn` left:530px

New layout (120px spacing, no overlaps):
- `#tape-measure-btn` left:200px (unchanged)
- `#terrain-btn` left:330px (unchanged, gap from tape=130px)
- `#sun-btn` left:460px (was 410px, +50px gap from terrain)
- `#excavate-btn` left:590px (was 460px, +130px gap from sun)
- `#terrain-analysis-btn` left:720px (was 480px, +130px gap from excavate)
- `#innovation-btn` left:850px (was 530px, +130px gap from terrain-analysis)

Wait — this would push buttons off screen on 1280px viewport. Let's use 130px spacing:
- `#tape-measure-btn` left:200px
- `#terrain-btn` left:330px  
- `#sun-btn` left:460px
- `#excavate-btn` left:590px
- `#terrain-analysis-btn` left:720px
- `#innovation-btn` left:850px

On 1280px viewport, innovation-btn right edge ≈ 850+120=970px. Still fits.

Panels should follow their buttons:
- `#sun-panel` left:460px (was 410px)
- `#excavate-panel` left:590px (was 460px)
- `#terrain-analysis-panel` left:720px (was 480px)
- `#innovation-panel` left:850px (was 530px)
- `#terrain-controls` left:330px (unchanged, follows terrain-btn)

---

## 6. TOP-RIGHT PANEL REPOSITIONING PLAN

Current top-right panels at right:340px:
- `#cut-fill-panel` top:16px, right:340px, z-index:52
- `#cross-section-panel` top:16px, right:340px, z-index:51
- `#permit-panel` top:200px, right:340px, z-index:50

These are only visible one at a time (cut-fill and cross-section both at top:16px). Permit at top:200px. No actual conflict since only one is visible at a time. But z-index should be normalized to 30.

Current top-right at right:16px:
- `#cost-panel` top:16px, right:16px (or 280px shifted), z-index:50
- `#depth-gauge-overlay` top:16px, right:16px, z-index:47
- `#compass-indicator` top:120px, right:16px, z-index:50
- `#layer-panel` top:200px, right:16px, z-index:49
- `#season-panel` top:200px, right:16px, z-index:48
- `#growth-panel` top:380px, right:16px, z-index:48
- `#innov-stats-overlay` (JS) top:60px, right:16px, z-index:55
- `#perf-panel` (JS) top:60px, right:16px, z-index:500

**Conflicts**:
1. cost-panel and depth-gauge-overlay at same position → depth gauge only shows in underground mode, cost panel only shows when opened. Different modes. z-index: normalize both to 30.
2. layer-panel and season-panel at top:200px, right:16px → only one visible at a time. z-index: normalize to 30.
3. compass at top:120px, right:16px → below cost-panel. If cost-panel is ~200px tall, it overlaps compass. Move compass to top:230px or ensure cost-panel doesn't extend that far.
4. innov-stats-overlay at top:60px and perf-panel at top:60px → both at same position, but different modes (innov-stats for terrain analysis, perf-panel for profiling). z-index: normalize innov-stats to 30, perf-panel to 500 (dev tool, should be on top).

---

## 7. SUMMARY OF ALL FIXES NEEDED

### z-index fixes (CSS):
1. `--modal-z` → 300 (was 200)
2. `#scale-bar` → z-index:10 (was 15)
3. `#tool-dock` → z-index:15 (was 20)
4. `#dock-panel-container` → z-index:19 (unchanged, already correct)
5. `.viewport-overlay` → z-index:10 (unchanged)
6. `#excavate-btn` → z-index:15 (was 10)
7. `#sun-btn` → z-index:15 (was 10)
8. `#sun-panel` → z-index:25 (was 10)
9. `#innovation-btn` → z-index:15 (was 10)
10. `#innovation-panel` → z-index:25 (was 11)
11. `#terrain-analysis-btn` → z-index:15 (was 11)
12. `#terrain-analysis-panel` → z-index:25 (was 60)
13. `#excavate-panel` → z-index:25 (was 11)
14. `#terrain-controls` → z-index:25 (mobile override only, desktop inherits)
15. `#sculpt-restore-pill` → z-index:25 (unchanged, already correct)
16. `#cost-panel` → z-index:30 (was 50)
17. `#cut-fill-panel` → z-index:30 (was 52)
18. `#cross-section-panel` → z-index:30 (was 51)
19. `#layer-panel` → z-index:30 (was 49)
20. `#permit-panel` → z-index:30 (was 50)
21. `#season-panel` → z-index:30 (was 48)
22. `#growth-panel` → z-index:30 (was 48)
23. `#terrain-height-legend` → z-index:30 (was 45)
24. `#grid-level-badge` → z-index:30 (was 46)
25. `#depth-gauge-overlay` → z-index:30 (was 47)
26. `#measure-readout` → z-index:40 (was 50)
27. `#ctx-menu` → z-index:40 (was 250)
28. `#ctx-tooltip` → z-index:40 (was 230)
29. `#mobile-ctx-menu` (JS) → z-index:40 (was 300)
30. `#walk-controls` → z-index:50 (was 150)
31. `#walk-exit` → z-index:55 (was 201) — above walk-controls
32. `#toast` → z-index:150 (unchanged)
33. `#topbar` → z-index:100 (unchanged)
34. `#batch-bar` → z-index:100 (unchanged)
35. `#onboarding-restart-btn` → z-index:100 (unchanged)
36. `#tour-overlay` → z-index:200 (was 240)
37. `#tour-spotlight` → z-index:200 (was 241)
38. `#tour-bubble` → z-index:200 (was 242)
39. `#export-menu` (inline) → z-index:200 (unchanged)
40. `.print-overlay-btn` → z-index:200 (was 210)
41. `#progressive-hint` → z-index:150 (was 220) — toast-level
42. `#compass-indicator` → z-index:30 (was 50)
43. `#properties` (mobile) → z-index:20 (was 50)
44. `#sidebar` (mobile) → z-index:20 (was 55)
45. `#mobile-lib-toggle` (mobile) → z-index:20 (was 60)
46. `#mobile-props-sheet` (mobile) → z-index:50 (was 70)
47. `#terrain-controls` (mobile) → z-index:50 (was 65)
48. `.discovery-badge` → z-index:40 (was 50) — tooltip-level
49. `.mi-spinner-overlay` → z-index:500 (unchanged)
50. `#perf-panel` (JS) → z-index:500 (unchanged)
51. `#innov-stats-overlay` (JS) → z-index:30 (was 55)
52. `.skip-link` → z-index:9999 (unchanged)
53. `.mi-progress` → z-index:9999 (unchanged)
54. `#webgl-error-overlay` (JS) → z-index:9999 (unchanged)
55. `#atmosphere-badge` → z-index:10 (was 12)
56. `#ta-cross-section-overlay` → z-index:30 (was 70)

### Position fixes (CSS):
57. `#sun-btn` left:460px (was 410px)
58. `#sun-panel` left:460px (was 410px)
59. `#excavate-btn` left:590px (was 460px)
60. `#excavate-panel` left:590px (was 460px)
61. `#terrain-analysis-btn` left:720px (was 480px)
62. `#terrain-analysis-panel` left:720px (was 480px)
63. `#innovation-btn` left:850px (was 530px)
64. `#innovation-panel` left:850px (was 530px)
65. `#compass-indicator` top:240px (was 120px) — moved below cost panel
66. `#innov-stats-overlay` (JS) top:240px (was 60px) — moved below cost panel

---

## 8. FILES MODIFIED
- `index.html` — z-index and position fixes (lines 62, 133, 158, 182, 219, 261, 266, 285, 295, 334, 345, 364, 378, 382, 414, 482, 498, 504, 515, 524, 535, 544, 593, 644, 665, 692, 696, 728, 729, 740, 743, 780, 812, 908, 954, 957, 981, 1011, 1035, 1069, 1176, 1224, 1264, 1350, 1358, 1364, 1391, 1406, 1418, 1432, 1633, 1814, 5123, 11392, 15164)

---

## END OF DISCOVERY LOG