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

**Commit:** 7bb5734. Byte bill paid in-file; budget 767,759/768,000 (+241 headroom).
