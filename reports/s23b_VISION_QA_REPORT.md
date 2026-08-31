# Sprint 23 — Agent 2 (PANEL-CONFLICT-RESOLVER) Vision QA Report

**Branch:** `sprint23-panel-conflict` (baseline `6056f88`) · **Port:** 8092 · **Byte budget:** 766,791 / 768,000 ✅
**Gate results on final tree:** s11 **143/143** · s15 **52/52** · s17 **81/81** · s21 **55/55** · s22 **43/43** · qa_s21 **16/16** · NEW `sprint23_panel_conflict_gate.py` **21/21**

## Root cause of the double "Underground View" bug

The claimed "two stacked floating panels" is architecturally **one dock panel with two stacked title bars**.
Sprint 13's setup code (`setupToolDock`, index.html ~line 11792) moves every child of the legacy
`#excavate-panel` into `#dock-underground-content` — *including the legacy panel's own
`.excavate-header` ("Underground View" title + working `#excavate-close` × button)*. The dock shell
already renders its own "Underground View" `dock-panel-header` with minimize/close. Result: two
"Underground View" titles and two × buttons stacked in one panel (vision verdict pre-fix: "Doubled
header with two close controls is clearly a bug"). The `#excavate-panel` shell itself is force-hidden
by CSS (`display:none !important`, line ~42), so it never shows; opening the Underground dock tab AND
#excavate-panel simultaneously could never literally produce two visible floats — the visible defect
is the duplicated header inside the single dock panel.

## Mutual exclusivity vs merge — decision

**Merge (single dock panel) + mutual-exclusivity state guard**, not a new panel:

1. **Duplicate header removed** — CSS `#dock-underground-content .excavate-header{display:none}`.
   The content-move machinery (which gates s11 `dock_replaced` checks and qa_s21's
   `#excavate-close` JS-click route depend on) stays intact; only the redundant chrome hides.
   The dock's own header × drives `closeDockPanel()`, which is the canonical close (disarms the
   dig clip, syncs `excavatePanelVisible`, resets `aria-pressed`).
2. **Stale-flag guard** — `closeDockPanel()` now clears any stale `visible` class + flag on the
   legacy `#excavate-panel` shell (mutual exclusivity invariant: dock open ⇒ legacy shell closed).
3. Existing toggle semantics preserved: `#excavate-btn` drives the dock via `.click()` (s21 behavior);
   dock-tab exclusivity (one dock at a time) unchanged; qa_s21's `excavate-close` route verified.

## Before/after table (vision = glm-5.3-flash, temperature 0, real CDP-driven states)

| # | Surface / state | Before (vision verdict) | Fix | After (vision verdict) |
|---|---|---|---|---|
| B1 | Underground dock tab open (before shot `s23b_before_1_docktab_only.png`) | "Two 'Underground View' titles stacked … Doubled header with two close controls"; dock panel covered tool-dock labels ("Pro Te…", "Sun &…", "Meas…", "Atmo…" cut) | F1 header hide; F3 dock reposition | after_docktab_underground.png: "**no true overlaps**: the Underground View dialog clears the SCULPT panel … sits above the bottom tool rows" |
| B2 | Dock-panel vs bottom-left toolbar (found during fix iteration) | Panel right edge (x≤724) overlapped Tape Measure button row (x≥660, y 690–760); reverse overlap existed in baseline for wide docks (innovate 340px) | `#dock-panel-container{bottom:118px;left:165px;max-height:calc(100% - 200px)}` | gate f3 sweep: dock vs toolbar/tooldock/statusbar/viewport = **0 overlap for all 6 docks** at 1280×800 |
| B2b | Tool-dock vs status bar | Bottom "Atmosphere" tab sliced by 8px behind #status-bar both before and after dock changes (pre-existing) | `#tool-dock{bottom:40px}` (flush above the 24px bar) | gate f4: tool bottom=760 < bar top=776 ✅; vision: no clipped Atmosphere row |
| B3 | Innovate dock (`after_docktab_innovate.png`) | "Doubled panel header: 'Pro Terrain Tools' with – ✕, immediately followed by a second titled row 'Innovation Lab' with its own ✕" | F2: `#dock-innovate-content .innov-header{display:none}` (same disease; `#innov-close` only hid the force-hidden legacy shell) | after2_innovate.png: innerHeaderDisplay=none, dock_vs_tooldock=0, dock_vs_toolbar=0; vision reports no doubled header (remaining notes = sidebar clip [Agent 1] + launcher duplication [documented]) |
| B4 | Sun & terrain-analysis docks | No inner headers found (`.sun-row` / `.ta-section-title` first) — **no defect**; legacy-launcher "nothing opens" bug already fixed Sprint 23 (S23-V10..12 per triage) | none needed | f3 sweep clean for dock-sun/dock-analyze |
| B5 | Cost + Layer + Season + Growth + Permit all open (`after_right_stack_all.png`) | "No other overlaps: the Permit Checker panel clears the compass, the Sculpt panel clears the sidebar and bottom buttons" (only sidebar-clip + cross-surface duplication notes = out of scope) | none needed | f6:no_overlap::right_stack_all ✅ (DOM rect matrix) |
| B6 | Underground dock + Cost; UG + Permit; Sun + Layer; Terrain → Sun replacement; UG + Cross-section | — (combination matrix) | — | f6 all 5 combos + cs: **zero panel-panel rect overlaps**; CS panel opens over the dock without conflict |
| B7 | 11-state rect matrix (`reports/sprint23_panel_audit/audit_after.json`) | baseline had tool-dock/status-bar 8px strip everywhere | B2/B2b fixes | **OVERLAPS: {}** across every state |

