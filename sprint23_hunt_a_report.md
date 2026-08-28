# Sprint 23 — Bug Hunt A: Terrain & 3D Interaction (READ-ONLY hunter)

- **Hunter:** Caddy (webdev), card `t_f8ca9fb6` — swarm root `t_2cd9931f`
- **Date:** 2026-08-27 (overnight sprint 23)
- **Baseline:** commit `0ed89dd`, `index.html` 759,791 bytes (≤766,000 budget; UNTOUCHED — no code edits made)
- **Server:** `python3 -m http.server 8301 --bind 127.0.0.1` (assigned port only)
- **Method:** Playwright/CDP, REAL mouse+keyboard events for every UI path
  (page.keyboard / page.mouse / locator.click). `page.evaluate` used ONLY to
  read state (`window._test`, `_groundVisibilityDebug`, DOM) and for test
  SETUP (camera framing, wizard dismiss). Scripts: `s23a_hunt*.py` +
  `s23a_common.py` in repo root; evidence PNGs `sprint23_hunt_a_*.png`.

## Claims (atomic, each reproduced two ways)

CLAIM|high|Sun & Shadow panel — sun-reset handler (index.html ~line 7488-7503)|Repro 1: open Sun dock via tab, ArrowRight x32 to 20:00, click Play, click Play again (pause), click Reset. Repro 2 (no Play): ArrowRight x32 to 20:00, click Reset.|Reset restores noon: clock reads 12:00 and sun light at canonical noon position (0,100,0) as produced by slider at 12:00|Clock text stays stale at '20:00' while slider=12 (repro 1: '22:45'); light sits at hard-coded (30,50,20) — canonical noon via slider is (-0.0,100,0). Handler never calls applySunPosition(); only sets slider value + hard-coded light|sprint23_hunt_a_11.png

CLAIM|high|Bottom-left toolbar — #sun-btn click handler (index.html ~line 7477-7481)|Repro 1: click the Sun launcher button in the bottom-left toolbar (Advanced mode). Repro 2: reload, repeat click, screenshot + DOM audit of computed styles|Clicking Sun opens the Sun & Shadow UI (dock or panel)|Button toggles .active (lights up), NOTHING opens: handler toggles 'visible' on legacy #sun-panel which CSS (`.legacy toolbar` rule, style block line ~34) force-hides with display:none !important, and whose children were moved into #dock-sun-content (line ~11672-77). Feature itself works via dock tab .td-tab[data-dock=sun]|sprint23_hunt_a_7.png

CLAIM|high|Bottom-left toolbar — #terrain-analysis-btn click handler (index.html ~line 8367-8371)|Same two repro paths as sun-btn (real click, then re-click to reset)|Clicking Terrain Analysis opens the analysis UI|Button toggles .active + aria-pressed, nothing visible opens (legacy #terrain-analysis-panel force-hidden, emptied into #dock-analyze). Works via dock tab .td-tab[data-dock=analyze]|sprint23_hunt_a_7.png

CLAIM|high|Bottom-left toolbar — #innovation-btn click handler (index.html ~line 9807+)|Same two repro paths as sun-btn (real clicks)|Clicking Pro Tools opens the innovation UI|Button toggles .active, nothing visible opens (legacy #innovation-panel force-hidden, children moved to #dock-innovate). Works via dock tab .td-tab[data-dock=innovate]|sprint23_hunt_a_7.png

CLAIM|medium|Terrain dock mode buttons (index.html line 575-582) vs keyboard IIFE brushModes (line 15794) vs SPRINT22_BRIEF.md keys map|Repro 1: open Terrain dock (Advanced), audit all .terrain-mode-btn text/aria/data-tmode via DOM; press keys 1-6 and record which mode activates. Repro 2: hunt1 PASS lines key1..key6 + dock_buttons dump (label 'Excavate' activating tmode=lower on both paths)|Every mode button label names its handler mode; 1-6 covers all brush modes (sprint 22 commit f71b79f claims the mislabel was fixed)|data-tmode=lower button still labeled 'Excavate' (aria-label 'Excavate terrain mode' too); 7th mode 'flatten' is unreachable from 1-6 (6 keys, 7 modes). Commit f71b79f only fixed the shortcuts-guide TEXT, not the buttons|sprint23_hunt_a_1.png

## Coverage — 16 distinct flows exercised (min required: 10)

