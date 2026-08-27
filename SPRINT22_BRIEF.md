# Sprint 22 Master Brief — Ease of Use & Keyboard Shortcuts Guide

## Mission
Backyard Designer 3D (`index.html`, single file, 17,500 lines, **741.4KB used of 750KB hard limit — only ~8.6KB headroom**).
Owner mandate: **ease of use is the primary goal this sprint**, with a quality feel throughout.
Centerpiece deliverable: **a dedicated Keyboard Shortcuts Guide** that walks users through every useful shortcut.

## GROUNDED SHORTCUT INVENTORY (verified in code — do not invent others without adding handlers)
Terrain (module `setupKeyboardShortcuts`, line ~17345):
- `1`-`6` → terrain brush modes: raise, lower, smooth, erode, dig, fill (auto-opens Terrain dock)
- `[` / `]` → brush size down/up (1-30 ft)
- `X` → toggle Terrain dock/mode
View & scene (line ~6935-7035):
- `V` 3D view • `B` bird's-eye (2D) • `W` walk mode (Esc exits) • `R` reset view • `G` toggle grid • `T` (registry) • `M` toggle Basic/Advanced mode
Selection & edit:
- Arrow keys move selected object • `Delete`/`Backspace` delete • `Escape` deselect/close panels
- `Alt+Tab` cycle placed objects • `Ctrl+A` select-all context (line 6950) • `Ctrl+D` duplicate
- `Ctrl+Z` undo • `Ctrl+Y`/`Ctrl+Shift+Z` redo
Files & tools:
- `Ctrl+S` save • `Ctrl+Shift+S` save-as • `Ctrl+K` command palette • `Ctrl+Shift+P` print/screenshot
- Precision mode toggle button (Enter/Space on it), `?` may be free — CHECK before claiming.
Command palette registry (line ~6230) carries `shortcut:` metadata — USE IT as source of truth for the guide.

## REQUIRED DELIVERABLE — Shortcuts Guide modal
- Open via: `?` (Shift+/), `F1`, a "?" help button in the topbar, and a link inside the existing Help modal.
- Organized by category (Terrain, View, Selection, Edit, Files, Modes, Walk Mode) with `<kbd>`-styled keys,
  matching the app's design tokens (var(--surface), var(--border), var(--text), radius, shadows).
- Every entry MUST be verified against the real handlers (agent 4 builds a doc-drift test).
- Group Basic-mode-relevant vs Advanced-only shortcuts; respect current mode display.
- Quality feel: clean two-column grid, consistent kbd chips, section headers, no scrolling if possible
  (compact grid; max-height with internal scroll only if truly needed).
- Discoverability: mention it in the first-run wizard's last step and in the Help modal header.

## Other ease-of-use work (agents 2/3)
- First-run wizard polish, tooltips on icon-only buttons, empty-state hints.
- Consistent hover/focus/active states, cursor feedback over canvas per active tool.
- No new features beyond the guide + polish; do not restructure panels (done in S21).

## Hard Constraints (violating any = rejected merge)
- Single file; no build tools; Three.js v0.160.0 unchanged. Desktop-only.
- **SIZE: final index.html ≤ 768,000 bytes (safety under 750KB/768,000).** Current 759,219. Net additions
  must be ≤ ~8KB — trim redundant CSS/prose elsewhere if needed. Report exact byte count.
- Do not break existing features; all gates must pass (see below). Keep all element IDs/data attributes.
- CSS: run brace-balance check after any style edit (missing {} previously caused site-wide dead buttons).
- Module scope: any inline-handler-called function must be on `window` (export block ~line 17080+).
- UI verification: real CDP mouse/keyboard events ONLY — never page.evaluate() calling app functions
  for click/key paths (false passes burned earlier sprints).
- Commits: `git -c user.name="Caddy" -c user.email="caddyaibot@gmail.com"`. No secrets in code.

## Verification (include results in your report)
- `python3 -m http.server 8175` → `python3 sprint17_quality_gate.py` → 81/81
- port 8115 → `python3 sprint11_quality_gate.py --port 8115` → 143/143
- port 8099 → `python3 sprint15_quality_gate.py --port 8099` → 52/52
- port 8099 → `python3 sprint21_quality_gate.py --port 8099` → 54/54
- qa_s21_dig_visibility.py (BASE_URL env) → 16/16
- New sprint22 gate from Agent 4 must pass on the merged tree.

## Key landmarks
- Command palette registry w/ shortcut metadata: ~line 6230
- Global keydown (edit/view keys): ~line 6933; terrain keys IIFE: ~17345; walk Esc: ~9444
- Help modal HTML: ~3046-3140; help CSS ~585; print overlay ~1166
- Wizard/welcome: #wizard, #welcome-prompt; Escape handlers ~9642, ~15236
- Window export block: ~17080+; status bar FPS ~1625; cmd palette ~6933-7030