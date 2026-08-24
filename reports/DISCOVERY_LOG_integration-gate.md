# Sprint 16 Discovery Log

## Date: August 24, 2026
## Agent: Agent 5 — Integration & Quality Gate Critic
## Working Copy: /root/byd16-integration-gate/

## Initial State

### File Info
- **File**: index.html
- **Lines**: 16,772 (initial) → 16,562 (after changes)
- **Size**: 724,181 bytes → ~710,574 bytes
- **Three.js**: v0.160.0 via importmap
- **Git HEAD**: 269de5d (Sprint 15 + UI fixes)

### Mobile Code Found

1. **@media blocks**: 18 total, 14 mobile-related (max-width/max-height)
   - Lines: 227, 341, 427, 495, 516, 538, 769, 829, 843, 868, 885, 1273, 1442, 3277
   - 4 non-mobile: @media print (934), @media prefers-reduced-motion (1239, 1450, 1825)

2. **Mobile HTML elements**:
   - `#mobile-lib-toggle` button (line 1998)
   - `#mobile-props-sheet` div with grabber, header, body, action bar (lines 2897-2919)
   - `#mobile-action-bar` with mab-duplicate, mab-rotate, mab-delete, mab-close buttons

3. **Mobile CSS**: ~75 lines of mobile-specific CSS (is-mobile selectors, mobile element styles)

4. **Mobile JS**:
   - `IS_MOBILE` detection: userAgent regex + innerWidth < 768 + maxTouchPoints
   - `if (IS_MOBILE) document.body.classList.add('is-mobile')`
   - Mobile CSS injection via dynamic `<style>` tag
   - Touch event handlers: 9 locations (walk mode, joystick, compare button)
   - IS_MOBILE conditional rendering: fog, shadows, pixel ratio, antialiasing

5. **Mobile references**: 124 lines containing "mobile", 23 "is-mobile" references

### Z-Index Hierarchy (Before)

Values used: 0, 1, 10, 11, 12, 15, 19, 20, 25, 45, 46, 47, 48, 49, 50, 51, 52, 55, 60, 65, 70, 100, 150, 200, 201, 210, 220, 230, 240, 241, 242, 250, 300, 500, 9999

### Layout Dimensions
- Sidebar width: 250px
- Properties panel width: 270px
- Dock panel min-width: 260px

### Key Code Locations
- IS_MOBILE definition: line 3247
- Mobile CSS injection: lines 3271-3309
- Touch handlers: lines 9095-9107, 9132-9133, 10389-10391
- Tool dock: line 2000 (HTML), line 157 (CSS)
- Terrain mode buttons: lines 2240-2247
- Terrain brush mode: `terrainBrushMode` variable (line 4253)
- Terrain brush size: `terrainBrushSize` variable (line 4254)

## Changes Made

### 1. Desktop-Only Layout
- Added `#desktop-gate` overlay CSS (position:fixed, z-index:9999, display:none, .visible class)
- Added `#desktop-gate` HTML element with desktop required message
- Added `setupDesktopGate()` IIFE that checks `window.innerWidth < 900`
- Removed all 14 mobile @media blocks
- Set `IS_MOBILE = false` (desktop-only)
- Removed `body.classList.add('is-mobile')` call

### 2. Mobile Code Removal
- Removed `#mobile-lib-toggle` button HTML
- Removed `#mobile-props-sheet` HTML block (grabber, header, body, action bar)
- Removed mobile CSS: ~75 lines of is-mobile selectors and mobile element styles
- Removed `setupMobileLibToggle()` IIFE
- Removed `setupMobileSheet()` IIFE (partially — had to clean orphaned code)
- Removed `mobileSheetEl`, `mobilePropsHeader`, `mobilePropsBody`, `mobileActionBar` variables
- Simplified `showProperties()` — removed isMob conditional, always uses desktop panel
- Removed `hideProperties()` mobile sheet references
- Removed touch event handlers (9 locations): walk mode, joystick, compare button
- Removed IS_MOBILE conditional rendering: fog, shadows, pixel ratio, antialiasing
- Removed mobile CSS injection block
- Removed `mobile-props-sheet` from content-visibility CSS list
- Removed mobile element references from transition CSS list

### 3. Z-Index Hierarchy Cleanup
- Established clean hierarchy: 1, 10, 15, 19, 20, 25, 30, 40, 50, 100, 150, 200, 500, 9999
- Remapped: 0→1, 11→10, 12→15, 45-49→50, 51-52→50, 55→50, 60→50, 65→50, 70→50, 201-300→200
- Status bar: z-index:30
- Terrain height legend: z-index:40

### 4. Desktop UX Polish
- **Wider panels**: sidebar 250→280px, properties 270→320px, dock panel min-width 260→320px
- **Tool dock labels**: Always visible (removed display:none from mobile @media)
- **Status bar**: Added #status-bar with tool name, brush size, height, FPS
- **Keyboard shortcuts**: 1-6 for brush modes (raise/lower/smooth/erode/flatten/dig), [/] for brush size, X for terrain toggle
- **Cursor feedback**: crosshair when terrain mode active, grab/grabbing for object interaction

### 5. Bug Fixes During Integration
- Fixed missing `<script type="module">` tag (was lost during IS_MOBILE replacement)
- Restored `import * as THREE` and `import { OrbitControls }` statements
- Restored `getCachedGeo` function declaration
- Restored `SHADOW_MAP_SIZE` variable declaration
- Restored `PIXEL_RATIO` constant
- Fixed orphaned code from `setupMobileSheet` removal (top-level return statements)
- Restored `#share-modal` HTML (was accidentally removed with mobile-props-sheet)
- Fixed duplicate `bodyEl` declaration in `showProperties()`

## Quality Gate Results

### Sprint 16 Quality Gate: 32/32 PASS
- 17 static tests (CSS, HTML, z-index, keyboard shortcuts, etc.)
- 15 browser tests (desktop gate, status bar, keyboard shortcuts, FPS, etc.)

### Existing Quality Gates
- Sprint 12: 41/41 PASS
- Sprint 13: 34/34 PASS
- Sprint 14: 41/41 PASS
- Sprint 15: 52/52 PASS
- Sprint 6, 8, 9, 11: Infrastructure issues (Playwright EPIPE crashes), not code failures