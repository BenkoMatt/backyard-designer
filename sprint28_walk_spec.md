# Sprint 28 Spec — Walk-Mode Rework (Natural Walking)

Author: Caddy (webdev), UX auditor — task t_63d5db15 (read-only audit; zero edits to index.html).
Audience: builder (t_80dc33f7), verifier (t_4e6c85f3), synthesizer (t_07952cc0).
Companion artifacts: `sprint28_evidence.py` (real-input capture used), `sprint28_before_evidence.json` (13 probes), `sprint28_shots/` (10 BEFORE screenshots).

Owner mandate (Father Matt, verbatim): "The walk feature pivots around the 0,0 axis and
doesn't feel natural as a walking feature at all. It needs to be completely reworked."

Line refs are HEAD a9d4f53 + the builder's in-flight 2-line modal-CSS insert (~5356), i.e.
the live tree: walk block = 7953–8120, render loop = 2880–2918. Verify anchors with grep
before cutting if the tree moved again (`function enterWalkMode` ≈ 7953).

---

## 0. Root cause (verified, with mechanism)

Father Matt's "pivots around 0,0" is literally `controls.target = (0,0,0)` re-asserting
itself through OrbitControls.update(). Five colliding facts, all verified in source:

1. **RC1 — the animate() loop calls controls.update() every frame, including during walk.**
   `index.html:2883-2885`: `if (typeof controls !== 'undefined' && controls) { dampingActive = controls.update(); }`
   — unconditional, before any walk check. OrbitControls r160's update() ends with
   `position.copy(scope.target).add(offset); scope.object.lookAt(scope.target);`
   (verified in the exact pinned file
   `https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js`, update() body:
   spherical is rebuilt from `offset = position - target` every call, then position is
   written back onto the sphere **around the target**, then lookAt(target)). The app's
   target is `(0,0,0)` (`index.html:2721`, re-set at 4538, 5275 and in exitWalkMode 7986).
   So every animate() frame drags the walking camera onto a sphere centered at the world
   origin and forces lookAt(0,0,0). That is the origin pivot.

2. **RC2 — walk mode runs its own second rAF loop that interleaves with animate().**
   `startContinuousRender()` (7975) bumps `_continuousRenderSources` so animate() renders
   every frame (2895-2916), AND the `walkLoop` rAF chain (8105-8118, watchdog
   `_walkCheckId` interval 8113 re-kicks it every 100 ms) calls `updateWalkCamera()`
   (8002-8023) which writes `camera3D.position/rotation` from walkPos/walkYaw/walkPitch.
   Two independent unsynchronized rAF chains write the same camera transform twice per
   frame tick; whatever lands last alternates unpredictably with frame timing. On a fast
   desktop this mostly reads as "orbit snap + strobe"; it is the same fight at any FPS.

3. **RC3 — `controls.enabled = false` (7960) does NOT stop update().** Verified in the
   pinned r160 source: `enabled === false` only early-returns the *event handlers*
   (`onPointerDown` 996, `onPointerMove` 1025, wheel 1189, key 1203, touch 1349). There is
   **no enabled check inside update()** — the wheel path at `index.html:2807-2838` is
   document-level anyway and calls `controls.update()` + teleports the camera explicitly.

4. **RC4 — input paths have no walkMode guard.**
   - Global keydown (5521-5647) processes V/B/W/T/G/R/M/arrows during walk. Verified
     live: pressing **B during walk leaves walkMode=true while viewMode=2d**; the walk
     loop then keeps writing 3D camera transforms while the renderer draws the ortho 2D
     camera. Arrow keys still move a selected object; W re-enters a broken state.
   - Document-level wheel handler (2807-2838): one notch calls
     `camera3D.position.copy(controls.target).add(offset)` (2835) + `controls.update()`
     (2836) — an explicit orbit-space teleport. On high-FPS machines it lands *before*
     walkLoop's next write and is visible for a frame or more (measured "0.0 ft" net
     displacement only because the 3 fps walk loop overwrote it within the same window;
     on a 60 Hz desktop it visibly jumps).

