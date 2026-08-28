# Sprint 23 — Bug Hunt C: Persistence, Modes & Edge Cases (READ-ONLY)

**Hunter:** Caddy (webdev) · **Card:** t_6c08ebd2 · **Swarm root:** t_2cd9931f
**Target:** /root/backyard-designer/index.html @ commit 0ed89dd (759,791 bytes — UNTOUCHED, read-only hunter)
**Server:** http://localhost:8303 (assigned port; no forbidden ports touched)
**Method:** Playwright 1.62 + raw CDP, REAL mouse/keyboard events for all click/key paths.
`page.evaluate` used only for state reads (window._bydState, DOM, localStorage) and clearly
labeled `window._bydLoadDesign` code-path probes (claims C3/C4) — never to drive UI.
**Runs:** 5 rounds, 44 executed flows, 45 evidence screenshots (sprint23/huntc/), 0 page errors, 0 uncaught console errors.

## Claims (CLAIM|severity|area:ref|repro|expected|observed|evidence)

CLAIM|HIGH|Keyboard: shortcuts guide F1/? capture handler (index.html:5270-5273)|Open command palette (Ctrl+K), type "terrain", press F1 (or ?)|Guide must NOT open while the user is typing in a text input; handler must skip e.target INPUT/TEXTAREA like the global keydown at :5383 does|Guide opens over the palette mid-typing and steals focus to #shortcuts-close-btn; user's typing flow is interrupted and their first Escape only closes the guide. Reproduced 3x: palette (F06), wizard #wiz-width (F19: input left as "5045"), palette '?' (V3)|sprint23/huntc/f06_f1_during_typing.png, f19_f1_in_wizard_input.png, v3_question_in_palette.png
CLAIM|HIGH|Escape stacking: global modal sweep (index.html:5409-5455) + unconditional wizard Escape (:8093-8098)|Open wizard, press F1 to open the guide on top, press Escape ONCE|Topmost layer closes only; wizard stays until its own dismissal|Single Escape closed BOTH the shortcuts guide and the wizard (side effect: initWithYard(50x100) ran on wizard dismissal); a second Escape was then needed for the welcome-prompt that popped up. Same collapse reproduced for help→shortcuts stack (F11: both closed by one Escape)|sprint23/huntc/f07a_wizard_plus_shortcuts.png, f07b_after_one_escape.png, f11a_help_then_shortcuts.png, f11b_after_escape.png
CLAIM|MEDIUM|Persistence: loadDesign duplicate-id handling (index.html:4229 state.objects.set in a loop)|Load a JSON whose objects array contains two entries with the same id (both valid CATALOG types) via the real Load flow|Both objects should load (Map keyed by id must not silently drop data); ideally last-one-wins is at least surfaced|Two objects sharing id 7 (fence_privacy + pergola) load as ONE (ids [7,8], n=2, pergola wins); toast still says "Design loaded successfully!" — silent data loss with no warning (LABELED-PROBE via window._bydLoadDesign)|sprint23/huntc/v1_dup_ids_valid.png, f10a_dup_ids.png
CLAIM|MEDIUM|Persistence: loadDesign nextId not reconciled with object ids (index.html:4171)|Load a JSON with nextId:5 while an object with id:5 exists (app's own autosave can produce near-collisions after id remapping), then click a catalog card|Next object must get a fresh unused id (e.g. max(ids)+1)|New fence got id 5, silently REPLACING the loaded tree: ids [5]→[5] with types [tree_deciduous]→[fence_privacy]; loaded object destroyed, undo/selection corrupted (LABELED-PROBE)|sprint23/huntc/x4_nextid_collision.png, v2_nextid_collision.png
CLAIM|MEDIUM|Files: Ctrl+Shift+S dead on real desktop key semantics (index.html:5390 e.key==='s' misses 'S')|On desktop Chrome, press Ctrl+Shift+S with no input focused|Save-As prompt appears, then JSON downloads|No prompt, no download, no toast. X1 observed Playwright's synthesized event carries key:'s' under Shift (why earlier gates passed); a raw CDP event with the real desktop key value 'S' produced NO dialog (X2). Ctrl+S control works (F20/W4)|sprint23/huntc/w4_ctrl_shift_s.png, x2 evidence in results5.jsonl
CLAIM|MEDIUM|Edit: Ctrl+Shift+Z redo dead on real desktop key semantics (index.html:5388 e.key==='z' misses 'Z')|Add object, Delete, Ctrl+Z to undo, then Ctrl+Shift+Z with desktop key value 'Z'|Object restored (redo)|Redo not applied (object count stays 1) when the event carries key:'Z' (CDP dispatch, X3). Ctrl+Y redo works as fallback (W1)|sprint23/huntc/w1_ctrl_shift_z.png, x3 evidence in results5.jsonl
CLAIM|LOW|Onboarding toast: showWelcomeOnboarding 500ms toast (index.html:5216-5220) fires after initWithYard from loadDesign (index.html:4211)|Load any valid design via Load button|Toast "Design loaded successfully!" remains visible for the user|Sequence captured: "✓Design loaded successfully!" at +1755ms replaced by "Welcome! Click items…" at +1942ms — success feedback erased on every load path (incl. Continue-previous and fresh finish)|sprint23/huntc/w5_toast_clobber.png
CLAIM|LOW|A11y: modals have no focus trap (openModal index.html:5223-5231)|Open Help modal, press Tab repeatedly|Focus cycles inside the dialog while open (aria-modal="true")|Tab escaped into background topbar on 13 of 14 presses (help-close-btn → body → skip-link → topbar buttons). Escape focus restore works correctly (returns to btn-help)|sprint23/huntc/f15_tab_order_help.png

## Doc-drift audit of the Keyboard Shortcuts guide (index.html:1530-1565) — all 21 rows driven with real keys

| Guide entry | Verdict | Evidence |
|---|---|---|
| 1–6 → Raise/Lower/Smooth/Erode/Dig/Fill | CORRECT — active brush observed per key | w2_brush_map.png |
| [ / ] brush size 1–30 ft | CORRECT — terrain-brush-val changed both directions | f08 probes |
| V 3D / B 2D / W walk / R reset / G grid | CORRECT — all verified (V5 camera snap, V12 toggle, V10 HUD, F08 grid) | v5, v10, v12, f08 |
| X toggle terrain dock / T terrain dock | CORRECT — aria-pressed + dock | f08 |
| M toggle Basic/Advanced | CORRECT — even count returns to start; exactly one body class; palette advanced items filter | f12, f08 |
| Esc deselect / close panels | CORRECT | f04, f11 |
| Arrows move 1 ft / Shift 0.1 ft | CORRECT — x: 0→-1→-0.9 | v6 evidence |
| Del / ⌫ delete | CORRECT | v6 evidence |
| Alt+Tab cycle (Shift reverses) | CORRECT — sel 2→1→2 | f18_alttab_cycle.png |
| Ctrl+A select all / Ctrl+D duplicate | CORRECT — 2 selected, batch bar, dup → 3 objects | x5_ctrl_a_d.png |
| Ctrl+Z / Ctrl+Y | CORRECT | w1 |
| Ctrl+Shift+Z | BUG (see C6 — dead with desktop 'Z') | x3 |
| Ctrl+S save | CORRECT — real download, valid JSON, matches state | f20 |
| Ctrl+Shift+S | BUG (see C5 — dead with desktop 'S') | w4/x2 |
| Ctrl+Shift+P Performance panel | CORRECT — toggles #perf-panel open/closed | v7_perf_panel.png |
| Ctrl+K palette + Esc close + arrows/Enter | CORRECT | f04, f05 |
| "Press ? or F1 anytime" | MISLEADING while typing (see C1 — fires inside inputs) | f06, v3, f19 |

## Verified NON-bugs (negative results — do not re-hunt)

- Corrupt/truncated/empty JSON via real Load input: clean error toast naming the JSON.parse error; state untouched (F09, W3).
- Unknown types, null params, string ids, missing ids, legacy 'tree' migration, wrong-length terrain arrays, non-square terrain: all rejected/sanitized correctly; terrainSegs resets to 200 when terrain rejected (F10, F21).
- Absurd yard dims (1e300) from file: clamped to 500x500 by initWithYard — NOT a bug (initially suspected, refuted).
- Autosave debounce (2s) + quota-exceeded warning path + Continue-previous restore across reload: correct (F03).
- Wizard complete/skip/back, quick-size links, mode persistence across reload: correct (F02, F03, F12).
- Rapid 8x M toggling and rapid Escape x3: idempotent, no state corruption (F12, V11).
- Window resize 1280x800 → 1920x1080: canvas backing store tracks viewport, no errors (F13).
- 21 catalog items across 5 sections render; Alt+Tab, palette nav, walk mode enter/exit all work.

## Harness artifacts

- sprint23/huntc/harness.py, harness_v2.py, verify3.py, verify4.py, verify5.py, extract.py
- results.jsonl (v1+v2), results3.jsonl, results4.jsonl, results5.jsonl, console_errors.json
- 45 evidence PNGs (f*, v*, w*, x4/x5) in sprint23/huntc/

## Notes for the fixer

1. C1 fix: gate the F1/? capture handler on `e.target.tagName` INPUT/TEXTAREA (mirror :5383) — one line.
2. C2 fix: in the :5409 Escape sweep, close only the topmost visible layer (ordered list + break), and make the wizard :8094 handler skip when another modal is open.
3. C5/C6 fix: case-insensitive combo matching (`e.key.toLowerCase()`) at :5388 and :5390.
4. C3/C4 fix: in loadDesign, renumber or reject duplicate ids (toast a warning), and set `state.nextId = Math.max(nextId, maxObjectId + 1)`.
5. Repro note for C5/C6: Playwright's keyboard.press sends lowercase letters under Shift on this platform — any regression test MUST dispatch key:'S'/'Z' via CDP to reproduce what desktop Chrome sends.