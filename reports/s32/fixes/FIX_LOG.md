# Sprint 32 FIX LOG — sole-editor fixer

Worktree `/root/byd32-fix`, branch `s32-fix` @ `75a9104` (S31.2). Byte cap 768,000.
One commit per fix, prefix `S32-<id>:`, author Caddy <caddyaibot@gmail.com> via `git -c`.
Vision: glm-5.3-flash temp 0, sequential. Evidence under `reports/s32/fixes/`.

Before-state probes: `probe_before.py` → `probe_before.json` (all defects reproduced on :8380):
- share copy → toast `✕Copy failed - select the link manually` (nav.clipboard EXISTS, isSecureContext=true, writeText rejects; `document.execCommand('copy')` returns true)
- export menu open @1280×800 → rect y=45.5 h=214 (bottom 259 ≫ topbar bottom 52), `elementFromPoint(center)` = CANVAS (REG-D01 confirmed); `#export-stl` Playwright click timed out under clip (stl_click FAIL recorded in probe run 1)
- topbar: scrollWidth 2656 / clientWidth 1280; wheel + Shift+wheel leave scrollLeft=1047 (unchanged); scrollBy works
- contour toggle on dug terrain (min −15/max 0 ft) → contourOverlay LineSegments CREATED, visible:true, 640 verts, in scene → yet 0 line pixels on screenshot (occlusion suspected, not a builder no-op)
- cut/fill: panel open before dig `fill 77.2 yd³` → after 2nd dig (terrain min −15) panel unchanged `77.2` (stale)
- label create works; dblclick near sprite → modal does NOT open (edit/delete dead confirmed)
- night 23.9h: starField visible, 800 pts, opacity 1; visible dark-sky region 36,413 px → **0** star-bright px, 0 moon px

---

## S32-C1 — Share Copy always-fails on http (A×B conflict arbitration)

**Verdict on the conflict:** BOTH agents saw real behavior. Root cause: `navigator.clipboard`
exists on `http://127.0.0.1` (Chromium treats localhost as secure), so the secure branch runs,
but `writeText()` rejects (document focus/permission in headless + http quirks) → catch →
A's 'Copy failed' toast. B's run had writeText resolve → success toast. The existing
textarea fallback was dead code (only reachable when `navigator.clipboard` is undefined —
practically never on Chromium).

**Fix:** secure path stays; on rejection fall through to textarea+`execCommand('copy')`
(moved out of the `else`, made primary fallback); exec failure → honest error toast.

- Files: `index.html` (share-copy handler; 5 redundant S23 whole-line comments trimmed to
  pay the byte bill — comment-stripped identity verified via size_budget js/css/id gates)
- Commit: `e051241` `S32-C1: share-copy falls back to textarea+execCommand when writeText rejects`
- Verification: after `after_share_copy.json` — toast `✓Link copied to clipboard!`
  (toast-success) on first click AND 3/3 repeats, zero pageerrors;
  vision (call 1): toast reads "Link copied to clipboard!" with green success checkmark.
  Evidence: `after_share_copy.py/.json/.png`, `vision_log.txt`
---

## S32-C2 — Export menu clipped by topbar overflow-y:hidden (D×E conflict arbitration)

**Verdict on the conflict:** D is right for real users; E's "downloads worked" were
artifacts — E never recorded a `#btn-export`/`#export-menu` click in evidence, and my
repro on 75a9104 shows Playwright's `#export-stl` click (with its own scroll/force
semantics) exported STL while a raw CDP mouse click at the item center hit CANVAS and
timed out with no download (`diag_export_click.py`). REG-D01 confirmed: menu rect
y=46..260 vs topbar bottom 52; elementFromPoint(item center)=CANVAS.

**Fix:** `#export-menu` → `position:fixed`, re-parented to `document.body` at setup,
re-positioned under the button on each open (follows topbar horizontal scroll).
S30 overflow cue + topbar geometry untouched (s17 gate asserts `#btn-export`
visibility only).

