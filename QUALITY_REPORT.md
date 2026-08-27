# Sprint 22 — Agent 4 (Quality Gates) QUALITY_REPORT.md

**Branch:** `sprint22-quality-gates` (baseline `7d7fef8`, clean tree)
**Scope:** Doc-drift regression gate for the Sprint 22 Keyboard Shortcuts Guide, plus a full
re-run of every existing gate against this tree.

---

## Pass matrix — all existing gates on this tree (baseline 7d7fef8)

| Gate | Serve | Command | Expected | Actual | Status |
|---|---|---|---|---|---|
| sprint17_quality_gate.py | port 8175 | `python3 sprint17_quality_gate.py` | 81/81 | **81/81** | ✅ PASS |
| sprint11_quality_gate.py | port 8115 | `python3 sprint11_quality_gate.py --port 8115` | 143/143 | **143/143** | ✅ PASS |
| sprint15_quality_gate.py | port 8099 | `python3 sprint15_quality_gate.py --port 8099` | 52/52 | **52/52** | ✅ PASS |
| sprint21_quality_gate.py | port 8099 | `python3 sprint21_quality_gate.py --port 8099` | 54/54 | **54/54** | ✅ PASS |
| qa_s21_dig_visibility.py | BASE_URL=http://localhost:8099 | `BASE_URL=… python3 qa_s21_dig_visibility.py` | 16/16 | **16/16** | ✅ PASS |
| sprint22_quality_gate.py (NEW) | port 8222 | `python3 sprint22_quality_gate.py --port 8222` | 43 total | **33 pass / 10 fail** (all 10 = pre-merge guide contract, see below) | ⚠️ expected pre-merge |

**No pre-existing failures were found in any existing gate** — nothing needed fixing.
`index.html` is untouched by this agent: **759,219 bytes (741.4 KB), 17,494 lines** —
inside the 768,000-byte hard limit (8,781 bytes headroom).

---

## New deliverable: `sprint22_quality_gate.py` (43 tests)

All UI interaction is **real CDP input** — `page.keyboard.press()` for every key path,
`locator.click()` for the topbar button. `page.evaluate()` is used **only** for test
setup (place/select an object via the exported `window._test.addObject` /
`window.selectObject` handles) and read-only state probes — never to drive click/key
paths, per the brief.

### Group A — the guide opens (5 tests)
- `?` (Shift+/) opens `#shortcuts-modal`; Escape closes it
- F1 opens it; Escape closes
- Topbar `?` button opens it (real mouse click)
- **Status: expected FAIL pre-merge** — Agent 1's guide is not on this baseline yet.
  The gate detects absence and reports a clear reason instead of crashing.

### Group B2 — verified shortcuts, real keys → real effects (16 tests, ALL PASSING)
Driven with `page.keyboard.press`, asserted on live app state:
- `1` → raise terrain brush mode (`.terrain-mode-btn.active`) **and** Terrain dock auto-opens
- `5` → dig brush mode
- `]` / `[` → brush size up/down (8→9→8 via `#terrain-brush-val`, ` ft` unit intact)
- `V` → 3D view (`state.viewMode` + topbar tab active)
- `B` → bird's-eye/2D view
- `W` → walk mode (`#walk-controls` visible); Escape exits
- `M` → Basic→Advanced→Basic toggle (`window.getCurrentMode()`)
- `Ctrl+K` → command palette opens; Escape closes
- `Delete` → deletes a placed+selected object (`#objects` 1→0, deselected)

### Group B1 — doc-drift lock (4 tests, expected FAIL pre-merge)
Parses the **rendered** `#shortcuts-modal` text and requires every entry of the brief's
grounded inventory (26 keys across Terrain/View/Selection/Edit/Files/Tools: 1–6, [ ], X,
V, B, W, R, G, M, Delete, Esc, Ctrl+D/Z/Y/S, Ctrl+Shift+S, Ctrl+K, Ctrl+Shift+P, Alt+Tab,
Arrows) to appear, plus ≥10 `<kbd>` chips and ≥5 category sections. If a future handler
change drops a shortcut, this gate breaks — that is its purpose.

### Group C — doc accuracy (3 tests; 2 pass now, 1 flips when the guide lands)
- Help modal mentions the Underground flow — **PASSES today** (Excavate/underground flow
  documented in `#help-modal`)
- Shortcuts guide link exists (Help modal link and/or inside the guide) — flips to PASS
  with Agent 1's deliverable
- Guide mentions Underground + walk-mode Esc-to-exit (part of B1 rendered-content lock)

### Group D — hard constraints (2 tests, PASSING)
- No console errors during the entire browser run
- `index.html` ≤ 768,000 bytes + CSS brace balance (934/934)

---

## Current sprint22 gate result (pre-merge baseline)

```
Results: 33 passed, 10 failed, 43 total
```

The 10 failures are **by design**: they test the Sprint 22 shortcuts-guide contract
(`#shortcuts-modal`, `?`/F1/topbar-button open paths, rendered-inventory lock, guide
link) against a tree that predates Agent 1's deliverable. They flip to PASS when the
guide lands; if the guide drops a documented shortcut or a handler loses a key, they
break the merge — exactly the intended ratchet.

## Notes for the merge coordinator
1. Serve the repo dir (`python3 -m http.server <port>`) and run gates with matching
   ports: 8175 (sprint17 via BASE_URL), 8115 (`--port`), 8099 (sprint15/21 + qa_s21
   via `--port`/BASE_URL), 8222 (sprint22 default).
2. `terrainBrushMode` / `terrainBrushSize` are module-scoped (not on `window`); the
   gate asserts their effects via DOM (`activeTMode`, `#terrain-brush-val`) — do not
   "simplify" those probes back to bare variables.
3. Delete-test setup uses `window._test.addObject('fence_privacy', …)` +
   `window.selectObject(id)` (test handles only; the Delete keystroke itself is a real
   CDP key event).
4. Existing results JSONs in the repo were refreshed by this re-run; counts unchanged.