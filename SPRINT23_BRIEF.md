# Sprint 23 Brief — Vision QA Sprint (Quality Checks Only)

**Baseline commit:** `03475abb` on `main` of `/root/backyard-designer` (Sprint 22 deployed live).
**Branch name:** `sprint23-<role>` from that commit. Work in `/root/byd23-<role>`.

## Mission
Pure quality verification + fix sprint. NO new features. Use vision (glm-5.3-flash
multimodal via Ollama Cloud, base64 image in image_url) to judge whether every surface of
the app "makes sense in 5 seconds" and has zero overlaps/clipping. Then FIX what vision
finds, and re-verify. Tests and vision must both pass — tests alone are not enough.

## Vision workflow (required)
```python
# GET https://ollama.com/v1/chat/completions
# Authorization: Bearer $OLLAMA_API_KEY  (in /root/.env or /root/.hermes/.env)
# body: {"model":"glm-5.3-flash","messages":[{"role":"user","content":[
#   {"type":"text","text":"<QA prompt>"},
#   {"type":"image_url","image_url":{"url":"data:image/png;base64,<b64>"}}]}],
#  "options":{"temperature":0}}
```
Per-surface prompt: "1280x800 screenshot of a 3D backyard design web app. (1) Anything
overlapping or clipped? (2) Would a new user understand what to do within 5 seconds?
(3) Anything confusing, ambiguous, or broken-looking? Reply CLEAN if perfect."

## Surfaces to audit (each: Basic AND Advanced mode, real CDP clicks only)
1. Wizard (first-run) — all steps
2. Main view default state
3. Left sidebar: every category expanded, item hover states
4. Bottom-left toolbar: Tape/Terrain/Excavate/Analyze/Innovate/Sun, each clicked
5. Every panel: terrain-controls, excavate, terrain-analysis, innovation, sun, cost, layer,
   season, growth, permit, cross-section, cut-fill
6. Every dock-panel via td-tab clicks (terrain, underground) at 1280x800 — verify ZERO scroll
7. Every modal: help, shortcuts (?), share, templates, gallery, label-edit, command palette (Ctrl+K)
8. Walk mode overlays; grid-level badge; depth gauge; recovery banner
9. Status bar + context hints + toasts
10. Print view

## Known issues found in Sprint 22 close-out vision pass (VERIFY FIXED, do not regress)
- FIXED: help-modal bottom clipping (content-visibility unhook) — re-verify scrolled-to-bottom
  shows last section fully.
- FIXED: help-modal opens mid-scroll (openModal now resets scrollTop).
- FIXED: shortcuts guide arrow-badge truncation (.sc-keys max-width:45% + flex-shrink:0).
- KNOWN REMAINING (fix in this sprint):
  a) Left sidebar last .lib-item partially hidden behind #status-bar at 800px height, no
     scroll cue — add bottom padding equal to status bar height (min 28px) to #sidebar.
  b) Opening the Underground dock tab AND #excavate-panel simultaneously produces TWO
     stacked "Underground View" floating panels at bottom-left. #excavate-panel and the
     underground dock panel must be mutually exclusive or merge into one.
  c) "Advanced mode" toast can overlap bottom toolbar buttons — shorten duration or shift up.

## Rules
- Single-file index.html; hard size limit 768,000 bytes (current: 766,138 — only 1,862
  bytes headroom! Any addition needs equal compensating trims. Run `wc -c` after every edit).
- Three.js v0.160.0 importmap unchanged; desktop-only; no geolocation.
- Real CDP pointer/keyboard events for interaction; page.evaluate allowed ONLY for
  read-only probes and window._test terrain setup.
- Do not break existing gates: s11 (143), s15 (52), s17 (81), s21 (55), s22 (43),
  qa_s21_dig_visibility (16) must all pass before you commit.
- Commit with: git -c user.name="Caddy" -c user.email="caddyaibot@gmail.com" commit
- Commit early and often; final commit message describes vision findings + fixes.
- Ports: use 8091+ (avoid 8099/8115/8175; other agents share the machine). Add a
  `--port` flag to any new test script; BASE_URL env var for CDP suites.

## Deliverables
1. Fixed index.html (≤768,000 bytes) with the fixes above + your own findings.
2. `VISION_QA_REPORT.md` — before/after table: surface → vision verdict → fix → re-verdict.
3. Screenshots (before/after) under `reports/sprint23_shots/`.
4. `sprint23_quality_gate.py` — regression locks for everything you fixed (CDP + DOM checks).
5. All 6 existing gates passing on your final tree.

## Roles (5 agents)
1. **VISION-AUDIT-SURFACES**: Run the full surface audit exactly as listed; fix issues
   found; produce before/after shots + report; own the sidebar status-bar padding fix.
2. **PANEL-CONFLICT-RESOLVER**: Own the double "Underground View" fix (mutual exclusivity)
   + audit panel stacking/z-order conflicts across all panels; write regression test.
3. **TOAST-HINT-HYGIENE**: Own toast overlap fix + audit all toasts/hints/badges for
   timing/stacking issues; ensure nothing permanent blocks toolbars.
4. **QUALITY-GATES-V23**: Build sprint23_quality_gate.py locking all the above fixes;
   verify all 6 existing gates pass; reconcile any harness quirks you find (document).
5. **SIZE-COP + FINAL SWEEP**: Monitor byte budget (reject >768,000), find compensating
   trims (dead CSS, duplicate rules, long comments) while others work; last mile: run all
   gates + full vision pass on final state; write final section of VISION_QA_REPORT.md.