- Files: `index.html` (menu markup + export setup block)
- Commit: `7612360` `S32-C2: export menu portaled to body (was clipped by topbar overflow-y:hidden)`
- Verification: `after_export_menu.json` — parent=BODY, centerHit=export-heightmap
  (was CANVAS), itemHitIsItem=true at BOTH 1280×800 and 1024×768; raw mouse click at
  item center → download `backyard-design.stl` (`after_export_rawclick.json`);
  vision: 1280 "fully rendered … no clipping" (after 1 empty-response retry) and
  1024 "fully visible and uncut, all four options". Before shot showed NO menu
  (vision: "no dropdown menu visible"). Evidence: `diag_export_click.py`,
  `after_export_menu.py/.json`, `after_export_rawclick.py/.json`,
  `before_export_menu_1280.png`, `after_export_1280.png`, `after_export_1024.png`

---

## S32-P0 — Welcome prompt + guided tour unreachable on first session (C32-A01/A02, R32-D07)

Root cause (confirmed in source): wizard-hide MutationObserver set `welcomeShown=true`
on ANY close and showed a toast instead of the modal; `showWelcomePrompt()` had zero
live callers; `Onboarding.init`'s `if (!s.tourCompleted && !s.welcomeShown) {}` was empty.

**Fix:** observer branch distinguishes first session (no `backyard-design-autosave`
objects -> `Onboarding.showWelcomePrompt()`) from repeat session (toast, unchanged);
init's dead branch now covers wizard-never-ran boots (delayed guard, observer owns
the wizard-visible path).

- Files: `index.html` (setupWizardObserver + Onboarding.init)
- Commit: `1cc267f` `S32-P0: first-session welcome prompt + tour reachability restored`
- Verification (`p0_flow.py` -> `p0_flow_results.json`, fresh profiles):
  - A: wizard finish -> `#welcome-prompt` visible (was toast-only); vision reads the
    modal with all five quick-start options.
  - A: `#wp-tour` -> tour Step 1 of 6 (vision: "STEP 1 OF 6" + dots) -> Next x5 ->
    Step 6 (vision yes) -> Finish -> toast 'Tour complete!', `tourCompleted=true`,
    restart pill visible (vision: green Take Tour pill).
  - B: wizard skip -> modal (vision yes) -> `#wp-remind-later` closes + toast.
  - C: `#wp-scratch` -> modal closes, 'Your empty yard is ready!' toast.
  - D: `#wp-template` -> modal closes, 'Choose your yard shape...' toast.
  - E: REPEAT session (autosave present) -> toast only, NO modal (per brief).
  - F (`p0_flowF.json`): tourCompleted profile -> pill visible -> click -> tour starts.
- Screenshots: `p0_after_finish_modal.png`, `p0_tour_step1.png`, `p0_tour_step6.png`,
  `p0_tour_done_pill.png`, `p0_after_skip_modal.png`

---

## S32-P0 (part 2) — Contour lines never render (C32-A03, R32-D06)

**Root cause (proven by isolation, reports/s32/fixes/diag_contour*.py):** the contour
overlay was `LineSegments` + `LineBasicMaterial{vertexColors:true, linewidth:2,
polygonOffset:-2}`. SwiftShader rasterizes **~0 px for vertex-colored lines** — in the
same live session a plain-color `LineBasicMaterial` line painted 108 px while a
vertexColors line painted 0 px; the overlay mesh itself was healthy (verts, visible,
frustum, camera all verified OK) yet never appeared. The audit's "mesh builds, visible,
renders nothing" is exactly this.

**Fix (index.html ~8630-8760):** contours now build as **flat quad ribbons** —
`Mesh` + `MeshLambertMaterial{vertexColors, DoubleSide}` at lift +0.08 over
`marchContourLevel` segment pairs (width 0.18 ft), matching the proven-painting
heatmap pattern. `removeContourLines()` traverse-removes all `isContourOverlay`
objects; the toggle toasts honestly when flat terrain yields no lines at the interval.

**Verify (reports/s32/fixes/verify_contour_diff.py, diag_final.py):**
- OFF-vs-ON pixel diff: **5296 px @1280 / 4911 px @1024**, bbox confined to the pit
  ([713,866,313,476] / [588,734,301,458]) — no UI churn in the diff.
- Vision (glm-5.3-flash, /tmp/ribcrop_real.png + c1280f_on crop): "dark contour lines
  clearly visible, forming concentric rings across the pit floor and continuing as a
  descending spiral down the funnel-shaped walls".
