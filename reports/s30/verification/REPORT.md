# SPRINT 30 — ADVERSARIAL VERIFICATION REPORT (independent verifier)

**Tree:** /root/byd30-fix @ 0c39d76 (s30-fix, 21 commits on bfbe1fa). Server: 127.0.0.1:8314 (own http.server, bind-tested 200/767,954 B). Baseline control served from a git-worktree copy of bfbe1fa on 8324 (read-only).
**Method:** real CDP input (Playwright mouse/keyboard), read-only evaluate probes, pixel forensics (PIL), glm-5.3-flash temp 0 vision. READ-ONLY on the app tree (git status clean except this report dir); NO PUSH.

## Environment setup (verified)
- http.server 8314 → 200, 767,954 B served.
- Byte ledger at start: index.html 767,954 / 768,000 (headroom +46). size_budget.py own run: **PASS 4/4**.
- Marker whitelist: `grep -c "S23-V" index.html` = 33 (bfbe1fa: 33); `grep -c "S29-"` = 32 (bfbe1fa: 32). **UNCHANGED.**

## Gate battery (own run, port 8314) — COMPLETE
| Gate | Expected | Own run | Result |
|---|---|---|---|
| sprint11_quality_gate.py | 143 | **143/143** (0 failed, 100.0%) | PASS |
| sprint15_quality_gate.py | 52 (PASS) | **52/52** — "QUALITY GATE: PASSED" | PASS |
| sprint17_quality_gate.py (BASE_URL) | 81 | **81/81** (0 failed) | PASS |
| sprint21_quality_gate.py | 55 | **55/55** (0 failed) | PASS |
| sprint22_quality_gate.py | 43 | **43/43** (0 failed) | PASS |
| qa_s21_dig_visibility.py (BASE_URL) | 16 | **16/16** | PASS |
| sprint23_quality_gate.py --skip-vision --expect-open-fixes | 24 | **24/24** | PASS |
| sprint29_quality_gate.py --skip-vision --expect-open-fixes | 33 | **33/33** | PASS |
| size_budget.py | 4/4 | **PASS 4/4** (767,954/768,000, +46) | PASS |

All gates green on the verifier's own run at 8314. Matches fixer claims exactly.

---

## Per-fix verification (real CDP input, port 8314, shots in shots/)

### S30-B-walkhint (981eb6a) — VERIFIED
- Fresh load 1280×800 → real `w` keypress enters walk mode.
- #walk-hint computed top **64px**; hint rect y=64-94 (x=391-888).
- Old neighbors (Sprint-23 lock targets): "3D View" (y=13-38) and "Bird's-eye" (y=13-38) → **overlap 0 px²**.
- Evidence: shots/v_f1_walkhint.png, v_f1_f3_results.json.

### S30-B-share (9dfdbcf) — VERIFIED
- Scrolled topbar right, real click #btn-share → modal visible. #share-url-box: clientW 290, scrollW 605 (overflow real), computed **text-overflow: ellipsis** (was clip); white-space:nowrap + overflow-x:auto retained (S29-R3e preserved).
- Copy path intact: DIV textContent 89 chars, select/copy unaffected.
- Evidence: shots/v_share.png, v_f1_f2_f3_results.json.

### S30-A-cs-overlay (e9fda02) + S30-A1 (30d688e) — VERIFIED (joint repro)
- Advanced: underground dock → cross-section-toggle → panel open.
- A1: canvas (859,266 390×176) **no overlap** with #cs-close (1230,170 19×21); elementsFromPoint = **cs-close**; **real click closes the panel** (no timeout).
- A-cs-overlay: #ta-cross-section-overlay .visible (real path 9044), real Esc → **taVisible:false AND dockVisible:false**.
- Evidence: shots/v_f3_cs_panel_open.png, v_f3_after_esc.png, v_f1_f3_results.json.

