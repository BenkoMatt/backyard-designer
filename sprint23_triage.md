# Sprint 23 Verifier Triage — Claim-by-Claim Refutation Attempt

**Verifier:** reviewer (Caddy) · Run 12 · 2026-08-28
**Port:** 8305 (dedicated; 8175/8099/8115/8222 untouched) · **Mode:** READ-ONLY — `index.html` untouched at 759,791 bytes (git clean, HEAD `9adffea`)

## Method

Every CLAIM| line from the three hunt handoffs on swarm root `t_2cd9931f` was collected (21 raw → 20 unique after dedup: Hunt B's Ctrl+Shift+Z claim == Hunt C's). For each claim I attempted to **refute** it: re-ran the repro myself with real CDP/Playwright input events (mouse down/move/up, CDP `Input.dispatchKeyEvent` with desktop key semantics, real clicks on library/dock/topbar elements), and searched the cited code regions for any validation/guard that would prevent the bug. `evaluate()` was used for observation and setup only (camera positioning, state reads, `loadDesign()` probes per hunt C's established convention) — never to fake user input.

A claim **survives** only if I reproduced it and found no counter-evidence.

**Verification environment:** Playwright chromium 1280×900, real-event driven; wizard dismissed with real Escape; welcome-prompt dismissed with real click on "Start from scratch" (the overlay otherwise intercepts pointer events at canvas center — this interception is itself consistent with the hunt-B click-interception notes).

**Results: 20/20 SURVIVE · 0 refuted · 0 inconclusive.** Every earlier REFUTED/INCONCLUSIVE label in my own run log was a harness error (wrong catalog type, wrong canvas selector, un-dismissed welcome-prompt, command pushed outside the app's real code path) and was superseded by a corrected re-run recorded below.

## Surviving claims (20) — severity + evidence

Evidence PNGs: `sprint23/verify/*.png` (23 files) · machine log: `sprint23/verify/results.jsonl`

### CRITICAL (2)

**S23-V01 · Drag-undo crash — drag moves are never undoable** (hunt B c1; index.html:3768-3780)
Real mouse drag of a bush (projection-targeted at object screen coords), then Ctrl+Z: undo command's closures reference `dragObject`/`dragStartPos`, which `onPointerUp` nulls immediately after `pushCommand`. Undo throws `TypeError: Cannot read properties of null (reading 'position')` (captured via pageerror listener); object stays at dragged position; the drag command is consumed with no effect.
Evidence: `sprint23/verify/v_b1_drag_undo.png`

**S23-V02 · Properties panel renders below the fold at body level** (hunt B c2; index.html:1185)
`#properties` parent is `<body>`; `getBoundingClientRect().top` = 900 with viewport height 900 and `body{overflow:hidden}` — the panel is NEVER visible after add/select. Side effect confirmed: focusing `#pos-x` scrolls the whole app (canvas top → −435px) while the panel still isn't docked.
Evidence: `sprint23/verify/v_b2_props_below_fold.png`, `v_b2_after_focus.png`

### HIGH (10)

**S23-V03 · F1/? open shortcuts guide while typing in inputs** (hunt C c1; index.html:5270-5273 capture handler gates nothing, vs :5383 global guard)
Ctrl+K → typed "terrain" into `#cmd-palette-input` → F1: shortcuts modal opened over the palette and stole focus (`document.activeElement` = `#shortcuts-close-btn`). `?` while typing: same result. Reproduced 2/2 paths.
Evidence: `v_c1_f1_palette.png`, `v_c1_question_palette.png`

**S23-V04 · Escape cascade: one Escape closes stacked layers (wizard + guide) and runs `initWithYard`** (hunt C c2; :5409-5455 sweep + :8093-8098 unconditional wizard handler)
Wizard open + F1 guide on top → ONE Escape closed **both** (expected: topmost only) and the wizard's Escape side effect ran (`initWithYard` → welcome toast fired). **Scope correction to the claim:** the help→shortcuts stack actually closes topmost-only (help closed, shortcuts stayed) — the cascade repro is wizard+guide (and wizard+any-sweep-layer), not help→shortcuts.
Evidence: `v_c2_wizard_guide_one_esc.png`, counter-example `v_c2_help_shortcuts_counter.png`

**S23-V05 · INPUT guard swallows ALL app shortcuts while a props input has focus** (hunt B c3; :5383-5402 early return)
Focused `#rot-slider` (auto-opened props panel after add): Ctrl+A selected nothing (state.selectedIds empty), Delete did nothing (objects stayed 1). Clicked canvas to blur → Delete removed the object (1→0). Guard confirmed as total shortcut blackout.
Evidence: `v_b3_input_guard.png`

**S23-V06 · Rotation-slider undo flood evicts the ADD command from the 50-cap history** (hunt B c4; :3878-3895 change handler pushes per-change + :4061 cap)
Focused rot-slider, 60 real ArrowRight presses → undoStack hit the 50 cap (oldest evicted). 50× Ctrl+Z later: stack empty but the object STILL EXISTS (rot 0.1745 rad) — the add command was evicted, placement is unrecoverable via undo.
Evidence: `v_b4_slider_flood.png`

**S23-V07 · Ctrl+Shift+Z redo dead with desktop key semantics** (hunt B c5 == hunt C c6 dup; :5388 matches lowercase 'z' only)
CDP dispatch with real desktop `key:'Z'` + Ctrl+Shift: nothing (redoStack stayed length 1, objects stayed 0). Control: Ctrl+Y restored the object (0→1). Matches hunt C's methodology warning (Playwright synthesizes lowercase under Shift — regression tests MUST use CDP with key:'Z').
Evidence: `v_b5_ctrl_shift_z.png`

**S23-V08 · loadDesign strips non-catalog params — save/load roundtrip loses seasonColor** (hunt B c8; :1702-1721 sanitizeObjectParams iterates `cat.params` only)
Loaded a design with `tree_deciduous` params `{species:'maple', size:'M', seasonColor:'#ff8844'}` → state params = `{"species":"maple","size":"M"}`. seasonColor silently dropped; canopy color lost on every load path.
Evidence: `v_b8_paramstrip.png`

**S23-V09 · Sun Reset desyncs clock text and light from slider** (hunt A c1; :7488-7503 never calls applySunPosition)
Sun dock, slider to 20:00 (32× ArrowRight), Reset: slider=12 but clock text stayed **"20:00"**; light snapped to hard-coded (30,50,20) instead of canonical noon (−0.0, 100, 0) measured immediately before.
Evidence: `v_a1_sun_reset.png`

**S23-V10 · #sun-btn launcher toggles a force-hidden legacy shell** (hunt A c2; :7477-7481 vs CSS line 34 `display:none !important`)
Real click: button gained `.active`, panel class became `visible` but computed display stayed `none`, rect 0×0 — nothing opens. Positive control: dock tab `data-dock="sun"` opens the real UI. Same pattern reproduced for:
**S23-V11 · #terrain-analysis-btn** (`v_a3_analyze_launcher.png`, dock analyze works)
**S23-V12 · #innovation-btn** (`v_a4_innovate_launcher.png`, dock innovate works)

### MEDIUM (6)

**S23-V13 · loadDesign duplicate ids silently drop objects, success toast still shown** (hunt C c3; :4229 `Map.set` overwrites)
File with ids [7, 7, 8] → state ids [7, 8], 3→2 objects, toast "✓Design loaded successfully!". No warning.
Evidence: `v_c3_dup_ids.png`

**S23-V14 · loadDesign nextId collision → new add silently REPLACES a loaded object** (hunt C c4; :4171 trusts file nextId)
Loaded `nextId:5` + object id 5 (state nextId=5, count=1). Real click on a library item: new object got id 5 and REPLACED the loaded tree — count stayed 1, types changed tree_deciduous→fence_privacy.
Evidence: `v_c4_nextid.png`

**S23-V15 · Ctrl+Shift+S dead with desktop key semantics** (hunt C c5; :5390 matches 's' only)
CDP `key:'S'` + Ctrl+Shift: no prompt() dialog fired, no save toast (stale welcome toast). Control: Ctrl+S (no shift) → "✓Design saved!" toast.
Evidence: `v_c5_ctrl_shift_s.png`

**S23-V16 · Plain-click then Shift+click loses the first selection** (hunt B c6; :3691-3695 selectObject never registers in selectedIds)
Plain click object 2: selectedId=2, selectedIds=[] (empty). Shift+click object 1: selectedIds=[1] only — object 2 silently dropped; batch bar never appeared for the pair.
Evidence: `v_b6_multiselect.png`

**S23-V17 · Library items all spawn at (0,0,0), perfectly overlapping** (hunt B c7; :4460 passes explicit `{x:0,y:0,z:0}` bypassing the addObject spread at :2923-2928)
Three consecutive library clicks (bush, hedge, patio): positions `{"x":0,"y":0,"z":0}` ×3.
Evidence: `v_b7_stack_origin.png`

**S23-V18 · 'Excavate' label vs data-tmode=lower + flatten unreachable from keys 1-6** (hunt A c5; :575-582 buttons vs :15794 6-mode key array)
Button audit: `data-tmode="lower"` is labeled "Excavate" (aria too) while the handler mode is *lower*; keys 1-6 map to raise/lower/smooth/erode/dig/fill — the 7th mode `flatten` is reachable only by mouse click, never by 1-6.
Evidence: `v_a5_brush_modes.png`

### LOW (2)

**S23-V19 · Welcome toast clobbers load-success toast on every load path** (hunt C c7; :5216-5220 500ms timeout + guard at :5218)
With welcome-prompt dismissed (realistic returning-user state), loadDesign → toast "✓Design loaded successfully!" at +200ms, replaced by "ℹWelcome! Click items…" from +800ms onward through +2600ms.
Evidence: `v_c7_toast_clobber.png`

**S23-V20 · No focus trap in modals** (hunt C c8; openModal :5223-5231)
Help modal open: 13/14 Tab presses escaped to background elements (last: `#btn-cost`); focus restore on Escape works.
Evidence: `v_c8_focus_trap.png`

## Corrections & notes for the fixer (from triage, not new claims)

1. **S23-V04 scope:** cascade repro is wizard-under-guide (and by code reading, wizard under ANY sweep-closed layer); help→shortcuts is topmost-only. Fix the unconditional wizard Escape handler + consider topmost-only break in the sweep.
2. **S23-V07/V15 regression tests** must dispatch CDP `Input.dispatchKeyEvent` with uppercase `key:'S'`/`'Z'` (desktop semantics) — Playwright `keyboard.press` synthesizes lowercase under Shift on this platform (confirmed by hunt C; my CDP runs agree).
3. **S23-V02 + S23-V05 interact:** the auto-opened props panel is invisible AND swallows shortcuts while focused — a user adding an object is stranded until they click away.
4. **S23-V13/V14:** same loadDesign block (:4171-4232) — fix nextId reconciliation (`max(file.nextId, maxLoadedId+1)`) and dup-id handling (reject/warn) together.
5. **Drag repro recipe (S23-V01):** dismiss welcome-prompt first (`#wp-scratch`); position camera above object (setup-only); project world→screen via `_bydTHREE.Vector3.project(activeCamera)`; drag ≥ ~1px threshold. The welcome-prompt panel otherwise intercepts the pointerdown (its `wp-template` button sits at canvas center).
6. **S23-V09 canonical noon reference:** slider input event at 12:00 gives light (−0.0, 100, 0); Reset gives (30, 50, 20). Fix = set slider, update `#sun-time-display`, call `applySunPosition()`.

## Refuted claims

None. All 20 unique claims survived refutation attempts. (Hunt-internal "suspected and cleared" items were already cleared by the hunts themselves and were not re-litigated.)

## Baseline integrity

- `index.html` 759,791 bytes before and after verification; `git status` clean for index.html; HEAD unchanged at `9adffea`.
- No edits made to any application file. New files: this report + `sprint23/verify/` evidence (23 PNGs + results.jsonl).