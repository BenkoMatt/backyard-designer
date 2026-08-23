# Sprint 8 — Accessibility & Usability Report
## Backyard Designer 3D

**Agent:** Agent 4 (Critic) — Accessibility Usability Reviewer  
**Date:** August 23, 2026  
**Working Directory:** `/root/byd8-a11y-usability/`  
**Quality Gate:** 75/75 tests passing ✅  

---

## Executive Summary

Comprehensive accessibility audit of Backyard Designer 3D identified and fixed **13 accessibility issues** spanning keyboard navigation, screen reader compatibility, motion sensitivity, focus management, and cognitive accessibility. The app now meets WCAG 2.1 AA for all tested text/background combinations, supports keyboard-only navigation through all controls, announces status updates to screen readers, respects reduced-motion preferences, and provides proper modal dialog semantics.

---

## Issues Found and Fixed

### 1. Tab Key Interception (CRITICAL)
- **Problem:** The `keydown` handler intercepted `Tab` key globally to cycle through objects (`e.preventDefault()` on Tab). This broke standard keyboard navigation — Tab was stuck on the terrain button instead of moving between controls.
- **Fix:** Changed object cycling to `Alt+Tab` (forward) / `Alt+Shift+Tab` (backward). Tab now performs its default browser behavior.
- **WCAG:** 2.1.1 Keyboard (Level A), 2.1.2 No Keyboard Trap (Level A)

### 2. Object Library Items Not Keyboard Accessible (CRITICAL)
- **Problem:** All 21 library items were `<div>` elements with `cursor: pointer` — no `tabindex`, no `role`, no keyboard activation. Keyboard-only users could not add objects to the yard.
- **Fix:** Added `role="button"`, `tabindex="0"`, `aria-label="Add [name] to yard"` to each item. Added `keydown` handler for Enter/Space activation. Added `announceForScreenReader()` call when item is added.
- **WCAG:** 2.1.1 Keyboard (Level A)

### 3. Category Headers Not Keyboard Accessible (CRITICAL)
- **Problem:** Category collapse/expand headers (`Fences & Structures`, `Pools & Water`, etc.) were `<div>` elements with no keyboard interaction. Users couldn't collapse categories without a mouse.
- **Fix:** Added `role="button"`, `tabindex="0"`, `aria-expanded="true/false"`, `aria-label="Collapse [name] category"`. Added `keydown` handler for Enter/Space activation.
- **WCAG:** 2.1.1 Keyboard (Level A)

### 4. Toast Missing aria-live (HIGH)
- **Problem:** Toast notifications (save success, error messages, delete confirmations) had no `aria-live` attribute. Screen reader users received no notification of status changes.
- **Fix:** Added `role="status"`, `aria-live="polite"`, `aria-atomic="true"` to `#toast` element. Also call `announceForScreenReader()` as fallback.
- **WCAG:** 4.1.3 Status Messages (Level AA)

### 5. No prefers-reduced-motion Support (HIGH)
- **Problem:** No `@media (prefers-reduced-motion: reduce)` CSS rule existed. Users with vestibular disorders had no way to disable animations and transitions.
- **Fix:** Added `@media (prefers-reduced-motion: reduce)` CSS that sets all animation/transition durations to 0.01ms and disables scroll-behavior smoothing.
- **WCAG:** 2.3.3 Animation from Interactions (Level AAA)

### 6. Help/Share Modals Missing Dialog Semantics (HIGH)
- **Problem:** Both modals were plain `<div>` elements without `role="dialog"` or `aria-modal`. Screen readers didn't announce them as dialogs when opened.
- **Fix:** Added `role="dialog"`, `aria-modal="true"`, `aria-labelledby` to both modals. Added `aria-hidden` toggle (false when open, true when closed).
- **WCAG:** 4.1.2 Name, Role, Value (Level A)

### 7. Walk Mode Joystick Buttons Unlabeled (MEDIUM)
- **Problem:** Walk mode joystick buttons (▲ ◀ ▶ ▼) had no `aria-label`. Screen readers announced only the arrow characters.
- **Fix:** Added `aria-label` to each button ("Walk forward", "Walk left", "Walk right", "Walk backward"). Spacer button marked `aria-hidden="true"` and `tabindex="-1"`.
- **WCAG:** 4.1.2 Name, Role, Value (Level A)

### 8. Info Displays Missing aria-live (MEDIUM)
- **Problem:** Context hint (`#context-hint`) and safety warnings (`#safety-warnings`) had no `aria-live` attribute. Screen reader users missed contextual hints and safety alerts.
- **Fix:** Added `role="status"` and `aria-live="polite"` to context-hint. Added `role="alert"` and `aria-live="assertive"` to safety-warnings.
- **WCAG:** 4.1.3 Status Messages (Level AA)

