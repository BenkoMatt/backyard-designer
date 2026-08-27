# Sprint 21 — STABILITY Agent Report

**Agent:** Sprint 21 Agent 5 (STABILITY)
**Branch:** `sprint21-stability` (baseline `da1163f`)
**Scope:** Clip-plane state management, render-loop correctness, and edge-case stability
across the terrain/excavate systems. No features or layout changed.

**File size after changes:** `wc -c index.html` → **744,864 bytes** (limit 750,000 ✓;
was 744,366 at baseline — net +498 bytes from comments/exports, minus removed dead CSS).

---

## 1. Clip-plane clobber matrix (audited, then fixed)

Writers of `yardMesh.material.clippingPlanes` / `solidEarthMesh.material.clippingPlanes`
at baseline. "State vars" = `terrainClipPlane` (cutaway), `crossSectionClipPlane`,
`autoDigClipPlane` (dig brush).

| # | Writer (old line ~) | Wrote to | Composed? | Clobber risk demonstrated |
|---|---------------------|----------|-----------|---------------------------|
| W1 | `_rebuildYardClipPlanes()` (~4099) | yard | ✅ all 3 vars | canonical — correct |
| W2 | `updateAutoDigClip()` (~4110) | yard | ✅ via W1 | correct (only writer of autoDig) |
| W3 | `initWithYard()` rebuild (~6565) | yard | ✅ via W1 (else-branch fallback was dead code) | fallback could never run (function is hoisted in module scope) |
| W4 | `buildSolidEarth()` tail (~7673) | solidEarth | ⚠️ partial — ad-hoc `[terrainClipPlane]` then concat cs | sequential ad-hoc writes; any future plane added here would be dropped by other writers |
| W5 | cutaway slider `input` (~10627) | yard + solidEarth | ❌ **val=0 branch wiped BOTH**: set yard `[]` (dropping autoDig + cs) and rebuilt solidEarth without cs plane | cutaway→0 killed dig reveal + cross-section clip |
| W6 | cutaway slider else-branch (~10641) | yard + solidEarth | ❌ yard rebuilt as `[terrain, cs]` — **dropped autoDig**; solidEarth `[terrain, cs]` | moving the cutaway slider while in dig mode silently disabled dig clip |
| W7 | `updateCrossSectionClip()` disable (~10786) | yard + solidEarth | ⚠️ filter-based; yard keep-all (OK), solidEarth filtered only cs (kept terrain) | worked, but 2nd divergent implementation |
| W8 | `updateCrossSectionClip()` enable (~10811) | yard + solidEarth | ⚠️ yard filtered to terrain+cs — **dropped autoDig**; solidEarth same | enabling cs clip killed dig reveal |
| W9 | flatten-all deferred reset (~11164) | yard + solidEarth | ❌ solidEarth := `[]` — **wiped cs plane** | flatten while cross-section active lost the clip |
| W10 | clear-carvings reset (~12090) | yard + solidEarth | ❌ same as W9 | same |
| W11 | `buildGridLevelPlane()` (~12862) | gridLevelPlane only | n/a | single site, read-only composition; left as-is (documented) |
| W12 | compare-mode end (~10791 old / now) | yard + solidEarth | ⚠️ filter-based removal | superseded by canonical writer |

### Root cause
Four different hand-rolled array-building strategies (overwrite-with-literal, filter-out,
concat, push-mutate) composed planes differently and none of them knew about
`autoDigClipPlane`. Any writer could silently drop any other feature's plane.

### Fix — canonical writers
All writes now go through two functions + one invariant enforcer (all exported on
`window` for tests):

- **`_rebuildYardClipPlanes()`** — composes `[terrainClipPlane, crossSectionClipPlane,
  autoDigClipPlane]` for `yardMesh` (pre-existing; now the ONLY yard writer besides init).
- **`_rebuildSolidEarthClipPlanes()`** (NEW) — composes `[terrainClipPlane,
  crossSectionClipPlane]` for `solidEarthMesh` (autoDig intentionally excluded: the
  terrain *surface* is clipped to reveal the *interior walls*, which must stay visible).
- **`syncAutoDigClip()`** (NEW) — enforces the invariant
  `autoDigClipPlane !== null ⇔ terrainBrushMode === 'dig'`; no-op (no rebuild, no render)
  when already in sync. `updateAutoDigClip()` is now an alias of it, so the brush-mode
  click handler and any other entry point share one code path.

Converted writers: W4 (buildSolidEarth tail), W5+W6 (cutaway, both branches),
W7+W8 (cross-section, both branches), W9 (flatten-all), W10 (clear-carvings),
plus the cutaway/`needsUpdate` handling now inside the writers.
W3's dead else-branch was left (guarded by `typeof` check, unreachable, harmless).
`initWithYard` re-applies planes to the new material via W1 on rebuild (verified).

