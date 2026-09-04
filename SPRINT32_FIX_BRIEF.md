# SPRINT 32 FIX BRIEF — sole-editor fixer (read EVERYTHING before touching code)

**Worktree:** `/root/byd32-fix` (branch `s32-fix` @ `75a9104`, byte size 767,973/768,000 — only 27 B headroom; compensating trims WILL be needed, use `/root/byd30-merge/s30_trim.py` pattern but VERIFY its output manually — its scanner mis-tracks quotes in HTML-in-JS strings (S31 lesson): census comments manually first, identity check = normalize-with-comments-stripped must be byte-identical, abort before write on any divergence).
**You are the ONLY editor.** Auditors were read-only; you land fixes; a separate verifier re-tests after you. NEVER touch `/root/backyard-designer` (canonical), NEVER push — Caddy holds deploy for Father Matt's explicit go.
**Model:** glm-5.3-flash / ollama-cloud (key from `/root/.hermes/.env` `OLLAMA_API_KEY=...`, never print it). Vision: base64 image_url, temperature 0, sequential calls only.
**Per-fix commit discipline:** one commit per fix, message prefix `S32-<id>:`, author via `git -c user.name="Caddy" -c user.email="caddyaibot@gmail.com"` (NEVER global config). Each commit includes before/after evidence (JSON probe + screenshot) under `reports/s32/fixes/`.
**Byte cap:** 768,000 hard. After EVERY edit run `python3 size_budget.py` in the worktree. Budget trims from your own added comments first.
**Gates:** serve `/root/byd32-fix` on port 8380 (bind-test first, +1 if taken). Full battery must be green before you finish: s11 (143, `--port 8380`), s15 (52, `--port`), s17 (81, `BASE_URL=http://127.0.0.1:8380`), s21 (55, `--port`), qa_s21 (16, `BASE_URL`), s22 (43, `--port`), s23 (24, `--port 8380 --skip-vision`), s29 (33, `--port 8380 --skip-vision`). s21's topsoil pixel window is centered (133,91,58) and hexhint 0x5c — do not disturb; if your fixes touch terrain colors, update the gate contract in the SAME commit, honestly.

## Audit evidence (READ THE FULL REPORTS FIRST — they are your source of truth)
- `/root/byd32-audit/A/REPORT.md` (133 features mapped, 64 vision calls)
- `/root/byd32-audit/B/REPORT.md` (38-step fresh-user session)
- `/root/byd32-audit/C/REPORT.md` (47 surfaces, terrain deep-sim, pixel forensics)
- `/root/byd32-audit/D/REPORT.md` (26 surfaces, atmosphere; REG-D01 with pixel proof)
- `/root/byd32-audit/E/REPORT.md` (21 flows, numeric evidence; source-line citations)
- Screenshots + JSON per report dir. Verify every claim yourself with DOM probes before fixing — agent findings are leads, not gospel.

## THE FIX QUEUE (in order; DOM-arbitrate the two conflicts first)

### CONFLICT ARBITRATION (do these two FIRST — agents disagree, you decide with DOM)
1. **Share Copy (A says always-fails / B says works):** B's run got toast '✓ Link copied to clipboard!', A's got '✕Copy failed — select the link manually'. Root cause to establish: `navigator.clipboard` is undefined on http:// (non-secure origin) and both agents served over http://127.0.0.1 — likely BOTH observed real behavior and the handler has a fallback path that works sometimes (document.execCommand?) or A's click missed. Probe `navigator.clipboard` existence + the actual handler code path in source. Fix direction: make Copy ALWAYS work on insecure origins via the classic textarea+execCommand('copy') fallback; keep the secure-path code. Evidence: which branch produced which toast.
2. **Export menu (D says REG-D01 clipped+unclickable / E says OBJ+STL+heightmap all downloaded fine):** D's pixel proof is strong (elementFromPoint → canvas; zero menu pixels). E's downloads succeeded — likely E ran flows with a different sequence (menu opened before topbar overflow state differed) or at different viewport. Reproduce BOTH: open export menu at 1280×800 in a fresh session and after the E-style flow. If REG-D01 confirms, fix = render the menu outside the topbar's `overflow-x:auto;overflow-y:hidden` context (absolute-position to body or `position:fixed`, or move menu element out of `#topbar` in DOM). Keep the S30 overflow cue intact (s23/s29 gates may assert topbar geometry — grep gate sources BEFORE restructuring; the S30 gate-locked-selector lesson: keep the gate-asserted artifact, achieve UX via an alternative element/structure).

### P0 — First-run dead features (A01+A02+B01/D07 converge on ONE root cause)
3. **Welcome-prompt + guided tour unreachable.** The wizard-hide MutationObserver (source ~15688-15709) sets `welcomeShown=true` on ANY wizard close and shows a toast; `showWelcomePrompt()` has zero live callers (def ~15127); `#onboarding-restart-btn` requires `tourCompleted=true` (only `endTour(true)` sets it — a tour can never start). Fix shape (restore S30-era behavior): after the wizard finishes OR is skipped on a FIRST session (no saved design, `welcomeShown` false), show the `#welcome-prompt` modal instead of the bare toast. Keep the toast for REPEAT sessions. Verify `#wp-tour` → tour actually starts (6 steps), `#wp-scratch`/`#wp-template`/`#wp-import`/`#wp-remind-later` all function from the modal. Add the tour-completed restart pill path unchanged.
4. **Contour lines silent no-op (C32-A05).** Toggle flips + success toast, but `buildContourLines()` early-returns (`marchingAllPoints<6` guard per A) or the mesh is added but invisible/culled. Instrument: call the builder path with real dug terrain (relief ≥15ft qualifies), find why nothing renders (likely the guard counts wrong or mesh material/depth is off). Fix so contour lines actually render at 0.5ft interval on real relief. Keep the toast honest — if the builder legitimately produces nothing (flat terrain), the toast must say so.

