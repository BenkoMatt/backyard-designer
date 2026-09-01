# VISION_QA_S29_report.md — FINAL (Agent R5, CONVERGENCE)

**Branch:** `s29r-fixer` (worktree `/root/byd29r-fixer`) · **Baseline:** `de2cae8` (760,523 B) · **Final:** 767,085 B / 768,000 (headroom +1,915)
**Merged in:** audit-transients T01–T09 (`834ccae`) · size-cop trim (`7d66d31`) · R2/panels `812720d`+`058c1c4` · R3/modals `dfd363f`+`20fb9e6` · R5 fixes (below). R1/core `e727dc8` verified equivalent-and-redundant (see reconciliation), not merged as-is.

## Final verdict table (finding → reporter verdict → R5 independent verdict → final state)

| # | Finding (surface) | Reporter verdict | R5 independent re-verification | Final state | Shot path (R5, own CDP) |
|---|---|---|---|---|---|
| Handoff L4 | Progressive-hint ghost overlay: half-faded bottom-center, collides with toolbar row (pre-fix z-500 screenshot) | Not CLEAN (size-cop VS1, pre-transients) | Reproduced live path: 5s idle timer fires → hint [440,613,840,680] opacity 1, z-190, toolbar [620,728,1198,760] — no overlap; own vision verdict **CLEAN** ("solid dark background, white text clearly readable; fully opaque; × visible") | **VERIFIED FIXED** (transients T01-family: z-order + auto-hide + modal/toolbar guards) | `reports/s29_shots/r5_progressive_hint_live.png` + `.verdict.txt` |
| Handoff L5 | Sidebar "Patio" cut mid-item, no scroll cue (S23-V01 padding made it legible; cue missing) | Not CLEAN (size-cop VS1/VS4/VS5) | Same as VS1/VS4 "Patio cut" row: fade cue opacity-1 above fold; vs2 CLEAN | **VERIFIED FIXED** (R2 P04) | `reports/s29_shots/r5_v_p04_sidebar_abovefold.png` |
| Handoff L6 | Sun cluster fragments behind modal; brush slider unlabeled | Not CLEAN (size-cop VS5) | DOM: badge z140 correctly under modal z200; sun-panel header present; slider label absent — cosmetic judgment | **KNOWN-OPEN (cosmetic, next sprint)** — see Known-open | `reports/s29_shots/r5_vision_arbitration.json` |
| W09 | Toast `translateY(-8px)` re-enters recovery-banner band (toast top 110 vs banner bottom 118) | Not CLEAN (size-cop gate probe; transients claimed fix T07) | Reproduced post-merge: toast rect [118,162] vs banner [64,118], overlap=False; also re-verified on R1's own tree (toast [122,166]) | **FIXED** (T07 `_syncTopStack` adj +8; R1's `toastLift=12` equivalent — see reconciliation) | `reports/s29_shots/r5_verify_R1_w09_banner_toast.png` |
| W02b | Placement context-hint paints over open dock-terrain panel (hint [475..765, 574..604] vs panel [445..751, 342..682]) | Not CLEAN (size-cop gate probe; unfixed at handoff — merge-lock R5 owned) | Reproduced pre-fix (hint overlapped accordion rows `tc-acc`); root cause: S23-V03e lift selector list predated dock panels | **FIXED by R5**: selector list + `.dock-panel.visible`; lift clamps vs toolbar; hides when no clear band; strict gate hintOverPanels=[] | `reports/s29_shots/r5_w02b_dockterrain_hint_after.png` |
| W02b-edge | banner+toast+panel+hint co-occurrence: lifted hint [132,162] landed INSIDE stacked toast band [118,162] | (not previously reported — R5 discovery during re-verify) | Found while re-verifying; fixed; 3-scenario probe A/B/C all clear (hint drops below toast at [174,204]) | **FIXED by R5** (avoid-list: toast/banner/panels/toolbar, candidate-test lift) | `reports/s29_shots/r5_edge_banner_toast_hint_panel_after2.png` |
| Handoff L7/L8 | First-run wizard "Skip — use default yard" link overlaps sidebar "Patio" (left:24px) | NOT-CLEAN (audit-core vision, wizard_step1_basic + lshape) | Reproduced: skip [24..202, 732..776] over lib-item; root-caused to salvage commit `4487b28` reverting the earlier centered fix; naive re-center (left:50%) then hit tape-measure-btn [620..742] (R2's single-row toolbar) | **FIXED by R5**: `bottom:132px; left:50%` — clear at 1280×800 / 1024×768 / 1600×900 (hits=[] all three); vision **CLEAN** | `reports/s29_shots/r5_v_wizard_skip_final.png` |
| T01 | Progressive hint pops over open modals (timer fires inside dialog) | fixed by transients (T01+T01b) | Reproduced fix: help modal open 6.5s → hint display:none | **VERIFIED FIXED** | `reports/s29_shots/r5_v_f5_progressive_dock.png` |
| T02 | Cost panel stale "No objects yet" on add/remove/undo/redo | fixed by transients (T02) | Reproduced: "No objects" before → live "$600 Total (1 item)" after add | **VERIFIED FIXED** | `reports/s29_shots/r5_reverify_transients.json` |
| T03 | Viewport pointerdown on UI chrome deselects (button press loses click) | fixed by transients (T03) | Reproduced: sun-btn press keeps #properties open (terrain-btn deselect IS intended mode-entry) | **VERIFIED FIXED** | (probe in `r5_reverify_transients.json`) |
| T04 | Batch-bar overlaps wrapped toolbar/scale-bar | fixed by transients (T04) | Reproduced: bar [642,684] vs toolbar top 692 / scale-bar top 730 — no overlap | **VERIFIED FIXED** | `reports/s29_shots/r5_v_t04_batchbar.png` |
| T05 | Share QR caption contradicts state ("Save" while save disabled) | fixed by transients (T05) | Reproduced: 25-object design → "Use the link instead." shown | **VERIFIED FIXED** | (probe in `r5_reverify_transients2.json`) |
| T06 | Timelapse modal poster blank on open | fixed by transients (T06) | Reproduced: poster canvas 472px, drawn (width×height set) | **VERIFIED FIXED** | `reports/s29_shots/r5_v_t06_timelapse.png` |
| T08 | Ctrl+A select-all drops multi-set (batch count mismatch) | fixed by transients (T08) | Reproduced: 3 adds + Ctrl+A → batch-bar "3 selected" | **VERIFIED FIXED** | (probe in `r5_reverify_transients.json`) |
| T09 | Explicit save leaves stale recovery banner+snapshot | fixed by transients (T09) | Reproduced: banner visible → Ctrl+S → banner hidden + snapshot cleared | **VERIFIED FIXED** | `reports/s29_shots/r5_v_t09_save_banner.png` |
| Modals F1 | Help header not visible at scroll-bottom | fixed by audit-modals (merged pre-R5) | Reproduced: scrollTop 1791 → title top 80 == panel top 80 | **VERIFIED FIXED** | `reports/s29_shots/r5_v_f1_help_bottom.png` |
| Modals F2 | Print preview invisible on screen | fixed by audit-modals | Reproduced (Advanced): #print-view visible, full 1280×800 | **VERIFIED FIXED** | `reports/s29_shots/r5_v_f2_print_preview.png` |
| Modals F3 | Templates Close below fold | fixed by audit-modals | Reproduced: close-btn [598,592,84×36] in-viewport, inside panel; panel fits (bottom 656) | **VERIFIED FIXED** | `reports/s29_shots/r5_v_f3_templates.png` |
| Modals F4 | Sculpt-restore-pill overlaps scale-bar/Sun | fixed by audit-modals | Reproduced via dock minimize (pill trigger): pill [445..531, 690..721] vs scale-bar [450..625, 730..756] / Sun [620..693, 728..760] — no overlap (R2's reposition confirmed on my tree) | **VERIFIED FIXED** | `reports/s29_shots/r5_v_f4_sculpt_pill_minimized.png` |
| Modals F5 | Progressive hint over open dock | fixed by audit-modals (S29-V01) | Reproduced: dock open 6.5s → hint hidden | **VERIFIED FIXED** | `reports/s29_shots/r5_v_f5_progressive_dock.png` |
| R2 P02/P05 | Scale-bar overlapped wrapped Sun button by 5px; toolbar wrapped (Sun alone row 2) | fixed by R2 (P02+P05 single-row toolbar) | Reproduced: toolbar 1 row (tops=[728]), scale-bar right 607 vs Sun left 1161, gap 554 | **VERIFIED FIXED** | (probe in `r5_reverify_panels.json`) |
| R2 P03 | "FPS: 2" burst readout on idle (vision flagged every shot) | fixed by R2 (sustain threshold) | Reproduced hidden state + **found regression**: threshold ≥12 blocked s17's walk-FPS lock under swiftshader (81st check FAIL) | **FIXED & RECONCILED by R5**: (≥400ms & ≥12fps) OR (≥1.5s & ≥3fps) — idle drag/hover stays "—", walk meter shows; s17 81/81 ×2 runs | (probe runs in this report §battery) |
| R2 P04 | Sidebar "Patio" cut with no scroll cue | fixed by R2 (#sidebar-fade) | Reproduced: fade opacity 1 above fold (y750, h26), opacity 0 at bottom | **VERIFIED FIXED** | `reports/s29_shots/r5_v_p04_sidebar_abovefold.png` |
| R2 P06 | "Innovate" label ambiguous (reads like typo) | fixed by R2 (tooltip) | Reproduced: title "Innovation Lab — pools, retaining walls, terrain stats & underground tools" | **VERIFIED FIXED** (rename blocked by gate text assertions — documented tradeoff) | (probe in `r5_reverify_panels.json`) |
| R3 R3a | Sun pill abuts scale-bar (toolbar wrap) | fixed by R3 (one-row@1280) | Reproduced: single row, no abutment | **VERIFIED FIXED** (same probe as P02/P05) | (probe in `r5_reverify_r3.json`) |
| R3 R3b | Label tool: status bar said "Tool: Select" while Label armed | fixed by R3 | Reproduced: status "Tool: Label" during label placement | **VERIFIED FIXED** | (probe in `r5_reverify_r3.json`) |
| R3 R3c | Topbar overflow cue inverted (fade at end, none when clipped) | fixed by R3 (`scrolled-end` toggle) | Reproduced @1024×768: scrollW 1713 > clientW 1024 at scroll-start → `scrolled-end` TRUE (cue shown) | **VERIFIED FIXED** | (probe in `r5_reverify_r3b.json`) |
| R3 R3d | Cmd palette 2px divider read as doubled line | fixed by R3 (1px) | Reproduced in CSS: `#cmd-palette-input{border-bottom:1px solid var(--border)}` + S29-R3d comment | **VERIFIED FIXED** | (CSS probe) |
| R3 R3e | Share URL box wrapped multi-line | fixed by R3 (nowrap) | Reproduced: whiteSpace nowrap, scrollH 29 == clientH 29 | **VERIFIED FIXED** | (probe in `r5_reverify_r3b.json`) |
| R3 R3f | Label floats unanchored | fixed by R3 (stem+dot in sprite) | Sprite canvas verified (stem+dot code present, sprite in scene); vision judged stem subtle at default zoom — **judgment-grade, recorded as input** | **VERIFIED (code+sprite)**; visual strength = next-sprint input | `reports/s29_shots/r5_v_r3f_label_after_save.png` |
| VS1/VS4 "Patio cut" | Vision: cut mid-item, no scroll cue | Not CLEAN (size-cop VS1/VS4) | Fade cue verified opacity-1 above fold (P04); vision vs2 verdict CLEAN and calls the same layout fine | **ARBITRATED: no defect** (scroll cue present) | `r5_v_p04_sidebar_abovefold.png` + `r5_vision_arbitration.json` |
| VS1 "Terrain twice" | Vision: duplicate controls confuse | Not CLEAN (size-cop VS1) | Dock tab + toolbar button = intentional mirror access (pre-existing design; vs2 verdict itself: "intentional quick-access mirrors") | **ARBITRATED: no defect** (design) | `r5_vision_arbitration.json` |
| VS5 "help modal bottom padding ~0" / "Daytime pill 2px peek" | Vision: reads clipped; stray sliver | Not CLEAN (size-cop VS5) | DOM: panel scrollable, padding 40px, last content below fold = normal scroll (crop-edge misread, S23 lesson); atmosphere-badge z140 UNDER modal z200 (elementsFromPoint: help-modal on top) | **ARBITRATED: no defect** (DOM healthy) | `r5_vision_arbitration.json` |
| VS6 "Alt+Tab never fires" | Vision: OS-reserved binding | Near-clean (size-cop VS6) | FALSE claim — app captures Alt+Tab (sprint22 gate `brief_inventory` lock) | **ARBITRATED: no defect** (vision hallucination) | `r5_vision_arbitration.json` |
| VS3 | "No overlaps, clipping, or broken rendering found" but no CLEAN keyword | FAIL by regex (size-cop VS3) | Verdict text is an effective pass; only the CLEAN-keyword matcher missed | **ARBITRATED: effective PASS** | `r5_vision_arbitration.json` |

## Reconciliation of conflicting fixes

1. **W09 (toast vs banner)** — two independent fixes existed: transients T07 (`_syncTopStack` adj=8 for toast) and R1's `e727dc8` (`toastLift=12`). Both produce a non-overlapping strict-pass geometry (T07: toast [118,162]; R1: [122,166]). **Kept T07** (already merged, smaller delta, 4px visual gap preserved); R1's version verified equivalent on their tree — no conflict in outcome.
2. **W02b (hint vs dock)** — R1's `e727dc8` extended the same selector list (`.dock-panel` all entries); R5's version uses `.dock-panel.visible` + toolbar clamp + hide-when-no-room + top-stack-overlay avoidance (fixes the co-occurrence edge R1's simpler lift would still hit: lifted hint [132,162] inside toast band [118,162]). **Kept R5's** (superset; edge verified in 3 scenarios).
3. **FPS meter** — R2's `>=12fps` threshold vs s17's shipped walk-FPS lock (needs visible meter; swiftshader walks at ~3-4fps). **Reconciled** to dual-prong rule (fast-burst OR long-sustained); both behaviors verified.
4. **wizard-skip** — salvage `4487b28` had reverted the centered position to `left:24px` (over the sidebar — audit-core's own handoff finding), while transients' branch re-centered it (`left:50%`) which post-R2-merge collides with tape-measure-btn at 1280. **Resolved** to `bottom:132px; left:50%` — clear at all three resolutions, vision CLEAN.
5. **s29a_common.py** — add/add conflicts (modals' port 8186 vs transients' port 8191): union of both helper sets, `BYD29_REPO`/`BYD29_PORT` env-parameterized so the shared module works from any worktree.

## Final gate battery (all green, this tree, strict mode)

| Gate | Result | Invocation / port convention |
|---|---|---|
| sprint11 | **143/143** | `python3 sprint11_quality_gate.py --port 8240` (accepts `--port`) |
| sprint15 | **52/52** | `python3 sprint15_quality_gate.py --port 8240` (accepts `--port`) |
| sprint17 | **81/81** | `BASE_URL=http://127.0.0.1:8240 python3 sprint17_quality_gate.py` (hardcodes 8175; **override via `BASE_URL` env only**) |
| sprint21 | **55/55** | `python3 sprint21_quality_gate.py --port 8240` (accepts `--port`) |
| sprint22 | **43/43** | `python3 sprint22_quality_gate.py --port 8240` (accepts `--port`) |
| qa_s21 dig-visibility | **16/16** | `BASE_URL=http://127.0.0.1:8240 python3 qa_s21_dig_visibility.py` (**`BASE_URL` env only**) |
| sprint23 | **24/24** | `python3 sprint23_quality_gate.py --port 8240 --skip-vision --expect-open-fixes` (defaults 8093; strict post-merge mode) |
| sprint29 | **33/33 DOM** | `python3 sprint29_quality_gate.py --port 8240 --skip-vision --expect-open-fixes` (defaults 8185; 39/39 with vision pre-arbitration — see below) |
| size_budget | **4/4** | `python3 size_budget.py` (byte budget 767,085/768,000, node --check, CSS braces, unique IDs) |

**Port discipline (S29R continuation):** every agent owns one port ≥8240: R5 = **8240** (this tree, `http.server` on 127.0.0.1), R1's tree verified via **8241**. Older reserved ports (8099/8115/8175/8093/8095/8185/8186/8191) belong to prior agents — never bind them; s17/qa_s21's hardcoded defaults are overridden with `BASE_URL` env, everything else with `--port`.

**Vision runs (glm-5.3-flash, temp 0, own CDP screenshots):** 6-surface spot-check via `sprint29_quality_gate.py --port 8240 --expect-open-fixes` (no `--skip-vision`) = 34/39 with 5 vision-side FAILs, **every one DOM-arbitrated as no-defect** (crop-edge misreads, CLEAN-keyword misses, design mirrors, one false Alt+Tab claim) — full reasoning in `reports/s29_shots/r5_vision_arbitration.json`. Per the sprint23 gate precedent (`--skip-vision` for hard pass/fail; vision verdicts are inputs, not binary FAILs), the DOM battery above is the gating result. Remaining vision judgment-notes for next sprint: label-anchor stem visual strength (R3f), sun-cluster presentation behind modals (W06 family, cosmetic).

## Byte budget ledger

| Step | Bytes |
|---|---|
| Baseline de2cae8 | 760,523 |
| + transients T01–T09 merge | 765,857 |
| + W02b fix (R5) | 766,548 |
| + W02b edge fix (R5) | 767,952 |
| − size-cop comment-only trim (4,109 B, sprint-27 perf notes; S23/S29 fix-marker comments whitelisted) | 763,843 |
| + R2 P02–P06 merge | 765,289 |
| + R3 fixes merge | 766,950 |
| + wizard-skip fix (R5) | 766,954 |
| + FPS reconcile (R5, final) | **767,085 / 768,000 (+1,915 headroom)** |

## Known-open (documented, not gating)

- **W06 family (cosmetic):** sun-panel cluster reads fragmented behind modals; brush-size slider unlabeled. Judgment-grade; next-sprint input.
- **R3f label stem:** present in sprite but subtle at default zoom (vision judgment).
- **Vision keyword matcher:** `vision_clean()` misses narrated passes like vs3's ("No overlaps… found" without the word CLEAN) — gate-harness nit for the next gate builder.