### Excavate-panel clip decision (documented, intentional)
The excavate button (now the `dock-underground` tab; `#excavate-btn` is a legacy hidden
shell whose content was moved into the dock at runtime) toggles a passive info/profile
panel. **Auto-arming a clip plane on panel open would cut away terrain the user did not
ask for, and closing the panel would need prior-state restoration.** The canonical route
into the ground is the Dig brush, which auto-arms `autoDigClipPlane` through
`syncAutoDigClip()`; cutaway, cross-section, and dig compose safely through the same
writers. This decision is recorded in a comment at the excavate handler (index.html
~10646).

### Composition matrix after fix (verified at runtime, see §6)

| Action | yard planes after | solidEarth planes after |
|---|---|---|
| Click Dig | `[autoDig(+y)]` | `[]` |
| + Enable cross-section clip | `[cs(x), autoDig]` | `[cs]` |
| + Disable cross-section | `[autoDig]` | `[]` |
| + Cutaway slider move | `[terrain(−y), autoDig]` | `[terrain]` |
| + Cutaway back to 0 (cs re-enabled) | `[cs, autoDig]` | `[cs]` |
| Leave dig mode (Raise) | `[cs]` | `[cs]` |
| Flatten all (cutaway reset) | `[cs]` | `[cs]` |

No plane is ever dropped by an unrelated writer.

---

## 2. Render-loop correctness

- Mechanism audited: `requestRender()` sets `needsRender = true`; `animate()` renders
  when `needsRender || dampingActive || _continuousRenderSources > 0` and clears the
  flag. Sound.
- Every clip-plane mutation path now ends in `requestRender()`:
  `updateAutoDigClip`/`syncAutoDigClip` (arm + clear), cutaway input handler,
  `updateCrossSectionClip` (enable/disable/axis/pos), flatten-all, clear-carvings,
  `initWithYard` (already had one).
- **Fix (stale-view bug):** `setGridLevel()` rebuilt the entire `solidEarthMesh` and
  moved grid/boundary objects but never called `requestRender()` — on-demand rendering
  left the underground stale until the next unrelated render. Added `requestRender()`
  at the end of `setGridLevel()` (its caller `applyGridLevel` already had one, but
  `setGridLevel` is also invoked directly via the grid-level slider path).
- 50× rapid rebuild cycles verified stable (heap flat at 18.2 MB, plane count == 1).

---

## 3. Edge cases (audited + runtime-probed, see §6 suite B)

| Edge case | Verdict | Evidence |
|---|---|---|
| Dig at yard boundary (ix/iz 0 and segs) | ✅ safe | `getTerrainIndex` clamps via `Math.round` + bounds check → `null` outside; loops `Math.max(0,…) / Math.min(segs,…)`; probed all 4 corners + center + far out-of-bounds: no throw, array intact (40,401 entries) |
| `paintTerrain` bounds after dedup fix (~7835) | ✅ safe | shared `center` reuse is bounds-checked before use; dirty-region expand uses the same clamped min/max |
| `radGridX/radGridZ` div-by-zero (yard.width/depth == 0) | ✅ safe | all 5 sites guard `w > 0 ? radius/w*segs : 0`; `getTerrainIndex` returns `null` for zero dims; `getTerrainHeight` returns 0; runtime-probed |
| `buildSolidEarth` with zero dug cells | ✅ safe | boundary skirt (4 strips) + bottom quad always emitted; floor cap & interior walls correctly skipped when `minH >= 0` (guarded by `if (minH < 0)` and `higherH>=0 && lowerH>=0 → return`); runtime-probed: 3,204 verts / 4,806 indices, finite bounding sphere; dug variant adds interior walls (3,628 verts) |
| Clip plane when `minTerrainHeight == maxTerrainHeight` | ✅ safe | cut formula `maxH + 0.5 − (v/100)*(maxH−minH+5.5)` stays finite when max==min (the `+5.5` keeps the divisor-free range non-degenerate); runtime-probed: cutY = 0.75 for max=min=3 |
| Zero-dim yard (`width=0` or `depth=0`) | ✅ safe | guarded at `getTerrainIndex` (returns null) and radGrid sites (0 radius); probed no-throw |
| Stale solidEarth after Flatten All | ✅ **fixed** | main flatten path rebuilt positions/colors but left the pre-flatten earth mesh in the scene (its own redo path *did* dispose it). Added `buildSolidEarth()` after flatten (index.html ~7236) |
| Repeated excavate/dock open-close | ✅ no leak | content is *moved* (reparented), not cloned; `updateBuriedObjects` writes `innerHTML` (no accumulating listeners); 6× open/close cycles error-free |
| Repeated clip rebuilds | ✅ no leak | writers only assign arrays of existing `THREE.Plane` singletons — no geometry/material churn; `THREE.Plane` is not a GPU resource |
| `initWithYard` dispose chain | ✅ complete | yard material+geometry, solidEarth material+geometry, gridHelper, boundaryLines all disposed before rebuild; noise texture is cached (single instance, intentionally shared) |
| Empty-body CSS rule | ✅ **fixed** | `.btn-gallery {  }` (line 928) — the exact pattern that previously caused the site-wide dead-button bug (parser swallows the next rule). Class is unused (button uses id + `tb-btn`); rule removed. |

---

## 4. CSS brace-balance audit (scripted, per sprint discipline)

