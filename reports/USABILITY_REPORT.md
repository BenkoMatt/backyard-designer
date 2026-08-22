# USABILITY REPORT — Backyard Designer 3D
## Sprint 5 Usability Testing — Agent 3 (Usability Tester)

### The Question: "Does everything make sense where it is?"

**Answer**: Largely yes. The app has a solid foundation with an intuitive onboarding wizard, well-organized tool panels, and logical workflows. Four usability issues were found and fixed. After fixes, all 10 user workflows pass.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Workflows tested | 10/10 |
| Workflows passing | 10/10 |
| Usability issues found | 4 |
| Issues fixed | 4 |
| Commits made | 4 |
| Console errors | 0 (only WebGL performance warnings) |

---

## Workflow Results

| # | Workflow | Status | Errors | Pain Points |
|---|----------|--------|--------|-------------|
| 1 | NEW USER | ✅ PASS | 0 | 0 |
| 2 | TERRAIN SCULPTOR | ✅ PASS | 0 | 0 |
| 3 | EXCAVATOR | ✅ PASS | 0 | 0 |
| 4 | POOL DESIGNER | ✅ PASS | 0 | 0 |
| 5 | CARVING USER | ✅ PASS | 0 | 0 |
| 6 | MOBILE USER | ✅ PASS | 0 | 0 |
| 7 | ANALYZER | ✅ PASS | 0 | 0 |
| 8 | SHARER | ✅ PASS | 0 | 1 (minor) |
| 9 | WALKER | ✅ PASS | 0 | 0 |
| 10 | POWER USER | ✅ PASS | 0 | 1 (expected) |

---

## Issues Found and Fixed

### 1. Floating Panels Extend Beyond Viewport (HIGH)
**Affected**: All bottom-anchored floating panels (#terrain-controls, #terrain-analysis-panel, #excavate-panel, #sun-panel, #innovation-panel)
**Impact**: Panel content could extend above the visible viewport, making controls unreachable. The terrain "raise mode" button was completely off-screen and unclickable.
**Fix**: Added `max-height: calc(100vh - 80px)` and `overflow-y: auto` to all 5 panels, ensuring content stays within the viewport with internal scrolling.
**Commit**: `18cb499`

### 2. Mobile Topbar Overflow (HIGH)
**Affected**: Top bar with 11+ buttons on 375px screens
**Impact**: Topbar scrollWidth was 1128px on a 375px viewport — buttons overflowed massively, making most toolbar actions inaccessible on mobile.
**Fix**: Added responsive CSS for `@media (max-width: 768px)`:
- Hide button text labels (icon-only mode)
- Reduce padding and gaps
- Hide less-critical buttons (#btn-screenshot, #btn-help)
- Enable horizontal scroll as fallback
- Result: scrollWidth reduced from 1128px → 469px (58% reduction)
**Commit**: `ebc1a1c`, `607bc52`

### 3. Mobile Floating Button Overlaps (MEDIUM)
**Affected**: Floating buttons at hardcoded left positions (200px–530px) on 375px screens
**Impact**: Sun button (left:410px) and Analysis button (left:480px) were completely off-screen on mobile. Tape measure and terrain buttons overlapped.
**Fix**: Added mobile CSS that stacks all floating buttons vertically at `left: 16px` with increasing `bottom` values (130px, 175px, 220px, 265px, 310px), eliminating all overlaps.
**Commit**: `ebc1a1c`

### 4. Top-Right Panel Overlaps (MEDIUM)
**Affected**: Cost panel, Layer panel, and Cross-section panel all at `top: 16px; right: 16px`
**Impact**: Opening multiple panels simultaneously caused them to visually overlap, making both unreadable.
**Fix**: Modified toggle functions (`toggleCostPanel`, `toggleLayerPanel`, cross-section toggle) to close other panels when one opens. Only one top-right panel visible at a time.
**Commit**: `801277f`

---

## What Works Well

1. **Onboarding Wizard**: 2-step setup (yard shape → dimensions) with pre-selected rectangle default and quick size presets. Intuitive for new users.
2. **Object Library**: Categorized (Trees & Plants, Structures, etc.) with icons and descriptions. Items are easily clickable.
3. **Terrain Sculpting**: Clear mode buttons (Raise/Lower/Smooth/Erode) with brush size and strength sliders. Precision mode toggle works correctly.
4. **Carving System**: Shape selection (Box/Round/Trench) with commit/clear buttons. Underground camera toggle provides clear visual feedback.
5. **Analysis Tools**: Well-organized panel with clear section titles. All 4 analysis toggles (contour, slope, water flow, cut/fill) work simultaneously without overwhelming.
6. **Walk Mode**: Clear instructions overlay, WASD navigation, Escape to exit. Mobile joystick controls included.
7. **Share/QR**: Generates QR code canvas, displays shareable URL, copy-to-clipboard button. URL hash encoding for design sharing.
8. **Cost Estimator**: Shows per-category costs with total. Updates when objects are added.
9. **Help Dialog**: Comprehensive instructions for getting started.
10. **Mobile Properties**: Bottom-sheet pattern for object properties on mobile — standard mobile UX.

---

## Remaining Observations (Not Bugs)

- **Innovation panel length**: With 12+ tools, the panel is long when all are active (2338px content). This is handled correctly with `max-height` + `overflow-y: auto`. Progressive disclosure could improve this in the future but is not a blocking issue.
- **Share modal link display**: The share URL is shown as text in a div (not an input field). This is a valid UX choice with a dedicated copy button — not a usability issue.
- **WebGL performance warnings**: GPU stall warnings appear in console during ReadPixels operations. These are performance advisories, not errors, and don't affect functionality.

---

## Test Methodology

- **Tool**: Playwright Python with Chromium (headless)
- **Desktop viewport**: 1280×800
- **Mobile viewport**: 375×812 (iPhone X size)
- **Approach**: Each workflow tested in isolation with fresh page load. Console errors captured. Element positions verified via getBoundingClientRect. CSS computed styles checked for responsive behavior.
- **Re-testing**: All workflows re-tested after each fix to ensure no regressions.

---

## Git Log

```
801277f Fix: cost/layer/cross-section panels overlap - opening one now closes the others since they share the same top-right position
607bc52 Fix: improve mobile topbar - hide screenshot/help buttons on small screens, compact icon-only layout with horizontal scroll
ebc1a1c Fix: mobile responsive topbar and floating buttons - hide text labels on small screens, stack floating buttons vertically to prevent overlap
18cb499 Fix: floating panels extend beyond viewport - add max-height and overflow-y:auto to all bottom-anchored floating panels (terrain, analysis, excavate, sun, innovation)
f6d855d Add Sprint 4 test results JSON
8cca2cd Sprint 4: 3D Volume Terrain & Voxel Carving — 5-agent merge
ba4c541 Add house icon favicon (inline SVG data URI)
40a2d6d Sprint 3: Terrain Precision & Solid Excavation — 5-agent merge
a3d9e05 Sprint 2: Terrain Overhaul — 5-agent merge
```