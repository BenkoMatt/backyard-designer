# Sprint 29 Brief — Overnight Full-Visual Quality Swarm

**Baseline:** `1934c12` on branch `s29-overnight` (origin/main incl. Sprint 27 perf + Sprint 23 toast-hygiene merge).
**Worktrees:** `/root/byd29-<role>` (create via `git worktree add /root/byd29-<role> -b s29-<role> 1934c12` from /root/backyard-designer).
**Sole-editor rule:** The kanban swarm's Sprint 28 walk-rework builder (t_80dc33f7) is the SOLE editor of `/root/backyard-designer`'s working tree. DO NOT touch, commit, stash, or check out anything in /root/backyard-designer. All your edits happen in YOUR worktree at /root/byd29-<role>. Final integration happens at the orchestrator level only.

## Mission
Full-visual overnight quality pass: screenshot EVERY user-reachable surface of the app with real CDP
clicks, judge each with glm-5.3-flash vision (base64 in image_url, temp 0), FIX everything not CLEAN,
re-verify, and lock all fixes behind a new gate. Token budget: unlimited — be exhaustive. If a verdict
says "Not CLEAN", that surface is a bug regardless of DOM tests passing (Excavate lesson, S20).

## Vision recipe (copy-paste)
```python
# key: /root/.hermes/.env OLLAMA_API_KEY
# POST https://ollama.com/v1/chat/completions  Authorization: Bearer $KEY
# {"model":"glm-5.3-flash","messages":[{"role":"user","content":[
#   {"type":"text","text":PROMPT},{"type":"image_url","image_url":{"url":"data:image/png;base64,..."}}]}],
#  "options":{"temperature":0}}
PROMPT = ("1280x800 screenshot of a 3D backyard design web app. QA: (1) any overlapping or clipped "
          "UI? (2) would a new user understand this screen in 5 seconds? (3) anything confusing, "
          "ambiguous, misplaced, or broken-looking? If perfect, reply CLEAN plus a one-line summary.")
```
Crop-edge false positives: a vision finding at the EXACT image edge is suspect (Agent 2's S23 lesson) —
confirm with element.getBoundingClientRect() before fixing. Two-vision-consensus for any ambiguous call.

## Surfaces (ALL of them — Basic AND Advanced unless noted)
**First-run:** wizard steps 1→final; welcome-prompt
**Topbar:** every tb-btn; mode toggle both ways
**Left sidebar:** every category expanded; every library item hover + click; long-list scroll cue
**Bottom-left toolbar (both rows!):** Tape, Terrain, Excavate, Analyze, Innovate, Sun — click each,
  screenshot panel open + closed; verify no toast/hint covers any button
**Every panel:** terrain-controls (all 3 accordions + presets), excavate, terrain-analysis
  (every toggle), innovation (every tool), sun (every control), cost, layer, season, growth, permit,
  cross-section, cut-fill, buried-objects list with 2+ buried items
**Dock panels (td-tab):** terrain, underground — zero-scroll mandate at 1280×800; also 1600×900
Every modal: help (scroll to bottom & back), shortcuts (?/F1/topbar/Help-link), share, templates,
  gallery, label-edit, cmd palette (Ctrl+K), print preview
**3D states:** grid on/off, underground view on/off, cutaway@50, cross-section x/z, walk mode entry+exit,
  grid-level badge at several levels, depth gauge, measure readout mid-measure
**Status surfaces:** toasts (trigger Save tip, Cost tip), context-hint, recovery banner (drop localStorage
  seed), sprint-24 atmosphere badge, timelapse modal, socialcard modal, batch-bar (if Advanced)
**Edge cases:** EMPTY yard after Clear All; yard at 200 objects (add via window._test loop); window
  sizes 1280×800 AND 1600×900 AND 1024×768 (minimum desktop)
That is 50+ surface-shots minimum. Save all to reports/s29_shots/<surface>_<mode>.png with
verdict JSON sidecars. EVERY verdict file stays in the repo.

## Hard rules
1. index.html ≤ 768,000 bytes. Baseline 756,969 (+11k headroom). Run `python3 size_budget.py` after every edit; FAIL = stop and trim before continuing.
2. Real CDP pointer/keyboard events only; page.evaluate ONLY for read-only probes + window._test setup.
3. Never run your http.server on ports 8099/8115/8175/8093/8095 (owned by others). Use 8180+. One server per agent, tear down after.
4. All existing gates must pass on your final tree: s11 (143), s15 (52, --port), s17 (81), s21 (55, --port), s22 (43, --port), qa_s21 (16, BASE_URL), sprint23 gate (24/24 REQUIRED now — V03 toast lock must be green), size_budget (4/4), sprint16 informational (29/32 expected, pre-existing).
5. Commit as: git -c user.name="Caddy" -c user.email="caddyaibot@gmail.com" commit. Commit after each surface group, not one mega-commit.
6. If a fix needs >200 bytes net, find compensating trims (dead CSS/comments only; keep S23-Vxx markers).
7. Three.js importmap unchanged; mesh terrain; no geolocation; desktop-only.

## Roles (6 agents)
1. **AUDIT-CORE-UI** (owner: surfaces first-run, topbar, sidebar, 3D states, edge cases): full sweep with before/after + fixes; reports/s29_shots; VISION_QA_S29_report.md section 1.
2. **AUDIT-PANELS** (owner: every panel listed above incl. buried-objects): sweep + fix + section 2.
3. **AUDIT-MODALS-DOCKS** (owner: every modal + dock panels, zero-scroll at both resolutions): sweep + fix + section 3.
4. **AUDIT-TRANSIENTS** (owner: toasts/hints/badges/banner + print view + share flows + cmd palette flows): sweep + fix + section 4.
5. **FIXER-CONVERGENCE**: do NOT sweep surfaces; instead consume sections 1-4 as they land (poll your inbox via task handoff files in /root/byd29-staging/S29_HANDOFF.md), independently re-verify every reported fix with your own screenshots, fix anything still dirty, reconcile conflicts between roles (e.g. two agents fixing the same rule differently). Own the final VISION_QA_S29_report.md verdict table.
6. **SIZE-COP+GATE**: watch byte budget; compensating trims; build sprint29_quality_gate.py locking every S29 fix (DOM rects + vision spot-check on 6 hot surfaces); run the FULL battery (item 4 in rules) on the final s29-overnight tree; write gate table into report section 6.

## Handoff protocol
Agents 1-4 append findings to /root/byd29-staging/S29_HANDOFF.md (create it; one JSON line per finding:
{"surface","verdict","issue","fixed_y_n","commit"}). Agent 5 polls it. Everyone commits to their own
branch s29-<role>. Orchestrator (Caddy) merges at dawn: core UI branches → transients → fixer-convergence
→ size-cop gate, then full battery, then push.