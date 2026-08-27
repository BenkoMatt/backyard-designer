# Sprint 22 — Agent 5: Visual Consistency Report

**Branch:** `sprint22-visual-consistency` (baseline 7d7fef8)
**Method:** screenshot-driven — every modal/panel/dock opened via real CDP clicks at 1280x800 in
Basic + Advanced modes (`sprint22_visual_consistency.py`, S21 harness pattern), computed-style
audit (`audit.json`), fixes, then re-render + pixel-diff verification. Real CDP only; no
page.evaluate-driven app calls.

## Byte budget

| | bytes |
|---|---|
| Before | 759,219 |
| **After (final)** | **760,580** ✅ ≤ 768,000 hard cap |
| Net delta | +1,361 (+1.2KB of ~8.8KB headroom used) |

## Gate results (all on this branch's final tree)

| Gate | Port | Result |
|---|---|---|
| sprint17_quality_gate.py | 8175 | **81/81** ✅ |
| sprint11_quality_gate.py --port 8115 | 8115 | **143/143** ✅ |
| sprint21_quality_gate.py --port 8099 | 8099 | **54/54** ✅ (also confirms 760,580 bytes) |
| qa_s21_dig_visibility.py | 8099 | ⚠️ pre-existing harness error (`reading 'state'`) — **fails identically on pristine baseline 7d7fef8** (verified via git stash), not in this agent's gate list, not a regression |

CSS brace balance verified after every style edit round: 936 `{` / 936 `}`. ✅

## `.kbd-chip` foundation for Agent 1 (Keyboard Shortcuts modal)

Added a shared, token-based key-chip style (~370 bytes CSS) in the `#cmd-palette` CSS block
(~line 1050). Both `class="kbd-chip"` and bare `<kbd>` elements get it automatically:

```css
.kbd-chip, kbd {
  font-family: inherit; font-size: var(--font-label); font-weight: 600; line-height: 1;
  color: var(--text); background: var(--hover-bg);
  border: 1px solid var(--border); border-bottom-width: 2px; border-radius: var(--radius-button);
  padding: 3px 6px 4px; display: inline-block; white-space: nowrap;
}
```

- All colors/radii/fonts are tokens (`--hover-bg`, `--border`, `--radius-button`, `--font-label`, `--text`).
- 2px bottom border gives the physical "keycap" feel; `var(--radius-button)` = 4px per app convention.
- Inside the command palette, `.cmd-item .kbd-chip` inherits a transparent-border variant, and
  selected/hover rows get the existing `rgba(255,255,255,0.2)` inversion.
- The palette's `cmd-shortcut` renderer now wraps shortcuts in `<span class="kbd-chip">` (JS line
  ~6319), so Agent 1's modal and the palette render identically. Agent 1 can use
  `<kbd>`/`.kbd-chip` directly in the shortcuts modal with zero extra CSS; the Help modal can use
  bare `<kbd>` too.
- Presence verified in-browser (stylesheet rule check: PASS).

## Fixes applied — before/after per surface

Evidence: `reports/sprint22_shots/{before,after}/*.png` (36 + 37 shots incl. wizard) + pixel-diff
(`reports/pixel_diff.py`); every row below has a confirmed nonzero pixel delta in the expected
region (table at bottom).

### 1. Corner-radius drift → tokens
| Surface | Before | After |
|---|---|---|
| Wizard panel | `border-radius:16px`, `background:white` | `var(--radius)` (10px), `var(--surface)` — verified: 16px→10px in pixels |
| Help modal panel | `16px`, `white` | `var(--radius)`, `var(--surface)` — 0.08% pixel delta |
| Templates / Share panels | already `var(--radius)` | unchanged (reference standard) |

All modal/panel containers now sit on `var(--radius)` (10px); controls on `var(--radius-sm)`/`var(--radius-button)`.

### 2. Panel header typography (section headers)
All right-stack panel titles were 14px green (`--primary`) or 13px (`--primary`); dock titles were
13px `var(--text)`. Normalized **every** panel/dock header to `13px / 700 / var(--text)`:
cost, season, growth, permit, layer (+ color), terrain dock, excavate, cross-section, innovate,
underground, analyze, sun, measure, experience. Verified: `cost-panel-header .title` computed
`14px/rgb(61,117,73)` → `13px/rgb(45,45,45)`; season/growth/permit same.

