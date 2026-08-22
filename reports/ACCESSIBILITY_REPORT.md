# Sprint 5 Accessibility Report — Backyard Designer 3D

**Agent 4 (Critic): Accessibility & Quality Gate Auditor**
**Date: August 22, 2026**
**Sprint: 5**

## Executive Summary

Answer to "Does everything make sense where it is?" from an accessibility perspective: **Mostly yes, with significant fixes applied.** The application had 24 accessibility failures across 6 categories. All 24 have been fixed. The quality gate now passes 112/112 tests.

## Issues Found and Fixed

### 1. Color Contrast (WCAG AA 4.5:1) — FIXED

**Problem:** The primary brand color `--primary: #4a8b5c` had a contrast ratio of only 4.09:1 against white (needs 4.5:1 for WCAG AA). The muted text color `--text-muted: #666` had 5.74:1 on white but only 5.19:1 on the app background.

**Fix:** Darkened the CSS variables:
- `--primary`: `#4a8b5c` → `#3d7549` (contrast: 5.47:1 on white, 5.0:1 on bg)
- `--primary-dark`: `#3a6b46` → `#2f5d3a` (contrast: 7.64:1 on white)
- `--text-muted`: `#666` → `#5a5a5a` (contrast: 6.9:1 on white, 6.31:1 on bg)

**Affected:** All text using `var(--primary)`, `var(--text-muted)`, and white-on-primary button combinations throughout the app.

### 2. Focus Visibility — FIXED

**Problem:** No `:focus-visible` CSS styles existed anywhere in the application. Keyboard users had no visual indication of which element was focused.

**Fix:** Added `:focus-visible` CSS rules:
```css
*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
*:focus:not(:focus-visible) { outline: none; }
.tb-btn.primary:focus-visible, #sun-btn.active:focus-visible, #walk-exit:focus-visible {
  outline-color: white; outline-offset: 1px;
}
```

### 3. Touch Target Sizes (44x44px minimum) — FIXED

**Problem:** 12 buttons on mobile viewport (375px) had heights of only 30-32px, below the WCAG 2.5.5 minimum of 44x44px. Affected buttons:
- Topbar: Save, Load, Screenshot, Layers, Cost, Walk, Share (all ~32px height)
- Floating: Tape Measure, Excavate, Analyze, Innovate, Sun (all ~32px height)

**Fix:** Added `min-height: 44px !important` with adjusted padding and font-size for all interactive controls in the `@media (max-width: 768px)` media query. Used `!important` to override dynamically injected mobile CSS that sets `font-size: 0` for icon-only mode.

### 4. ARIA Labels on Sliders — FIXED

**Problem:** 5 sliders had no `aria-label` attribute, making them invisible to screen readers:
- `#terrain-brush-size`, `#terrain-strength`, `#grid-level-slider`
- `#terrain-cutaway`, `#terrain-opacity`

**Fix:** Added descriptive `aria-label` attributes to all 5 sliders and extended to ALL range inputs in the app (28 total sliders/inputs now labeled).

### 5. ARIA Roles on Toggle Switches — FIXED

**Problem:** 6 custom toggle switch `<div>` elements (ta-toggles) had no `role`, `tabindex`, or `aria-checked` attributes. They were not keyboard-accessible and invisible to screen readers.

**Fix:** Added `role="switch"`, `tabindex="0"`, `aria-checked="false"`, and `aria-label` to all 6 ta-toggle elements. Added keyboard event handlers (Enter/Space) via `setupToggleKeyboard()` utility function. Added `aria-checked` synchronization on toggle.

### 6. Additional ARIA Labels — FIXED

**Problem:** Several buttons and inputs lacked `aria-label` or `aria-pressed`:
- `#wireframe-toggle`, `#cross-section-toggle` — missing aria-label
- `#terrain-flatten`, `#terrain-toggle-height`, `#terrain-toggle-drainage` — missing aria-label
- `#carving-commit-btn`, `#carving-clear-btn` — missing aria-label
- `#ta-crosssection-btn`, `#ta-compare-btn` — missing aria-label
- `#sun-geo`, `#sun-play`, `#sun-reset` — missing aria-label
- `#sun-lat`, `#sun-lng`, `#sun-date`, `#sun-time` — missing aria-label

**Fix:** Added appropriate `aria-label` attributes to all listed controls.

## Test Results

**Quality Gate: 112/112 passed, 0 failed**

### Test Categories:
1. **ARIA Correctness** — 25 tests, all pass
2. **Keyboard Navigation** — 22 tests, all pass
3. **Touch Target Sizes** — 18 tests, all pass
4. **Color Contrast (WCAG AA)** — 13 tests, all pass
5. **Focus Visibility** — 3 tests, all pass
6. **Focus Order** — 2 tests, all pass
7. **Additional Accessibility** — 29 tests, all pass

## Files Modified

- `index.html` — CSS variable color changes, focus-visible CSS, mobile touch target CSS, ARIA labels on 28+ elements, toggle keyboard accessibility
- `sprint5_quality_gate.py` — Quality gate test suite (112 tests)
- `sprint5_quality_gate_results.json` — Test results

## Remaining Considerations

1. **Onboarding wizard** — The wizard overlay covers the full screen on load. While it has proper buttons and can be dismissed, keyboard focus management (focusing the first interactive element when the wizard opens) could be improved.
2. **Panel focus trapping** — When panels open (terrain, excavate, innovation, etc.), focus is not trapped within the panel. Users can Tab out of the panel to elements behind it.
3. **Screen reader announcements** — The app has a `_srLiveRegion` for announcements, but it could be used more extensively for state changes (toggle on/off, panel open/close).
4. **Dynamic mobile CSS** — The app injects mobile-specific CSS at runtime that sets `font-size: 0` for topbar buttons (icon-only mode). The `!important` overrides ensure 44px minimum height, but the text labels remain hidden on mobile.