- Honest flat-terrain toast verified earlier (after_contours2 run).

**Commit:** aeeca48. Byte bill paid in-file; budget 767,943/768,000 (+57 headroom).

---

## S32-P1 (1/3) — Topbar vertical wheel dead (R32-D04)

Root cause: document-level wheel handler only respected `overflowY: auto/scroll`;
#topbar is `overflow-x: auto, overflow-y: hidden` so wheel over it fell through to
preventDefault + camera zoom (evidence: 900px viewport, sw=1713/cw=900, wheel →
scrollLeft stayed 0, camera (25,40,50) → (31,50,63)).

Fix: wheel handler now checks `closest('#topbar')` first; overflowing topbar
consumes `deltaY` as `scrollLeft` and returns. Verify: scrollLeft 0 → 240,
camera unchanged. Commit: `4a57fa8`.

---

## S32-P1 (2/3) — Label edit/delete dead code (C32-E-01)

Root cause: `showLabelEditModal` had exactly one live caller — the label-creation
click (`labelId=null`); no handler ever opened the modal for an existing label
sprite, so Edit/recolor/Delete were unreachable UI.

**Fix (index.html, after the label-creation click handler):** `#viewport`
`dblclick` listener raycasts the label sprites (`raycaster.intersectObjects`
over `labels.values().map(l=>l.mesh)`) and calls `showLabelEditModal(hit.
userData.labelId)` — populating text+color, Delete button visible. Creation
path untouched.

**Verify (/tmp/label_full2.py -> after_label_edit.json):**
- Creation flow intact: btn-label -> click -> modal open, saved 'Pond'/#ff8800.
- dblclick at sprite screen-projected point -> modal opens 'Edit Label' with
  text 'Pond', color '#ff8800', Delete visible.
- Edit: text 'Koi Pond' + '#33ccff' -> labels map updated (n=1).
- Delete: modal Delete btn -> labels.size 0.
- Vision (3 calls): created pill 'Pond' visible at yard center; Edit modal
  shows field/color/Delete; after edit the pill reads 'Koi Pond'.
- pageerrors: none. Screenshots: label_created.png, label_edit_modal.png,
  label_edited.png, label_deleted.png.

**Byte bill:** +609B fix paid by trimming 14 stale S29/S30/S31 in-file
comments to short markers (-837B). Budget 767,705/768,000 (+295).
Commit: `343281c`.

---

## S32-P1 (3/3) — Cut/fill panel stale while open across digs (C32-E-02)

Root cause (live repro on 75a9104+/fixes, /tmp/e2_repro3.py): with the panel
enabled BEFORE digging, mid-stroke terrain updates flow through the debounce
timer -> `applyTerrainFull(region)` — the REGION branch of applyTerrainFull
never called `updateCutFillVolume` (only the full-rebuild else-branch did), so
the panel stayed at 0 yd³ while terrainMin hit -15.00. The pointer-up flush
path (`_flushTerrainFull` -> `applyTerrainFull(null)`) does hit the else-branch,
which is why OFF->ON or enable-after-dig showed exact values (matches E's
J32-E-01 note).

**Fix (index.html, applyTerrainFull region branch):** add the same guarded
`updateCutFillVolume()` call the full-rebuild branch has. Arithmetic untouched.

**Verify (/tmp/cutfill_verify.py -> after_cutfill_refresh.json):** panel
enabled BEFORE any dig; 3 consecutive digs with NO toggle:
0 yd³ -> 43.2 -> 77.8 -> 121.0 yd³ fill (terrainMin -14.27/-14.27/-14.66),
each read live while the panel stayed open. pageerrors: none.
Vision (1 call) on cutfill_panel_crop.png: panel (titled "Earthwork Volume")
reads Fill 121.0 yd³ — matches the DOM read at dig 3.
Screenshot: cutfill_live_panel.png, cutfill_panel_crop.png.

**Byte bill:** +182B. Budget 767,887/768,000 (+113).
Commit: `e7619f6`.

---

## S32-P2 — Night-sky investigation (R32-D01 stars, R32-D02 moon)

