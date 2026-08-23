# Sprint 8 — Discovery Log
## Backyard Designer 3D — Accessibility & Usability Review

**Agent:** Agent 4 (Critic) — Accessibility Usability Reviewer  
**Date:** August 23, 2026  
**Working Directory:** `/root/byd8-a11y-usability/`

---

## Setup

- Cloned working copy at `/root/byd8-a11y-usability/` (11,748 lines)
- Started HTTP server on port 8741
- Playwright + chromium available for automated testing
- Read FEATURE_INVENTORY.md for control IDs

---

## Discoveries

### DISC-001: Tab key intercepted globally (CRITICAL)
- **When:** Initial keyboard testing
- **What:** `document.addEventListener('keydown', ...)` at line 4504 called `e.preventDefault()` on Tab key to cycle through objects. This prevented normal Tab navigation between controls — focus was stuck on the terrain button.
- **Impact:** Keyboard-only users could not navigate the app. WCAG 2.1.1 violation.
- **Fix:** Changed `e.key === 'Tab'` to `e.key === 'Tab' && e.altKey` — object cycling now uses Alt+Tab. Tab performs default browser behavior.
- **File:** index.html line 4519

### DISC-002: Library items are div elements with no keyboard access (CRITICAL)
- **When:** Playwright focusable elements audit
- **What:** All 21 object library items (`.lib-item`) were `<div>` elements with `cursor: pointer` — no `tabindex`, no `role`, no keyboard event handlers.
- **Impact:** Keyboard-only users could not add objects to the yard. WCAG 2.1.1 violation.
- **Fix:** Added `role="button"`, `tabindex="0"`, `aria-label="Add [name] to yard"`. Added keydown handler for Enter/Space. Added `announceForScreenReader()` call.
- **File:** index.html buildLibrary() function (line 4205)

### DISC-003: Category headers not keyboard accessible (CRITICAL)
- **When:** Playwright focusable elements audit
- **What:** 5 category collapse headers (`.cat-title`) were `<div>` elements with click handler only. No keyboard activation, no `aria-expanded`.
- **Impact:** Keyboard users couldn't collapse/expand categories. WCAG 2.1.1 violation.
- **Fix:** Added `role="button"`, `tabindex="0"`, `aria-expanded`, `aria-label`. Added keydown handler and aria-expanded toggle in click handler.
- **File:** index.html buildLibrary() function

### DISC-004: Toast missing aria-live (HIGH)
- **When:** Initial screen reader compatibility test
- **What:** `#toast` div had no `aria-live` attribute. Screen reader users received no notification of save success, errors, or delete confirmations.
- **Impact:** WCAG 4.1.3 violation.
- **Fix:** Added `role="status"`, `aria-live="polite"`, `aria-atomic="true"`. Also added `announceForScreenReader()` call in `showToast()` as fallback.
- **File:** index.html line 1853

### DISC-005: No prefers-reduced-motion CSS (HIGH)
- **When:** CSS audit via Playwright
- **What:** No `@media (prefers-reduced-motion: reduce)` rule anywhere in the stylesheet.
- **Impact:** Users with vestibular disorders had no way to disable animations. WCAG 2.3.3 violation.
- **Fix:** Added `@media (prefers-reduced-motion: reduce)` block that disables all animations, transitions, and scroll-behavior smoothing.
- **File:** index.html CSS section

### DISC-006: Help/Share modals missing dialog semantics (HIGH)
- **When:** Modal accessibility test
- **What:** `#help-modal` and `#share-modal` were plain `<div>` elements. No `role="dialog"`, no `aria-modal`, no `aria-labelledby`.
- **Impact:** Screen readers didn't announce them as dialogs when opened. WCAG 4.1.2 violation.
- **Fix:** Added `role="dialog"`, `aria-modal="true"`, `aria-labelledby` to both. Added `aria-hidden` toggle. Added focus management (focus moves inside on open, returns to trigger on close).
- **File:** index.html lines 1816, 1856

### DISC-007: Walk mode joystick buttons unlabeled (MEDIUM)
- **When:** Playwright accessibility tree scan
- **What:** 4 walk mode joystick buttons had no `aria-label`. Screen readers would announce only "▲", "◀", "▶", "▼".
- **Impact:** WCAG 4.1.2 violation.
- **Fix:** Added `aria-label` to each button. Spacer button marked `aria-hidden="true"`, `tabindex="-1"`, `disabled`.
- **File:** index.html lines 1836-1843

