# Sprint 32 FIX LOG — sole-editor fixer

Worktree `/root/byd32-fix`, branch `s32-fix` @ `75a9104` (S31.2). Byte cap 768,000.
One commit per fix, prefix `S32-<id>:`, author Caddy <caddyaibot@gmail.com> via `git -c`.
Vision: glm-5.3-flash temp 0, sequential. Evidence under `reports/s32/fixes/`.

Before-state probes: `probe_before.py` → `probe_before.json` (all defects reproduced on :8380):
- share copy → toast `✕Copy failed - select the link manually` (nav.clipboard EXISTS, isSecureContext=true, writeText rejects; `document.execCommand('copy')` returns true)
- export menu open @1280×800 → rect y=45.5 h=214 (bottom 259 ≫ topbar bottom 52), `elementFromPoint(center)` = CANVAS (REG-D01 confirmed); `#export-stl` Playwright click timed out under clip (stl_click FAIL recorded in probe run 1)
- topbar: scrollWidth 2656 / clientWidth 1280; wheel + Shift+wheel leave scrollLeft=1047 (unchanged); scrollBy works
- contour toggle on dug terrain (min −15/max 0 ft) → contourOverlay LineSegments CREATED, visible:true, 640 verts, in scene → yet 0 line pixels on screenshot (occlusion suspected, not a builder no-op)
- cut/fill: panel open before dig `fill 77.2 yd³` → after 2nd dig (terrain min −15) panel unchanged `77.2` (stale)
- label create works; dblclick near sprite → modal does NOT open (edit/delete dead confirmed)
- night 23.9h: starField visible, 800 pts, opacity 1; visible dark-sky region 36,413 px → **0** star-bright px, 0 moon px

---

## S32-C1 — Share Copy always-fails on http (A×B conflict arbitration)

**Verdict on the conflict:** BOTH agents saw real behavior. Root cause: `navigator.clipboard`
exists on `http://127.0.0.1` (Chromium treats localhost as secure), so the secure branch runs,
but `writeText()` rejects (document focus/permission in headless + http quirks) → catch →
A's 'Copy failed' toast. B's run had writeText resolve → success toast. The existing
textarea fallback was dead code (only reachable when `navigator.clipboard` is undefined —
practically never on Chromium).

**Fix:** secure path stays; on rejection fall through to textarea+`execCommand('copy')`
(moved out of the `else`, made primary fallback); exec failure → honest error toast.

- Files: `index.html` (share-copy handler; 5 redundant S23 whole-line comments trimmed to
  pay the byte bill — comment-stripped identity verified via size_budget js/css/id gates)
- Commit: `e051241` `S32-C1: share-copy falls back to textarea+execCommand when writeText rejects`
- Verification: after `after_share_copy.json` — toast `✓Link copied to clipboard!`
  (toast-success) on first click AND 3/3 repeats, zero pageerrors;
  vision (call 1): toast reads "Link copied to clipboard!" with green success checkmark.
  Evidence: `after_share_copy.py/.json/.png`, `vision_log.txt`