### P1 — Broken interactions
5. **Topbar not scrollable by real input (C32-A04).** Programmatic scrollBy works; wheel deltaX / Shift+wheel leave scrollLeft=0 (S30's chevron cue renders, but the affordance is dead). Fix: a wheel handler on `#topbar` translating vertical wheel to horizontal scroll (only when overflowing), and/or Shift+wheel native passthrough. Do NOT break the S30 overflow cue or the gate-locked topbar geometry (see conflict-2 note).
6. **Label edit/delete dead code (C32-E-01).** `showLabelEditModal` only ever called with `labelId=null` (creation); no raycast/click handler for existing label sprites; `editingLabelId` never set to a real id. Fix: click (or dblclick) on an existing label sprite raycasts and opens the modal in edit mode (populate text+color, `#label-delete-btn` deletes, updateLabel applies). Gate: creation path must keep working exactly as now (E's F10b verified create+color works).
7. **Cut/fill panel stale after digs while enabled (C32-E-02).** Panel shows 0 yd³ after new digs when already open; correct only after toggle OFF→ON. Refresh guard sits in `applyTerrainFull()` full-rebuild branch; the pointer-up flush path (`_flushTerrainFull` → `applyTerrainFull(null)`) doesn't reach `updateCutFillVolume`. Fix: call the refresh on the flush path too (instrument call sites first, per E's J32-E-01 hint). Arithmetic itself is exact — don't touch the math.

### P2 — Night-sky investigation (fix if root cause is in-app; document if environmental)
8. **Stars never rasterize (R32-D01) + no moon mesh (R32-D02).** starField.visible=true, opacity 1, 800 points, yet 0 star pixels even with sky-dome hidden; moon mesh absent from scene traversal entirely. Investigate: Points material size (SwiftShader may need sizeAttenuation false / larger size), render order/depth against sky dome, and whether the moon mesh is ever created (grep the creation path — D found no mesh by name). If stars render with a material tweak, fix it (verify by pixel-diff at night). If it's a genuine SwiftShader-only rasterization limit, document precisely what you proved and leave the code correct-but-environmentally-unverifiable — with the evidence.

### P3 — Small UX fixes (cheap, high-value)
9. **Recovery banner 'Discard' → 'Start Fresh' (J32-B02)** — keep aria/behavior, change visible label only (check no gate asserts the string 'Discard').
10. **Double recovery path (J32-B03):** when the recovery banner is visible on boot, hide the wizard's 'Continue previous design' button (one canonical restore path); if banner is absent (explicit save), wizard Continue remains. Verify B's S24 scenario (banner + wizard co-occurrence) is resolved.
11. **Permit region switch wipes typed inputs (E minor):** preserve user-typed setback/fence-height when switching region; only reset values the user hasn't touched (or warn). Low risk, small diff.
12. **Dig Down chip × Sun pill 31px overlap (J32-B01, known-open):** fix direction from S30 verifier — right-align the chip or clamp its width so the Sun pill no longer overlaps the chip's text zone. s29 gate locks some geometry — grep before moving anything.

### DO NOT FIX (refuted by auditors — phantom work)
Templates dead-end (R32-A01), QR broken (R32-A03), export buttons dead (R32-A04 — unless conflict-2 proves REG-D01), walk-hint overlap (R32-A06), label creation broken (R32-A08), recovery banner never shows (R32-E-01), templates double-click (R32-E-02), tape measure stale (R32-E-03), permit inputs dead (R32-E-04), Patio sidebar clip (R32-B01), share URL truncation as defect (R32-B05).

### KNOWN-OPEN, NOT IN SCOPE (do not spend bytes)
walk-hint × toast band, sub-px crater seam slivers, yard-boundary skirt, cut-face strata/brightness (C confirmed it includes brightness — queue for a future render sprint, needs real-GPU testing), Innovate discoverability restructure (J32-C-4.12/J32-A04 — design decision for Father Matt, not a solo fix).

## Vision verification (Father Matt's standing requirement)
For every fix: reproduce the defect scene before (screenshot), apply fix, reproduce after (screenshot), vision-judge BOTH with glm-5.3-flash (temp 0), record verdicts in the fix's evidence JSON. For REG-D01 and contour lines, also verify at a second viewport (1024×768). For the welcome/tour fix, run the FULL first-session flow (fresh profile, wizard → finish → welcome modal → tour → complete) and screenshot each stage.

## Finish checklist
1. All queue items resolved (fixed or evidence-documented as environmental).
2. Full gate battery green (list actual counts in your report).
3. `python3 size_budget.py` PASS, byte size ≤ 768,000, reported exactly.
4. Every fix committed `S32-<id>:` with evidence, tree clean, NO push.
5. Write `/root/byd32-fix/reports/s32/fixes/FIX_LOG.md` (fix id → files touched → commit SHA → verification verdict → evidence paths).
6. Final chat answer < 60 lines: FIX_LOG pointer, commit list, battery tallies, byte size, any items you could NOT fix and why.

## Incremental-write discipline
Write FIX_LOG.md entries AS YOU GO (one entry per fix, immediately). Never hold the whole log for a single final write. Long final answers die to the 90s timeout — the log on disk is the deliverable.