### 3. Close-button consistency (heights 18–21px mixed → uniform)
`×` close buttons were font-size 16px in some panels, 18px in others, with no transition and
default (Arial) font. Normalized **all 12 close buttons** (dock headers, excavate, cross-section,
cost, layer, innovate, season, growth, permit) to `font-size:18px; font-family:inherit;
transition:color 0.15s`. Verified computed: `transitionDuration=0.15s`, `fontSize=18px`,
font = app stack (was Arial).

### 4. Minimize buttons
`.dock-panel-header .minimize` + `#terrain-controls .minimize`: added `font-family:inherit;
transition:color 0.15s` (was Arial, no transition).

### 5. Missing hover/active transitions (0.15s pattern)
Added `transition: all 0.15s` (or `color 0.15s` for glyph buttons) to: `.terrain-mode-btn`,
`.tc-acc`, `.sun-play-btn`, `.view-toggle button`, `.innov-btns button`,
`#terrain-flatten`, `.excavate-btns button` (incl. wireframe toggle), `.share-actions button`,
`.templates-close button`. Before-audit: 30 buttons with `transition: none` → after: only
intentional icon toggles remain. Verified: share-copy 0.15s in pixels.

### 6. Icon alignment / font inheritance
`layer-panel` close, `layer-toggle` label, dock `close`/`minimize`, `tc-acc`, plus all modal
action buttons now inherit the app font (Arial fallback drift eliminated on text controls).

### 7. Color-token drift
| Selector | Before | After |
|---|---|---|
| `.discovery-badge` shadow | `rgba(255,107,53,.4)` (old orange brand) | `rgba(201,123,79,.4)` = `--secondary` |
| `#progressive-hint` shadow | `rgba(102,126,234,.4)` (foreign indigo) | `rgba(61,117,73,.4)` = `--primary` |
| `.layer-row .layer-toggle` | hardcoded `36px/20px/10px`, `background:var(--primary)`, 0.2s | `--toggle-w/h/radius`, `--toggle-on`, 0.15s |
| Wizard/Help panels | `background: white` | `var(--surface)` |

### 8. Section-header typography system
Unified the three uppercase section-title patterns to one spec — `11px/700/uppercase/
letter-spacing 0.5px/var(--text-muted)`:
- `.exp-section-title` 12px→11px
- `.innov-section-title` color `--analysis`→`--text-muted`
- `.ta-section-title` already compliant (reference)

## Pixel-diff evidence (before → after, per surface)

All 36 surface shots re-rendered; diff vs before (1280x800, meaningful-delta threshold 12/255):

| Surface | pixels changed | Surface | pixels changed |
|---|---|---|---|
| wizard | 1.51% | advanced-dock-underground | 0.49% |
| layer-panel (adv) | 0.90% | excavate-panel (adv) | 0.50% |
| layer-panel (basic) | 0.89% | cross-section (adv) | 0.45% |
| baseline (adv) | 0.67% | sun-panel (adv) | 0.45% |
| dock-innovate (adv) | 0.67% | terrain-analysis (adv) | 0.45% |
| baseline (basic) | 0.57% | innovation-panel (basic) | 0.35% |
| baseline-2D/other surfaces | 0.07–0.50% | share/templates (chip-only) | 0.00–0.01% |

Every opened surface shows a delta confined to its panel region (diff-bboxes in
`reports/pixel_diff.py` output) — fixes are real and localized, no collateral layout shifts.

## Computed-style verification (real browser, `reports/verify_fixes.py`)

12/12 PASS: close-btn transition+font, panel-title 13px/var(--text) (cost/season), close 18px,
wizard/help/templates/share panel radius 10px, share-btn transition, `.kbd-chip` rule live.

## Files

- `index.html` — all fixes (CSS + 1-line palette chip markup)
- `sprint22_visual_consistency.py` — screenshot + style-audit harness (reusable; BYD_MODE/BYD_URL env)
- `reports/sprint22_shots/{before,after}/` — 1280x800 PNGs + `audit.json`
- `reports/{analyze_audit,list_offenders,inspect_none,pixel_diff,verify_fixes,shot_wizard}.py` — audit tooling
- Gate result JSONs/PNGs refreshed by gate runs

## Handoff notes for Agent 1 (shortcuts modal)

- Use `<kbd>` or `class="kbd-chip"` — styles are global, token-based, and already palette-compatible.
- Suggested modal container recipe (matches Help/Templates): `background: var(--surface);
  border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow-lg);` with
  `h2 { font-size: 20px; }` and section headers at `11px/700/uppercase/0.5px/var(--text-muted)`.
- Two-column grid gap in the app is dominantly 8px (30 uses) / 12px (54 uses); either reads native.
- Budget remaining after this pass: 768,000 − 760,580 = **7,420 bytes**.