**Moon — IN-APP BUG, FIXED.** Live probe: moonMesh EXISTS in scene (visible:true,
parented to Scene at (-40,50,-30) — D's "absent from traversal" was wrong), but
at the default camera (25,40,50) it projected to NDC y=1.88 → screen y=-278,
i.e. always above the viewport top. `updateSky` hard-set y=50 every frame.
Fix: `position.set(-40,12,-30)` for moonMesh + moonLight (sweep of y=12..30
showed y=12 lands at screen (597,134), upper sky). After: NDC y 0.78,
2100 moon-disc px at that region; vision (1 call): "large pale/cream circle
visible in the upper-left/center of the 3D viewport".
Evidence: night_moon_after.png, night_investigation.json.

**Stars — ENVIRONMENTAL (documented, code left correct).** App state is healthy
at 23.9h: starField visible, 800 verts, opacity 0.6, camera.far 1000 > dome 550.
Four live experiments, all zero star pixels:
1. shader size constant 300->900 (larger attenuated points);
2. constant gl_PointSize=3.0 (screen-space points);
3. texture2D sampling removed, plain-color fragment;
4. control: bare 30-point red 8px cloud at z~10-30 from camera, no texture —
   still 0 pixels.
Conclusion: this Chromium/SwiftShader rasterizes NO gl.POINTS at all — a hard
environmental limit, not an app defect. Star code reverted to the original
textured attenuated shader (correct on real GPUs); proof in
night_investigation.json. Before-state evidence: before_night_23h.png,
night_239_fixed.png (vision: no stars, no moon pre-fix).

---

## S32-P3 — Small UX batch (J32-B02, J32-B03, E-minor)

**1. Recovery 'Discard' -> 'Start Fresh' (J32-B02).** Visible label only;
`#rb-discard` id, aria and behavior untouched (no gate asserts 'Discard').
DOM: label reads 'Start Fresh'; vision (1 call): heading 'Restore unsaved
changes?', buttons 'Restore' + 'Start Fresh'. Click clears banner + snapshot
(snapGone:true).

**2. Single recovery path (J32-B03).** `renderWizard` step-1 template now emits
the green 'Continue previous design' button ONLY when an autosave exists AND
the recovery banner is not visible. Verified both ways:
- boot with recovery banner -> bannerVisible:true, continueBtn ABSENT;
- after Start Fresh (banner cleared, autosave persists) -> banner absent,
  continueBtn PRESENT.

**3. Permit region switch preserves typed inputs (E minor).** Region 'change'
only resets setback/maxheight/fenceheight when the user has not typed since
boot (`permitRegion.dataset.touched` set by any input on the three fields;
cleared after applying a region so a manual region re-pick re-applies defaults).
Verify: typed setback 10/fence 4 survive generic->tx switch (10/4); fresh
untouched switch applies region defaults (5/6).
Vision (1 call): permit panel reads setback 5 / max 12 / fence 6 (defaults
state, panel healthy).
Evidence: after_p3_ux.json, p3_recovery_boot.png, p3_recovery_discarded.png,
p3_permit_preserved.png.

**Byte bill:** +302B fixes, -274B comment trims (incl. retiring the long
S29-R3e comment). Budget 767,987/768,000 (+13).
Commit: `e0e8eef`.

---

## GATE BATTERY (final, all on :8380, index 767,987 B)

- s11: 143/143 PASS
- s15: 52/52 PASS
- s17: 81/81 PASS
- s21: 55/55 PASS (topsoil contract untouched)
- qa_s21: 16/16 PASS
- s22: 43/43 PASS
- s23 --skip-vision: 24/24 PASS
- s29 --skip-vision: 33/33 PASS
- size_budget: PASS (767,987/768,000, headroom +13)

## NOT FIXED (with reasons)
- Stars at night (R32-D01): environmental — SwiftShader rasterizes zero
  gl.POINTS (even a bare red 8px control cloud paints 0 px). Code left
  correct-for-real-GPU; proof in night_investigation.json.
- Dig Down chip x Sun pill overlap (J32-B01): NOT touched this sprint —
  brief lists it as known-open with fix direction from S30 verifier, but any
  move risks the s29-locked geometry battery; queued with the render-sprint
  out-of-scope items. (All other P3 items fixed.)
