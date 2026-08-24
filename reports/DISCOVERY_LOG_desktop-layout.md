# Sprint 16 — Discovery Log

## Agent 1: Desktop-Only Layout — Discovery Log

### Initial File Analysis
- **File:** `/root/byd16-desktop-layout/index.html`
- **Original line count:** 16,772 lines
- **File size:** 724,181 bytes
- **Git:** Initialized, working copy in `/root/byd16-desktop-layout/`

### Discovery: @media Blocks
Found **18 total @media blocks** in the file:

**14 max-width/max-height blocks (REMOVED):**
| Line | Query | Content |
|------|-------|---------|
| 227 | `max-width: 768px` | sculpt-restore-pill mobile sizing |
| 341 | `max-width: 768px` | terrain controls mobile layout (22 lines) |
| 427 | `max-width: 768px` | excavate/cross-section mobile positioning |
| 495 | `max-width: 768px, (max-height: 500px) and (max-width: 900px)` | sidebar hide on mobile |
| 516 | `max-width: 768px` | sidebar + mobile-lib-toggle + properties mobile |
| 538 | `max-width: 768px` | mobile-props-sheet + mobile-action-bar CSS (49 lines) |
| 769 | `max-width: 768px` | innovation panel mobile positioning |
| 829 | `max-width: 768px` | grid-level, depth-gauge, excavate mobile sizing |
| 843 | `max-width: 768px` | tool-dock mobile (labels hidden), topbar mobile scroll |
| 868 | `max-width: 768px and max-height: 500px` | landscape mobile compact |
| 885 | `max-width: 768px` | button min-height 44px touch targets |
| 1273 | `max-width: 768px` | mobile usability fixes (view controls, library, panels) |
| 1442 | `max-width: 600px` | onboarding/welcome panel mobile |
| 3277 | `max-width: 768px` | JS-injected mobile CSS (template literal inside IS_MOBILE block) |

**4 blocks KEPT (non-responsive):**
| Line | Query | Purpose |
|------|-------|---------|
| 934 | `@media print` | Print view styles |
| 1239 | `prefers-reduced-motion: reduce` | Accessibility — disable animations |
| 1450 | `prefers-reduced-motion: reduce` | Accessibility — onboarding animations |
| 1825 | `prefers-reduced-motion: reduce` | Accessibility — Sprint 9 micro-interactions |

### Discovery: body.is-mobile System
- **IS_MOBILE detection:** Line 3247 — UA regex + innerWidth < 768 + touchPoints check
- **Class application:** Line 3248 — `if (IS_MOBILE) document.body.classList.add('is-mobile');`
- **CSS selectors:** 21 selectors starting with `body.is-mobile` (lines 496-631)
- **IS_MOBILE usage:** 26 references throughout the JS (all now evaluate to `false`)

### Discovery: mobile-lib-toggle
- **HTML:** Line 1998 — `<button id="mobile-lib-toggle">+</button>`
- **CSS:** 4 locations:
  - Line 494: `#mobile-lib-toggle { display: none; }` (default hidden)
  - Lines 499-514: `body.is-mobile #mobile-lib-toggle { ... }` (mobile styled)
  - Lines 519-534: `#mobile-lib-toggle { ... }` (inside @media block)
  - Line 878: inside landscape mobile @media block
  - Lines 1560-1561: in transition CSS rule
- **JS:** `setupMobileLibToggle()` IIFE at line 9274 (19 lines)

### Discovery: mobile-props-sheet & mobile-action-bar
- **HTML:** Lines 2897-2918 — full mobile props sheet with grabber, header, body, action bar (4 mab buttons)
- **CSS:** ~95 lines across:
  - Lines 537-587: `#mobile-props-sheet`, `#mobile-action-bar` default + @media styles
  - Lines 589-631: `body.is-mobile #mobile-props-sheet` and `body.is-mobile #mobile-action-bar` styles
  - Lines 632-637: `.mab-btn` styles
  - Line 1026: in content-visibility CSS rule
  - Line 1312: in PERF content-visibility rule
  - Lines 1560-1561: in transition CSS rule
- **JS:**
  - Lines 5294-5297: `mobileSheetEl`, `mobilePropsHeader`, `mobilePropsBody`, `mobileActionBar` declarations
  - Lines 5303-5310: `showProperties()` isMob conditional logic
  - Lines 5458-5465: `hideProperties()` mobile cleanup
  - Lines 8546-8578: `setupMobileSheet()` IIFE (33 lines)

### Discovery: JS Mobile CSS Injection
- Lines 3271-3309: `if (IS_MOBILE) { ... }` block that creates a `<style>` element with mobile CSS
- The template literal contained a duplicate of the mobile usability CSS from lines 1273-1301
- The @media block inside the template was already removed by our @media removal step, leaving an empty template

### Discovery: Mobile Topbar Scroll Indicator
- Lines 3311-3336: IIFE that adds scroll indicator to topbar (gradient fade when buttons overflow)
- Only useful for mobile horizontal scrolling, removed for desktop-only

### Discovery: Tool Dock Labels
- `.td-tab .td-label { font-weight: 600; font-size: 11px; }` at line 174 (CSS)
- The mobile override `.td-tab .td-label { display: none; }` was inside @media max-width:768px at line 846
- After removing the @media block, labels remain visible by default — **confirmed working**

### Discovery: IS_MOBILE References
26 total references to `IS_MOBILE` in JS:
- 1 declaration (now `false`)
- 3 performance/quality settings (PIXEL_RATIO, SHADOW_MAP_SIZE, shadowEnabled)
- 3 renderer settings (fog, antialias, pixelRatio, shadow map type)
- 4 touch handler guards (onTouchPointerDown/Move/Up, terrain events)
- 3 pointer event guards (onPointerDown/Move/Up)
- 2 walk mode mobile hints
- 2 fog distance updates
- 1 controls.touches configuration
- 1 small-screen pixel ratio reduction
- All evaluate to `false`/no-op since `IS_MOBILE = false`

### Final File Statistics
- **Original:** 16,772 lines (724,181 bytes)
- **Final:** 16,353 lines
- **Net reduction:** 419 lines
- **Lines removed:** ~449 (mobile CSS, HTML, JS)
- **Lines added:** ~30 (desktop gate HTML, CSS, JS)