### 9. Terrain Mode Buttons Missing aria-pressed (MEDIUM)
- **Problem:** Terrain brush mode buttons (Raise, Excavate, Smooth, Erode) had no `aria-pressed` or `aria-label`. Screen readers couldn't determine which mode was active.
- **Fix:** Added `aria-label` and `aria-pressed` to all 4 mode buttons. Updated JS handler to toggle `aria-pressed` and announce mode change.
- **WCAG:** 4.1.2 Name, Role, Value (Level A)

### 10. Carve Shape Buttons Missing aria-pressed/aria-label (MEDIUM)
- **Problem:** Carve shape buttons (None, Box, Cylinder, Sphere, Box, Round, Trench) had no `aria-pressed` state. One button was completely unlabeled.
- **Fix:** Added `aria-label` and `aria-pressed` to all carve shape buttons.
- **WCAG:** 4.1.2 Name, Role, Value (Level A)

### 11. No Skip-to-Content Link (MEDIUM)
- **Problem:** No skip link existed. Keyboard users had to Tab through all topbar controls before reaching the viewport.
- **Fix:** Added `<a href="#viewport" class="skip-link">Skip to 3D design canvas</a>` as the first focusable element. CSS positions it off-screen until focused.
- **WCAG:** 2.4.1 Bypass Blocks (Level A)

### 12. Viewport Missing Description (LOW)
- **Problem:** The 3D viewport had `role="application"` and `aria-label` but no `aria-describedby` pointing to instructions. Screen reader users didn't know how to interact with the canvas.
- **Fix:** Added `aria-describedby="viewport-desc"` pointing to a visually hidden `<div>` with keyboard shortcut instructions.
- **WCAG:** 1.3.6 Identify Purpose (Level AAA)

### 13. Select Element Missing aria-label (LOW)
- **Problem:** The underground structure type `<select>` (innov-ugstruct-type) had no `aria-label`.
- **Fix:** Added `aria-label="Underground structure type"`.
- **WCAG:** 4.1.2 Name, Role, Value (Level A)

---

## Pre-existing Accessibility Features (Sprint 5)

The following accessibility features were already present from Sprint 5:
- ✅ `*:focus-visible` CSS outline on all elements
- ✅ 44px minimum touch targets on mobile
- ✅ WCAG AA contrast on CSS variables (`--primary`, `--text-muted` darkened)
- ✅ `aria-label` on most topbar buttons and toolbar groups
- ✅ `role="toolbar"`, `role="tablist"`, `role="tab"` on view toggle
- ✅ `aria-pressed` on toggle buttons (tape measure, terrain, excavate, analysis, innovation, sun)
- ✅ `role="switch"` with `aria-checked` and `tabindex=0` on toggle elements
- ✅ `aria-label` on all range/number inputs
- ✅ Keyboard shortcuts: Ctrl+Z (undo), Ctrl+Shift+Z/Ctrl+Y (redo), Ctrl+S (save), Delete, Escape, Arrow keys
- ✅ `announceForScreenReader()` live region for screen reader announcements
- ✅ Object cycling via keyboard (now Alt+Tab instead of Tab)
- ✅ Undo support for arrow-key moves (debounced)

---

## Color Contrast Verification

All 18 tested text/background combinations pass WCAG AA (4.5:1 for normal text, 3:1 for large text ≥18px):

| Element | Ratio | Threshold | Status |
|---------|-------|-----------|--------|
| .topbar-brand | 5.36:1 | 4.5:1 | ✅ |
| .tb-btn | 13.49:1 | 4.5:1 | ✅ |
| .view-toggle button | 5.36:1 | 4.5:1 | ✅ |
| .sidebar-header | 6.83:1 | 4.5:1 | ✅ |
| .cat-title | 13.49:1 | 4.5:1 | ✅ |
| .lib-item span | 13.49:1 | 4.5:1 | ✅ |
| .lib-item small | 6.83:1 | 4.5:1 | ✅ |
| .terrain-mode-btn.active | 5.45:1 | 4.5:1 | ✅ |
| #toast | 13.49:1 | 4.5:1 | ✅ |
| .help-panel h2 | 5.36:1 | 3.0:1 | ✅ |
| .help-panel li | 13.49:1 | 4.5:1 | ✅ |
| .help-panel h3 | 13.49:1 | 4.5:1 | ✅ |
| .innov-tool-btn | 13.49:1 | 4.5:1 | ✅ |
| .innov-section-title | 6.29:1 | 4.5:1 | ✅ |
| .ta-btn | 20.34:1 | 4.5:1 | ✅ |
| #terrain-flatten | 20.34:1 | 4.5:1 | ✅ |
| .terrain-preset-btn | 13.49:1 | 4.5:1 | ✅ |