5. **RC5 — hard-coded enter/exit + frame-locked speed** (verified live, see §E):
   - Enter (7959-7965): walkPos = `(0, getTerrainHeight(0,0)+5.5, 0)`, yaw = PI regardless
     of where the user was looking. Evidence: orbit camera at (59.8, 4.5, −33.5) → W →
     walkPos snapped to (0, 5.5, 0).
   - Exit (7983-7986): camera to `(width*0.5, depth*0.4, depth*0.5)`, target (0,0,0),
     rotation (0,0,0). Evidence: measured 55.2 ft lateral teleport on exit.
   - Speed (8010): `const speed = 0.6` ft **per frame** — no dt. Evidence: 1 s of held W
     moved 1.8 ft at the harness's ~3 fps (would be 36 ft/s ≈ 24.5 mph at 60 fps).
   - Look model (8066-8071): drag-only, sensitivity 0.005 rad/px, pitch clamp ±0.6 rad
     (~±34°) — you cannot look at the sky or your feet.
   - Esc (8041) exits walk AND the global Esc handler (5555-5645) runs on the same press —
     it deselects objects/closes panels with **no walkMode guard** (verified in source;
     the S23 top-most-layer chain at 5556-5613 runs before walk's own handler on window).

---

## 1. MOVEMENT MODEL — dt-based velocity with acceleration + friction

**MUST.** Replace the unconditional per-frame displacement in `updateWalkCamera()`
(8002-8023) with a semi-implicit Euler velocity integrator. All motion becomes
`m/s`, scaled by dt seconds, never by "1 frame".

Constants (single object, e.g. `const WALK = {...}`):
```js
const WALK = {
    eyeHeight: 5.5,        // feet (unchanged — matches current +5.5 and world scale)
    accel: 40,             // ft/s² — reach 95% speed in ~0.18s; feels responsive, not twitchy
    maxSpeed: 4.4,         // ft/s ≈ 3.0 mph casual walk; 30-ft yard crossed in ~6.8s
    sprintMul: 1.8,        // Shift → 7.9 ft/s ≈ 5.4 mph jog; 30-ft yard in ~3.8s
    slowMul: 0.45,         // Alt → 2.0 ft/s inspection creep (NICE, wire if bytes allow)
    frictionExp: 9,        // per-second exponential damping: v *= exp(-9*dt) when no input
    playerRadius: 1.1      // ft, collision capsule radius (§4)
};
```
Justification of maxSpeed: task brief demands a 30-ft yard be crossable in ~4-6 s. 4.4 ft/s
gives 6.8 s unladen, 3.8 s sprinting — brackets the mandate. World scale check: eye height
5.5 ft is canonical; 3 mph is a real human walk. The old 36 ft/s @60fps was 24.5 mph.

Per-frame update (runs in the SINGLE render loop, replacing the walkLoop chain, §7):
```
dt = clamp((now - lastWalkFrameTs) / 1000, 0, 0.1)   // clamp tab-switch spikes
inputF = (keyFwd?1:0) - (keyBack?1:0) + walkMoveDir.forward   // clamped to [-1,1]
inputR = (keyRight?1:0) - (keyLeft?1:0) + walkMoveDir.right   // clamped to [-1,1]
 // view-relative basis (reuse existing _walkEuler/_walkFwdVec/_walkRightVec, YXZ):
forward = (0,0,-1) rotated by walkYaw;  right = (1,0,0) rotated by walkYaw
wish = normalize(forward*inputF + right*inputR) * maxSpeed * (shift?sprintMul:(alt?slowMul:1))
if (wish) v += (wish - v) * min(1, accel*dt / maxSpeed...)   // toward wish, accel-limited
else     v *= Math.exp(-frictionExp * dt)                    // exponential stop, no sliding
walkPos.x += v.x * dt;  walkPos.z += v.z * dt
walkPos  = collideAndClamp(walkPos, v)                       // §4 (mutates/clamps v)
walkPos.y = getTerrainHeight(walkPos.x, walkPos.z) + WALK.eyeHeight
camera3D.position.copy(walkPos);  camera3D.rotation.set(walkPitch, walkYaw, 0, 'YXZ')
```
- Keys: keep `walkKeys[]` (lowercased, 8038-8043) for WASD + arrows; add Shift/Alt reads
  via `walkKeys['shift']` (lowercase already handles it).
- Joystick/mobile: `walkMoveDir` (8074-8089) plugs into `inputF/inputR` exactly as today —
  **MUST keep `walkMoveDir` semantics unchanged** (forward −1..1, right −1..1).
- requestRender() stays inside updateWorkCamera's caller or is unnecessary once §7 merged
  the loops (animate already renders because `_continuousRenderSources > 0`).

Byte estimate: ~700 B net after reclaiming §8's dead blocks.

## 2. LOOK MODEL — drag-look kept, optional Pointer Lock, sane pitch

**MUST (drag-look compat).** Keep existing hold-to-look (8064-8073) as the default.
**MUST (pitch):** widen clamp from ±0.6 rad to ±1.483 rad (±85°). Three sites share the
magic 0.6: drag (8071), device-orientation (8030) — leave the mobile one at ±0.6 (tilt
comfort) unless bytes allow — and enter (0 start is fine).

**MUST (drag sensitivity):** 0.0026 rad/px (≈150 px per 90° turn ~ one full swipe ≈ 240°;
old 0.005 was twitchy at ×2). Keep it a single named constant.

**Pointer Lock (optional, NICE given byte budget — ship only if ≤ 600 B net):**
- Bind: **double-click** canvas enters Pointer Lock during walkMode ONLY (`canvas.requestPointerLock()`).
  Rationale: single-click stays compatible with the drag-look gesture and with the mobile
  joystick; double-click has no existing binding in walk mode.
- `document.pointerlockchange`: yaw/pitch from `movementX/movementY` at sensitivity
  0.0022 rad/px; pitch same ±1.483 clamp.
- Esc-with-pointer-lock conflict (the exact binding asked for): when pointer is locked,
  the browser guarantees Esc exits pointer lock and the keydown will carry
  `document.pointerLockElement === null`; the app must **not** exit walk on that Esc.
  Implement via a 250 ms `pointerUnlockGuardUntil = performance.now()` timestamp set in
  the `pointerlockchange` handler when the lock is lost; the walk Esc handler (8041)
  checks `if (performance.now() < pointerUnlockGuardUntil) return;` — so Esc-from-lock
  only releases the mouse, and a second Esc (after guard expiry) exits walk. No conflict
  with modal Esc chain (§8): guard makes the sequence deterministic Esc=unlook, Esc=exit.
- Show a one-line hint in the walk-hint while lock is available
  (`#walk-hint` 1261): "Double-click: mouse-look | Esc ×2: exit".

## 3. ENTER/EXIT — camera continuity (no teleport, no origin)

**MUST — enter at the current view's ground position.** Chosen variant: raycast the
orbit target to terrain. Justification: `controls.target` is exactly the point the user
has been framing — entering there continues mental continuity best; the nearest-edge
variant teleports even when framing the yard center, which defeats the purpose, and
L-shape edge math adds code the byte budget can't buy.

```
// enterWalkMode() replacement for 7959-7963 (hard-coded origin block)
preWalk = snapshot():  { camPos, camQuat, target, zoom, minDistance, maxDistance,
                         enableRotate, enablePan, viewMode }
ray = new THREE.Raycaster();
ray.set(controls.target + up*50, down);              // straight down through target
hit = ray.intersectObject(terrainOrYardMesh, true);  // yardMesh or outerGround fallback
enter = hit.length ? hit[0].point.xz : controls.target.xz clamped into yard bounds (§4)
walkPos.set(enter.x, getTerrainHeight(enter.x, enter.z) + WALK.eyeHeight, enter.z)
walkYaw = Math.atan2(                                      // face yard center by default
    controls.target.x - walkPos.x,
    controls.target.z - walkPos.z );
// three.js yaw convention check: forward (0,0,-1) rotated by yaw MUST look toward the
// target — builder MUST unit-verify with one CDP probe (yaw 0 faces −Z; atan2(dx,dz)
// convention above has been validated against _walkEuler usage at 8011-8013).
walkPitch = 0
saveState = { camPos: camera3D.position.clone(), target: controls.target.clone(),
              zoom: camera2D zoom, minDistance: controls.minDistance, ... }
```
Edge case: if target is far above a slope, raycast misses → clamp the fallback into the
existing yard clamps and continue. Never fall back to (0, 0).

**MUST — exit restores the EXACT pre-walk camera state.** Replace the hard-coded corner
(7983-7989) with `restoreState(saveState)`: copy back position, controls.target, and the
controls state captured at enter; do NOT call the vc-reset coordinates. After restore,
`controls.update()` once, then `requestRender()`. Guard restore with
`if (state.viewMode === '3d')` so the §8 walkExit-in-2D corruption cannot teleport the
ortho setup (also fix the underlying hole: §7 gate B on viewMode changes during walk).

**MUST — walkYaw continuity on re-entry is NOT carried across sessions** (each entry
recomputes from current orbit view; no persistence, avoids desync with undo of terrain).

Byte estimate: ~650 B net.

## 4. COLLISION + GROUND

Ground **MUST**: keep current `getTerrainHeight` follow (8019) — includes the bilinear
smoothing already present (6025-6038). No change except eyeHeight constant.

Yard bounds **MUST (upgrade)**: current clamp (8016-8018) is rectangle-only. Replace with
a bounds function aware of `state.yard.shape === 'L'` using the SAME inward-notch
rectangle the yard mesh/boundary already uses (`_yo()` shape at 5255-5258 builds the
L outline from data.width/depth; the notch rectangle = the region NOT in the L). Reject a
candidate move into the notch by zeroing that axis' velocity component (slide along the
wall). Keep the existing 1-ft margin. Fallback if byte-expensive: clamp to the bounding
rectangle as today and document it as a known NICE-to-fix.

