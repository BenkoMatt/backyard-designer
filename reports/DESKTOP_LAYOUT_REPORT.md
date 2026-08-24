# Sprint 16 — Desktop-Only Layout Report

## Agent 1: Desktop-Only Layout

### Summary
Converted Backyard Designer 3D from a responsive (desktop + mobile) layout to a **desktop-only** layout. All responsive/mobile CSS breakpoints removed, mobile UI elements stripped, and a desktop gate notice added for small screens.

### Changes Made

#### 1. Desktop Gate (NEW)
- Added `#desktop-gate` div as the first element inside `<body>`
- Full-screen overlay (position:fixed, inset:0, background:white, z-index:99999)
- Shows "Backyard Designer 3D is optimized for desktop use. Please open this on a computer for the best experience."
- JS: `_updateDesktopGate()` function checks `window.innerWidth < 900` and shows/hides gate
- Resize listener attached for dynamic response
- **CSS:** Added `#desktop-gate` styles (display:none default, .visible class shows flex)

#### 2. @media (max-width/max-height) Blocks Removed
- **14 @media blocks removed** (all max-width/max-height based)
- Blocks were at original lines: 227, 341, 427, 495, 516, 538, 769, 829, 843, 868, 885, 1273, 1442, 3277 (template literal)
- **4 @media blocks kept** (non-responsive):
  - `@media print` (line 934 → now 677) — print view styles
  - `@media (prefers-reduced-motion: reduce)` × 3 — accessibility styles

#### 3. body.is-mobile Class System Removed
- **21 CSS selectors** starting with `body.is-mobile` removed
- JS line `if (IS_MOBILE) document.body.classList.add('is-mobile');` removed
- `IS_MOBILE` constant changed from UA detection to `const IS_MOBILE = false;`
- All `IS_MOBILE` references remain but evaluate to `false` (no functional impact)

#### 4. mobile-lib-toggle Removed
- HTML `<button id="mobile-lib-toggle">` element removed
- All CSS rules for `#mobile-lib-toggle` removed
- JS `setupMobileLibToggle()` IIFE removed (19 lines)

#### 5. mobile-props-sheet and mobile-action-bar Removed
- HTML block for `<div id="mobile-props-sheet">` removed (23 lines, included sheet-grabber, sheet-header, sheet-body, mobile-action-bar with mab-duplicate/rotate/delete/close buttons)
- All CSS rules for `#mobile-props-sheet`, `#mobile-action-bar`, `.mab-btn` removed
- `#mobile-props-sheet` removed from content-visibility CSS rule
- `#mobile-props-sheet`, `#mobile-lib-toggle` removed from transition CSS rule
- JS references cleaned up:
  - `mobileSheetEl`, `mobilePropsHeader`, `mobilePropsBody`, `mobileActionBar` const declarations removed
  - `showProperties()` simplified to desktop-only path (no isMob conditional)
  - `hideProperties()` simplified to remove mobile element references
  - `setupMobileSheet()` IIFE removed (33 lines)

#### 6. Mobile CSS Injection Block Removed
- JS block that injected mobile-specific CSS via `<style>` tag (13 lines)
- Only ran when `IS_MOBILE` was true, so already a no-op after IS_MOBILE=false

#### 7. Mobile Topbar Scroll Indicator Removed
- JS IIFE for mobile topbar scroll gradient indicator removed (26 lines)
- Only relevant for mobile overflow scrolling

#### 8. Tool Dock Labels — Always Visible ✓
- `.td-tab .td-label { font-weight: 600; font-size: 11px; }` — no `display:none` override
- The mobile CSS that hid labels (`.td-tab .td-label { display: none; }` inside @media max-width:768px) was removed
- Verified: 7 labels visible at desktop width, first label "Terrain" with display:block

### Testing Results

#### Playwright Tests (1280×800 desktop)
- ✓ Desktop gate display: **none** (hidden at desktop width)
- ✓ Tool dock labels: **7 visible**, first label "Terrain" display:block, font-size:11px, font-weight:600
- ✓ Body is-mobile class: **false** (not applied)
- ✓ mobile-lib-toggle: **removed** (not in DOM)
- ✓ mobile-props-sheet: **removed** (not in DOM)
- ✓ mobile-action-bar: **removed** (not in DOM)
- ✓ JS errors: **none**
- ✓ Canvas (WebGL): **present**
- ✓ Core UI elements: topbar, sidebar, viewport, tool-dock all present

#### Playwright Tests (800×600 small screen)
- ✓ Desktop gate display: **flex** (visible at small width)
- ✓ Gate text: "🖥️ Desktop Recommended — Backyard Designer 3D is optimized for desktop use..."

#### Sprint 15 Quality Gate
- 20 tests passed, 0 failed, 10 errors (pre-existing "no test obj" eval failures — identical to pre-change results)
- **No regressions introduced**

### File Statistics
- **Before:** 16,772 lines
- **After:** 16,353 lines
- **Lines removed:** 419 lines (mobile/responsive code)
- **Lines added:** ~30 lines (desktop gate HTML, CSS, JS)

### Commits
See `git log --oneline` for commit history.