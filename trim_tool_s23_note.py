#!/usr/bin/env python3
"""Sprint 23 SIZE-COP comment trimmer (Agent 5) — one-shot, already applied.

Removed ONLY whole-line comments (never code): full-line // and /* */ comment
lines inside the two script blocks + full-line <!-- --> HTML comments.
Protected: any line containing an S23-Vxx marker (tests grep for these markers).

Equivalence proof used before applying (re-runnable):
  - normalized module + plain script (comments stripped, blank lines dropped) identical
  - node --check on the trimmed module script: OK
  - HTML skeleton diff: only pure <!-- --> lines removed
Re-run the audit with:  python3 size_budget.py
"""
print(__doc__)
