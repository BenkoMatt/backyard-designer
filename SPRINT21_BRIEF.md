# Sprint 21 Master Brief — UI Accessibility & Dig Visibility

## Mission
Backyard Designer 3D (single-file `index.html`, 17,271 lines, ~728KB — hard limit 750KB).
The owner has two blocking complaints plus a general mandate:

1. **MANDATE — No unnecessary scrolling:** Every panel must show its primary/essential
   controls without scrolling. Specifically: in the Terrain dock, the user must scroll
   to reach the **Dig** and **Fill** mode buttons. Reorganize so primary actions are
   always visible. Collapsible/progressive-disclosure is preferred over scrolling for
   secondary controls (carving, presets, overlays, grid-level).

2. **MANDATE — Excavate must reveal the ground:** The user's primary way into the
   ground is the **Excavate button** (#excavate-btn, bottom toolbar). Its click handler
   (line ~10610) ONLY toggles `excavatePanelVisible` — it never activates the auto-dig
   clip plane. Result: the user sees only the flat green plane, never the geological
   layers. The auto-dig clip plane (`updateAutoDigClip()`, line ~4110) currently arms
   ONLY when the Terrain dock's Dig brush button is clicked (line ~7052-7064 sets
   `terrainBrushMode` then calls `updateAutoDigClip()`).

   **Required fix (root cause, not symptom):** Entering the Excavate/Underground flow
   must make the underground visible. Minimum viable behavior: when the Excavate panel
   opens, enable the clip-plane pathway so dug areas reveal geological layers, and
   restore normal view when it closes. Preferred: unify the excavate panel with the
   dig-brush state so ANY route into the ground (Excavate button, Terrain dock Dig
   mode, V key, etc.) drives ONE canonical clip-plane state function. Audit ALL entry
   points to underground/ground visibility (excavate button, cross-section, cutaway
   slider, wireframe, opacity slider, vc-underground button, keyboard shortcuts) and
   ensure each one actually exposes the subsurface — no dead or half-wired controls.

3. **MANDATE — Full UI accessibility audit:** With the app's vision capability
   (screenshots can be analyzed by the model), do a screenshot-driven review of every
   panel/modal/dock in Basic AND Advanced mode. Anything a user needs must be visible
   in its menu without scrolling unless genuinely unavoidable. Fix panel heights,
   reorganize into tabs/collapsible sections, and ensure controls are reachable in
   ≤1 click from panel open.

## Hard Constraints (violating any = rejected merge)
- Single-file architecture. Do NOT split files. Do NOT add build tools.
- Three.js v0.160.0 via importmap — do not change version.
- 750KB total size limit — current 728KB. Net additions must stay under ~20KB total.
- Do not break existing features. All existing quality gates must pass at current
  pass rates (see Verification). No renames of public functions/IDs used by tests.
- Desktop-only — no mobile CSS.
- CSS SYNTAX DISCIPLINE: a missing `{ }` body on a selector list previously caused a
  site-wide dead-button bug (the parser swallowed the NEXT rule as the body). After
  ANY CSS edit, run a brace-balance check on the <style> block.
- MODULE SCOPE: the main script is `<script type="module">` (line ~3008). Any function
  invoked from inline/HTML event handlers or global-scope listeners must be exported on
  `window` (see the GLOBAL SCOPE EXPORTS block near file end, ~line 16880+).
- UI verification MUST use real CDP mouse events (Playwright page.mouse / Input.dispatchMouseEvent
  or element.click() via CDP), NOT page.evaluate() calling page functions — evaluate
  bypasses hit-testing and global-scope, giving false passes (this exact failure
  burned Sprints 16-18).
- Commit author: `git -c user.name="Caddy" -c user.email="caddyaibot@gmail.com"`.
- No API keys or credentials in code.

## Verification (run these, include results in your final report)
- `python3 -m http.server 8115` → `python3 sprint11_quality_gate.py`  → expect 143/143
- `python3 -m http.server 8175` → `python3 sprint17_quality_gate.py`  → expect 81/81
- sprint15 gate (51 tests) if your changes touch terrain/cross-section.
- For any UI change: real-CDP click test + a screenshot analyzed visually (confirm the
  change is visible in the rendered pixels, not just in the DOM).
- Report file size after changes: `wc -c index.html` must stay ≤ 768,000 (safety margin).

## Key file landmarks
- `<script type="module">` line ~3008
- Terrain dock HTML: lines ~2104-2262 (mode buttons ~2110-2118, carving ~2180-2240,
  presets/overlays ~2245-2262)
- Excavate button handler: line ~10610; excavate panel HTML ~2280-2345
- updateAutoDigClip(): line ~4110; single call site line ~7064
- terrainBrushMode default 'raise': line ~4071
- buildSolidEarth / solidEarthMesh (geological interior walls): ~7409
- NAMED_GEO_LAYERS (topsoil/subsoil/clay/bedrock): line ~7359
- Quality gates: sprint11_quality_gate.py (port 8115), sprint17 (8175), sprint15 (port 8155)
- Window exports block: ~line 16880+