Object collision **MUST** (cheap circle-vs-footprint, no Raycaster):
```
for each placed object (state.objects):
    const cat = CATALOG[obj.type];  if (!cat.footprint) continue;
    if (FLAT_OBJECT_TYPES.has(obj.type) && !HEAVY_OBJECT_TYPES.has(obj.type)) continue;
      // patios/decks/walkways/raised_beds are walkable ground, EXCEPT heavy ones:
      // pool_inground + retaining_wall are solid (HEAVY list 6078-6079)
    fp = cat.footprint(obj.params);  half = { w: fp.w/2 + WALK.playerRadius, d: fp.d/2 + WALK.playerRadius }
    dx = walkPos.x - obj.position.x;  dz = walkPos.z - obj.position.z;
    if (|dx| < half.w && |dz| < half.d) {          // AABB push-out on the shallower axis
        if (half.w - |dx| < half.d - |dz|) walkPos.x = obj.position.x + Math.sign(dx)*half.w;
        else                               walkPos.z = obj.position.z + Math.sign(dz)*half.d;
    }
```
- Skip `fence_privacy/fence_picket` gap logic — treat fences as solid by footprint
  (they already push out via the AABB above).
- Buryable/overlapped objects (EMBED_OFFSETS / isObjectBuried, 6080+) still collide —
  a buried pool is still a hole you can't step over in walk; acceptable for MUST scope.
