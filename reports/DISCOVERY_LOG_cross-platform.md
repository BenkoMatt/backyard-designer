# Discovery Log — Cross-Platform Audit

**Sprint 9, Agent 4 (Critic)**
**Date:** August 23, 2026
**Working Copy:** `/root/byd9-cross-platform/index.html`

---

## Discovery #1: No WebGL Graceful Degradation (CRITICAL)
**Found:** 2026-08-23, during initial test run
**Location:** Line 3588 (`initScene()`)
**Symptom:** When WebGL is disabled (--disable-webgl flag in Chromium), the app crashes with "Cannot read properties of undefined" and shows a blank page. No user feedback.
**Root Cause:** `new THREE.WebGLRenderer({...})` called without try/catch. If WebGL context creation fails, the constructor throws, and the uncaught error prevents all subsequent module code from executing.
**Fix Applied:** Added `checkWebGLSupport()` function (tests for webgl2/webgl/experimental-webgl contexts), `showWebGLError()` function (displays styled error overlay), wrapped renderer creation in try/catch, added early return if WebGL unavailable.
**Verification:** Test "graceful_degradation_webgl_disabled" now passes — error overlay shows, no console errors, module loads completely.

---

## Discovery #2: Module-Scope `scene.add()` Crashes (CRITICAL)
**Found:** 2026-08-23, during WebGL disabled debugging
**Location:** Lines 9803, 9805 (innovation group initialization)
**Symptom:** "Cannot read properties of undefined (reading 'add')" — app crashes before `window._test` is set up.
**Root Cause:** `const innovMarkerGroup = new THREE.Group(); scene.add(innovMarkerGroup);` and `const innovRetWallGroup = new THREE.Group(); scene.add(innovRetWallGroup);` execute at module scope (top level), not inside a function. When WebGL is disabled and `initScene()` returns early, `scene` remains `undefined`, causing these lines to crash.
**Fix Applied:** Added `if (typeof scene !== 'undefined' && scene)` guards before both `scene.add()` calls.
**Verification:** No more crash at lines 9803/9805. Module loads to completion.

---

## Discovery #3: `buildGridLevelPlane()` Null Reference (HIGH)
**Found:** 2026-08-23, during WebGL disabled debugging
**Location:** Line 11505 (setTimeout callback)
**Symptom:** "Cannot read properties of undefined (reading 'add')" — delayed crash 300ms after module load.
**Root Cause:** `setTimeout(() => { buildGridLevelPlane(); requestRender(); }, 300)` fires 300ms after module load. `buildGridLevelPlane()` calls `scene.add(gridLevelPlane)` at line 11441. If `scene` is undefined, crash.
**Fix Applied:** Added `if (!scene) return;` at the top of `buildGridLevelPlane()`.
**Verification:** No delayed crash.

---

## Discovery #4: `controls.addEventListener` at Module Scope (HIGH)
**Found:** 2026-08-23, during WebGL disabled debugging
**Location:** Line 10767
**Symptom:** "Cannot read properties of undefined (reading 'addEventListener')" — crash during module load.
**Root Cause:** `controls.addEventListener('change', () => { if (undergroundViewActive) updateDepthGauge(); })` at module scope. `controls` (OrbitControls) is created inside `initScene()`, so it's undefined when WebGL is disabled.
**Fix Applied:** Wrapped in `if (typeof controls !== 'undefined' && controls)` guard.
**Verification:** No crash at line 10767.

---

## Discovery #5: `updateScaleBar()` Null Renderer (MEDIUM)
**Found:** 2026-08-23, during WebGL disabled debugging
**Location:** Line 7020 (called from setTimeout at line 7268)
**Symptom:** "Cannot read properties of undefined (reading 'domElement')" — delayed crash via overlay rendering timer.
**Root Cause:** `updateScaleBar()` calls `renderer.domElement.getBoundingClientRect()`. When `renderer` is undefined (WebGL disabled), crash. The overlay rendering timer at line 7266-7271 fires every 16ms via setTimeout.
**Fix Applied:** Added `if (!renderer || !activeCamera) return;` at top of `updateScaleBar()`.
**Verification:** No more crashes from overlay timer.

---

## Discovery #6: `updateDimensionLines()` Null Scene (MEDIUM)
**Found:** 2026-08-23, during WebGL disabled debugging
**Location:** Line 7213
**Symptom:** Would crash if called when `scene` is null.
**Root Cause:** `updateDimensionLines()` calls `scene.remove(dimLineGroup)` at line 7213 without null check.
**Fix Applied:** Added `if (!scene) return;` at top of `updateDimensionLines()`.
**Verification:** No crash.

---

## Discovery #7: `initWithYard()` Null Scene/Renderer (MEDIUM)
**Found:** 2026-08-23, during code audit
**Location:** Line 5447
**Symptom:** Would crash if user clicks wizard "Continue" when WebGL is disabled.
**Root Cause:** `initWithYard()` immediately calls `scene.remove(yardMesh)` without checking if scene exists.
**Fix Applied:** Added `if (!scene || !renderer) { showToast('3D view unavailable — WebGL not supported'); return; }` guard.
**Verification:** Toast notification shows instead of crash.

