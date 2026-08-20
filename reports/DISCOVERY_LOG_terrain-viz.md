# Discovery Log — Underground Visualization & Excavation View

## Sprint: Backyard Designer 3D — Adversarial Convergence
**Agent:** Agent 2 (Builder) — Underground Visualization & Excavation View
**Date:** August 20, 2026

---

## Features Built

### 1. Clipping Plane Cutaway Slider
- **What:** A slider (0-100) that uses `renderer.clippingPlanes` to clip the terrain mesh at a variable Y height. At 0, full terrain is visible. At 100, terrain is fully hidden.
- **How:** `renderer.localClippingEnabled = true` set in initScene. A `THREE.Plane` with normal (0,-1,0) is created and applied to `yardMesh.material.clippingPlanes`. The slider value maps to a Y height interpolated between the max and min terrain heights.
- **Discovery:** The clipping plane normal must be (0, -1, 0) to clip everything ABOVE the plane (since Three.js clips the half-space behind the plane normal). The constant in `THREE.Plane(normal, constant)` represents the signed distance from origin along the normal, which for a horizontal plane at height Y is simply Y.

### 2. Terrain Opacity Slider
- **What:** A slider (15%-100%) that controls `yardMesh.material.opacity`, making the ground semi-transparent so users can see objects below.
- **How:** Material created with `transparent: true, opacity: 1.0`. Slider sets `material.opacity` directly.
- **Discovery:** The minimum opacity is 15% rather than 0% — at 0% the terrain becomes completely invisible which is disorienting. 15% provides a ghost outline while still revealing buried objects. The material in `initWithYard()` also needed the `transparent: true` flag so opacity persists across yard rebuilds.

### 3. Wireframe Terrain Toggle
- **What:** A button that toggles `yardMesh.material.wireframe` between true and false, letting users see through the ground mesh to objects below.
- **How:** Simple boolean toggle on `material.wireframe`.
- **Discovery:** Wireframe mode combined with opacity slider creates an excellent "x-ray" view. The wireframe shows the terrain grid structure (useful for seeing the 50x50 vertex resolution) while opacity lets you see objects through it.

### 4. Buried Objects Indicator
- **What:** A panel showing count and list of objects that are partially or fully underground. Each item shows the object name, burial depth, and a colored dot (red = fully buried, orange = partially buried). Clicking a buried item selects that object in the 3D view.
- **How:** `getBuriedObjects()` iterates `state.objects`, compares `getTerrainHeight(x,z)` with `obj.position.y`. If terrain > object Y + 0.1, the object is buried. The object's approximate height is estimated from its params (height, diameter, footprint).
- **Discovery:** 
  - Object height estimation is tricky — different object types store height differently. Trees use `size` param (S/M/L), fences use `height`, pools use `depth`, etc. I created `getObjectHeightAboveGround()` with fallbacks.
  - "Fully buried" vs "partially buried" distinction is important — a fence with 6ft height buried under 2ft of terrain is only partially buried (4ft still visible). This helps users understand severity.
  - Clicking a buried object to select it is a natural UX expectation — users want to find and fix the problem.
  - The polling approach for detecting changes was necessary because ES module scope doesn't allow reassignment of function declarations. A 300ms poll checking `state.objects.size` and a terrain hash is lightweight and effective.

### 5. Cross-Section View
- **What:** A 2D canvas elevation profile. User clicks two points on the ground to define a cross-section line. A side panel shows the terrain elevation profile along that line, with objects overlaid (green = on surface, red = buried). Shows length, elevation range, and object/buried counts.
- **How:** 
  - Click picking uses the existing `getGroundPointFromEvent()` raycaster.
  - Terrain is sampled at 100 points along the line using `getTerrainHeight()`.
  - Objects within 10ft perpendicular distance from the line are projected onto the profile.
  - Canvas 2D rendering with axes, filled terrain profile, and object markers.
  - 3D scene shows a purple line following the terrain between the two points, plus sphere markers at endpoints.
- **Discovery:**
  - The perpendicular distance threshold of 10ft is important — too small and you miss objects slightly off-line, too large and the profile gets cluttered. 10ft feels right for a backyard scale.
  - Showing both the 3D line marker AND the 2D canvas profile gives users spatial context (where the section is) plus detailed elevation data (what the profile looks like).
  - The canvas needs devicePixelRatio scaling for crisp rendering on high-DPI displays.
  - Object labels on the profile are only shown when there are ≤8 objects to avoid clutter.