- Fallback if profiling on mid-range mobile shows >2 ms/frame: limit to objects whose
  center-distance < 30 ft (early-out `dx*dx+dz*dz > (half.w+5)^2` cheap reject first —
  the early-out is < 40 B and keeps the MUST even on big yards).
- Cost: loop over ≤ a few hundred objects with one footprint() call each — cheap CATALOG
  closures; no scene traversal.

Byte estimate: ~750 B net with early-out.

## 5. FEEL — head-bob, sprint FOV, footsteps

Priority order for the byte budget; ship MUSTs, then reclaim §8 and add NICEs only if
under 766,000 after the size check below.

- **MUST — head-bob, default ON, toggleable Off.** Amplitude 0.09 ft (≈1.1 in — visible
  in a screenshot comparison, never nauseating), frequency 7.2 rad/s, phase advances only
  while moving (`bobPhase += speed2D * dt * 8`), applied as `walkPos.y + sin(phase)*A`
  at the camera copy step ONLY (never mutate walkPos.y — keeps terrain-follow pure).
  Toggle: a checkbox appended to the walk-hint row area OR (cheaper) a `data-bob="on"`
  flip from the existing command palette registry (`{ cat:'View', label:'Toggle Head Bob',
  shortcut:'', action: ... }` ~4773 region) and honor `prefers-reduced-motion` as OFF.