Additional vision notes deliberately **not** mine (owner noted for orchestrator): sidebar last-item
clip behind status bar (Agent 1's assigned fix), "Advanced mode" toast overlap (Agent 3), duplicated
launcher labels dock-tab vs bottom toolbar (Sprint 13 architecture, needs a product decision),
compass needle overflow, empty RECENTLY USED header.

## Regression locks — `sprint23_panel_conflict_gate.py` (21 checks, all passing)

- **f1** single Underground View header (legacy `.excavate-header` inside dock content must be display:none)
- **f2** single innovate header (same invariant)
- **f3** for each of the 6 dock tabs: dock panel does not intersect #tool-dock, #bottom-left-toolbar,
  #status-bar, and stays inside the 1280×800 viewport
- **f4** tool-dock flush above status bar
- **f5** stale-`visible` guard on closeDockPanel; excavate launcher end-to-end (opens dock, arms dig
  clip, excavate-close closes dock + button)
- **f6** five combination matrices + cross-section-over-dock with zero rect overlaps

Run: `python3 sprint23_panel_conflict_gate.py --port 8092` (or `BASE_URL=…`).

## Evidence

- Before: `s23b_before_1_docktab_only.png`, `s23b_before_2_docktab_plus_excavate.png`,
  `s23b_before_3_dock_area.png`, `reports/sprint23_panel_audit/*` (pre-fix prefix `docktab_`, `right_stack_all`, …)
- After: `reports/sprint23_panel_audit/after_*.png`, `gate_*.png`
- Machine state: `reports/sprint23_panel_audit/audit_after.json`, `sprint23_panel_conflict_results.json`

## Files changed

- `index.html` — 4 edits (duplicate-header CSS hides ×2, dock-panel-container position, tool-dock bottom), 766,791 bytes
- `sprint23_panel_conflict_gate.py` — new regression gate (21 tests)
- `s23b_*.py` — audit/probe/vision harness scripts (kept for rerun)
- `reports/sprint23_panel_audit/` — before/after screenshots + audit JSON

## Harness quirks reconciled

1. Playwright actionability on inner dock buttons (`#cross-section-toggle`) flakes right after
   dock-open (the sync clip-flush render blocks event dispatch briefly) — gate uses the same
   JS-click fallback + verify-retry convention as `qa_s21_dig_visibility.py`; the *dock tab itself*
   is always real-CDP-clicked.
2. Vision misreads screenshot **crop boundaries** as "viewport clipping" — always include generous
   margins (≥100px) or full-frame shots when asking vision to judge clipping; DOM rect probes are
   the ground truth for geometry.
3. A bare `.visible` classList probe on moved-in headers overcounts: check computed `display !== 'none'`.