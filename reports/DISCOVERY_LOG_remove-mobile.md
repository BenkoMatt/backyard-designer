# DISCOVERY LOG — Sprint 16 Agent 4: Remove Mobile Features

## File Analyzed
- **File**: `/root/byd16-remove-mobile/index.html`
- **Original lines**: 16,772
- **Final lines**: 16,010
- **Lines removed**: 762 (net), 789 deletions + 27 insertions

## Discovery Process

### 1. Touch Event Handlers
Found 9 touch event listener references:
- Lines 9095-9107: Walk mode touch controls (touchstart/touchmove/touchend on canvas)
- Lines 9132-9133: Walk joystick touchstart/touchend
- Lines 10389-10391: Terrain compare button touchstart/touchend/touchcancel
- Line 16461: 'touchstart' in inactivity reset array

### 2. Mobile Detection JS
- Line 3247: `const IS_MOBILE = /Android|webOS|iPhone|.../i.test(navigator.userAgent) || window.innerWidth < 768 || ...`
- Line 3248: `if (IS_MOBILE) document.body.classList.add('is-mobile');`
- Line 3249: `const PIXEL_RATIO = Math.min(window.devicePixelRatio, IS_MOBILE ? 1 : 2);`
- Line 3251: `let SHADOW_MAP_SIZE = IS_MOBILE ? 1024 : 2048;`
- Lines 3275-3309: Mobile CSS injection block (IS_MOBILE conditional, injects `<style id="mobile-usability-css">`)
- 19 total IS_MOBILE references across the file

### 3. Mobile-specific HTML Elements
- Line 1998: `<button id="mobile-lib-toggle">` — mobile library toggle button
- Lines 2897-2918: `<div id="mobile-props-sheet">` — mobile bottom sheet with grabber, header, body, action bar
  - Contains: sheet-grabber, mobile-props-header, mobile-props-body, mobile-action-bar
  - Mobile action bar buttons: mab-duplicate, mab-rotate, mab-delete, mab-close
- Line 2936: `<div id="walk-hint-mobile">` — mobile walk mode hint
- Line 2937: `<button id="walk-motion-btn">` — device orientation toggle button

### 4. Mobile-specific CSS
**body.is-mobile rules (22 occurrences):**
- Lines 496-631: body.is-mobile selectors for sidebar, mobile-lib-toggle, properties, mobile-props-sheet, mobile-action-bar
- All sheet-grabber, sheet-header, sheet-body mobile-props-sheet sub-selectors

**#mobile-props-sheet rules (standalone, lines 537-586):**
- display, positioning, grabber, header, body, action bar sub-selectors

**#mobile-action-bar rules (lines 574-580)**

**#mobile-lib-toggle rules (lines 494, 519-534, 878)**

**.mab-btn rules (lines 632-642)**

**#walk-motion-btn rules (lines 737-738)**

**#walk-hint-mobile rules (line 1289)**

**#sidebar.mobile-visible rules (lines 498, 518)**

**@media (max-width: 768px) blocks (14 occurrences):**
- Lines 227, 341, 427, 495, 516, 538, 769, 829, 843, 868, 885, 1273
- All set mobile-specific sizes, positions, touch targets (44px min)

**@media (max-width: 600px) block:**
- Line 1442: Mobile adjustments for onboarding panels

**@media (max-width: 768px) and (max-height: 500px) block:**
- Line 868: Extra-small screen adjustments

**Other mobile CSS:**
- Line 9: `* { -webkit-tap-highlight-color: transparent; }`
- Lines 123-124: `touch-action: none` on viewport/canvas
- Line 734: `touch-action: none` on walk-joy-btn
- Line 87: `height: 100dvh; height: var(--app-height)` — mobile viewport height workaround
- Line 48: `--app-height: 100vh;` — CSS variable (set by JS on mobile)
- Line 86: `overscroll-behavior: none` — mobile scroll chaining prevention

