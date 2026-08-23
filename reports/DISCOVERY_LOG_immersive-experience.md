# Sprint 7 — Immersive Experience Researcher: Discovery Log

## Agent
Agent 3 (Builder) — The Immersive Experience Researcher

## Working Directory
`/root/byd7-immersive-experience/`

## Date
2026-08-23

---

## Feature Selection Process

### Ideas Evaluated
1. **VR MODE** — WebXR VR button, walk through yard in VR
2. **AR MODE** — 'View in AR' button, camera overlay
3. **AMBIENT SOUND** — birds, wind, water, crickets tied to sun/shadow
4. **WEATHER EFFECTS** — rain, snow, fog particle systems
5. **DAY/NIGHT CYCLE ENHANCEMENT** — realistic sky gradient, moonlight, stars
6. **GARDEN JOURNAL** — notes timeline of yard history

### Three Selected (Most Impactful)

1. **Day/Night Cycle Enhancement** — Highest visual impact. Transforms the existing flat blue sky into a living gradient that shifts from deep night with stars, through dawn/dusk golden hours, to full blue day. Integrates directly with the existing NOAA sun/shadow simulator. Moonlight at night adds subtle illumination. This is the feature that makes people say "wow" when they slide the time control.

2. **Ambient Sound** — Adds an entirely new sensory dimension. Synthesized entirely in-browser via Web Audio API — no external audio files needed. Four channels (birds, wind, water, crickets) that automatically mix based on sun position: birds sing during day, crickets chirp at night, wind gusts gently. Makes the yard feel alive.

3. **Weather Effects** — Lets users see their yard in different conditions. Rain (3000 particle streaks falling), snow (2000 drifting flakes), and fog (density-controlled scene fog). Particle systems are GPU-accelerated and tie into the sky color (rain darkens sky, fog grays it out). Combined with the day/night cycle, users can see their yard on a rainy night or snowy dawn.

### Bonus: VR Mode
Also implemented as a prototype: VR mode using WebXR. The VR button appears only when a headset is detected. Entering VR activates first-person walk mode and hands rendering to the XR session. This was included because it's the ultimate "wow" feature for users with headsets, and the infrastructure (button, session management, renderer.xr integration) was straightforward to add alongside the other features.

---

## Technical Implementation Details

### 1. Day/Night Sky Enhancement (`Atmosphere` module)

**Architecture:** IIFE module returning a public API, integrated into the existing sun/shadow system.

**Key Components:**
- **Sky gradient dome** — A 600-unit radius sphere with custom ShaderMaterial. Vertex shader computes world position; fragment shader mixes top/bottom colors based on normalized height. Uses `BackSide` rendering so the inside of the sphere is visible.
- **Star field** — 800 points distributed on the upper hemisphere of a 550-unit sphere. Custom ShaderMaterial with additive blending and a CanvasTexture for soft star points. Opacity is driven by night factor (1 - dayFactor).
- **Moon** — Simple sphere mesh with MeshBasicMaterial. Paired with a DirectionalLight (cool blue-gray color, max intensity 0.15) to simulate moonlight.
- **Color logic** — Five sky states based on sun elevation:
  - `< -6°` → Deep night (dark navy/indigo)
  - `-6° to 6°` → Dawn/dusk (orange horizon, dark blue zenith)
  - `6° to 20°` → Golden hour (transition from orange to blue)
  - `> 20°` → Full day (blue sky)
  - Dawn vs dusk determined by time of day (morning = dawn, evening = dusk)

**Integration:** Hooks into existing `sun-time`, `sun-date`, `sun-lat`, `sun-lng` input events. Also polls every 100ms during sun play animation to update atmosphere frame-by-frame.

**Discovery — UTC time offset:** The existing `solarPosition` function uses UTC hours, not local hours. The time slider value (0-24) is passed directly as `hoursUTC`. This means:
- Solar noon in Detroit (lat=42.33, lng=-83.05) is at t=17.6, not t=12
- At t=12 (UTC noon = 8am EDT), sun elevation is only ~12° (golden hour)
- At t=0 (UTC midnight = 8pm EDT), sun elevation is ~3° (still dusk)
- At t=6 (UTC 6am = 2am EDT), elevation is -10° (deep night)

This is existing behavior and not a bug in the atmosphere system — the atmosphere correctly reflects the solar position at any given UTC time.

### 2. Ambient Sound (`AmbientSound` module)

**Architecture:** Web Audio API with a master gain node and four independent channels.

**Channels:**
- **Birds** — Random chirp generator. Creates short oscillator bursts (2000-4000 Hz sine waves with frequency modulation) at random intervals (0.5-3.5s). Active during day, silent at night.
- **Wind** — Brown noise through a lowpass filter (400 Hz) with a slow LFO (0.1 Hz) modulating the filter frequency for natural gusts. Slightly stronger at night.
- **Water** — White noise through a bandpass filter (800 Hz, Q=2) with a faster LFO (0.3 Hz) creating a bubbling stream effect.
- **Crickets** — Square wave pulses at 4-4.5 kHz in bursts of 3-5 pulses, repeated every 0.3-0.8s. Active at night, silent during day.