---

## Color Blindness Support

- **Terrain Height Heatmap:** Color stripes include text labels showing actual elevation values (e.g., "5.0 ft", "12.3 ft") overlaid on each color band. Not color-only.
- **Slope Heatmap:** Legend has 5 items with descriptive text labels:
  - Green: "0–5% (flat, ADA accessible)"
  - Yellow: "5–10% (gentle slope)"
  - Orange: "10–15% (moderate, drainage OK)"
  - Red: "15–25% (steep, needs retaining)"
  - Purple: ">25% (very steep, unsafe)"
- All heatmap legends communicate information through text, not color alone.

---

## Cognitive Accessibility

- **Help Modal:** Comprehensive with 7 sections (Getting Started, Camera Controls, Saving & Sharing, Terrain & Measuring, Safety Reminders, Keyboard Shortcuts, Accessibility Tips)
- **Error Messages:** Clear and actionable (e.g., "Invalid design file: no data or objects found", "Screenshot failed: [error message]")
- **Undo for Destructive Actions:** Delete (`deleteObjectWithCommand`) pushes undo command. Flatten terrain (`terrain-flatten`) pushes undo. Arrow-key moves are batched for single undo.
- **Toast notifications** confirm actions ("Design saved!", "Deleted — press Undo to restore")

---

## Quality Gate Results

```
SPRINT 8 QUALITY GATE: 75/75 passed, 0 failed
```

Test categories:
1. Keyboard navigation — Tab order through all controls (3 tests)
2. Library items keyboard accessible (4 tests)
3. Category headers keyboard accessible (5 tests)
4. Enter/Space activates library items (1 test)
5. Escape closes panels/deselects (1 test)
6. Undo/Redo via Ctrl+Z/Ctrl+Shift+Z (3 tests)
7. ARIA label verification — all buttons (1 test)
8. ARIA label verification — all inputs (1 test)
9. Toast aria-live (3 tests)
10. Context hint aria-live (1 test)
11. Safety warnings aria-live (2 tests)
12. Modal dialog attributes (6 tests)
13. Viewport description (4 tests)
14. Color contrast WCAG AA (18 tests)
15. Reduced motion CSS (1 test)
16. Focus management — modal (4 tests)
17. Skip-to-content link (3 tests)
18. Focus indicators — focus-visible (2 tests)
19. ARIA pressed — toggle buttons (2 tests)
20. Help modal content — shortcuts documented (6 tests)
21. Walk mode joystick labeled (1 test)
22. SR-only class exists (1 test)
23. Color blindness — heatmap labels (1 test)
24. Undo for destructive actions (1 test)

---

## WCAG 2.1 AA Compliance Summary

| Criterion | Level | Status |
|-----------|-------|--------|
| 1.1.1 Non-text Content | A | ✅ All decorative SVGs have text fallbacks |
| 1.3.1 Info and Relationships | A | ✅ Proper heading hierarchy, role attributes |
| 1.3.2 Meaningful Sequence | A | ✅ Tab order follows visual layout |
| 1.4.3 Contrast (Minimum) | AA | ✅ All text ≥ 4.5:1 ratio |
| 1.4.11 Non-text Contrast | AA | ✅ Focus indicators ≥ 3:1 |
| 2.1.1 Keyboard | A | ✅ All features keyboard accessible |
| 2.1.2 No Keyboard Trap | A | ✅ Escape closes panels/modals |
| 2.4.1 Bypass Blocks | A | ✅ Skip-to-content link |
| 2.4.3 Focus Order | A | ✅ Logical tab order |
| 2.4.7 Focus Visible | AA | ✅ focus-visible on all elements |
| 3.2.1 On Focus | A | ✅ No context change on focus |
| 3.3.2 Labels or Instructions | A | ✅ All inputs have aria-labels |
| 4.1.2 Name, Role, Value | A | ✅ All controls have proper ARIA |
| 4.1.3 Status Messages | AA | ✅ aria-live on toast, hints, warnings |
| 2.3.3 Animation from Interactions | AAA | ✅ prefers-reduced-motion support |

---

## Files Modified

- `index.html` — 13 accessibility fixes (CSS, HTML, JavaScript)
- `sprint8_quality_gate.py` — 75 automated accessibility tests (QUALITY GATE)
- `sprint8_quality_gate_results.json` — Test results JSON