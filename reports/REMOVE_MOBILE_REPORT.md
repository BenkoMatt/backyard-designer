# REMOVE MOBILE REPORT — Sprint 16 Agent 4

## Summary
Stripped all mobile features from Backyard Designer 3D, converting the codebase to desktop-only use. Removed touch event handlers, mobile detection JS, mobile-specific HTML/CSS, and mobile-only JS functions while preserving all mouse/keyboard handlers and accessibility features.

## Changes Made

### 1. Touch Event Handlers Removed
- Walk mode canvas touchstart/touchmove/touchend (3 listeners)
- Walk joystick button touchstart/touchend (2 listeners)
- Terrain compare button touchstart/touchend/touchcancel (3 listeners)
- 'touchstart' removed from inactivity reset array

### 2. Mobile Detection JS Removed
- `const IS_MOBILE = /Android|webOS|iPhone|.../i.test(navigator.userAgent) || ...` — userAgent/width/touchPoints detection
- `if (IS_MOBILE) document.body.classList.add('is-mobile')` — body class injection
- Mobile CSS injection block (IS_MOBILE conditional that injected `<style id="mobile-usability-css">`)
- `setAppHeight()` function and `orientationchange` listener — mobile viewport height workaround
- All 19 IS_MOBILE references replaced with desktop defaults or removed

### 3. Mobile-specific HTML Elements Removed
- `<button id="mobile-lib-toggle">` — mobile library toggle FAB
- `<div id="mobile-props-sheet">` — entire mobile bottom sheet (grabber, header, body, action bar with 4 mab buttons)
- `<div id="walk-hint-mobile">` — mobile walk mode hint text
- `<button id="walk-motion-btn">` — device orientation toggle button

### 4. Mobile-specific CSS Removed
- All `body.is-mobile` selector rules (22 selectors)
- All `#mobile-props-sheet` standalone CSS rules (including .sheet-grabber, .sheet-header, .sheet-body sub-selectors)
- `#mobile-action-bar` CSS rules
- `#mobile-lib-toggle` CSS rules
- `.mab-btn` CSS rules
- `#walk-motion-btn` CSS rules
- `#walk-hint-mobile` CSS rules
- `#sidebar.mobile-visible` CSS rules
- 14 `@media (max-width: 768px)` blocks
- 1 `@media (max-width: 600px)` block
- 1 `@media (max-width: 768px) and (max-height: 500px)` block
- `* { -webkit-tap-highlight-color: transparent; }` — mobile tap highlight
- `touch-action: none` on #viewport, #viewport canvas, .walk-joy-btn
- `overscroll-behavior: none` on html/body
- `--app-height: 100vh` CSS variable and `height: 100dvh` / `height: var(--app-height)` mobile viewport height workaround
- `#mobile-props-sheet` and `#mobile-lib-toggle` from content-visibility and transition CSS rule lists

### 5. Mobile-only JS Functions Removed
- Touch state variables: `TAP_DURATION_MS`, `TAP_MOVEMENT_THRESHOLD`, `TOUCH_DRAG_THRESHOLD`, `LONG_PRESS_MS`, `LONG_PRESS_THRESHOLD`, `touchState` object
- `_getMeshesForRaycast()` — touch raycast helper
- `_raycastFromScreenPoint()` — touch raycast helper
- `onTouchPointerDown()`, `onTouchPointerMove()`, `onTouchPointerUp()` — touch gesture handlers
- `_attachTouchGestureHandlers()` — touch listener attachment function and its call
- `_showMobileContextMenu()` — mobile context menu creation
- `setupMobileSheet()` IIFE — mobile sheet grabber and action bar button handlers
- `setupMobileLibToggle()` IIFE — mobile library toggle handler
- `onWalkDeviceOrient()` — device orientation handler
- Walk motion button click handler (DeviceOrientationEvent.requestPermission)
- `mobileSheetEl`, `mobilePropsHeader`, `mobilePropsBody`, `mobileActionBar` DOM references
- Mobile-specific showProperties/hideProperties branching (simplified to desktop-only)
- `_getTerrainEventPoint()` touch offset code (simplified to direct call)
- Terrain pointerdown/pointermove mobile touch offset code

### 6. Viewport Meta Tag
- Replaced `width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=5.0` with `width=1280`

### 7. IS_MOBILE References in Rendering Code
- `shadowEnabled: !IS_MOBILE` → `shadowEnabled: true`
- Fog near/far: `IS_MOBILE ? 80 : 100` / `IS_MOBILE ? 300 : 500` → `100` / `500`
- `antialias: !IS_MOBILE` → `antialias: true`
- Pixel ratio: `IS_MOBILE ? 1 : 1.5` → `1.5`
- Shadow map type: `IS_MOBILE ? THREE.BasicShadowMap : THREE.PCFSoftShadowMap` → `THREE.PCFSoftShadowMap`
- Shadow map size: `IS_MOBILE ? 1024 : ...` → desktop sizing
- OrbitControls touch configuration block removed
- Mobile pixel ratio reduction for small screens removed
- `PIXEL_RATIO = Math.min(window.devicePixelRatio, IS_MOBILE ? 1 : 2)` → `Math.min(window.devicePixelRatio, 2)`
- `SHADOW_MAP_SIZE = IS_MOBILE ? 1024 : 2048` → `2048`

## What Was Preserved (NOT Removed)
- ✅ All mouse event handlers (mousedown, mousemove, mouseup, click, wheel)
- ✅ All keyboard event handlers (keydown, keyup)
- ✅ Pointer events (pointerdown, pointermove, pointerup) — these work with mouse
- ✅ Accessibility features (aria-label, aria-pressed, sr-only, focus-visible, skip-link)
- ✅ Command palette (Ctrl+K)
- ✅ Help panel and guided tour
- ✅ Right-click context menu (desktop)
- ✅ Walk mode (keyboard + mouse drag to look)
- ✅ Walk joystick buttons (mouse-based)
- ✅ Topbar scroll indicator (handles overflow on any viewport width)
- ✅ @media print and @media (prefers-reduced-motion: reduce) blocks

## Testing Results

| Test | Result |
|------|--------|
| Page loads at 1280px | ✅ Pass |
| No JS console errors | ✅ Pass |
| No missing mobile element errors | ✅ Pass |
| Topbar visible | ✅ Pass |
| Canvas renders (WebGL) | ✅ Pass |
| Sidebar + library visible | ✅ Pass |
| Wizard skip works | ✅ Pass |
| Mouse click on canvas | ✅ Pass |
| Mouse wheel/scroll | ✅ Pass |
| Mouse drag | ✅ Pass |
| Mobile elements absent | ✅ Pass (all counts = 0) |
| Body has no is-mobile class | ✅ Pass |

## Metrics
- **Original lines**: 16,772
- **Final lines**: 16,010
- **Lines removed (net)**: 762
- **Lines deleted**: 789
- **Lines inserted**: 27
- **File size reduction**: ~34KB (724KB → 690KB)