| # | Flow | Scripts | Result |
|---|------|---------|--------|
| 1 | Brush modes 1-6 via real keyboard | hunt1 | 6/6 modes activate correct tmode |
| 2 | Brush mode buttons via real mouse clicks | hunt1 | 6/6 correct |
| 3 | Brush size [ ] keys | hunt1, hunt2c | grows 8→9, shrinks→8, floors at 1 |
| 4 | Dig brush real mouse drag (vertex-level) | hunt2, hunt2c | max h 0→-0.859; pristine size-1 dig → min -3.506 |
| 5 | Dig clip arm/disarm across mode switches | hunt2, hunt2b | key5 arms, raise disarms, dig re-arms, size-1 keeps armed |
| 6 | Underground dock open/close (button + Escape) | hunt2, hunt2b | both close paths disarm clip cleanly |
| 7 | Excavate launcher → dock-underground | hunt5b | works (children moved; drives dock) |
| 8 | Walk mode: W enter, W move, Esc exit, button exit | hunt3 | all pass |
| 9 | Walk stuck-key probe (hold W, 2nd W during alert, Esc) | hunt3 | no ghost motion, controls re-enable |
| 10 | View toggles V / B / R / G + X + M | hunt4 | all pass (R verified vs vc-reset math) |
| 11 | Sun dock: slider Arrow keys, light tracking, Play/pause | hunt5c | pass (see Reset claim) |
| 12 | Sun panel Reset | hunt5, hunt5d | BUG (stale clock + wrong light) |
| 13 | Bottom-left launcher buttons sun/analysis/innovate/excavate | hunt5b | 3 BUGS (excavate works) |
| 14 | Dock tabs sun/analyze/innovate open docks | hunt5b | all work |
| 15 | Cross-section toggle on/off (in dock-underground) | hunt5b | works (aria-pressed + visible panel) |
| 16 | Analyze content: contour, slope, cut/fill; Innovate: advanced section, stats overlay, ghost preview | hunt6 | all work (cut/fill panel shows volumes; stats overlay renders) |
| 17 | Undo/redo of terrain strokes: Ctrl+Z x2, Ctrl+Y x2, Ctrl+Shift+Z | hunt7 | exact vertex-level restore, stack depths correct |

## Evidence index

- `sprint23_hunt_a_1.png` — terrain dock modes + label audit state (hunt1)
- `sprint23_hunt_a_2.png` — after real-mouse dig strokes (hunt2)
- `sprint23_hunt_a_3.png` — pristine-yard size-1 dig result (hunt2c; hunt2b also wrote a `_3` before crashing pre-shot — this file is the valid size-1 evidence)
- `sprint23_hunt_a_4.png` — walk stuck-key probe final state (hunt3)
- `sprint23_hunt_a_5.png` — view-toggle final state (hunt4)
- `sprint23_hunt_a_6.png` — not written (hunt5 died at the dead sun launcher before its screenshot; superseded by hunt5b/5c/5d evidence)
- `sprint23_hunt_a_7.png` — final state after launcher/dock-tab/cross-section sweep (hunt5b)
- `sprint23_hunt_a_8.png` — analyze/innovate content final state (hunt6)
- `sprint23_hunt_a_9.png` — undo/redo final state (hunt7)
- `sprint23_hunt_a_10.png` — sun dock via tab (hunt5c)
- `sprint23_hunt_a_11.png` — sun Reset desync state (hunt5d: slider 12, display '20:00', light (30,50,20))

## Non-bugs investigated and cleared

1. `sun-play` toggling label Play↔Pause works; stopping at t≥24 resets to 12:00 correctly.
2. Walk-mode keydown/keyup handlers lack an input-field guard (index.html ~7895-7900) but no textarea exists in the DOM and the real-input probe showed no stuck keys; global handler guard covers INPUT/SELECT.
3. `#innov-stats-btn` hidden until "Advanced Tools" disclosure expanded — intended progressive disclosure; works after expanding.
4. Dig at clamp floor (-15) legitimately moves 0 vertices (MIN_TERRAIN_HEIGHT clamp).
5. No terrain array exists until first sculpt stroke (lazy creation) — `state.terrain` null on pristine load is by design.

## Baseline verification (no regressions, nothing masked)

- `python3 sprint22_quality_gate.py --port 8301` → **43/43 passed**
- `BASE_URL=http://localhost:8301 python3 qa_s21_dig_visibility.py` → **16/16 passed**
- `index.html` byte count unchanged: **759,791** (≤766,000); git diff on index.html: empty

## Handoff notes for the fixer

- The launcher fix likely = mirror excavate-btn's pattern (drive `openDockByTab('sun'|'analyze'|'innovate')` + keep button active state in sync with the dock), or retire the three legacy buttons from the toolbar. Note the CSS rule that force-hides the legacy shells (style block ~line 34) — a brace/CSS check is mandatory after touching it.
- Sun reset fix = call `applySunPosition()` after setting slider to 12 (and drop the hard-coded light block, or keep it but update `#sun-time-display`).
- Label fix = button text/aria 'Excavate'→'Lower' (data-tmode=lower) and decide: add a 7th key for flatten or drop the flatten button; the shortcuts guide text already says 1-6 = Raise/Lower/Smooth/Erode/Dig/Fill, so aligning the dock is the smaller change.