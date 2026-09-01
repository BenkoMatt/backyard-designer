# VISION QA — Sprint 29 Report

## Section 4 — Transient Overlays + Flow Surfaces (Agent 4: AUDIT-TRANSIENTS)

**Owner:** every transient/status overlay + print/share/cmd-palette flows.
**Method:** real CDP pointer/keyboard events (Playwright), 1280×800, glm-5.3-flash vision verdicts
(base64 image_url, temp 0), every verdict saved as a JSON sidecar next to its shot in
`reports/s29_shots/`. DOM `getBoundingClientRect` proof required before acting on any vision
claim (S23 crop-edge lesson). Byte cap checked after every edit (`size_budget.py` 4/4 at all times;
final 761,589 / 768,000).

### 4.1 Surfaces swept (before/after shots + verdict sidecars)

| Surface | Trigger | Shots (reports/s29_shots/) | Verdict history |
|---|---|---|---|
| #toast — Save tip | topbar Save Design | t1_toasts_hints_save_toast_basic_before | first-sweep findings triaged, V03 lock PASS |
| #toast — item-added/Cost tip | lib-item click + cost panel open | t1_…_cost_panel_item_toast_before, t4_…_cost_live_update | pre-fix stale-cost bug found → fixed |
| #context-hint | item drag, sculpt mode | t1/t3 …_context_hint_drag_before, …_sculpt_hint_after | CLEAN (S23-V03e suppression verified) |
| #recovery-banner | seeded `backyard-recovery-snapshot` + reload | t1/t2b/t3/t4 …_recovery_banner*, …_banner_toast_stack | overlap w/ toast found → fixed (T07); restore + discard flows verified |
| #grid-level-badge | terrain dock Grid Level slider → Y=4 | t2b/t3 …_grid_badge_after, …_grid_badge_plus_toast_after | CLEAN; stacks with toast w/o overlap |
| #depth-gauge-overlay | #vc-underground | t2b/t4 …_depth_gauge_after/_final | CLEAN (vision overlap claim = false positive, rect-checked) |
| #atmosphere-badge (S24) | default Daytime | t1/t2/t3 probes | CLEAN; compass-overlap claim disproven by rects |
| Timelapse modal | #btn-timelapse | t2/t2b/t4 …_timelapse_* | black-box canvas → poster fix (T06); hint-blocked Close → T01/T01b |
| Socialcard modal | #btn-socialcard + Regenerate | t2/t2b …_socialcard_* | CLEAN (its vision nits = topbar scroll edge, Agent 1) |
| Batch-bar | Ctrl+A multi-select | t2/t2b/t4 …_batch_bar_* | covered toolbar rows 2-3 + scale bar → lift fix (T04) |
| Print view | #btn-print (12 objects) | t2b/t3 …_print_view_* | CLEAN; 12-row table + totals render |
| Share QR flow | #btn-share, copy link | t2b/t3/t4 …_share_qr_* | contradictory captions → fixed (T05); QR pixels verified drawn |
| Cmd palette | Ctrl+K, arrows, type, Enter | t2b/t4 …_cmdk_* | CLEAN: focus, navigation, filter, execute, close |
| Full top stack | banner+toast+grid badge+atmo badge | t3/t4 …_full_top_stack / _banner_toast_stack | toast dipped 8px into banner → fixed (T07) |

### 4.2 Bugs found & fixed (all re-verified with live DOM rects + fresh vision)

