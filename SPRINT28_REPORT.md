# Sprint 28 Report — Walk-Mode Rework

Date: 2026-08-31
Swarm: root/blackboard t_b1b841ad · spec t_63d5db15 (sprint28_walk_spec.md @ 3eec128) · builder t_80dc33f7 (this card) · verifier t_4e6c85f3
Work: local commit on main (NOT pushed — only a "push" card may push). Base: 9f02942 (post-Sprint-27 origin/main).
Bytes: 760,362 on disk (cap 766,000; hard ceiling 850,000). Note: the run-43 heartbeat's "759,529" was a character count; byte count is 760,362.
Walk rework diff: +199 / −71 lines in index.html (single file, Three.js 0.160 unchanged).

## What shipped

All 15 spec MUSTs implemented; 2 NICEs shipped (pointer lock, Alt slow-walk); 1 NICE deferred (WebAudio footsteps). The five verified root causes from the auditor's t_63d5db15 handoff are fixed:

1. **0,0 orbit pivot during walk (B1 — sole camera authority).** `animate()` is now the only camera authority: during walk it skips `controls.update()` entirely (in r160 `controls.enabled=false` does NOT gate `update()`, which re-applied the orbit spherical around `controls.target=(0,0,0)` every frame) and `updateWalkCamera(ts)` owns the camera. The parallel `walkLoop`/`_walkCheckId` rAF chain and its 100 ms watchdog interval are deleted — one render loop, no frame fight. Gate asserts `walkLoop` refs = 0 and the `animate()` walk branch exists.
2. **Input routing (B2).** Wheel, zoom in/out, reset, 2D/3D view switching, the app-level key handler (B/V/R/M/T/G/arrows/Ctrl+S), and the terrain brush 1-7/[/] handler are all guarded on `walkMode` during walk. Escape still falls through to the S23 topmost-layer chain (one press = walk-exit + topmost-panel-close, per spec §9).
3. **Frame-locked movement (dt normalization).** Movement is now semi-implicit Euler with accel 40 ft/s², exponential friction (exp(−9·dt)), speed cap 4.4 ft/s (sprint ×1.8, Alt ×0.45), all integrated with a dt clamped to 0.25 s (tab-switch spike guard; 0.1 would clamp real dt on this software-GL host at 3–12 fps). View-relative basis from `walkYaw` (forward = (0,0,−1) rotated yaw, YXZ). Also fixed: the old code used a `Vector2` with `.z`, silently poisoning `walkPos.z` with NaN — now a plain object.
4. **Enter-at-current-position + exact-exit restore.** Enter raycasts `controls.target` down onto `yardMesh` (never (0,0); clamps to yard minus 1 ft margin; L-yard notch exclusion), faces yard center (`yaw = atan2(x,z)`), and snapshots the exact camera pose + controls state. Before snapshotting, in-flight orbit damping is fully drained via `controls.update()` loops while the visible position is restored, so r160's private `sphericalDelta` is zeroed without the user seeing it applied — the same problem that caused the auditor's measured 55 ft Esc teleport. Exit restores the EXACT saved position and quaternion (posErr 5e-9, quatErr 0 on the gate), re-aims with `lookAt` from the final position, then drains residual delta again (120 damping calls) and pins the pose so post-exit `animate()` cannot drift it.
5. **Movement quality.** Terrain following via existing `getTerrainHeight` (bob never mutates `walkPos.y` — applied only at the camera copy); rectangle yard bounds with hard clamp; L-yard notch slide-out; solid-object collision as AABB push-out on the shallower axis with velocity kill + lateral slide (flat walkable types and non-heavy sheds are walkable, per spec §4 priority walkables); sprint FOV lerp 50→55; head-bob default ON, 0.09 ft at cadence 8, toggleable via command palette ("Toggle Head Bob") and disabled under `prefers-reduced-motion`; drag-look re-tuned to 0.0026 rad/px with ±85° pitch; double-click pointer-lock (guarded: the Esc that releases pointer lock only unlocks, a second Esc exits, via a 250 ms unlock guard); joystick feeds the same wish-vector (clamped ±1) at keyboard speed; mobile tilt-look preserved.