### 5. Mobile-only JS Functions
- Lines 4918-4934: Touch state variables (TAP_DURATION_MS, TAP_MOVEMENT_THRESHOLD, TOUCH_DRAG_THRESHOLD, LONG_PRESS_MS, LONG_PRESS_THRESHOLD, touchState object)
- Lines 4935-4940: `_getMeshesForRaycast()` — helper for touch raycasting
- Lines 4941-4990: `_raycastFromScreenPoint()` — touch raycast helper
- Lines 4977-5104: `onTouchPointerDown()`, `onTouchPointerMove()`, `onTouchPointerUp()` — touch gesture handlers
- Lines 5105-5113: `_attachTouchGestureHandlers()` — attaches touch listeners to canvas
- Lines 5114-5175: `_showMobileContextMenu()` — creates mobile context menu
- Lines 5294-5297: `mobileSheetEl`, `mobilePropsHeader`, `mobilePropsBody`, `mobileActionBar` — DOM refs
- Lines 8546-8578: `setupMobileSheet()` IIFE — mobile sheet grabber and mab button handlers
- Lines 9274-9292: `setupMobileLibToggle()` IIFE — mobile library toggle handler
- Lines 9010-9019: Walk mode mobile hint and motion button show/hide
- Lines 9034-9037: Device orientation cleanup in exitWalkMode
- Lines 9067-9076: `onWalkDeviceOrient()` — device orientation handler
- Lines 9135-9146: Walk motion button click handler (DeviceOrientationEvent.requestPermission)
- Lines 3275-3309: Mobile CSS injection block (IS_MOBILE conditional)
- Lines 3338-3343: `setAppHeight()` — mobile viewport height fix, orientationchange listener
- Lines 8100-8107: `_getTerrainEventPoint()` — touch offset for terrain brush
- Lines 8108-8126: Terrain pointerdown/pointermove mobile touch offset code

### 6. Viewport Meta Tag
- Line 5: `<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=5.0">`
- Replaced with: `<meta name="viewport" content="width=1280">`

### 7. IS_MOBILE References in Rendering Code
- Line 4239: `shadowEnabled: !IS_MOBILE` → `shadowEnabled: true`
- Line 4300: `scene.fog = new THREE.Fog(0x87CEEB, IS_MOBILE ? 80 : 100, IS_MOBILE ? 300 : 500)` → desktop values
- Line 4302: `antialias: !IS_MOBILE` → `antialias: true`
- Line 4307: `Math.min(PIXEL_RATIO, IS_MOBILE ? 1 : 1.5)` → `1.5`
- Line 4311: `IS_MOBILE ? THREE.BasicShadowMap : THREE.PCFSoftShadowMap` → `THREE.PCFSoftShadowMap`
- Line 4312: `IS_MOBILE ? 1024 : (...)` → desktop shadow map size
- Lines 4332-4335: Mobile renderer settings block
- Lines 4464-4468: Mobile pixel ratio reduction for small screens
- Lines 13276-13277: `scene.fog.near/far = IS_MOBILE ? ...` → desktop values
- Lines 9010-9019: Walk mode mobile checks

## Verification Results

### Playwright Test (1280x800, headless Chromium)
- **Page loads**: ✅ No JS errors
- **Console errors**: 0 (only WebGL performance warnings, expected in headless)
- **Mobile elements removed**: ✅ (all counts = 0)
  - #mobile-lib-toggle: 0
  - #mobile-props-sheet: 0
  - #walk-motion-btn: 0
  - #walk-hint-mobile: 0
- **Body class**: Empty (no `is-mobile` class)
- **Topbar visible**: ✅
- **Canvas renders**: ✅ (3 canvases in viewport)
- **Sidebar visible**: ✅
- **Library populated**: ✅ (21 library items)
- **Mouse interactions**: ✅ (click, wheel/scroll, drag all work)
- **Wizard flow**: ✅ (skip button works, scene initializes)