---

## Additional Discoveries & Observations

### E1: Terrain Material Persistence Across Yard Rebuilds
**Discovery:** When `initWithYard()` rebuilds the ground mesh (e.g., after loading a design or changing yard dimensions), it creates a new `MeshLambertMaterial` without the `transparent` flag or clipping planes. This means opacity and cutaway settings are lost.
**Fix:** Updated `initWithYard()` to create the material with `transparent: true` and read the current opacity slider value. Also re-applies clipping planes and wireframe state if active.

### E2: ES Module Scope Limitations
**Discovery:** In `<script type="module">`, function declarations create immutable bindings — you cannot reassign them for monkey-patching. Attempting `paintTerrain = function() {...}` silently fails (or throws in strict mode).
**Fix:** Replaced monkey-patching with a polling approach that checks `state.objects.size` and a terrain data hash every 300ms. This is actually cleaner and more maintainable.

### E3: window._test Object Staleness
**Discovery:** The `window._test` object captured `yardMesh` by value at initialization time. When `initWithYard()` replaces `yardMesh`, the test object still pointed to the old (disposed) mesh.
**Fix:** Changed `yardMesh`, `gridHelper`, `boundaryLines` to getter properties (`get yardMesh() { return yardMesh; }`) so they always return the current value.

### E4: Clipping Plane Y-Axis Convention
**Discovery:** Three.js `THREE.Plane(normal, constant)` clips geometry in the half-space OPPOSITE to the normal direction. To clip terrain ABOVE a certain height Y, the normal must point downward (0, -1, 0), and the constant is the Y height. This is counterintuitive — you'd expect (0, 1, 0) to mean "keep things above."

### E5: Cutaway Slider Range Mapping
**Discovery:** The slider needs to map from "full terrain visible" to "terrain fully hidden." This requires knowing the actual terrain height range. I compute `getMaxTerrainHeight()` and `getMinTerrainHeight()` from the `state.terrain` Float32Array. When terrain is flat (all zeros), both return 0, and the slider maps to a narrow range around 0 — which is correct since there's nothing to cut away.

### E6: Cross-Section as Diagnostic Tool
**Discovery:** The cross-section view serves double duty — it's not just for seeing buried objects, it's also a valuable terrain analysis tool. The elevation profile with Δ (delta) shows the grade/slope along any line, which is useful for:
- Checking drainage grade (should be ~5% away from house)
- Verifying retaining wall heights
- Planning patio/pool excavation depth
- Understanding how terrain modifications affect the landscape

### E7: Potential Future Features (Not Built, Logged)
During development, I identified several related features that would be valuable but were beyond the current sprint scope:
- **Ghost Mode for Objects:** Make buried objects semi-transparent red so they're visible even without cutaway. Would require modifying each object's material.
- **Foundation Depth Visualization:** For structures (shed, pergola), show required footing depth below terrain.
- **Excavation Volume Calculator:** Calculate cubic feet of material to remove for inground pools based on terrain profile.
- **Drainage Flow Animation:** Show water flow direction based on terrain slope (using the cross-section profile data).
- **Terrain Contour Lines:** Generate topographic contour lines at regular intervals on the terrain surface.
- **Sunken Pool Detection:** Special indicator when a pool's depth exceeds the terrain height, meaning it needs excavation.
- **Section Export:** Allow exporting the cross-section profile as an image or data file for sharing with contractors.

---

## Technical Notes

- All features are in the single `index.html` file
- No external dependencies added — uses only existing Three.js v0.160.0
- CSS follows existing design system variables (`--primary`, `--border`, `--shadow`, etc.)
- Purple (#5b4a8b) chosen as accent color for excavation features to distinguish from terrain editing (brown #8B5E3C) and sun simulation (amber #f59e0b)
- Mobile responsive: excavate button repositioned for mobile, cross-section panel spans full width
- All controls have ARIA labels and `aria-pressed` states for accessibility
- Help modal updated with excavation feature documentation
- `window._test` extended with new function references for testing

## Test Results
- 22/22 tests passing on desktop (1280x800)
- 22/22 tests passing on mobile (375x667, iPhone UA)
- Zero console errors on both platforms