Copy updated per spec: walk hint, Help "Advanced Features" walk bullet, shortcuts panel W row. `enterWalkMode`/`exitWalkMode` remain window-exported and call-compatible; no element IDs or data-* attributes changed; CSS brace-balanced (970/970); `node --check` clean.

## Gates (final bytes md5 c2648171, 760,362 B, port 8349)

- sprint28_walk_gate.py (NEW, real CDP/Playwright): **23/23** — (a) drag rotates without translating (posDelta 0.0000 ft), (b) W follows view direction (180° reversal flips displacement, dot −22), (c) dt-normalized (3× throttled traversal ratio 1.00, within 10%), (d) exit restores exact pre-walk camera (posErr 5.2e-09, quatErr 0) + controls.target runtime check, (e) joystick moves (2.33 ft) + Esc exits, (f) bounds (worst overflow 0.000 ft on 50×100), (g) shed footprint blocked + lateral slide works, (h) sprint FOV 55 + palette head-bob toggle, + 6 static/audit assertions + zero console page errors. Re-verified LIVE this run (23/23) on the final bytes after the run-43 timeout.
- sprint22: **43/43** · sprint17: **81/81** (BASE_URL harness — `--port` unsupported, documented invocation note below) · sprint11: **143/143** · sprint15: **52/52** (true baseline; the brief's "55" is a known misprint per Hunter C sweep + S27 pusher) · sprint21: **55/55** · qa_s21_dig_visibility: **16/16** (BASE_URL harness) · sprint26: **34/34**
- Legacy total: **424/424**
- sprint27_digperf: **9/13** — the 3 documented host-ceiling deviations from the S27 baseline (absolute avg-fps, worst-1s, zero_new_programs 11→12 one-time warm-up), plus modeswitch longtask variance: max 259 ms battery / 174 ms recheck — inside the 92–459 ms band documented on the SHIPPED sprint-27 bytes (SPRINT27_REPORT residuals); reentry compiles/links = 0 and dig-path CPU ~5% both still hold. Variance, not a walk-rework regression; flagged transparently rather than masked.
- Static: CSS braces 970/970 balanced; `node --check` rc=0; window exports intact (`enterWalkMode`, `exitWalkMode`, new `walkBobEnabled`).

Harness invocation note for future workers: sprint17 and qa_s21 ignore `--port` and read `BASE_URL` env (defaults 8175 / 8311). Run as `BASE_URL=http://localhost:<port> python3 …`.

## Byte accounting

765,000→766,000 concern did not materialize: started this rework at 751,024 (post-S27 push), ended at 760,362 (+9,338 net) — under the 766,000 soft cap with ~5.6 KB headroom. Reclaim-first was honored in-sprint: dead `if (false && DeviceOrientationEvent)` branch, dead mobile hint-swap block, the walkLoop/watchdog chain, and eleven blank stub lines were removed (~1.4 KB) inside the feature work; the ~26 KB parallel dev-chat reclaim (orchestrator note) had already landed in the 751,024 base.

## Residuals / notes for verifier t_4e6c85f3

1. sprint27 modeswitch longtask now bands 174–259 ms on this host (S27 report documented 92–459 ms residual class on the same bytes: no shader compiles, CPU-bound transition). Absolute-FPS deviations remain host-ceiling (SwiftShader; real-GPU pass still owed on the RTX A4500).
2. Collision scope: solid-footprint AABB push-out on the shallower axis with velocity kill + lateral slide — exactly the spec §4 pseudocode (playerRadius-expanded half-extents; FLAT walkables excluded except HEAVY; fences solid by footprint; buried objects still collide — no buried-check exclusion exists). Heavy shed verified (gate g/g2); decorative walkables (patio/deck/walkway/raised_bed, non-heavy) are walkable by design. The optional 30 ft early-out was not needed (per-frame CATALOG-footprint loop is within the spec's cost estimate).
3. dt clamp is 0.25 s (spec-suggested 0.1 rejected in-source: on this SwiftShader host 3–12 fps makes real dt up to ~0.3 s; clamping at 0.1 would break dt-normalization exactly where it matters).
4. Pointer lock is mouse-only and optional (double-click to engage) per spec §2; joystick/mobile paths untouched by it.
5. Push is reserved for a "push" card per brief §7 — the verifier (t_4e6c85f3) gates that handoff.