**Time-of-day mixing:** The `updateFromTimeOfDay` function adjusts channel gains based on sun elevation:
- `dayFactor` = normalized sun elevation (0 at horizon, 1 at 15°+)
- `nightFactor` = inverse of dayFactor
- Birds gain = channelVolume × dayFactor
- Crickets gain = channelVolume × nightFactor × 0.3
- Wind gain = channelVolume × (0.7 + 0.3 × nightFactor) × 0.5
- Water gain = channelVolume × 0.3 (constant)

**User interaction:** Audio context must be activated by user interaction (browser autoplay policy). The master toggle triggers `ctx.resume()` on first enable.

### 3. Weather Effects

**Rain:** 3000 particle Points system with downward velocity (-0.8 to -1.2 units/frame). Particles wrap to top when they hit ground. Material: PointsMaterial, light blue, semi-transparent. Size and opacity scale with weather intensity slider.

**Snow:** 2000 particle Points system with slow downward + horizontal drift velocity. Particles wrap to top on ground hit. Material: PointsMaterial, white, semi-transparent. Larger point size than rain.

**Fog:** Uses the existing THREE.Fog on the scene. When fog weather selected, fog near/far are reduced to 20/60-140 units (depending on intensity). Fog color blends toward gray. When cleared, fog returns to original 100/500 range.

**Weather animation:** A dedicated `requestAnimationFrame` loop runs when rain or snow is active, updating particle positions. The loop self-terminates when weather is cleared.

### 4. VR Mode (`VRMode` module)

**Implementation:** Uses `navigator.xr.isSessionSupported('immersive-vr')` for availability check. On entry, requests an XR session with `local-floor`, `bounded-floor`, and `hand-tracking` features. Sets `renderer.xr.enabled = true` and `renderer.xr.setSession(xrSession)`. Also enters walk mode for first-person navigation.

**UI:** The VR button only appears in the dock panel when VR is available. Status text shows "VR headset detected" or "VR not supported" or "No VR headset detected".

**Rendering integration:** Added VR rendering check to the main `animate()` loop — when `renderer.xr.isPresenting` is true, it renders to the XR session.

---

## Files Modified
- `index.html` — All three features + VR mode + UI controls (~1134 lines added)

## Files Created
- `test_immersive.py` — 67-test Playwright suite
- `DISCOVERY_LOG.md` — This file

---

## Discoveries & Bugs Found

### 1. Module scope issue (FIXED)
The main script is `<script type="module">`, so `const Atmosphere = ...` is module-scoped, not on `window`. Tests couldn't access it. Fixed by explicitly assigning `window.Atmosphere = Atmosphere` etc.

### 2. UTC time in solar position (NOT A BUG — existing behavior)
The `solarPosition` function uses the slider value as UTC hours. This means solar noon is at ~t=17.6 for Detroit, not t=12. The atmosphere system correctly reflects this.

### 3. Star field shader (DESIGN DECISION)
Initially tried using THREE.PointsMaterial for stars, but it produces square points. Switched to a custom ShaderMaterial with a CanvasTexture radial gradient for soft, round, glowing stars.

### 4. Weather particle performance (OPTIMIZATION)
Rain uses 3000 particles and snow uses 2000. Both update in a dedicated animation loop that only runs when weather is active. Particle positions are updated in-place on the BufferGeometry to avoid reallocation.

### 5. Sky dome fog interaction (DESIGN DECISION)
The sky gradient dome has `fog: false` in its material so it doesn't get fogged out when weather reduces visibility. This ensures the sky is always visible as a backdrop.

### 6. VR renderer integration (MINOR ADDITION)
Added `renderer.xr.isPresenting` check to the main animate loop. Three.js WebXRManager handles the XR render loop when active, but our conditional render ensures the scene updates.

---

## Test Results
```
67 passed, 0 failed
```

Test categories:
- Module existence and API (12 tests)
- UI element existence (19 tests)
- Day/night sky functionality (7 tests)
- Weather functionality (8 tests)
- Atmosphere badge (2 tests)
- Sound module (3 tests)
- VR module (3 tests)
- Existing feature regression (8 tests)
- Slider interaction (2 tests)
- Console errors (1 test)
- Page load (1 test)

---

## Commits
```
701ab1a Fix window exposure for Atmosphere/AmbientSound/VRMode + test fixes
3ee811b Sprint 7: Immersive Experience — Day/Night sky, Ambient sound, Weather, VR mode
```

---

## Summary

Three immersive features were prototyped and tested:
1. **Day/Night Sky Enhancement** — Gradient sky dome with 5 sky states, 800 stars, moon + moonlight
2. **Ambient Sound** — 4-channel Web Audio synthesis (birds/wind/water/crickets) with time-of-day mixing
3. **Weather Effects** — Rain (3000 particles), snow (2000 particles), fog with intensity control

Bonus: **VR Mode** — WebXR VR button with session management and walk mode integration.

All 67 Playwright tests pass. No existing features broken. Everything in single index.html.