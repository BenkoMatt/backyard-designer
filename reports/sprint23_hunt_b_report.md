# Sprint 23 — Bug Hunt B: Objects, Selection & Editing (read-only hunter)

- Worker: webdev (Caddy) · Card: t_488b362b · Port: 8302 (exclusive)
- Method: Playwright/Chromium headless, REAL CDP mouse+keyboard input events only.
  `page.evaluate()` was used ONLY for read-only state observation (`window._bydState`,
  `window._expertTest.raycastAt` for click-coordinate lookup) — never to invoke app
  functions for a click/key path.
- Baseline at start: commit 0ed89dd, index.html 759,791 bytes. NO app files modified
  (hunt is read-only). Sprint 22 gate re-run at end on my port: 43/43 PASS (no
  regression introduced; results saved to sprint22_quality_gate_results.json).

## VERIFIED CLAIMS (8) — all reproduced with real input events

CLAIM|critical|onPointerUp drag undo command (index.html:3768-3775)|Drag any object to a new spot, release, press Ctrl+Z|Object returns to its pre-drag position (drag pushes an undo command; Undo button is enabled by updateUndoRedoButtons)|Undo throws "TypeError: Cannot read properties of null (reading 'position')" and the object stays moved: the command closures reference module-level dragObject/dragStartPos, which onPointerUp nulls at lines 3779-3780 immediately after pushCommand. Drag moves are NEVER undoable; the error fires on every attempt. Repro: drag fence from (0,0) to (-15.5,-22.1), Ctrl+Z -> position unchanged, pageerror recorded.|sprint23_hunt_b_0X_bug5_drag_undo.png + /tmp/hb/results_a3.json (P6)

CLAIM|critical|index.html layout: `<div id=properties>` (line 1185) is a BODY-level sibling of #main instead of a child of the #main flex row (FEATURE_INVENTORY.md documents it as the Right Sidebar; CSS defines #main as flex row)|Open app, add any object from the library (properties panel opens)|Properties panel docks as the right sidebar beside the 3D canvas|Panel renders at y=900 with parent <body> — entirely below the 900px viewport. body has overflow:hidden so there is no scrollbar; the panel is NEVER visible on screen. It only scrolls into view when keyboard focus enters one of its inputs (focus-scroll), which simultaneously scrolls the whole app including the canvas off-screen (canvas rect.y -> -433). Canvas shrinks to 1320x848 because #main's flex row has only sidebar+viewport.|sprint23_hunt_b_0X_bug8_props_below_fold.png + /tmp/hb/results_b.json (P11)

CLAIM|high|Global keydown handler (index.html:5386-5402)|Select an object, press Ctrl+D / Ctrl+A / Alt+Tab / Delete / Escape while the keyboard focus is in ANY properties-panel input (e.g. after clicking the rotation slider or a number field — the panel opens automatically on every add, and Tab lands in its inputs)|Shortcut performs its action|All shortcuts are dead: the handler's first line returns early for INPUT targets (line 5383) and never special-cases the app's own editing panel. Ctrl+Z/Ctrl+D/Ctrl+A/Alt+Tab/Delete/Escape all no-op while a props input has focus; Ctrl+D works again only after clicking away to blur. This also breaks command-palette-less workflows right after every object add.|sprint23_hunt_b_0X_bug1_slider_focus.png + /tmp/hb/results_a2.json (P3)

CLAIM|high|showProperties rot-slider 'change' handler (index.html:3878-3895) + pushCommand 50-entry cap (4061)|Select object, click rotation slider, hold ArrowRight (~60 presses, each fires a separate 'change'), click away, then Ctrl+Z repeatedly|A continuous slider adjustment creates ONE undo entry (as arrow-key nudging does via its 600ms debounce); undoing all actions empties the yard|Every keypress pushes a separate command: 5 presses = 5 entries (measured 1 -> 6). 60 presses overflow the 50-deep cap and EVICT the add command; after 50 undos the object still exists with an empty undo stack — the placement is unrecoverable via undo.|sprint23_hunt_b_0X (P2, P6b) + /tmp/hb/results_a4.json

CLAIM|high|Global keydown handler redo branch (index.html:5388) — Ctrl+Shift+Z|Edit any object param (creates undo entry), press Ctrl+Z, then press Ctrl+Shift+Z|Ctrl+Shift+Z redoes the undone change (documented in Help line 1490, shortcuts guide line 1555, aria hint line 150)|Nothing happens: with Shift held e.key is 'Z' (uppercase), so `e.key === 'z' && e.shiftKey` never matches; redo is unreachable via this combo anywhere in the app (Ctrl+Y works). Note: the expression `e.key === 'z' && e.shiftKey || e.key === 'y'` also binds redo to plain Ctrl+Shift combos of other keys only when key is exactly 'z'/'y'.|sprint23_hunt_b_0X (P1) + /tmp/hb/results_a2.json