### S30-A-topbar (d1a1d71) — VERIFIED (behavioral caveat noted)
- 1280/1024/1600 basic + 1920 control, rest + after real wheel-scroll:
- 1280 rest: `scrolled-end`, ::after 48px, '›' chevron, sw1713/cw1280. 1024: cue=True. 1600: cue=True, Share x=1548 partially cut; after wheel right: Share fully visible, hit-test = btn-share.
- **1920 (no overflow): no cue** (sw==cw, chev none) — requirement holds.
- Caveat: `scrolled-end` stays set at exact scroll-end (no scroll event fires); pointer-events:none → cosmetic only, strictly better than pre-fix permanent 24px gradient. Not a regression.
- Evidence: v_topbar_results.json, shots/v_topbar_*.png.

### S30-B-basic (e66a697 → 63ace65 → c63fa88) — VERIFIED (final form; 1 new minor defect recorded)
- Basic 1280: underground tab computed **display:none** (S17 gate state kept; s17 81/81 on my run).
- #vc-underground in Basic: 96.7px wide, **"Dig Down" ::after chip + accent outline, correctly scoped to `body.byd-basic-mode`** (Advanced keeps 40px icon-only — rules verified scoped).
- REAL click → active:true + toast "Underground view active — orbit to explore carved spaces". Dead-end resolved.
- Advanced: tab display:flex, opens dock — **no neighbor regression**.
- **NEW minor defect (see NEW DEFECTS #1): chip tucks under the Sun pill in Basic.**
- Evidence: v_basic_underground_results.json, v_digdown_arb.json, shots/v_basic_*.png.

### S30-B-skip (cf7b72f) — VERIFIED
- 1280×800, 1024×768, 1600×900 × steps 1+2: skip **inside .wizard-panel**, fullyInside:true everywhere (old defect y=624 vs panel 588 → now e.g. bottom 579 < 611).
- Progressive tip: intersects:false at all viewports (old 7,832px² collision structurally gone).
- elementsFromPoint at skip center = wizard-skip; REAL click dismisses wizard at all 3 viewports.
- Short-viewport control 1024×600: panel fits (bottom 511 ≤ 600), skip inside.
- Evidence: v_wizard_skip_results.json, shots/v_wizard_*.png, v_hunt_results.json.

### S30-B3 (611dd48) — VERIFIED
- Real wizard finish (#wizard-finish) → +1.8s: welcomeVisible:false, wpDisplay:none, **single ready-toast**. No second welcome.
- SKIP path also verified (no second welcome; toast text set).
- Recovery flow intact (S29-T09): real add → dirty → reload → **banner visible** ("Restore unsaved changes? Saved 6:33 PM") → real Ctrl+S → **banner cleared**, "✓ Design saved!".
- Evidence: v_b3_results.json, v_b3_banner_results.json, shots/v_b3_*.png.

### S30-A2 crater wall sealing (24d1b2f) — VERIFIED (sub-pixel residue documented, NOT a regression)
- Original path reproduced: Advanced, Dig, brush 25, 3×2 strokes, 2 sites (status Height −11.1 ft).
- The fixer's "remaining exact (0,117,255) rect" reproduced **inside the open dock's range slider (Chromium #0075ff UI accent)**; dock-closed scene-only re-run: **zero (0,117,255) px** — fixer's DOM-UI arbitration confirmed.
- **A/B vs bfbe1fa** (identical recipe/camera, worktree copy on 8324): sky-family census 87,129 vs 86,848 px; runs≥6px 2,596 vs 2,621; row profiles within ±0.5% → **no new seams/z-fighting/wall flicker**.
- Residual (pre-existing at BOTH revisions): 1-3px sky-gradient slivers (99,167,215 = dayTop→dayBottom t≈0.28) along terrain triangle seams while dig-clip armed, 99.6% of runs ≤3px. Fixer's own camera framing showed 14k+ → 1,781 (−87%) wedge elimination. Next-sprint: seam welding / depth-aware clip.
- Magenta-backdrop GPU-diff: not executable — app re-copies fog color into scene.background every frame (src 12453-56). Noted.
- Evidence: v_a2_b1_b2_results.json, v_a2_sceneonly_results.json, v_ab_crater_census.json, v_ab_magenta.json, shots/v_a2_*.png, v_ab_*.png.

### S30-B1/B2 (e8ff746) — VERIFIED (B2) / VERIFIED w/ documented residual (B1)
- B2: no `.negative` on dig/fill readout; `.carve-target` label+value (CSS + comment `/* S30-B2 */` present); status Height separate → target-vs-current reconciled. qa_s21 16/16.
- B1: SLOPE_DIRT 0.32 + sunlit tint in source; mound shot captured; "reads as a hill" residual acknowledged by fixer (SwiftShader shading, next sprint).
- Evidence: v_a2_b1_b2_results.json, shots/v_b1_raise_mound.png, v_b2_dig_readout.png.

### S30-S2 (5995dc3) — VERIFIED
- badge display:block (flag false) → real click #btn-help → modal open: **badge display:none, body.byd-modal-open=true** → close: **badge restored, flag false**. Old neighbor (S29-T01 observer) works.
- Evidence: v_grid_s2_results.json, shots/v_s2_modal_badge_hidden.png.

### S30-S3 (0ad9de1) — VERIFIED
- Terrain dock rows margin-bottom **7px** (2px on 2 divider rows); "Brush Size" label present; strength 0.3 → **"30%"** + title "Strength: how deep each pass carves".
- Evidence: v_s3_sidebar_results.json, shots/v_s3_sliders.png.

### S30-B-sidebar (095840c) — VERIFIED
- padding-bottom **64px** at 1280/1024/1600; scroll-end: last .lib-item inside sidebar at all 3 (734.2/800, 702.2/768, 834.2/900).
- S23-V01 padding assertion green within s23 24/24.
- Evidence: v_s3_sidebar_results.json, shots/v_sidebar_*_end.png.

### S30-C-A3 + C-A4 (bc3ec89) — VERIFIED
- `window._test.gridHelper`: y **0.03** at sun 0/6/12/18.5/22 × cameras V/B/W; noon **opacity 0.8 #cccccc**, midnight/dawn/dusk/night **0.25 #5a6a7a**; vertexColors:false.
- Grid visible in all 3 cameras (pixel census + shots); close-zoom (6× wheel-in) shows no float-gap band; s23 grid gates green.
- Evidence: v_grid_results.json, shots/v_grid_*.png.

### S30-S1 (4d7959e) — VERIFIED
- Real label placed via button path + seam; sprite texture (512×128) bottom-band census 1,124 opaque px ≈ **10px stem + 14px dot + 6px pupil** (source-verified, S29-R3f comment intact).
- Evidence: v_s1_final.json, shots/v_s1_label_seam.png.

---

## Fresh-eyes adversarial hunt (8 probes)
1. Share select/copy after ellipsis — OK (visual-only ellipsis).
2. #vc-underground × scale-bar/status at 1024 — OK (rects clear).
3. Wizard at 1024×600 — OK (skip inside, panel fits).
4. B3 SKIP path — OK (no second welcome).
5. Topbar scrolled-start fade — no click blockage; wheel-over-topbar scroll unreliable at rest (pre-existing S29-era behavior).
6. **Walk-hint (y64-94) × active toast (y64-108) intersect when W pressed with toast up — CONFIRMED, pre-existing class, LOW, transient both.**
7. Grid 0.03 vs flat object — no z-fight ring (vision pass).
8. Esc cascade w/ dock+cost — covered by sprint23 panel-conflict gate (24/24).

Hunt: 6 CONFIRMED-OK, 1 new minor finding (#6), 1 deferred-to-gate.

---

## Byte ledger audit — PASS
- Per-commit index.html sizes (git show <c>:index.html | wc -c): bfbe1fa 763,943 → final 0c39d76 **767,954 / 768,000 (headroom +46)**. Peak interim 767,956 at 0ad9de1 — never over cap.
- Deltas: +59 share, +415 cs-overlay, +158 A1, +655 topbar, −53 basic-v1, +273 skip, +420 A2, +854 B1/B2, +444 B3, +677 S2, +111 S3, −737 S1+trim, 0 chore, +61 sidebar, +641 C-A3/A4, +19 basic-compat, +14 basic-rework, 0 docs. Net +4,011.
- Markers: S23-V = 33 and S29- = 32 at **every one of the 21 commits** (verified per-commit), equal to bfbe1fa. t_ tokens + R3e/R3f comments intact.
- Non-index changes: reports/ + probe-harness removal only. No app files outside index.html.

---

## Vision re-verification (glm-5.3-flash temp 0, sequential, 38 calls, 0 HTTP-429)
Model note: glm-5.3-flash is a reasoning model — content empty at low max_tokens; verdicts read from `message.reasoning` (max_tokens 3000). Raw: vision_verdicts.jsonl (38 rows: 28 touched + 10 random).

### Touched-surface re-verify (28 shots) — summary
1. **"Sun vs Dig Down overlap in Basic"** (flagged on ~8 shots) — **CONFIRMED as NEW minor defect** (NEW DEFECTS #1; vision had direction inverted — DOM shows chip tucks UNDER the Sun pill).
2. **"Patio clipped at sidebar bottom"** (~15 verdicts) — REFUTED (scroll content at scrollTop 0; inside at scroll-end). Known noise class.
3. **"Daytime/Night pill overlaps toast/compass"** — REFUTED by rects (pill 755,130,50×20 vs toast 440,64,400×54 → intersect false; compass = device design).
4. **"Modal overlaps toolbar"** — correct z-order (modal on top).
5. Walk-hint shots — hint clears tabs (0 px²); hint×toast stack → NEW DEFECTS #2.
6. Craters/underground — no solid-blue wedges reported; residue documented under A2.
7. Grid — noon bright / night dimmed confirmed visually; distance moiré = known LOW judgment item (grid density, out of sprint scope).
8. Wizard 1280/1024 — skip inside panel at both; no glitch read; tooltip adjacency = phantom (both pe:none, Δ12px).
9. Share — ellipsis cue renders.
10. cs panel / after Esc — clean; overlay dismissed.
11. Sliders — "fully visible, not clipped" per vision.
12. B3/banner — banner readable; pill-behind-modal = intended dimming (S2).

### Random 10-shot regression sample (untouched surfaces)
templates / cost / palette / shortcuts / print / batch / season / object / sunpanel / birdview:
- templates, palette, season: modal-vs-chrome reads = correct layering (refuted).
- cost, shortcuts, print, batch, object: clean (print "diagonal seam" = sculpt-residue judgment family; batch toolbar claim = phantom, rects clear 25.8px).
- sunpanel, birdview: "Dig Down clipped/overlapping" → NEW DEFECT #1 again (chip overlap) + "clipped at right edge" REFUTED (chip right 1264 < 1280).
- shortcuts guide CLEAN apart from cosmetic "W = sprint)" wrap (pre-existing).

## NEW DEFECTS (fresh-eyes hunt)
1. **[CONFIRMED — NEW in S30, LOW-MED cosmetic] Basic-mode "Dig Down" chip tucks under the Sun pill.**
   S30-B-basic rework widened #vc-underground to 96.7px (x1167-1264); #sun-btn spans x1131-1198 with z=30 (chip z=auto → sun paints on top, sun-btn wins hit-test under its rect). Chip icon (x1178-1196) fully under the pill; "Dig Down" text (x≈1204-1256) fully visible; chip clickable right of x≈1198. bfbe1fa control: chip 40px @x1224 → no overlap. Introduced by the rework, missed by fixer + auditors (vision flagged it, inverted). Fix: right-align chip or clamp width. NOT a ship-blocker.
2. **[CONFIRMED — pre-existing class, LOW cosmetic] Walk-hint (391-888 × 64-94) intersects active toast (466-814 × 64-108)** when W pressed with a toast up (both top-anchored y=64). Pre-fix state was strictly worse (hint at y16 over tabs). Both transient. Next sprint.
3. [REFUTED] Topbar scrolled-end fade at exact end — pointer-events:none, no click impact.
4. [REFUTED] Share ellipsis breaking copy — textContent intact.
5. [REFUTED] vc-underground × scale-bar/status at 1024 — rects clear.

## Per-commit verdict table (all 21 commits bfbe1fa..0c39d76)

| Commit | Fix ID | Verdict | Key evidence |
|---|---|---|---|
| 981eb6a | B-walkhint | **VERIFIED** | top:64; 0px² overlap w/ tabs |
| 9dfdbcf | B-share | **VERIFIED** | ellipsis live; R3e preserved; copy OK |
| e9fda02 | A-cs-overlay | **VERIFIED** | Esc → overlay+dock both closed |
| 30d688e | A1 | **VERIFIED** | topHit=cs-close; real click closes |
| d1a1d71 | A-topbar | **VERIFIED** | 48px+'›' when cut; no cue at 1920 |
| e66a697 | B-basic v1 | **VERIFIED (superseded chain)** | — |
| cf7b72f | B-skip | **VERIFIED** | inside panel ×3 viewports ×2 steps |
| 24d1b2f | A2 | **VERIFIED** (residue pre-existing, A/B-confirmed) | wedge class gone; no new seams |
| e8ff746 | B1 | **VERIFIED w/ documented residual** | SLOPE_DIRT 0.32 + tint |
| e8ff746 | B2 | **VERIFIED** | carve-target readout; qa_s21 16/16 |
| 611dd48 | B3 | **VERIFIED** | finish AND skip → single welcome; banner flow intact |
| 5995dc3 | S2 | **VERIFIED** | badge retires behind modal, restores |
| 0ad9de1 | S3 | **VERIFIED** | 7px margins; 30% + tooltip |
| 4d7959e | S1 | **VERIFIED** | stem/dot/pupil in sprite texture |
| e08673a | chore | **VERIFIED (no app impact)** | 0 bytes |
| 095840c | B-sidebar | **VERIFIED** | 64px; last row inside ×3 viewports |
| bc3ec89 | C-A3 | **VERIFIED** | y=0.03 all states/cameras |
| bc3ec89 | C-A4 | **VERIFIED** | 0.25↔0.8, #5a6a7a↔#cccccc |
| 63ace65 | B-basic compat | **VERIFIED (chain)** | s17 stayed green |
| c63fa88 | B-basic rework | **VERIFIED w/ NEW minor defect noted** | chip works; tucks under Sun pill |
| f53ed34/7938276/0c39d76 | docs/artifacts | **VERIFIED (no app impact)** | 0 byte delta |

**Basis: 17 logical fixes across 18 code commits (+3 docs) = 21. All 17 VERIFIED, 0 NOT-VERIFIED, 0 REGRESSION-FOUND verdicts; 1 new minor (non-blocking) defect recorded against the B-basic rework.**

## Final verdict
- Battery all green (own run): s11 143/143, s15 52/52 PASS, s17 81/81, s21 55/55, s22 43/43, qa_s21 16/16, s23 24/24, s29 33/33, size_budget 4/4.
- Byte ledger clean: 767,954/768,000, markers unchanged at every commit.
- Vision: 38 calls, 0 429s; touched surfaces re-verified + 10-shot random sample; recurring NOT-CLEANs re-refuted with live rects.
- **Blockers: none.** Ship-recommendation: hold; file (a) Dig-Down-chip×Sun-pill overlap (Basic), (b) sub-pixel crater sliver residue (pre-existing), (c) walk-hint×toast transient as next-sprint items.
- NO PUSH performed. App tree left clean (git status: only this report dir untracked).