Checker: full-rule parser over the `<style>` block (lines 8–1636) — per-rule body
emptiness, stray `}`, unclosed rule, plus global brace counts.

- Baseline: `{` 884 / `}` 884, **1 empty-body rule** (`.btn-gallery {  }`) → removed.
- After fix: `{` 883 / `}` 883, 0 empty rules, 0 stray closes, 0 unclosed.
- Re-run after every CSS-touching edit (none since); final file re-verified.

---

## 5. Memory / leak audit summary

| Rebuild path | Disposal | Status |
|---|---|---|
| `buildSolidEarth` re-entry | geometry + material disposed, mesh removed | ✅ |
| `initWithYard` | yard + solidEarth + gridHelper + boundaryLines disposed | ✅ |
| flatten-all redo | disposes solidEarth | ✅ (and main path now rebuilds — see §3) |
| clip-plane rebuilds | array assignment only, no GPU resources | ✅ |
| excavate panel cycles | DOM reparenting + innerHTML, no listeners accumulated | ✅ |
| terrain noise texture | module-level cache (`_terrainTextureCache`) | ✅ |

---

## 6. Gate + test results

### Quality gates (authoritative, run on final file)

| Gate | Port | Result | Exit |
|---|---|---|---|
| sprint11_quality_gate.py | 8115 | **143 / 143 (100%)** | 0 |
| sprint17_quality_gate.py | 8175 | **81 / 81 (100%)** | 0 |
| sprint15_quality_gate.py | 8099 (its own server port) | **52 / 52 (100%)** | 0 |

Notes:
- sprint15 requires an external server on its `--port` (default 8099); run with
  `python3 -m http.server 8099` + `python3 sprint15_quality_gate.py --port 8099`.
- One **stale static assertion repaired** in `sprint15_quality_gate.py`: it expected
  `UNDERGROUND_BRIGHTNESS_BOOST = 0.25`, but the constant has been `0.45` since Sprint 19
  (verified present at baseline commit `da1163f`; the gate's own browser-behavioral check
  `brighten:boost_is_25pct` passed). Assertion updated to the shipped value. No app code
  changed for this.

### STABILITY runtime suites (real CDP clicks/keys; `page.evaluate` used only to *read*
state, never to drive UI — per brief discipline)

**Suite A — clobber matrix (16/16 PASS)** `/tmp/stability_smoke.py`
1. onboarding dismissed, yard initialized — PASS
2. advanced mode active — PASS
3. terrain dock opened — PASS
4. dig click arms auto-dig clip (ny=+1) — PASS
5. underground dock opened — PASS
6. cross-section enable **composes** with auto-dig clip — PASS
7. solidEarth has cross-section plane after enable — PASS
8. cross-section disable keeps auto-dig clip — PASS
9. cutaway change keeps auto-dig clip + adds terrain plane — PASS
10. solidEarth tracks terrain cutaway plane — PASS
11. cutaway=0 preserves cross-section + auto-dig planes — PASS *(failed-by-design pre-fix)*
12. solidEarth keeps cross-section plane after cutaway=0 — PASS
13. leaving dig mode clears auto-dig, keeps cross-section — PASS
14. flatten resets cutaway plane, preserves cross-section — PASS
15. 50× clip rebuild cycles keep state sane — PASS
16. no page errors during all interactions — PASS

**Suite B — edge cases (8/8 PASS)** `/tmp/stability_edge.py`
1. degenerate range (min==max) cutY finite — PASS
2. paintTerrain at 4 corners + center + far out-of-bounds: no throw — PASS
3. zero yard dims: getTerrainIndex null / height 0, no throw — PASS
4. buildSolidEarth zero dug cells: valid geometry — PASS
5. buildSolidEarth with dug cells: interior walls added — PASS
6. 6× dock open/close cycles: no page errors — PASS
7. cutaway 0→100→0 leaves clean plane state — PASS
8. no page errors in edge-case suite — PASS

---

## 7. Files changed

| File | Change |
|---|---|
| `index.html` | +`_rebuildSolidEarthClipPlanes()`, +`syncAutoDigClip()`; `updateAutoDigClip()` aliased; 8 clip-plane write sites converted to canonical writers; `setGridLevel()` +`requestRender()`; flatten-all +`buildSolidEarth()`; removed empty-body CSS rule `.btn-gallery{}`; +window exports for the two new functions. Net +498 bytes. |
| `sprint15_quality_gate.py` | Stale static assertion repaired (`0.25` → shipped `0.45`, stale since Sprint 19). |
| `STABILITY_REPORT.md` | This report. |

## 8. Known limitations (documented, not fixed — out of stability scope)

1. `buildGridLevelPlane()` keeps its original one-off clip write (single site, startup
   only, try/catch-guarded); it does not pick up planes enabled later. Feature-level
   decision, no instability observed.
2. Excavate panel open/close intentionally does not arm/disarm clip planes (rationale in
   index.html ~10646). If the owner wants the excavate flow to force-reveal the
   subsurface, that is a feature change to route through `syncAutoDigClip()` — one call.