| ID | Bug | Root cause | Fix | Commit |
|---|---|---|---|---|
| S29-T01 | Inactivity hint (#progressive-hint) rendered ABOVE open modals (z 500 > modal 200) with `pointer-events:auto` — blocked modal buttons (timelapse Close literally unclickable in CDP) | z-index above `--modal-z`; no suppression when dialogs open | z 500→190; MutationObserver auto-hides hint whenever any modal surface gains `.visible` | db19f8b |
| S29-T01b | 5s idle timer could pop the hint over a modal that was ALREADY open (T01's observer only watched class changes) | timer fires inside dialog | `showProgressiveHint()` bails if any modal/wizard is visible | cd71fb0 |
| S29-T02 | Cost panel stale: showed "No objects yet" with objects placed; didn't track add/remove/undo/redo | `updateCostPanel()` only ran on open/layer-toggle/season/template | called from `pushCommand`/`undo`/`redo` (all mutation paths) | db19f8b |
| S29-T03 | Pressing any bottom-left toolbar button while an object was selected DESELECTED it, closing #properties → viewport widened 320px → toolbar re-wrapped (3-row→1-row) → the pressed button moved 36px mid-press → the click landed on the canvas and the toggle was lost (Terrain/Sun/etc. needed 2 presses) | main viewport `onPointerDown` raycast/deselect had no UI-chrome guard (sibling handlers had one) | same established `e.target.closest(...)` guard added (toolbar, view-cube, dock, floating panels, right stack) | b7ec4ed |
| S29-T04 | Batch-bar (fixed, bottom:60, centered) covered toolbar rows 2–3 (excavate/analyze/innovate/sun) and the scale bar whenever the toolbar wrapped 3 rows (properties open) | static position ignores wrapped toolbar | `showBatchBar()` lifts the bar above any element intersecting its x-range (toolbar/scale bar), S23-hint pattern | 45b75da |
| S29-T05 | Share modal showed contradictory states — canvas "Design too large for QR" + caption "QR may be hard to scan" simultaneously; caption referenced a nonexistent "Save" button | caption toggle ignored wayTooLong; stale copy | caption only when a QR actually renders (210<len≤4096); "or Save" dropped | 45b75da |
| S29-T06 | Timelapse canvas was an empty black box before Play — vision read it as a broken video load | no poster state | light poster + "Press Play to preview your build" drawn on open; stage label/progress reset | 45b75da |
| S29-T07 | With recovery banner + toast stacked, the visible toast's own `translateY(-8px)` transform dipped it 8px INTO the banner (110 < 118) | `_syncTopStack` ignored the toast transform | +8px stack adjustment for the toast element (alone-state unchanged: still top 64) | a6f5ba4 |

### 4.3 Sprint 23 hard locks — verified

- **V03 (toast NEVER intersects toolbar buttons):** probed live at every toast state across all four sweeps
  (save toast, item toast, copy-link toast, stacked toast) — **zero intersections, every pass**.
- S23-V03e hint suppression under panels, S23-V03c/d top-stack sync — all still behave; T07 tightens d.

### 4.4 Vision false positives (rect-disproven, per S23 lesson)

- "Daytime pill overlaps compass": badge x 748–812 vs compass x 1208–1264 — no overlap.
- "Toast covers compass": toast x 475–805 vs compass x 1208–1264 — no overlap.
- "FPS: — spills off the status bar": FPS chip at x 311–317, bar spans 0–1280 — contained.
- "Innovate is a typo for Irrigate": Innovate opens the innovation panel — by design.

### 4.5 Cross-agent handoff (evidence attached, surfaces owned by others)

- **→ Agent 1 (core UI):** Advanced topbar overflows (scrollWidth 2656 vs 1280; only 11/25 buttons visible;
  overflow-x:auto) — vision repeatedly flags the fold button ("Label/Permits clipped"); consider a scroll
  affordance. FPS meter shows "—" or "1" in shots (reads broken). Compass needle renders past its ring.
  btn-walk sits beyond the topbar fold while a progressive tip references "Walk Mode".
- **→ Agent 2 (panels):** floating Sun button cluster overlaps the scale ruler label ("10" cut) in
  underground-view shots — bottom-cluster spacing.

### 4.6 Status

All 10 fixes committed incrementally on `s29-audit-transients` (Caddy identity), size_budget 4/4 after every
commit (final headroom +5,697 bytes). Findings appended as JSON lines to `/root/byd29-staging/S29_HANDOFF.md`
for FIXER-CONVERGENCE (Agent 5).

### 4.7 Late additions (final-verify round)

| ID | Bug | Fix | Commit |
|---|---|---|---|
| S29-T08 | Ctrl+A "Select All" collapsed multi-select to a single object (selectObject(ids[0]) reset selectedIds) — batch bar said "1 selected" while the toast promised "Selected 3 object(s)" | re-populate selectedIds after the anchor select | 31d174f |
| S29-T09 | Recovery banner lingered next to a "✓ Design saved!" toast after an explicit save — contradictory state | saveDesign/saveDesignAs clear the stale snapshot + dismiss the banner | 31d174f |

### 4.8 Full gate battery on the final tree (server :8191, my port)

| Gate | Result | Expected |
|---|---|---|
| sprint11 | **143 / 143 PASS** | 143 |
| sprint15 | **52 / 52 PASS** | 52 |
| sprint17 | **81 / 81 PASS** | 81 |
| sprint21 | **55 / 55 PASS** | 55 |
| sprint22 | **43 / 43 PASS** | 43 |
| qa_s21 (BASE_URL) | **16 / 16 PASS** | 16 |
| **sprint23** | **24 / 24 DOM gates PASS — V03 toast lock GREEN** | 24/24 required |
| sprint23 vision spot-checks | 0/5 (pre-existing: identical 5 failures at baseline 644f31c — compass needle / sidebar fold, other agents' surfaces) | informational |
| size_budget | **4 / 4 PASS** (762,303 / 768,000) | 4/4 |
| sprint16 (informational) | 29 / 32 | 29/32 pre-existing |

Sprint 23 V03 lock detail: static check PASS (showToast never forces #toast into the toolbar band) and live
check PASS (visible toast rect intersects zero toolbar buttons) — verified at every toast state during all
four sweeps (save toast, item toast, copy-link toast, stacked-with-banner toast).