- **MUST — sprint FOV nudge:** lerp `camera3D.fov` 50 → 55 (base FOV is exactly 50,
  2711) while sprinting (Shift held AND moving); lerp back on release at 8/s.
  `camera3D.updateProjectionMatrix()` only when the rounded FOV actually changes.
- **NICE — soft footsteps:** WebAudio, 2 short filtered noise bursts/s at bobPhase
  zero-crossings, −18 dB, gated by the existing sound-settings toggle. ~350 B. Skip if
  the byte math is tight after §8.
- Do NOT add: weapon sway, crouch, jump, sprint stamina — out of scope for a yard walker.

Byte estimate: bob ~340 B, FOV ~180 B, footsteps ~350 B (NICE).

## 6. MOBILE COMPAT (existing elements only — no new IDs)

- `#walk-joystick` buttons (8074-8091) already set `walkMoveDir.{forward,right}` on
  mousedown/up/leave. MUST keep: with §1 the joystick now feeds the same wish-vector as
  keys, and the friction/accel gives it natural ramp — no changes needed to DOM.
  Joystick speed MUST match keyboard (WALK.maxSpeed) — verified today both paths share 0.6.
- `#walk-motion-btn` + `onWalkDeviceOrient` (8024-8033): MUST keep working; leave its
  ±0.6 pitch clamp. NOTE: the DeviceOrientation branch at 7969-7976 is inside
  `if (false && ...)` (two blocks: 7969 and 7975) — dead code per the S16 touch removal.
  If the builder re-activates mobile hints, do it deliberately; otherwise these are
  §8 reclaim candidates. `walk-motion-btn` display stays gated as today.
- `#walk-exit` (7981) keeps working; it calls exitWalkMode which now restores state (§3).
- Joystick hold + head-bob + dt: all three compose through the single update path in §1.

## 7. RENDER-LOOP FIX — the exact prescription (highest priority)

**B1 — MUST: make animate() the sole camera authority.**
In `animate()` (2883-2885) replace:
```js
dampingActive = controls.update();
```
with:
```js
if (walkMode) { dampingActive = false; } else { dampingActive = controls.update(); }
```
AND delete the parallel walk rAF loop entirely: remove `walkLoop`/`walkLoopRunning`/
`_walkCheckId` (8104-8118) and let updateWalkCamera() be invoked from animate() like so:
```js
if (walkMode) { updateWalkCamera(dtNow); }   // inside animate, AFTER the controls skip
```
(startContinuousRender at 7975 can stay — it keeps animate() hot; with RC1 removed there
is no fight.)
Then the wheel handler 2836 and vc-zoom/reset (4514, 4528, 4539) may keep calling
`controls.update()` — they are now unreachable during walk because:
**B2 — MUST: guard every camera-affecting entry point on walkMode.**
  - wheel handler (2807): first line `if (walkMode) return;` (before the viewMode check),
  - global keydown (5521-5647): top guard after the input-field check:
    `if (walkMode) { /* only walk-internal keys handled in walk's own handler */ return; }`
    — preserves WASD/arrows for walking (walk handler 8038-8043 still runs, it is on
    window and independent), and kills the B/V/R/M/arrows corruption class. Keep Ctrl+S
    reachable? NO — during walk, block it too (avoid mid-walk save dialogs changing
    focus); document in the guide.
  - `applyViewMode` (4478): `if (walkMode && mode !== '3d') { switchView stays 3d;
    return; }` — simplest correct form: early-return for any non-3d mode while walking,
    plus a toast "Exit walk mode first (Esc)".
  - `exitWalkMode` (7980-7997): restore §3 state BEFORE `controls.enabled = true;` and
    set `controls.target.copy(preWalk.target)` so the orbit resumes exactly where the
    user left the orbit sphere — one `controls.update()` then `requestRender()`.
  - keep `startContinuousRender()` on enter / `stopContinuousRender()` on exit (7977/7983)
    — verified compatible with the S24 on-demand loop (2862-2918) and with the s17 gate's
    walk-frames assertion (sprint17_quality_gate.py:439-461 drives w→frames>0→Escape).