### DISC-008: Info displays missing aria-live (MEDIUM)
- **When:** Screen reader compatibility test
- **What:** `#context-hint` and `#safety-warnings` had no `aria-live`. Contextual hints and safety alerts were not announced.
- **Impact:** WCAG 4.1.3 violation.
- **Fix:** Added `role="status"` and `aria-live="polite"` to context-hint. Added `role="alert"` and `aria-live="assertive"` to safety-warnings.
- **File:** index.html lines 1120, 1136

### DISC-009: Terrain mode buttons missing aria-pressed/aria-label (MEDIUM)
- **When:** Playwright accessibility tree scan
- **What:** 4 terrain mode buttons (Raise, Excavate, Smooth, Erode) had no `aria-pressed` state and no `aria-label`.
- **Impact:** Screen readers couldn't determine which mode was active. WCAG 4.1.2 violation.
- **Fix:** Added `aria-label` and `aria-pressed` to all 4 buttons. Updated JS handler to toggle `aria-pressed` and announce mode change.
- **File:** index.html lines 1194-1197, 4742-4750

### DISC-010: Carve shape buttons missing aria-pressed/aria-label (MEDIUM)
- **When:** Playwright accessibility tree scan
- **What:** 7 carve shape buttons had no `aria-pressed` state. One button was completely unlabeled.
- **Impact:** Screen readers couldn't determine which shape was active. WCAG 4.1.2 violation.
- **Fix:** Added `aria-label` and `aria-pressed` to all buttons.
- **File:** index.html lines 1259-1262, 1284-1295

### DISC-011: No skip-to-content link (MEDIUM)
- **When:** HTML structure audit
- **What:** No skip link existed. Keyboard users had to Tab through all topbar controls before reaching the viewport.
- **Impact:** WCAG 2.4.1 violation.
- **Fix:** Added `<a href="#viewport" class="skip-link">Skip to 3D design canvas</a>` as first body element.
- **File:** index.html body start

### DISC-012: Viewport missing description (LOW)
- **When:** Screen reader compatibility test
- **What:** Viewport had `role="application"` and `aria-label` but no `aria-describedby` pointing to interaction instructions.
- **Impact:** Screen reader users didn't know how to interact with the 3D canvas.
- **Fix:** Added `aria-describedby="viewport-desc"` and created sr-only description div with keyboard shortcuts.
- **File:** index.html

### DISC-013: Select element missing aria-label (LOW)
- **When:** Quality gate test run
- **What:** `#innov-ugstruct-type` `<select>` element had no `aria-label`.
- **Impact:** Screen readers couldn't identify the select's purpose. WCAG 4.1.2 violation.
- **Fix:** Added `aria-label="Underground structure type"`.
- **File:** index.html line 1664

### DISC-014: Terrain preset buttons missing aria-label (LOW)
- **When:** ARIA label audit
- **What:** 6 terrain preset buttons had visible text but no explicit `aria-label`.
- **Impact:** Screen readers would read the text, but adding aria-label provides clearer context.
- **Fix:** Added `aria-label="Apply [name] terrain preset"` to each button.
- **File:** index.html lines 1325-1330

---

## Pre-existing Features Verified

- All 20 toolbar/view-control buttons have aria-labels (Sprint 5)
- All range/number inputs have aria-labels (Sprint 5)
- `*:focus-visible` CSS outline exists (Sprint 5)
- 44px minimum touch targets on mobile (Sprint 5)
- WCAG AA contrast on CSS variables (Sprint 5)
- `role="switch"` with `aria-checked` and `tabindex=0` on 7 toggle elements (Sprint 5)
- `announceForScreenReader()` live region function (Sprint 5)
- Keyboard shortcuts: Ctrl+Z, Ctrl+Shift+Z/Ctrl+Y, Ctrl+S, Delete, Escape, Arrow keys (Sprint 5)
- Undo support for arrow-key moves with debouncing (Sprint 5)
- Object cycling via Alt+Tab (Sprint 8, was Tab in Sprint 5)
- Slope heatmap legend has text labels for color blindness (pre-existing)
- Height legend has elevation values as text labels (pre-existing)

---

## Quality Gate

- **Tests:** 75
- **Passing:** 75
- **Failing:** 0
- **Status:** ✅ PASS

Test file: `sprint8_quality_gate.py`  
Results: `sprint8_quality_gate_results.json`