---

## Discovery #8: `onResize()` Null Renderer (MEDIUM)
**Found:** 2026-08-23, during code audit
**Location:** Line 3712
**Symptom:** Would crash if user resizes browser window when WebGL is disabled.
**Root Cause:** `onResize()` calls `renderer.setSize(w, h)` without checking if renderer exists.
**Fix Applied:** Added `if (!renderer || !camera3D || !camera2D) return;` guard.
**Verification:** No crash on resize.

---

## Discovery #9: Missing `-webkit-backdrop-filter` Prefix (LOW)
**Found:** 2026-08-23, during CSS audit
**Location:** Lines 386, 413, 966, 1063
**Symptom:** Modal overlays (wizard, help, templates, command palette) would not show blurred background on Safari < 18.
**Root Cause:** 4 instances of `backdrop-filter: blur(4px)` without the `-webkit-` prefix. Safari requires `-webkit-backdrop-filter` for versions 9-17. (Safari 18+ supports unprefixed.)
**Fix Applied:** Added `-webkit-backdrop-filter: blur(4px)` before each `backdrop-filter` declaration.
**Verification:** CSS compatibility test confirms `-webkit-backdrop-filter` is now present.

---

## Discovery #10: Missing `-webkit-user-select` Prefix (LOW)
**Found:** 2026-08-23, during CSS audit
**Location:** Lines 74, 81, 97, 297, 606
**Symptom:** UI elements (category titles, library items, scale bar, grid labels, layer rows) could be selected with long-press on iOS Safari.
**Root Cause:** 5 instances of `user-select: none` without the `-webkit-` prefix required by Safari/iOS.
**Fix Applied:** Added `-webkit-user-select: none` to all 5 instances.
**Verification:** CSS prefix coverage verified.

---

## Discovery #11: Missing Mobile/Touch Enhancements (LOW)
**Found:** 2026-08-23, during viewport and input audit
**Location:** Lines 5, 9, 52, 88-89, 2569
**Symptom:** Various minor mobile UX issues:
- `env(safe-area-inset-bottom)` used in 3 places (lines 278, 506, 551) but viewport meta tag didn't include `viewport-fit=cover`, so safe-area insets were always 0 on iOS notch devices
- No `-webkit-tap-highlight-color: transparent` — blue/gray tap flash on iOS
- No `touch-action: none` on viewport/canvas — browser scroll/zoom gestures could interfere with app 3D controls
- No `overscroll-behavior: none` — pull-to-refresh could trigger on mobile
- No `maximum-scale` in viewport meta — allowed zoom past usable level
- IS_MOBILE detection only used UA sniffing + width, missing touch detection for hybrid devices (Surface Pro)

**Fix Applied:**
- Updated viewport meta: `width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=5.0`
- Added `* { -webkit-tap-highlight-color: transparent; }` global CSS rule
- Added `touch-action: none` to `#viewport` and `#viewport canvas`
- Added `overscroll-behavior: none` to `html, body`
- Enhanced IS_MOBILE: `navigator.maxTouchPoints > 1 && window.innerWidth < 1024`

**Verification:** Touch test passes, IS_MOBILE detection correctly identifies touch-capable narrow devices.

---

## Discovery #12: WebXR/VR Already Properly Handled (PRE-EXISTING)
**Found:** 2026-08-23, during code audit
**Location:** Lines 12329-12342 (VRMode module)
**Note:** The WebXR feature detection was already properly implemented:
- `navigator.xr` checked before use
- `isSessionSupported('immersive-vr')` wrapped in try/catch
- VR button hidden by default (`#vr-btn-container { display: none; }`)
- Only shown when VR is available (`.available` class added)
- Enter button disabled when VR unavailable
- Status text provides user feedback
**No fix needed** — this was already correct.

---

## Discovery #13: WebGL Context Loss Already Handled (PRE-EXISTING)
**Found:** 2026-08-23, during code audit
**Location:** Lines 3700-3705
**Note:** WebGL context loss was already properly handled:
- `webglcontextlost` event listener with `e.preventDefault()` and toast notification
- `webglcontextrestored` event listener with toast and `requestRender()`
- `window._bydContextLost` flag checked in `animate()` to skip rendering during context loss
**No fix needed** — this was already correct. This is especially important for iOS 17 where backgrounding Safari can trigger context loss.

---

## Discovery #14: Pointer Events Used Consistently (PRE-EXISTING, GOOD)
**Found:** 2026-08-23, during input method audit
**Location:** 22+ pointer event listeners across the app
**Note:** The app consistently uses the Pointer Events API (`pointerdown`, `pointermove`, `pointerup`) rather than separate mouse/touch event handlers. This is the modern best practice and works across mouse, touch, and pen/stylus input methods without any special handling.
**No fix needed** — this is excellent cross-platform design.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total discoveries | 14 |
| Critical issues found and fixed | 2 |
| High issues found and fixed | 2 |
| Medium issues found and fixed | 4 |
| Low issues found and fixed | 3 |
| Pre-existing (no fix needed) | 3 |
| **Total issues fixed** | **11** |
| **Total issues found** | **11** (requiring fixes) |