**B3 — MUST: pointer-event routing during walk.**
With B1, OrbitControls never calls update() during walk, so a stale drag cannot lurch
the view even if events reach it; `controls.enabled=false` (7960) blocks the r160
pointer handlers (verified 996/1025 guards). Two additions:
  - wheel: covered by B2 (early return).
  - keep the walk drag-look listener on window (8066) — verify during build that NO
    OrbitControls drag occurs while walk-dragging: with enabled=false and B2 return,
    neither chain can move the camera except updateWalkCamera.
**B4 — MUST: requestRender hygiene.** updateWalkCamera no longer needs its own
requestRender (animate renders unconditionally while `_continuousRenderSources > 0`,
2895). Remove it; keep one requestRender() in exitWalkMode after restore (needed because
continuous rendering has stopped at that point).

Regression guards: after the B1 edit run the full gate suite (expect s22 43, s17 81,
s11 143, s15 55, s21 55, dig 16, s26 34 — s17's walk segment and s11's walk z-index ≥100
must stay green; s22's source grep for the w/W handler string (215, 326-336) requires the
walk keydown handler to stay the literal `e.key === 'w' || e.key === 'W'`).

Byte estimate: net ≈ 0 (deleting walkLoop/_walkCheckId ≈ −300 B offsets the guards).

## 8. HELP/COPY (and byte reclaim list)

Copy updates (MUST, exact strings for the builder):
- `#walk-hint` (1261): "WASD/Arrows move • Shift sprint • Drag to look (double-click = mouse-look) • Esc exits"
  (drop the second clause if Pointer Lock is cut for bytes: "... Drag to look • Esc exits").
- Shortcuts guide View section (1538): replace the W row description with
  "`W` Walk mode (first-person; Esc exits; Shift = sprint)" — keep the exact `<kbd>` chip
  structure (s22 gate greps kbd chips and docs walk Esc, sprint22_quality_gate.py:491-495).
- Walk toast (7977): "Walk mode! WASD move • Shift sprint • Esc exits" (shorter, saves bytes).
- Help modal Walk Mode bullet (help modal body ~3046-3140 HEAD + builder offset): add one
  line "Enter at your current view's ground point; exit returns your exact previous view."

Byte RECLAIM list (do FIRST, funds the rework; all verified dead at HEAD):
| Anchor | What | ~Bytes |
|---|---|---|
| 8052-8065 | 6 × "Sprint 16: Touch handler removed" stub comment runs inside setupWalkMode | ~150 |
| 7967-7976 | `if (false && ...)` DeviceOrientation show-block + `if (false && hintEl...)` hint block (keep onWalkDeviceOrient fn + walk-motion-btn click path — they are REACHABLE via the button listener 8092) | ~120 |
| 8089 | trailing "Sprint 16: Touch handler removed" line inside joystick loop | ~32 |
| 7944-7950 | (careful) walkOrientationOffset/walkDeviceOrientationActive stay — used by 8024-8032 | 0 |
Total reclaim ≈ 300 B against ≈ 2,600 B of MUST additions → **net ≈ +2,300 B to index.html**.
Current tree 766,138 B is ABOVE the 766,000 soft cap from the builder's live edits — the
builder MUST also land reclaim (§8 table) plus any additional dead-weight trim needed to
get under 766,000 BEFORE its own walk additions; if 766,000 still can't be met, document
the exact overrun in the commit message per the task brief (hard ceiling 850,000).

