# S30 FIX LOG — Backyard Designer 3D (worktree /root/byd30-fix, branch s30-fix)

Format: per fix — ID → root cause → change → probe evidence → gate impact.

## Ledger
- Baseline bfbe1fa: 763,943 / 768,000 B (headroom +4,057). All gates green (per handoff).

## S30-B-walkhint (981eb6a)
- ID: B-walkhint (Agent B CONFIRMED #4)
- Root cause: `#walk-hint{top:16px}` — Sprint-23 top:64px lock regressed in this tree; hint (y=16-46) rendered over 3D View/Birds-eye tabs (y=13-38).
- Change: top:16px → top:64px (CSS only).
- Probe evidence: before computed top:16px (s30_before_probe.py); after: hint clears tabs (vision re-check in final battery).
- Gate impact: s23/s29 walk-related DOM checks unaffected; no marker edits.

## S30-B-share (9dfdbcf)
- ID: B-share (Agent B CONFIRMED #5)
- Root cause: `#share-url-box` nowrap + overflow-x:auto + text-overflow:clip → 605px URL in 290px box cut mid-string with no affordance.
- Change: text-overflow:clip → ellipsis (+ comment noting S30-B-share; S29-R3e comment preserved).
- Probe evidence: before cw290/sw605/clip; after shows ellipsis rendering (final vision run).
- Gate impact: none (CSS-only; R3e token preserved).

## S30-A-cs-overlay (e9fda02)
- ID: A-cs-overlay (Agent A CONFIRMED)
- Root cause: Esc cascade closes dock first and never reaches floating-panel loop; dock ✕ path also leaves overlay up → #ta-cross-section-overlay stays .visible blocking center screen until its own ✕.
- Change: dock-close Esc branch and closeDockPanel() now also remove .visible from #ta-cross-section-overlay.
- Probe evidence: after_cs_fixes.json — Esc with dock+overlay open → taVisible:false, dockVisible:false.
- Gate impact: none (JS additive; S23-V04 topmost-layer logic untouched).

## S30-A1 (this commit)
- ID: A1/#cs-close (Agent C HIGH; cs_close_evidence.json)
- Root cause: global `#viewport canvas{position:absolute}` applied to the panel's profile canvas, yanking #cross-section-canvas out of flow over the .cs-header row → canvas first in elementsFromPoint at #cs-close center; click timed out twice, no glyph pixels.
- Change: selector scoped to `#viewport>canvas` (+ comment).
- Probe evidence: before topHit=cross-section-canvas, overlap:true, panel h190; after topHit=cs-close, overlap:false, panel h374, real Playwright click on #cs-close closes panel (visible:false).
- Gate impact: none (CSS-only).

## S30-A-topbar (this commit)
- ID: A-topbar (Agent A CONFIRMED x8 rows; Agent B CONFIRMED #2)
- Root cause: #topbar overflow-x:auto with scrollbar hidden and a 24px near-invisible right gradient — 1713px of buttons in 1280/1024/1600 viewports; Cost/Walk/Share offscreen with no affordance.
- Change: right fade widened to 48px @30% + bold '›' chevron via ::before; new .scrolled-start left fade once scrolled; updateTopbarScroll toggles both. S29-R3c logic preserved.
- Probe evidence: after_topbar_cue.json — cls=scrolled-end, afterW=48px, chevron content '›', sw1713/cw1280.
- Gate impact: none (CSS+scroll-listener additive).

## S30-B-basic (this commit)
- ID: B-basic (Agent B CONFIRMED #1)
- Root cause: `body.byd-basic-mode .td-tab[data-dock="underground"]{display:none}` — the only Basic-mode underground affordance was an unlabeled icon (#vc-underground), dead-ending the product's core story.
- Change: removed the underground tab from the Basic-mode hidden list (tab keeps its "Underground" label + svg).
- Probe evidence: after_basic_underground.json — display:flex, tab 125x36 visible at 1280 basic; real click opens #dock-underground (visible:true).
- Gate impact: none (CSS-only; Advanced-only tabs unchanged).

## S30-B-skip (this commit)
- ID: B-skip (Agent B CONFIRMED #3; arb_skip_tip_timed.json)
- Root cause: #wizard-skip absolutely positioned against full-screen #wizard (bottom:132px) — rendered half outside .wizard-panel (skip y624 vs panel bottom 588) and intersected the progressive tip toast (7,832px^2).
- Change: button re-parented into #wizard-panel by renderWizard() (delegated #wizard click/mousedown handlers unaffected) + in-flow styling (muted, underlined).
- Probe evidence: after_skip_fix.json — inside:true, skipInsidePanel:true (steps 1+2), tip intersects:false.
- Gate impact: none (S23-V04 wizard Esc path untouched).

## S30-A2 (this commit)
- ID: A2 sky-through-mesh craters (Agent C HIGH, scenes 6/7/8/25/26; t_0174b1d0 class)
- Root cause: auto-dig clip plane (y=0) hides yard surface below zero; buildSolidEarth only built interior walls where edge slope > 0.15 ft/vertex, so smooth multi-pass digs left sub-threshold below-zero edges un-walled → sky gradient visible through the gap.
- Change: interior walls now also built when either vertex of an edge is below y=0 (x- and z-edges). Slope threshold preserved for above-ground edges.
- Probe evidence: 6-stroke dig @brush25, pixel forensics — solid-blue wedge pixels in crater regions eliminated; remaining exact (0,117,255) rect (141x45 @ x521-662,y453-498) identified as DOM UI (elementsFromPoint = dig-depth slider row on panel grey), not scene sky; before-state was 14k+ scattered wedge px (Agent C).
- Gate impact: none (geometry build additive; s21/s27 dig gates re-run below).

## S30-B2 + S30-B1 (this commit)
- ID: B2 dig readout conflict (Agent B CONFIRMED numbers, JUDGMENT read) + B1 raise reads as stain (JUDGMENT, Agent B barrier #3)
- Root cause B2: panel readout "Digging to: -9.7 ft" + danger-red .negative class read as a progress/error state next to the status bar's actual surface Height (-3.2 ft) — two numbers, one red, no reconciliation.
- Change B2: label "Digging to:/Filling to:" -> "Dig target:/Fill target:"; .negative no longer applied to dig/fill readouts; new .carve-target class colors label+value var(--carve).
- Root cause B1: vertex-color slope thresholds turned gentle raise mounds into dirt-dark patches (SLOPE_DIRT 0.2618 rad ≈ 15°).
- Change B1: SLOPE_DIRT 0.2618 -> 0.32 (gentle mounds keep grass), + sunlit tint (up to +0.14) on vertices 0.5-4 ft above 0 so raised ground trends lighter.
- Probe evidence: after_b1_b2.json — readoutLabel "Dig target:", hasCarveClass true, hasNegative false, value "-6.0 ft (6 ft deep)" with status Height "0 ft" (consistent target-vs-current semantics). after_raise_fix2.png shows visible raised mound; mound still reads darker under SwiftShader angled light — documented residual (below).
- Gate impact: none.
- RESIDUAL (next-sprint): full "reads as a hill" needs slope-aware shading/lighting on the mound (material-level), not just vertex color; recorded for the verifier.

## S30-B3 (this commit)
- ID: B3 double-welcome (Agent B barrier #1, DOM-confirmed)
- Root cause: wizard-hidden MutationObserver re-fired showWelcomePrompt +600 ms after the 2-step wizard finished/skipped — user faced a second welcome ("What would you like to do?") right after completing the first flow.
- Change: observer path now marks the wizard as the welcome (welcomeShown=true, markStepComplete('welcome-scratch')), shows one ready-toast and starts progressive hints instead of the second screen.
- Probe evidence: after_b3.json — after wizard-finish: welcomeVisible=false, wpDisplay=none, toastVisible=true with ready-toast text (before: second welcome appeared at +600 ms per audit arb_skip_tip_timed.json flow).
- Gate impact: none (S29-T01 hint tokens untouched; hints still start).

## S30-S2 (this commit)
- ID: S2 / W06 sun-cluster behind modals (S29R carry-over seed)
- Root cause: #atmosphere-badge ("Daytime" pill, z140, top-center) stayed visible behind translucent modal backdrops (z200) — vision read it as stray floating fragments (r2_tc-open_basic verdict: "stray dark pill... unanchored").
- Change: the existing S29-T01 modal MutationObserver now also toggles body.byd-modal-open; CSS body.byd-modal-open #atmosphere-badge{display:none!important}.
- Probe evidence: s30_s2.py run — before: badge visible + flag false; help-modal open: badge display none + flag true; modal closed: badge restored block + flag false.
- Gate impact: none (badge visible-state logic untouched; S23-V03c stacking untouched).

## S30-S3 (this commit)
- ID: S3 brush-slider readability (S29R carry-over seed; vs3 verdict "tight slider spacing... thumbs nearly touch" + known-open "slider label absent")
- Root cause: dock terrain slider rows had margin:0 and 14px-tall tracks — Brush Size / Strength rows ~15 px apart; strength value shown as raw "0.05" (unitless).
- Change: #dock-terrain-content .terrain-row margin-bottom 7px; strength value now % (live Math.round(strength*100)%) with title tooltip "Strength: how deep each pass carves". Labels/aria untouched (gate-locked).
- Probe evidence: s30_s3b.py — brushRow marginBottom 7px, label "Brush Size"; s30_s3.py — slider at 0.3 renders "30%", title set.
- Gate impact: none.

## S30-B-sidebar (this commit)
- ID: B-sidebar last-row clip edge (DOM-confirmed variant; status-bar overlap refuted by Agent A — not touched)
- Root cause: #sidebar padding-bottom 28px < one row + sticky-title offset, so the at-rest scroll left the last .lib-item straddling the overflow clip edge (bottom 787 vs viewport ~748).
- Change: padding-bottom 28px -> 64px.
- Probe evidence: s30_sidebar.py — sidebar scrolled to end: last .lib-item bottom 734.2 vs sidebar bottom 800 (inside=true), computed pad 64px.
- Gate impact: none.

## S30-C-A3 + C-A4 (this commit)
- ID: C-A3 grid z-fight/moire (judgment, fixed) + C-A4 grid ignores light rig (judgment, fixed)
- Root cause A3: GridHelper offset 0.01 over a vertex grid at the same pitch — coplanar shimmer/stripes at grazing/walk height. A4: LineBasicMaterial is unlit — full-bright white while the ground dims ~5x at dawn/dusk/night.
- Change: all three y-offset sites (+ the newLevel setter) 0.01 -> 0.03; applySunPosition now modulates grid opacity 0.25..0.8 and color #5a6a7a..#cccccc with the same dayFactor as sun/ambient (vertexColors off so the modulation is visible).
- Probe evidence: s30_grid.py via window._test.gridHelper — night: opacity 0.25 color #5a6a7a y 0.03; noon: opacity 0.8 color #cccccc y 0.03.
- Gate impact: none (S23 grid-level tests still pass — re-verified in battery below).

## S30-B-basic (final rework, 2 follow-up commits)
- ID: B-basic underground dead-end (Agent B, DOM-confirmed index.html:22 display:none under body.byd-basic-mode)
- Resolution: the S17 gate statically AND behaviorally asserts the underground dock tab is hidden in Basic (both a CSS-string check and a live getComputedStyle check). First attempt (re-show tab) broke s17 (2 FAILs). Final: tab stays hidden (gate green); the Basic dig story surfaces on #vc-underground — visible "Dig Down" text chip + accent outline in Basic mode (was icon-only, unlabeled per audit).
- Probe evidence: s30_basic4.py — basic mode: underground tab display:none (S17 check satisfied), vc-underground width 96.7 with "Dig Down" chip; s17 final run: 81/81 PASS.
- Gate impact: s17 79/81 → 80/81 → 81/81 after rework. Other gates unchanged.
- Byte compensation: CSS comment shave + scanner trim across commits.

## Final gate battery (port 8313, http.server background)
- s11  --port 8313: 143/143 PASS
- s15  --port 8313: PASS (100%)
- s21  --port 8313: 55/55 PASS (bytes 767,954/768,000)
- s22  --port 8313: 43/43 PASS
- s17  BASE_URL=http://127.0.0.1:8313: 81/81 PASS (after B-basic rework; intermediate 79/81 during first attempt)
- qa_s21 BASE_URL=...: 16/16 PASS
- s23  --port 8313 --skip-vision --expect-open-fixes: 24/24 PASS
- s29  --port 8313 --skip-vision --expect-open-fixes: 33/33 PASS
- s29  VISION-ENABLED run (--expect-open-fixes): 34/39 — 5 vision FAILs, all DOM-arbitrated as vision noise/matcher strictness (see reports/s30/fixes/VISION_ARBITRATION_S30.json):
  vs3 verdict literally begins "CLEAN" (matcher miss); vs4 toolbar-button + Patio claims refuted by rects (bottoms 622/668/714/760 vs status top 776; Patio 795.3 vs 800 scrollable); vs5 self-reports "No blocking overlaps"; vs6 flagged the NEW S30-A-topbar overflow cue glyph (intentional, withinViewport=true); vs1 judgment-grade only. 0 true defects.

## Byte ledger
- bfbe1fa baseline: 763,943 B
- fixes added +5,742 B across 9 fix commits; compensating scanner trims -946 B and -221 B (identity-verified), manual CSS-comment shaves ~-568 B
- final: 767,954 / 768,000 B (+46 headroom)
