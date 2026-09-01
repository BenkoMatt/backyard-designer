# Sprint 23 — Vision QA Report — Agent 1 (VISION-AUDIT-SURFACES)

**Branch:** `sprint23-vision-audit` · **Baseline:** `03475abb` (via `6056f88`) · **Port:** 8091→8095 (8091 was squatted by a foreign process; documented below)
**Harness:** `sprint23_vision_audit.py` (real Playwright CDP pointer/keyboard events, 1280×800, Basic + Advanced mode) · **Vision runner:** `sprint23_vision_run.py` (glm-5.3-flash via Ollama Cloud, `temperature: 0`, per-surface QA prompt from SPRINT23_BRIEF.md)
**Evidence:** `reports/sprint23_shots/before-*.png` (43), `reports/sprint23_shots/after-*.png` (43), verdict JSONs `vision_verdicts_before.json` / `vision_verdicts_after.json`

## Execution summary

- Walked **43 surfaces** (all 10 brief items, each in Basic AND Advanced mode where the surface exists in that mode) with real CDP clicks only; `page.evaluate` used solely for read-only geometry probes and the sidebar wheel-scroll.
- Ran every screenshot through **glm-5.3-flash** with the exact per-surface QA prompt: 43 BEFORE + 43 AFTER verdicts.
- Fixed every issue in my lane, re-shot, and re-ran vision until my lanes show no remaining overlaps.

## Before → After (per-surface table)

Full 43-row table with verbatim verdicts is embedded below; condensed findings shown. Full text in the verdict JSONs.

