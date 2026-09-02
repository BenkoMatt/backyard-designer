# SPRINT30_FIX_BRIEF.md — Fix Wave (SOLE EDITOR)

**Worktree:** `/root/byd30-fix` (branch `s30-fix`, at `bfbe1fa`). You are the ONLY editor of this tree this sprint. Never touch `/root/backyard-designer`, `/root/byd30-merge`, or other worktrees.

## Inputs
- `/root/byd30-merge/reports/s30/surface-sweep/REPORT.md` (Agent A) + shots/verdicts in same dir
- `/root/byd30-merge/reports/s30/fresh-user/REPORT.md` (Agent B) + shots
- `/root/byd30-merge/reports/s30/render-quality/REPORT.md` (Agent C) + shots
- Carry-over seeds from S29R (characterize then fix): (1) label-anchor stem+dot too subtle at default zoom; (2) sun-cluster fragments read poorly behind modals; (3) brush slider unlabeled.

## Hard rules
1. **Fix only CONFIRMED findings** (DOM-evidenced). JUDGMENT items: fix only the three carry-over seeds + comprehension barriers the reports rank top-3; leave the rest listed in your report as "not fixed, rationale". REFUTED: never touch.
2. **Every fix DOM-verified before commit** — reproduce the defect rect/state first, fix, re-probe, and capture before/after screenshots in `/root/byd30-fix/reports/s30/fixes/` with a per-fix note (finding ID → root cause → change → probe evidence → gate impact).
3. **Preserve gate-asserted markers:** any comment containing S23-V*, S29-V01/T0x/W-checks, `t_[0-9a-f]{6,}`, R3 tokens must survive edits (gates grep them).
4. **Byte budget: hard cap 768,000.** Check `python3 size_budget.py` after every change; `wc -c index.html` after every commit. Compensate with scanner-safe whitespace/comment trims ONLY if needed (see `/root/byd30-merge/s30_trim.py` for the proven safe approach — reuse it, it verifies normalized-JS-identical).
5. **Gates before you finish:** full battery on your tree, port 8313 (`python3 -m http.server 8313 --bind 127.0.0.1`): s11 143, s15 52, s17 81 (BASE_URL env), s21 55, s22 43, qa_s21 16 (BASE_URL env), s23 24 (`--skip-vision --expect-open-fixes`), s29 33 (`--skip-vision --expect-open-fixes`), size_budget 4/4. Also run `sprint29_quality_gate.py --port 8313 --expect-open-fixes` WITH vision once at the end; classify every vision FAIL via DOM arbitration (verdicts are inputs, not ship-blockers — record them for the verifier).
6. **Commit discipline:** one commit per logical fix, messages prefixed `S30-<finding-id>:`, author via per-commit `git -c user.name="Caddy" -c user.email="caddyaibot@gmail.com"`. NO PUSH ever.
7. **Onboarding overlays:** dismiss `#wizard-skip` then `#wp-scratch`/`#wp-remind-later` before driving UI. Real CDP input only for interactions; evaluate = read-only probes.
8. **429s:** vision calls sequential, sleep 60s on HTTP 429, retry, log.
9. Incremental report: `/root/byd30-fix/reports/s30/fixes/FIX_LOG.md` — append per fix as you go. Final chat response <60 lines.

## Suggested order
1. Cheap wins first: brush slider label, label-stem visibility, any CONFIRMED overlap/clip.
2. Then comprehension barriers ranked by Agent B.
3. Then Agent C render artifacts with CONFIRMED DOM evidence.
4. Keep a running byte ledger; if you approach 767,000, stop adding and trim.