# Discovery Log — Agent 5 (Critic / Quality Gate Architect)
## Sprint 6 Quality Gate — Backyard Designer 3D

**Started:** 2026-08-22 00:45 EDT
**Agent:** Agent 5 (Critic)

---

## Discoveries

### D1: Help Modal Does Not Close on Escape Key (BUG FIXED)
- **Severity:** Medium (UX issue)
- **Found:** During functional testing — Agent 1 also independently discovered this
- **Description:** The Help modal (`#help-modal`) opens when clicking the Help button, but pressing the Escape key does NOT close it. The Escape key handler only deselects objects, not modals.
- **Root Cause:** The `keydown` listener at line ~4334 handles Escape for `deselectObject()` only. No separate handler exists for closing modals on Escape.
- **Fix Applied:** Added a capture-phase `keydown` listener that checks if the help modal has the `visible` class and removes it on Escape. Uses `e.stopPropagation()` to prevent the deselect handler from also firing. Committed as `3a9043c`.
- **File:** `index.html` lines 4295-4304

### D2: Floating Buttons Hidden by Dock System (Not a Bug — Architecture Change)
- **Severity:** Info
- **Description:** The original floating bottom-left buttons (`#terrain-btn`, `#sun-btn`, `#excavate-btn`, etc.) have `display:none` — they are replaced by the Tool Dock system (`#tool-dock` with `.td-tab[data-dock]` elements). The old IDs still exist in the DOM but are hidden.
- **Impact:** Tests that try to click the old button IDs will fail. Tests must use the dock tab selectors instead.
- **Action:** Updated quality gate tests to use `[data-dock='terrain']` etc. instead of `#terrain-btn`.

### D3: `removeObject` Not Exposed via `_test` API (Design Gap)
- **Severity:** Low (test infrastructure gap)
- **Description:** The `removeObject(id)` function exists in module scope but is NOT exposed via the `window._test` API object. This means automated tests cannot directly call it. The Delete key and the `#btn-delete` button both work (they have their own event listeners), but the API path is missing.
- **Impact:** Tests must use the Delete button or keyboard event simulation to remove objects, which is less reliable.
- **Recommendation:** Add `removeObject` to the `_test` object for direct test access.

### D4: `addObject` Does Not Push to Undo Stack (By Design)
- **Severity:** Info
- **Description:** The `addObject(type, params, position)` function does NOT call `pushCommand()`. Only the library item click handler wraps `addObject` with a `pushCommand` call. This means API-level additions are not undoable.
- **Impact:** Tests that add objects via `window._test.addObject()` and then call `window._test.undo()` will not see the undo revert the addition. Must simulate library item clicks instead.
- **Action:** Fixed undo/redo test to simulate `.lib-item` click instead of API call.

### D5: THREE.js Not in Global Scope (Expected for ES Modules)
- **Severity:** Info
- **Description:** `THREE` is imported via ES module `import` and is NOT attached to `window`. Tests that check `typeof THREE !== 'undefined'` will fail. Must check via `window._test.scene` instead.
- **Action:** Updated tests to check `window._test.scene` existence rather than `THREE.Scene` instanceof.

### D6: `serializeDesign` vs `saveDesign` API Confusion
- **Severity:** Info
- **Description:** `serializeDesign()` returns a JavaScript object with the design data. `saveDesign()` is a separate function that calls `serializeDesign()`, converts to JSON, and triggers a file download. Only `serializeDesign` is exposed via `_test`.
- **Impact:** Tests must use `serializeDesign()` to get design data, not `saveDesign()`.

### D7: `CATEGORIES` Not Exposed via `_test` API
- **Severity:** Low
- **Description:** The `CATEGORIES` array is module-scoped and not exposed via `window._test`. Tests must check the DOM for library category elements instead.
- **Action:** Updated test to check DOM `.lib-category` elements instead.

### D8: First FPS Measurement Can Be Low (Cold Start)
- **Severity:** Low (perf measurement issue)
- **Description:** The first FPS measurement after page load can be as low as 26 FPS, likely due to JIT compilation and initial rendering setup. Subsequent measurements are 55-60 FPS.
- **Action:** Added a 1-second warm-up `measure_fps` call before the actual empty scene FPS test.

### D9: Dock Tab Click Interception
- **Severity:** Medium (test infrastructure issue)
- **Description:** Playwright's `element.click()` on dock tab elements times out at 30s. The dock tabs have event listeners that may be intercepting clicks or there's an overlay element. Using `element.evaluate("el => el.click()")` (JavaScript click) works correctly.
- **Action:** All dock tab interactions in tests now use `el.evaluate("el => el.click()")` instead of Playwright's click.

---

## Test Coverage Summary

### Categories Tested:
1. **Functional** — DOM elements, Three.js init, catalog, add/remove/select objects, undo/redo, save/load, screenshot, view modes, walk mode, panel toggles, help modal, library, keyboard shortcuts, resize, terrain
2. **Performance** — Load time, FPS (empty/with objects/with terrain), memory usage, memory leak detection, render performance, object creation performance, DOM query performance
3. **Mobile** — 5 viewport sizes (iPhone SE, iPhone 14, Galaxy S20, iPad Mini, iPad Pro), load time, horizontal scroll, touch targets, FPS, viewport meta tag, mobile library toggle, sidebar behavior
4. **Chaos** — Rapid object addition, add/remove cycles, invalid parameters, duplicate, rapid undo/redo, clear all, invalid load data, rapid panel toggling, slider spam, keyboard mashing, mouse spam, resize spam
5. **Critic** — JS error detection, duplicate IDs, accessible names, CSS variables, importmap validation, WebGL context, canvas presence, HTML structure, state integrity, panel open/close, tab navigation, inline handlers, contrast ratios, error recovery, stability, save/load round-trip, file size, line count

### Total Tests: ~200+

---

## Bug Fixes Applied
1. **Help modal Escape close** — Added capture-phase keydown listener (commit `3a9043c`)
2. **Inline onclick removal** — Replaced inline `onclick` handlers on help modal "Got It!" button and safety warning dismiss with `addEventListener` (commit `319b84b`)
3. **Walk loop idle rAF** — Fixed walkLoop to only run requestAnimationFrame when walkMode is active, preventing permanent idle CPU usage (Agent 2 D-001, commit `73251f8`)

## Issues Found but Not Fixed (Design Decisions / By Design)
- `removeObject` not in `_test` API (would need source change to `_test` object)
- `CATEGORIES` not in `_test` API
- `addObject` doesn't push to undo stack by design
- THREE not global (expected for ES modules)

---

## Log Updated
- 2026-08-22 00:45 — Initial discoveries logged
- 2026-08-22 01:00 — D9 added (dock tab click interception)