# VISION_QA_REPORT.md — Agent 4 (QUALITY-GATES-V23) Section

**Agent:** Sprint 23 #4 · **Branch:** `sprint23-quality-gates` @ `6056f88` (baseline, pre-merge)
**Gate:** `sprint23_quality_gate.py` (CDP + DOM locks) · **Vision:** glm-5.3-flash via Ollama Cloud, temp 0, per-surface QA prompt from SPRINT23_BRIEF.md
**Final gate result on this tree:** 18 PASS / 11 FAIL / 29 total — every FAIL is a documented, expected pre-merge lock (see table).

## Merge-lock accounting (read this first)

This agent does not own fixes (a)/(b)/(c). Agent 1 owns the sidebar status-bar clearance (a), Agent 2 the double-Underground (b) and panel-stacking audit, Agent 3 the toast overlap (c) and hint hygiene. This gate locks ALL SIX fix surfaces; on the pre-merge baseline the three unmergeed fixes fail **by documented design** (same pattern as the Sprint 22 gate's pre-merge guide tests):

| Gate lock | Surface | Pre-merge | Post-merge (expected) |
|---|---|---| run |
|---|---|---|---|
| V01 (static+live, basic+advanced) | Sidebar status-bar clearance (a) | FAIL (documented) | PASS |
| V02 (static+live) | No double Underground panels (b) | FAIL (documented) | PASS |
| V03 (static+live) | Toast never covers toolbar (c) | FAIL (documented) | PASS |
| V04 (static+live) | Modal scroll-top reset | **PASS now** | PASS |
| V05 (static+live) | content-visibility un-hooked (help modal scrollable) | **PASS now** | PASS |
| V06 (static+live) | sc-keys badge no-clip | **PASS now** | PASS |

## CDP/DOM proof (pre-merge baseline, port 8093)

- **V01:** `#sidebar` padding-bottom = 0px; last `.lib-item` bottom = 798.2px vs status-bar top = 776px → 22px of the last catalog row is behind the status bar even at full scroll. Fix (a) is needed exactly as briefed.
- **V02:** after a single real click on `#excavate-btn`, two "Underground View" headers render simultaneously at y=590 (dock header) and y=629 (relocated excavate header) — the brief's bug (b), confirmed live.
- **V03:** toast band (491–788 × 678–722) intersects terrain/excavate/terrain-analysis/innovation buttons after a real item add — fix (c) is needed.
- **V04:** scrollHeight 2416 / clientHeight 640; reopen lands at scrollTop 0. **V05:** content-visibility 'visible', last section fully shown at bottom. **V06:** 21 rows, 0 clipped, computed max-width 45%.
- 0 console errors, file size 766,138 ≤ 768,000, CSS braces balanced.

## Vision before/after table (5 surfaces)

| Surface | Verdict (full text in `reports/sprint23_shots/<name>.verdict.txt`) | Classification |
|---|---|---|
| v_main_basic | NOT CLEAN: sidebar last item clipped by status bar; Sculpt rail labels occluded/truncated when panels overlap it; toast over toolbar rows | (a) + Agent 2 stacking + (c) — all owned, no new bug |
| v_sidebar_advanced (all categories expanded, scrolled) | NOT CLEAN: "Innovate" label unclear; bottom quick-bar duplicates left-rail tools; initial library scroll position | report-only wording/duplication nits |
| v_toolbar_panel_basic (terrain panel open) | NOT CLEAN: sculpt-rail truncated labels under panel; dock panel lower edge reaches ~784px under/behind status bar; toast over toolbar | Agent 2 stacking + (c); brief lists dock panels through the end of the surface list |
| v_underground_advanced | NOT CLEAN: **two duplicated "Underground View" panels** (matches V02 live proof), tip tooltip covers panel first row, sidebar/status-bar collision, panel bottom edge near fold | (b) + Agent 2 stacking + (a) + Agent 3 hint hygiene |
| v_help_modal_basic | NOT CLEAN: modal text "clipped mid-sentence with no scrollbar, no close button visible" | headless-scroll artifact (CDP proves scrollHeight 2416 > clientHeight 640; close button + last section reachable at bottom per V05 live) — reportable UX nit: close button below the fold at scrollTop 0 |

## Sprint 23 quality-gates conclusion

- All three known open issues (a)/(b)/(c) are **independently confirmed by CDP geometry** on the baseline and locked with regression tests that flip PASS when agents 1/2/3 merge.
- Fixes 4/5/6 (help-modal content-visibility un-hook, openModal scroll reset, sc-keys no-clip) are **verified present and locked**.
- No index.html change was authored by this agent; nothing in the findings is un-owned or a new regression introduced by Sprint 23 work.
- Harness quirks reconciled: toast-visibility timing race (poll `wait_for_function`), toolbar re-wrap shifts geometry after object add (probe before asserting), dock strip hides when a dock panel is open (force-click per repo precedent), `page.evaluate` used only for read-only probes + wizard-dismiss setup.

Caddy · Sprint 23 Agent 4 · 2026-08-31