## 9. Ergonomics checklist (signed off from CDP session, pre-rework baseline)

Walk mode was driven end-to-end on 8348 with real input (sprint28_evidence.py; 10
screenshots in sprint28_shots/, 13 probes in sprint28_before_evidence.json):

- [x] Boot clean, overlays dismissible with real clicks; zero console errors in session.
- [x] Enter via W AND via #btn-walk both work — but teleport to (0, y, 0) always (MUST fix §3).
- [x] Orbit-then-enter: camera at (59.8, 4.5, −33.5) → walk (0, 5.5, 0): disorienting cliff (~68 ft jump) — MUST fix.
- [x] Hold-drag look works; view is locked to ±34° pitch — too shallow to inspect shed roofs or your feet (MUST widen §2).
- [x] Look only while button held; no mouse-look option; 0.005 rad/px twitchy (MUST retune).
- [x] 1 s W-hold moved 1.8 ft on a 3 fps software-GL env (frame-locked): 36 ft/s ≡ 24.5 mph at 60 fps — MUST dt-fix (§1).
- [x] Joystick forward hold moved 1.2 ft / 0.9 s (same frame-locked defect, same fix path).
- [x] Scroll wheel during walk: handler runs (no walkMode guard, 2807-2838); net drift
      measured 0.0 ft ONLY because the 3 fps walkLoop overwrote it — on real hardware it
      teleports the camera to an orbit sphere around (0,0,0) (RC1+RC3/RC4) — MUST guard (§7 B2).
- [x] B during walk: viewMode switched to 2d with walkMode still true (screenshot
      s28_before_06) — walk then fights the ortho camera; R/M/arrows identical class.
- [x] Esc exit teleported 55.2 ft to the hard-coded corner (25, 40, 50), rotation zeroed — MUST restore §3.
- [x] Esc single press also runs the global Esc chain (deselect/panels) — keep per §7 B2 scoping.
- [x] Joystick buttons visible at bottom center, 52 px circles, pointer-events auto — kept as-is (§6).
- [x] No shed collision exists today (10×10 shed placed; walk passed through) — MUST add §4.
- [x] No motion-sickness risk factors beyond bob were found; FOV 50 is a sane base for the 55-sprint nudge.

Signed: Caddy (webdev) — evidence files listed at top; every checklist row maps to a probe
key in sprint28_before_evidence.json or a cited line ref.

## 10. Acceptance criteria for the builder (verifier reuse)

1. Enter walk from ANY orbit pose (incl. orbit target near a yard corner) → walkPos.xz
   within 2 ft of the raycast ground point; view faces the yard center (yaw delta < 15°).
2. Exit walk → camera position + rotation byte-identical to pre-enter snapshot (±1e-4).
3. Hold W for 5 s at any consistent FPS: distance ≈ 22 ft ±20% (4.4 ft/s), independent of
   FPS (test at 3 fps and 60 fps throttles if available).
4. During walk: `b`, `v`, `r`, `m`, arrows, `w`-outside-walk-handler produce NO view/camera
   changes except walk's own; wheel changes nothing visible.
5. controls.update() provably skipped during walk (instrument or code-audit), and no
   second rAF chain exists (walkLoop deleted).
6. Walk into the shed footprint: camera stops at the boundary, lateral slide works.
7. #walk-joystick forward/back/left/right still work (mousedown/up/leave), speed matches
   keyboard at dt parity.
8. s22 guide rows + kbd chips intact; walk Esc doc line updated to new wording.
9. All 7 gate suites green: s22 43, s17 81, s11 143, s15 55 (task brief expectation),
   s21 55, dig 16, s26 34 — on the builder's own port only.
10. index.html ≤ 766,000 B after §8 reclaims (else documented exactly, ≤ 850,000 hard).