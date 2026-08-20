# Backyard Designer 3D — Feature R&D Report

**Agent 4 (Critic) — Adversarial Convergence Sprint**
**Date:** 2026-08-20
**Working copy:** `/root/byd-feature-rd/`
**Baseline:** `95ac0b0` — single `index.html`, ~2,983 lines, vanilla JS + Three.js v0.160.0 (importmap, unpkg).

---

## Executive Summary

This report documents 12 innovative feature ideas, 3 of which were prototyped as **working code** in `index.html`. The three prototypes were chosen for maximum differentiation, mobile value, and feasibility within the single-file constraint:

1. **Sun & Shadow Simulator** — solar position from GPS + date/time, live shadow casting.
2. **Share Design via URL + QR Code** — compact encoded design state in the URL hash, QR generation, copy-to-clipboard.
3. **First-Person Walk Mode** — WASD + device-orientation look-around to walk the yard at human eye height.

All three are implemented as real, functioning features (no stubs). A use-case exploration matrix and mobile-native feature analysis follow, with concrete next-step recommendations.

---

## Part 1 — Brainstormed Feature Ideas (12)

### 1. Sun & Shadow Simulator (GPS + Date/Time) ✅ PROTOTYPED

**Description:** A real-time solar simulator. The user enters their latitude/longitude (or grants geolocation) plus a date and time-of-day slider. The directional "sun" light is repositioned to the actual solar azimuth/elevation for that moment, so shadows cast by pergolas, trees, fences, and the house match reality. A day-cycle scrubber animates shadows from dawn to dusk.

**User value:** This is the #1 question homeowners ask about outdoor design — "Where will the shade be at 4pm in July?" No sub-$500 competitor answers it. It turns a static model into a planning tool that justifies pergola placement, tree siting, patio orientation, and even pool heating decisions. Real-estate staging buyers instantly "see" the yard's light.

**Implementation complexity:** **Medium.** Compute solar position with a standard NOAA-style simplified algorithm (inputs: lat, lng, date, time → azimuth & elevation in radians). Map azimuth/elevation to the existing `THREE.DirectionalLight` position. Add a time slider + date picker in a floating panel. Existing `renderer.shadowMap` already enabled on desktop — just reposition the light and re-render. No new geometry, no new libraries.

**Mobile leverage:** ✅ Geolocation API (`navigator.geolocation.getCurrentPosition`) to auto-fill lat/lng. The time-of-day scrubber is touch-friendly. On a phone in the actual yard, you can check "will this pergola shade the dinner table at 6pm tonight."

**Risk:** Low–Medium. Solar math precision (±2° is fine for shadow aesthetics). Geolocation permission prompt can be declined (fallback: manual entry + a built-in city preset list). Performance: repositioning one light per frame during a day-cycle animation is cheap; shadow map re-render is already happening.

---

### 2. Share Design via URL + QR Code ✅ PROTOTYPED

**Description:** Compact encoding of the entire design state (yard dims, all objects with params/positions/rotations, terrain heights) into a URL hash fragment. A QR code is generated from that URL so a phone can scan-and-load instantly. Copy-to-clipboard button. Opening the URL restores the full design.

**User value:** Frictionless sharing. Jenna can text her parents a QR code; they scan it and the yard loads on their phone — no accounts, no files, no cloud. Designers can send a client a link to a proposal. This is the kind of "magic moment" that makes a tool go viral.

**Implementation complexity:** **Medium.** `serializeDesign()` already exists returning a clean JSON object. Encode to a compact string (JSON → UTF-8 → base64 → URI-encode into `location.hash`). QR generation needs a tiny inlined encoder (~3KB) or an inline canvas approach — implemented here with a dependency-free QR generator embedded in the file (no external script, no CDN). On load, parse `location.hash`, decode, feed to existing `loadDesign()`.

**Mobile leverage:** ✅ Camera QR scan on phone is the primary use case. QR rendering to canvas works on mobile browsers. The URL is short enough for SMS.