| Surface | BEFORE vision finding (summary) | Fix applied | AFTER vision finding (summary) |
|---|---|---|---|
| `01/02-wizard-step1/2` (+scrolled) | "Skip — use default yard" collides with floating Sun chip / toolbar; sidebar sliver cut | (toast/hint lane, Agent 3) | Same residual toast collision (Agent 3's lane) |
| `03-main-default` | Tour toast covers bottom toolbar; **sidebar bottom clipped behind #status-bar** | (a) + (Agent 3 toast) | Toolbar clear; sidebar scrolls cleanly (residual: unscrolled-at-top slice, by design) |
| `05/05b-sidebar-all-expanded/hover` | Last category/item clipped mid-glyph behind #status-bar; toast over toolbar | **(a) `#sidebar{padding-bottom:28px}`** | Scroll ends 6px above status bar (measured); toast residual only |
| `06–11-toolbar-*` (Tape/Terrain/Excavate/Analyze/Innovate/Sun) | Toast/hint pile-ups at bottom center; duplicate Underground panels on Excavate | (Agent 2 + Agent 3 lanes) | Unchanged — other agents' lanes |
| `p-cost / p-layer / p-sun` | **Lowest right-edge view-control button clipped by #status-bar** | **`#view-controls{bottom:16px→40px}`** | Clip mentions gone from these surfaces |
| `p-terrain-controls / s-context-hint` | Same right-edge clip + toast overlaps | **`#view-controls bottom:40px`** + (Agent 3) | Right-edge clip gone |
| `p-cross-section / p-excavate / d-underground / 08-toolbar-excavate` | **TWO stacked "Underground View" floating panels** (brief known-issue b) | (Agent 2's lane — mutual exclusivity) | Unchanged pending Agent 2 |
| `p-cut-fill / p-terrain-analysis / p-innovation` | Panel-over-rail truncation + toast overlaps | (Agent 3 + z-order audit lane) | Unchanged — cross-agent lane |
| `m-help / m-help-bottom` | Help modal overflow line + mid-scroll open (Sprint 22 fixes re-verified) | none needed (re-verified fixed) | Residual: modal-over-toolbar is inherent to modals |
| `m-shortcuts(+F1)` | Sidebar last item cut behind status bar; toast over toolbar | **(a)** + (Agent 3) | Sidebar residual only (unscrolled state) |
| `m-share / m-gallery / m-templates / m-label-edit` | Sidebar bottom clip + toast over toolbar | **(a)** + (Agent 3) | Modals layer cleanly; topbar 1280px overflow documented below |
| `m-command-palette` | Right-edge button clipped + toast | **`#view-controls bottom:40px`** | Palette modal itself clean |
| `o-walk-mode` | **Walk hint overlaid the topbar tab row** | **`#walk-hint{top:16px→64px}`** | Hint now at y=64, only canvas above (verified via elementFromPoint) |
| `o-grid-level-badge / o-depth-gauge` | Sidebar bottom clip; right-edge clip | **(a) + `#view-controls bottom:40px`** | Both fixed |
| `s-status-bar / t-toast` | Sidebar bottom clip; Advanced toast overlaps toolbar | **(a)** + (Agent 3 lane) | Sidebar clean; toast residual Agent 3 |
| `x-print` | Sidebar bottom clip; right-edge button flush | **(a) + `#view-controls bottom:40px`** | Sidebar item no longer runs under the bar |

## Owned fixes shipped (all in index.html, +20 bytes net)

1. **(a) Sidebar/status-bar collision (brief known-remaining issue a)**
   `#sidebar{ … padding-bottom:28px; }` — equals the 24px min status-bar height + 4px breathing room (brief: "min 28px").
   **Numeric verification** (`s23_verify_sidebar.py`, real wheel-scroll to bottom): status-bar top y=**776**, last `.lib-item` bottom y=**770**, `scrollTop` reaches end of scroll range, `padding-bottom: 28px` in computed style → `itemClearsBar: true`.
2. **Right-edge view-control stack clipped by the fixed status bar** (flagged by vision on 10+ surfaces)
   `#view-controls{bottom:16px → bottom:40px}` — the 4-button stack (lowest = underground button, previously half-hidden at y≈744–784) now clears the status bar at 800px height. Verified: before/after verdicts dropped every "lowest button clipped/cut by status bar" mention on p-cost, p-layer, p-sun, p-terrain-controls, p-cut-fill, p-cross-section, s-context-hint, o-depth-gauge, m-command-palette, x-print.
3. **Walk-mode hint overlaid the 52px topbar** (o-walk-mode BEFORE: hint pill covered the tab row)
   `#walk-hint{top:16px → top:64px}` — sits fully below the topbar; verified via `elementFromPoint` (only canvas above it) + re-screenshot.

## Verified-fixed known issues re-checked (no regression)

- Help modal bottom clipping / mid-scroll open: `m-help` + `m-help-bottom` (scrolled to bottom) show the last section fully — Sprint 22 fixes hold.
- Shortcuts guide `.sc-keys` truncation: no truncation flags in `m-shortcuts` / `m-shortcuts-f1`.

## Residual findings after my pass (owned by other agents — documented, not fixed)

- **Duplicate stacked "Underground View" panels** (brief issue b) — Agent 2 (PANEL-CONFLICT-RESOLVER): surfaces `08-toolbar-excavate`, `d-underground`, `p-excavate`, `p-cross-section`.
- **Toast/context-hint overlaps on the bottom toolbar** (brief issue c + tour toast) — Agent 3 (TOAST-HINT-HYGIENE): nearly every surface pre-fix; my surfaces' residuals all reduce to this.
- **Topbar horizontal overflow at 1280px** (`m-gallery`: "Templa…" cut at right edge): by design (`overflow-x:auto` with thin scrollbar) but the scroll-cue gradient only renders at `.scrolled-end`; recommend a left-edge gradient hint too (Agent 3/5 optional).
- "FPS: 1"/"FPS: —" in the status bar: **headless software-rendering artifact**, not reproducible on real hardware; recommend hiding FPS when `hardwareConcurrency` low or under CDP (Agent 5 optional).

## Harness quirks found (for Agent 4's reconciliation section)

1. **Port 8091 was already bound** by an unrelated long-running process (`/root/.../http.server 8091`, started 2026-08-25, cwd `~`); brief guidance says "use 8091+". I used **8095** (and 8096 for the baseline A/B). Recommendation: check `ss -tlnp` before trusting the assigned port.
2. **Gate port conventions differ per gate** (cost me a full misleading gate run): `sprint16/17/21` expect `BASE_URL` **without** `/index.html`; `sprint22` takes `BASE_URL` root; `sprint11` ignores `BASE_URL` and needs `--port`; `qa_s21_dig_visibility` expects `BASE_URL` **with** `/index.html`. Doc this in the gate report.
3. **Wizard/welcome determinism:** on a fresh profile (no autosave) the wizard always shows, but with a warm storage state it may or may not, and post-wizard a `#welcome-prompt` modal intercepts real clicks (Playwright reports `welcome-prompt-panel … intercepts pointer events`). The harness now dismisses both on every page boot (real clicks).
4. **First-load race:** the module script imports Three.js from unpkg; on a busy shared machine `networkidle` can pass before the module executes — `wait_for_selector("#mode-toggle button…")` (30s) is the reliable readiness probe.
5. sprint16's 3 fails ("Z-index hierarchy", "Wider panels", "FPS ≥ 30") are **pre-existing on the 03475abb baseline** (verified by A/B with saved JSONs); not caused by Sprint 23 edits.

## Gate status on final tree (766,158 bytes ≤ 768,000 − 1,842 headroom)

| Gate | Result |
|---|---|
| sprint11 `--port 8095` | 143/143 (100%) |
| sprint15 | PASSED |
| sprint17 | 81/81 |
| sprint21 | 55/55 |
| sprint22 | 43/43 |
| qa_s21_dig_visibility | 16/16 |
| sprint16 (informational) | 29/32 — 3 pre-existing baseline fails |

## Byte budget

Baseline 766,138 → final **766,158** (+20: three one-line CSS edits). `wc -c index.html` = 766,158 ≤ 768,000. ✅
---

# Sprint 23 — Vision QA Report — Agent 3 redo (TOAST-HINT-HYGIENE)

**Branch:** `sprint23-toast-hygiene` (redo after predecessor timeout) · **Tree:** merged canonical/main at `c925e87` · **Port:** 8095 · **Gate harness:** `sprint23_quality_gate.py` · **Audit harness:** `s23_agent3_overlay_audit.py` (real CDP clicks/keys; `page.evaluate` only for read-only geometry + recovery-snapshot seed), vision via glm-5.3-flash (`temperature: 0`)
**Evidence:** `reports/sprint23_shots/agent3-{before,after}-<overlay>.png` (7 states × 2), verdicts `agent3_overlay_results_{before,after}.json`, per-shot `.verdict.txt`

## V03 — the assigned gate failure (FIXED)

**Root cause (measured, not assumed):** adding any library item opens the `#properties` panel → `#viewport` shrinks 1000→680px → `#bottom-left-toolbar` `max-width:calc(100% - 460px)` compresses it to 220px → the toolbar re-wraps into **3 rows ending at y=614** — directly under the toast band (678–722). `#context-hint` (bottom:40px) shared toolbar rows too.

**Fix (no size-budget risk, ~1.7KB):**
1. `#toast` — moved `bottom:70px` → **`top:64px`** (below the topbar, above everything bottom-anchored; toolbar can wrap as much as it likes).
2. `#context-hint` — `bottom:40px` → **`bottom:196px`** (clears the worst-case 3-row toolbar at 800px height) + `z-index:170`.
3. Toast duration capped in `showToast` (success/info **2600ms**, warning 4000, error 5000 — previously flat 3000) to shrink the exposure window.
4. Walk-mode toast-over-joystick collision eliminated by the same top anchoring.

**Gate result: V03 [live] toast does not intersect any toolbar button → PASS** (probe: toast 492–788 × 56–100; wrapped toolbar buttons all ≥ y614 in the repro state — zero intersection).

## Transient-overlay audit (all 6 + stacked states) — Playwright geometry + glm-5.3-flash vision

Triggered via real interactions: `.lib-item` click (toast+hint), Terrain panel → Grid-Level accordion → slider ArrowKeys (grid badge), `#vc-underground` click (depth gauge), snapshot+reload (recovery banner), sun/time change (atmosphere badge). Fixed-position phantom-overlap bug in the auditor itself was fixed (computed-style visibility).

| Overlay | BEFORE conflicts (geometry) | AFTER conflicts | Verdict files |
|---|---|---|---|
| `#toast` | terrain/excavate/terrain-analysis/innovation-btn | **none** | agent3-{before,after}-toast |
| `#context-hint` | (clipped sun-btn pre-fix) | **none** | agent3-{before,after}-context-hint |
| `#grid-level-badge` | overlapped `#atmosphere-badge` | **none** | agent3-{before,after}-grid-level-badge |
| `#depth-gauge-overlay` | none (right rail, clears stack) | **none** | agent3-{before,after}-depth-gauge-overlay |
| `#atmosphere-badge` | overlapped `#grid-level-badge` | **none** | agent3-{before,after}-atmosphere-badge |
| `#recovery-banner` | covered `#topbar` (top:16) | **none** (moved below topbar) | agent3-{before,after}-recovery-banner |
| toast+badge stacked | clean pre-fix, re-verified | **none** | agent3-{before,after}-toast-badge-stack |

**Geometry:** before **3/7 states clean** → after **7/7 clean**.

## Fixes shipped for audit findings (all verified by re-probe)

- **`_syncTopStack` resolver (JS, MutationObserver-wired):** deterministic non-overlapping ladder for every top-center transient — recovery banner / toast / grid badge / atmosphere badge — plus selected-object `#dim-readout` dropped below a visible toast (vision caught toast clipping the readout chip; re-probe: toast 56–100 vs readout 136–184, no overlap).
- **`#recovery-banner`** `top:16px` → `top:64px` (was under the topbar; banner z160 still outranks toast).
- **`#grid-level-badge` icon:** literal `\u2B06` rendered as the text "u2B06" inside the app toast/badge → real **⬆ glyph** (vision flagged this on 3 separate shots).
- **`#context-hint` z-order + panel dodge:** hint now `z-index:170` and `showHint()` lifts it above any floating panel whose bottom edge would bury it — fixed vision-flagged burying behind `#dock-underground` (was y574–604 under panel 506–682; hint now renders above, z-winner) and the Terrain-panel tooltip graze.
- **`.help-panel` / `.sc-panel` `overflow-y:scroll`** (always-visible scrollbar — vision "no visible scrollbar / looks cut off") and **visible ✕ close button** added to the help-modal header (`#help-x-btn`, same `.sc-close` styling as the shortcuts modal; wired to `closeModal`).

## Out-of-lane findings documented (NOT fixed — other agents' components)

Sidebar bottom items clip mid-row in screenshots only when the list is NOT scrolled to the end (at true scroll-bottom: lastBottom 770 < statusTop 776, both modes — Agent 1's V01 fix verified working; gate V01 checks pass 2/2). Compass-needle overshoot, empty BUILD group, "Innovate" label, grid-level slider label overlap, FPS placeholder, help-modal content overflow line — belong to surface/component agents and are unchanged by my edits.

## Gate status on final tree (744,957 / 768,000 bytes, headroom +23,043)

| Gate | Result |
|---|---|
| sprint11 (`--port 8095`) | **143/143** |
| sprint15 | **52/52** PASSED |
| sprint17 | **81/81** |
| sprint21 | **55/55** |
| sprint22 | **43/43** |
| qa_s21_dig_visibility (`BASE_URL`) | **16/16** |
| sprint23_quality_gate | **24/24 sprint-23 checks PASS** incl. V03 [live]; gate also runs 5 cross-lane glm-vision spot-checks (documented above) |
| size_budget.py | **PASS** (4/4 sub-gates, 744,957 bytes) |

## Byte budget

Merged baseline 740,810 → final **744,957** (+4,147: toast/hint repositioning, `_syncTopStack` resolver, hint panel-dodge in `showHint`, help ✕ button + close wiring, scrollbar visibility). All artifacts in `reports/sprint23_shots/agent3-*`.
