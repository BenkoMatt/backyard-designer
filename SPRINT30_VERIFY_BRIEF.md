# SPRINT30_VERIFY_BRIEF.md — Independent Verifier (adversarial, READ-ONLY)

**Tree to verify:** `/root/byd30-fix` (branch `s30-fix`) at whatever commit HEAD is when you start. You are an ADVERSARIAL verifier with fresh eyes. You never edit anything except your own report dir.

## Your job — try to break it
1. Read `/root/byd30-fix/reports/s30/fixes/FIX_LOG.md` + the three auditor reports under `/root/byd30-merge/reports/s30/`.
2. For every claimed fix: reproduce the ORIGINAL defect path yourself with real CDP input on port 8314 (serve `/root/byd30-fix` yourself; bind-test first; never 8099/8115/8175/8093/8095/8185/8186/8191/8240/8241/8300/831x-others). Verify the fix holds AND no neighbor regression: repositioned panels → vision+DOM check BOTH old neighbors and new neighbors (S23 lesson).
3. Run the full gate battery yourself on 8314 (invocations in `/root/byd30-fix/SPRINT30_FIX_BRIEF.md` §5). Report exact N/N per gate. size_budget must be 4/4.
4. Vision re-verify EVERY surface the fixer touched (glm-5.3-flash, temp 0, own CDP shots) plus a random sample of 10 untouched surfaces (regression sniff).
5. Byte ledger audit: `git log --stat` the fixer's commits; confirm per-commit sizes and final ≤768,000 with the marker whitelist intact (`grep -c "S23-V" index.html` count must equal the pre-fix count you record at start; same for S29- tokens).
6. Try to find NEW defects the auditors missed — 15 minutes of fresh-eyes adversarial poking at the weakest-looking surfaces. Classify anything found CONFIRMED/JUDGMENT/REFUTED with DOM evidence.

## Verdict rules
- Verdict per claimed fix: VERIFIED / NOT-VERIFIED (with evidence) / REGRESSION-FOUND (with evidence).
- Findings are files: `/root/byd30-fix/reports/s30/verification/REPORT.md` (incremental writes).
- Final chat response <60 lines: verdict table + any blockers. You do NOT fix anything. NO PUSH.