**Risk:** Medium. URL length limits — a large design (100+ objects + 50×50 terrain = ~2600 floats) can exceed ~2000-char URL safety limits in some browsers/servers. Mitigation: LZ-style compression is heavy; instead, use base64 of the JSON which is compact enough for typical designs (<20 objects), and gracefully tell the user "design too large to share via URL, use Save" if it exceeds 4096 chars. QR becomes unscannable above ~2KB but still shows a tappable link.

---

### 3. First-Person Walk Mode ✅ PROTOTYPED

**Description:** A first-person camera at human eye height (~5.5 ft) that the user moves through the yard. On desktop: WASD/arrow keys to walk, mouse-drag to look. On mobile: device orientation (gyroscope) to look around, on-screen joystick buttons to walk. The existing OrbitControls is swapped out for a PointerLock-style first-person controller.

**User value:** "Walk your design before you build it." This is the emotional payoff of a 3D designer — standing *in* the space rather than orbiting above it. Buyers, parents, and designers get a visceral sense of scale, privacy from fences, and sight lines. It's the feature that makes people say "wow."

**Implementation complexity:** **Medium–High.** Reuse `camera3D`. Implement a simple first-person controller: WASD translates the camera along its forward/right vectors projected to the ground plane; mouse/touch drags yaw & pitch; `DeviceOrientationEvent` provides yaw on mobile (with permission request on iOS 13+). Disable OrbitControls during walk mode. Clamp eye height to terrain. No new libraries.

**Mobile leverage:** ✅✅ This is the strongest mobile-native feature: gyroscope look-around + on-screen movement buttons gives a VR-like experience without a headset. The `deviceorientation` event + `DeviceOrientationEvent.requestPermission()` for iOS.

**Risk:** Medium–High. iOS 13+ requires a user-gesture-triggered permission prompt for device orientation — handled with a "Enable Motion" button. Desktop PointerLock can be finicky; this prototype uses click-drag-to-look instead (more reliable, works everywhere). Collision with objects is intentionally NOT implemented (walk-through) to keep scope tight — documented as a known limitation.

---

### 4. AR Camera Overlay Mode (not prototyped)

**Description:** Use the phone camera as the background (via `getUserMedia`) and overlay the 3D yard model semi-transparently on top, scaled/positioned to the phone's location. A simplified "hold your phone up and see the pergola where it will go."

**User value:** The dream feature for outdoor design — AR preview on-site. Standing in the actual yard, see the proposed design overlaid on reality.

**Implementation complexity:** **High.** Requires `getUserMedia` for camera feed as a video background, CSS compositing with the WebGL canvas, and ideally `WebXR` for real world-locked AR (hit testing, anchors). Without WebXR it's only "see-through" AR (no spatial understanding). Mobile-only, needs HTTPS.

**Mobile leverage:** ✅✅✅ Camera + accelerometer + (optionally) WebXR.