CLAIM|medium|onPointerDown shift/ctrl-click -> selectObjectMulti (index.html:3638, 3691) vs selectObject (3310)|Click object A once, then Shift+click object B (the standard way to build a multi-selection)|A and B both selected; batch bar shows "2 selected" — Shift+click should EXTEND the current selection|Plain selectObject() never inserts the object into state.selectedIds, so the first Shift+click starts from an empty set: A is silently dropped and only B is selected. Multi-select only works if EVERY object is Shift+clicked, including the first; Shift+clicking an already-Shift-selected object then REMOVES it instead of extending.|sprint23_hunt_b_0X_bug6_multiselect.png + /tmp/hb/results_a4.json (P7b)

CLAIM|medium|buildLibrary click handler (index.html:4459-4478) vs addObject no-position spread (2923-2928)|Add any 3+ items from the object library without dragging|Successive placements occupy distinct positions (addObject's fallback spreads items by count*5 — the code path exists for exactly this case)|Every library click passes explicit position {x:0,y:0,z:0}, bypassing the spread: all items spawn at the exact same world point, perfectly overlapping. Users see one object; the rest are hidden underneath, reachable only via Alt+Tab. Repro: Privacy Fence + Shade Tree + Garden Shed all serialize at exactly (0,0,0).|sprint23_hunt_b_0X_bug7_stack_origin.png + /tmp/hb/results_a4.json (P10)

CLAIM|high|serializeDesign/loadDesign (index.html:4106-4238, sanitizeObjectParams 1702-1721)|Build a design with objects whose params include keys not in CATALOG[type].params (e.g. Shade Tree's seasonColor, added at runtime by seasonal logic), Save via Ctrl+S/topbar, then Load the downloaded file|Loaded state is identical to saved state (byte-fidelity roundtrip)|sanitizeObjectParams keeps ONLY keys listed in cat.params, so seasonColor:"#4a8b5c" is silently stripped on load: serialize(load(save(state))) != serialize(state) for tree_deciduous (params shrink from {species,size,seasonColor} to {species,size}). Canopy color info is lost; any non-catalog param suffers the same silent drop.|/tmp/hb/results_b.json (P14) + /tmp/hb/roundtrip.json

## FLOWS TESTED (14 distinct, all with real input events; 120+ assertions recorded)

1. Library placement — single item, toast/selection/props/undo-booking/recent-chips (A-flow1)
2. Library placement across ALL 21 catalog types in one session; ids sequential; scene meshes 1:1 (A-flow2)
3. Alt+Tab cycling — order, wrap-around, all 21 objects reached (A-flow3)
4. Properties edits — number param fill, min/max clamping (9999->200, 0.5->4), rotate buttons, position inputs (A-flow4)
5. Rotation slider keyboard (ArrowRight x30) + live label update (A-flow5, probes 5b)
6. Duplicate via Ctrl+D and via props button; undo/redo of duplicate (A-flow6, A2-P5)
7. Ctrl+A select-all, batch bar, batch-delete-all, batch-delete-type, delete-undo (A-flow7, A4-P9)
8. Arrow-key nudging incl. Shift fine-step, debounced single undo entry, redo (A-flow8)
9. Drag repositioning + undo (BUG-5 crash) (A3-P6)
10. Mixed undo/redo across op types (add/param/rotate/position), interleave with new op clears redo (A4-P8)
11. Cost estimator arithmetic on a known basket — PASSED: $1,000 + $1,536 + $600 = $3,136 exact (B-P12)
12. Layers panel counts, hide/show category, scene group visibility, cost-exclusion interplay — PASSED (B-P13)
13. Save -> Load JSON roundtrip via REAL download capture + import-input file load (BUG-9) (B-P14)
14. Share modal — link hash decodes to correct compact JSON (2 objects), QR canvas drawn (14,784 dark modules), copy-button feedback, Escape closes (B-P15)

## KEY CLEAN PASSES (no claim)
- Cost arithmetic exact for the known basket; category subtotals correct; hidden-layer exclusion correct.
- Layers show/hide correctly toggles scene group visibility and restores it.
- Empty-design load clears the yard; load validates malformed yard dims.
- Share hash encodes/decodes losslessly for well-formed designs; QR renders.
- Param min/max clamping; rotate buttons; Alt+Tab insertion order; undo of param/pos/rotate ops (via keyboard path).

## EVIDENCE FILES
- Screenshots: reports/sprint23_hunt_b_01..15_*.png (placement, cycling, props edits, slider focus, duplicate, select-all/batch, multiselect, drag-undo, origin stacking, cost panel, layers, roundtrip, share modal)
- Machine results: /tmp/hb/results_a.json, results_a2.json, results_a3.json, results_a4.json, results_b.json
- Roundtrip artifact: /tmp/hb/roundtrip.json (saved design download)

## HARNESS NOTES (for fixers re-verifying)
- Opening/closing the properties panel resizes the canvas (props panel is body-level); re-scan raycast
  screen coordinates after ANY panel change before clicking a mesh.
- Playwright scroll_into_view on library items can scroll the BODY (app has no scrollbar but is
  focus-scrollable); call window.scrollTo(0,0) before canvas scans.
- After typing into a props input, blur via a real canvas click before sending app shortcuts,
  otherwise the INPUT guard swallows them (this is BUG-1 itself).
- Baseline gate re-verified at end of hunt: sprint22_quality_gate.py --port 8302 -> 43/43 PASS,
  index.html 759,791 bytes (unchanged, read-only hunt).