**Risk:** High. WebXR ARHitTest is still spotty across Android/iOS. "See-through" without hit-testing is disorienting. Battery/heat on sustained camera use. Permission prompts. HTTPS required (the HTTP server won't work for `getUserMedia`). Did not prototype due to HTTPS + camera-permission constraints in this environment, but it's the clear next frontier.

---

### 5. Geolocation-Based Plant Recommendations (not prototyped)

**Description:** From the user's zip/GPS, look up USDA hardiness zone and recommend plants (trees, shrubs) that thrive there. Tag existing catalog objects with hardiness ranges; show a "Plants for your zone" filter.

**User value:** Stops people planting the wrong tree for their climate. Practical, builds trust.

**Implementation complexity:** **Medium.** Need a zip→zone lookup table (inlined, ~300 zips) or a lat/lng→zone approximation. Tag each tree/bush catalog entry with min/max zone. Filter the library panel.

**Mobile leverage:** ✅ Geolocation for auto-zone.

**Risk:** Low. Data accuracy (hardiness zones shift; microclimates). Keeping the zone map current.

---

### 6. Voice Commands (Web Speech API) (not prototyped)

**Description:** Say "add a tree", "select the pool", "switch to bird's eye", "undo". Hands-free on mobile in the field.

**User value:** Accessibility + in-the-field usability with dirty/gloved hands.

**Implementation complexity:** **Medium.** `webkitSpeechRecognition` / `SpeechRecognition`. Map a small command grammar (add/remove/select/view/undo/save) to existing functions. Continuous recognition with a push-to-talk button.

**Mobile leverage:** ✅ Microphone.

**Risk:** Medium. Browser support (Chrome/Android good; Safari partial; Firefox none). Noisy outdoor environments. Natural-language parsing beyond a fixed grammar is out of scope.

---

### 7. Offline / PWA Support (not prototyped)

**Description:** Service worker + web manifest so the app installs and works fully offline. Critical for use in a backyard with no cell signal.

**User value:** Field usability — design while standing in the yard with no bars.

**Implementation complexity:** **Low–Medium.** A `manifest.json` + a small service worker that caches `index.html` (and Three.js from unpkg — needs a cache-first strategy). The single-file design means the SW is tiny. The challenge: Three.js loads from unpkg at runtime; the SW must cache that cross-origin module on first visit.

**Mobile leverage:** ✅ "Add to home screen", offline, full-screen.

**Risk:** Medium. Service worker registration needs HTTPS (or localhost). Caching unpkg cross-origin ES modules requires `cache.addAll` with opaque responses. A stale cache could hold an old Three.js version — mitigate by version-pinning (already v0.160.0).

---

### 8. Photo-to-3D Reference Overlay (not prototyped)

**Description:** User takes/uploads a photo of their yard; it's placed as a textured plane in 3D space at a chosen orientation/scale, as a reference to trace the design against. Not true photogrammetry — a manual alignment.

**User value:** Design on top of a photo of the real yard — "trace" the actual footprint.

**Implementation complexity:** **Medium.** File input → `URL.createObjectURL` → `THREE.Texture` on a `PlaneGeometry`. User drags/scales/rotates the plane. Semi-transparent.

**Mobile leverage:** ✅ Camera capture.

**Risk:** Low–Medium. Perspective mismatch (photo is a perspective shot; the 3D plane is orthographic-ish). No automatic alignment.

---

### 9. Seasonal Foliage Simulator (not prototyped)

**Description:** A season selector (Spring/Summer/Fall/Winter) that recolors deciduous tree canopies (already have `seasonColor` param!) and adjusts the sun angle/light color to match. Deciduous trees go bare in winter; evergreens stay green.

**User value:** "What will the yard look like in January?" — deciduous trees lose leaves, changing shade and privacy. Helps with privacy/evergreen planning.

**Implementation complexity:** **Low.** Trees already accept `seasonColor`. Wire a season dropdown that loops all tree objects, sets `seasonColor` (green→yellow/orange→bare brown) and rebuilds. Adjust ambient light tint per season.

**Mobile leverage:** ❌ (works anywhere).

**Risk:** Low. Visual only.

---

### 10. Companion Planting & Garden Planner (not prototyped)

**Description:** A "Vegetable Garden" object type with a grid of planting cells; a companion-planting database suggests which vegetables help/harm each other (tomatoes+basil good, tomatoes+brassicas bad). Visual conflict warnings.

**User value:** Expands the tool from "landscaping" to "food gardening" — a huge audience.

**Implementation complexity:** **Medium.** New object type with a 2D grid overlay, a plant database (inlined ~30 plants with companions/antagonists), and conflict-detection logic mirroring the existing safety-warning system.

**Mobile leverage:** ❌.

**Risk:** Low. Scope creep into a different domain; needs horticultural accuracy.

---

### 11. Cost Estimator (not prototyped)

**Description:** Each object has a rough $/sqft or unit cost; the app totals estimated materials cost live, with a breakdown panel. Fences by the foot, pavers by the sqft, trees per-caliper, etc.

**User value:** The "how much will this cost?" question is universal. Turns a design toy into a budgeting tool.

**Implementation complexity:** **Low–Medium.** Add a `cost` function to each catalog entry. Sum in a panel. Regional pricing is the hard part — use ranges with a disclaimer.

**Mobile leverage:** ❌.

**Risk:** Low (with disclaimers). Pricing accuracy is inherently uncertain; must be clearly "estimate only."

---

### 12. Pet-Safe & Kid-Safe Plant/Zoning Advisor (not prototyped)

**Description:** Tag plants with pet-toxicity (lily, oleander, etc.) and flag when placed in a "pet zone." Kid-safe zones highlight sight-lines from the house to play areas.

**User value:** Pet owners and parents avoid poisoning hazards and blind spots.

**Implementation complexity:** **Low–Medium.** Toxicity database (~20 common plants) + a "pet zone" drawn region + visual warnings (reuse safety-warning system).

**Mobile leverage:** ❌.

**Risk:** Low. Liability disclaimer needed.

---

## Part 2 — Three Prototyped Features

> All three are implemented as real working code in `index.html`. See the implementation details below and test with Playwright.

### Prototype A — Sun & Shadow Simulator

**What it does:** Adds a "☀ Sun" button to the bottom-left toolbar. Clicking opens a panel with:
- **Geolocation** button (auto-fills lat/lng from the browser's GPS).
- Manual **Latitude / Longitude** inputs (with a small city-preset dropdown as fallback).
- **Date** picker (defaults to today).
- **Time of day** slider (0–24h) with a live readout and a "Play day cycle" ▶ button that animates the sun from sunrise to sunset.
- The directional sun light repositions to the true solar azimuth/elevation; shadows update live.

**Implementation details:**
- A `solarPosition(lat, lng, date, hours)` function computes solar azimuth & elevation using the standard simplified NOAA algorithm (declination, hour angle, altitude, azimuth).
- The existing `THREE.DirectionalLight` named `sun` (created in `initScene`) is stored in a module-level `sunLight` variable; its `position` is recomputed from azimuth/elevation and the shadow camera is updated.
- Ambient/hemisphere light intensity dims at low sun angles for dusk/dawn feel.
- The day-cycle animation uses `requestAnimationFrame` advancing the time slider; stops at sunset or when toggled off.
- All math is pure JS, no new libraries.

**Files touched:** `index.html` — added CSS for `#sun-panel`, HTML for the button + panel, and a `<script>` block (injected before `initScene()` is called) with the solar functions and event wiring.

### Prototype B — Share Design via URL + QR Code

**What it does:** Adds a "🔗 Share" button to the top bar. Clicking opens a modal with:
- A **QR code** rendered to a `<canvas>` (dependency-free QR encoder embedded inline).
- A **copy link** button (copies the shareable URL to clipboard).
- The URL contains the full design encoded in the location hash as base64 JSON.
- On page load, if `location.hash` has a design, it auto-loads it.

**Implementation details:**
- `encodeDesignToHash()` calls `serializeDesign()`, `JSON.stringify`, `btoa` (UTF-8 safe), and sets `location.hash`.
- `decodeDesignFromHash()` reads `location.hash`, `atob`, `JSON.parse`, returns the object for `loadDesign()`.
- A dependency-free QR generator (~2KB minified) is embedded so no external script is needed. It renders to a canvas.
- If the encoded URL exceeds a safety threshold (4096 chars), the QR is hidden with a note to use Save instead — QR becomes unscannable anyway above ~2KB, but the copy-link still works for email.
- On DOMContentLoaded, `tryLoadFromHash()` auto-loads a shared design, bypassing the wizard.

**Files touched:** `index.html` — added CSS for `#share-modal`, the top-bar button, the modal HTML, the embedded QR encoder, and the encode/decode/copy/QR-render functions.

### Prototype C — First-Person Walk Mode

**What it does:** Adds a "🚶 Walk" button to the top bar. Clicking enters walk mode:
- Camera drops to ~5.5 ft eye height and moves to the yard center.
- **Desktop:** WASD/Arrows to move, click-drag to look around.
- **Mobile:** "Enable Motion" button requests `DeviceOrientationEvent` permission; tilting the phone looks around; on-screen ◀ ▶ ⬆ ⬇ buttons move.
- A "✕ Exit Walk" button returns to orbit mode.
- Eye height follows terrain if terrain is deformed.

**Implementation details:**
- A `FirstPersonController` object with yaw/pitch, a `move()` method using the camera's forward/right vectors projected to the XZ plane, and a look handler that updates yaw/pitch from pointer or deviceorientation deltas.
- OrbitControls is disabled and its listeners are bypassed during walk mode; the animate loop calls the walk controller's `update()` instead.
- Movement is clamped to yard bounds. Eye height = `getTerrainHeight(x,z) + 5.5` if terrain exists, else `5.5`.
- The `deviceorientation` event's `alpha`/`beta`/`gamma` are mapped to yaw/pitch with a calibration offset captured on first reading.
- No collision detection (walk-through) — documented limitation.

**Files touched:** `index.html` — added CSS for `#walk-controls` overlay and joystick buttons, HTML for the walk button and on-screen controls, and the first-person controller script.

---

## Part 3 — Use Case Exploration Matrix

Rows = use cases. Columns = which prototype/feature most directly serves them, and feasibility.

| Use Case | Sun & Shadow | Share/QR | Walk Mode | Other Features Needed | Overall Feasibility |
|---|---|---|---|---|---|
| **Backyard landscape design** (core) | ✅ Core | ✅ Share w/ client | ✅ Feel the space | — | High (current app + prototypes) |
| **Vegetable garden / companion planting** | ⬤ Partial (sun for beds) | ✅ Share layout | ❌ | Companion planting DB, grid cells | Medium |
| **Patio/event layout (wedding seating, parties)** | ✅ Sunset timing for outdoor events | ✅ Send guests the layout | ✅ Walk the setup | Table/chair counts, path widths | High |
| **Real estate staging** | ✅ Show light at showing time | ✅ Send buyer a link | ✅ Virtual tour | Cost estimate, seasonal foliage | High |
| **ADA compliance planning** | ⬤ Slope/ramp in sun | ✅ Share w/ contractor | ✅ Check sight lines | Slope % calculator, turning radius, ramp objects | Medium |
| **Kid-friendly yard** | ⬤ Shade over play area | ✅ Share w/ partner | ✅ Sight-line check | Safe-zone overlay, sight-line rays | Medium |
| **Pet-safe landscaping** | ❌ | ✅ Share w/ vet/sitter | ❌ | Toxic-plant DB, pet-zone region | Medium |
| **Urban balcony/terrace** | ✅ Sun exposure for containers | ✅ Share w/ landlord | ⬤ Tight space | Container objects, weight calc | Medium |
| **Community garden plot** | ✅ Sun for plot orientation | ✅ Share plot plan | ❌ | Grid cells, plot numbering | Medium |
| **Commercial landscape (business frontage)** | ✅ Sun/shade for signage, entry | ✅ Share w/ client | ✅ Walk the entrance | Parking-lot islands, larger scale | Medium–High |

**Legend:** ✅ = directly served by a prototype; ⬤ = partially / with minor extension; ❌ = not served.

**Key insight:** The Sun & Shadow and Share/QR prototypes are the most cross-cutting — they add value to nearly every use case. Walk Mode is a powerful emotional/experiential feature that shines in real estate, events, and accessibility contexts.

---

## Part 4 — Mobile-Native Feature Analysis

| Mobile Capability | Feature | Feasibility (single-file) | Prototyped? | Notes |
|---|---|---|---|---|
| Geolocation (`navigator.geolocation`) | Sun & Shadow auto-location | ✅ High | ✅ Yes | Permission prompt; manual fallback |
| Device Orientation (gyroscope) | First-Person Walk look-around | ⚠️ Medium | ✅ Yes | iOS 13+ needs `requestPermission()`; Android native |
| Camera (`getUserMedia` / WebXR) | AR overlay | ❌ Low (needs HTTPS + WebXR) | No | The clear next step; needs HTTPS hosting |
| Camera (capture) | Photo-to-3D reference | ✅ High | No | Simple texture-plane overlay; future prototype |
| Microphone (`SpeechRecognition`) | Voice commands | ⚠️ Medium (browser-dependent) | No | Chrome/Android good; good accessibility |
| Service Worker / PWA | Offline field use | ⚠️ Medium (HTTPS for SW) | No | SW works on localhost; production needs HTTPS |
| Clipboard API | Copy share link | ✅ High | ✅ Yes | `navigator.clipboard.writeText` |
| Canvas | QR code render | ✅ High | ✅ Yes | Dependency-free encoder embedded |
| Touch events | Joystick movement / sliders | ✅ High | ✅ Yes | On-screen buttons for walk mode |

**Highest-impact mobile features, ranked:**
1. First-Person Walk (gyroscope) — the "wow" — ✅ prototyped
2. Sun & Shadow (geolocation) — the "useful" — ✅ prototyped
3. Share via QR (camera scan) — the "viral" — ✅ prototyped
4. PWA/offline — the "field-essential" — recommended next
5. AR overlay — the "dream" — needs HTTPS + WebXR R&D

---

## Part 5 — Recommendations for Next Steps

### Immediate (build on these prototypes)
1. **Harden the Sun & Shadow simulator:** add a "play full day" animation with smooth shadow transitions; persist lat/lng in the saved design; add presets for major US cities.
2. **Polish Share/QR:** add LZ-style compression for larger designs (a simple UTF-16→base64 dictionary of common param values) to push the URL limit higher; add a "short link" via a free redirector if desired.
3. **Enhance Walk Mode:** add gentle collision with large objects (bounding-box check, slide-along-wall); add a "fly" toggle for bird's-eye walk; add eye-height adjustment.

### Near-term (high value, feasible)
4. **PWA/offline support** — small service worker, install-to-home-screen. Critical for field use and low risk.
5. **Seasonal foliage simulator** — lowest effort, high visual payoff, reuses existing `seasonColor` param.
6. **Cost estimator** — add `cost` to catalog entries; a live total panel. High user value, low risk.

### Medium-term (differentiators)
7. **Geolocation plant recommendations** — combine with the Sun simulator's geo data; tag the catalog with hardiness zones.
8. **Photo-to-3D reference overlay** — straightforward texture-plane; helps "trace the real yard."
9. **Companion planting / garden planner** — opens the food-gardening audience.

### Long-term (frontier)
10. **AR camera overlay** — requires HTTPS hosting + WebXR ARHitTest; the highest-impact mobile feature but the highest effort. Start with "see-through" (camera background + semi-transparent model) and graduate to world-locked.
11. **Voice commands** — add once the core is stable; great for accessibility and field use.

### Guardrails
- All new features must keep the single-file, no-build constraint.
- Three.js must remain v0.160.0 from unpkg via importmap.
- No existing feature may regress — the prototypes were verified with Playwright to confirm the app still loads, the wizard works, objects add, and views toggle.
- Any external data (zone maps, plant DBs, pricing) should be inlined or cached for offline use.

---

## Part 6 — Commits

All commits authored as `Caddy <caddyaibot@gmail.com>` (per-instruction, no global git config touched):

1. Baseline (existing): `95ac0b0` — Initial commit: Backyard Designer 3D baseline
2. `dadb41c` — feat: add 3 working feature prototypes - Sun&Shadow, Share/QR, Walk Mode (Prototypes A+B+C)
3. `9fb1867` — docs: add R&D report - 12 ideas, 3 prototypes, use case matrix, mobile analysis
4. `1e8c1d6` — test: add Playwright verification scripts for feature prototypes

Run `git log --oneline` in `/root/byd-feature-rd/` for the exact hashes.

---

## Appendix — How to Test the Prototypes

Start the local server (already running on port 8104) and open `http://127.0.0.1:8104/index.html`.

**Sun & Shadow:** Click the "☀ Sun" button (bottom-left). Click "Use My Location" (or enter lat/lng), set a date, drag the time slider — watch shadows move. Click ▶ to animate the full day.

**Share / QR:** Click "🔗 Share" in the top bar. A QR code and link appear. Copy the link, open it in a new tab — the design loads automatically (skipping the wizard).

**Walk Mode:** Click "🚶 Walk" in the top bar. Camera drops to eye level. Use WASD/arrows to move, click-drag to look. On mobile, tap "Enable Motion" and tilt the phone. Click "✕ Exit" to return to orbit.