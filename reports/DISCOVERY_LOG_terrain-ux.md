# Discovery Log

## Terrain UX Sprint — Agent 4 (Critic)
### All discoveries during persona testing and implementation

---

## Discoveries Logged

### D1: Catalog Object Type Names
**Severity: Low (Test Issue)**
**Date: 2026-08-20**

**Discovery:** The CATALOG uses prefixed names (`pool_inground`, `fence_privacy`, `fence_picket`) rather than generic names (`pool`, `fence`). This caused initial persona test failures when trying to add objects via `window._test.addObject()`.

**Impact:** Low — only affects programmatic test access. The UI library displays correct names.

**Resolution:** Fixed persona tests to use correct catalog names.

---

### D2: Desktop Terrain Button Sizes Too Small
**Severity: Medium (Accessibility)**
**Date: 2026-08-20**

**Discovery:** The original terrain mode buttons were only 24px height on desktop, preset buttons were 25px. This is below the 32px minimum recommended for users with limited dexterity.

**Impact:** Medium — users with limited dexterity (elderly, motor impairments) would have difficulty clicking these buttons precisely.

**Resolution:** Increased all desktop terrain buttons to 32px minimum height, increased font sizes from 10-11px to 12px.

---

### D3: No Pool Fence Compliance Warnings for Sloped Terrain
**Severity: High (Safety)**
**Date: 2026-08-20**

**Discovery:** When placing a pool and fence on sloped terrain, there are no warnings about:
- Whether the fence height is adequate on the downhill side
- Whether the fence complies with local pool barrier codes on slopes
- Whether the pool wall height is sufficient relative to terrain

**Impact:** High — safety-critical for families with children. A 4ft fence on a 3ft slope effectively becomes a 1ft barrier on the downhill side.

**Status:** Logged — not fixed in this sprint (outside terrain UX scope).

**Recommendation:** Add automatic safety warnings when pool + fence are placed on terrain with >1ft elevation variation within the fence perimeter.

---

### D4: No Terrain Statistics Display
**Severity: Low (UX Enhancement)**
**Date: 2026-08-20**

**Discovery:** There's no display of terrain statistics such as:
- Maximum height/depth
- Average slope percentage
- Volume of earth to move (cut/fill)
- Surface area

**Impact:** Low — would be useful for contractors and landscapers estimating work.

**Status:** Logged — not implemented in this sprint.

**Recommendation:** Add a terrain statistics panel that shows max height, min height, slope %, and estimated cut/fill volume.

---

### D5: Drainage Arrows Could Show Slope Percentage
**Severity: Low (UX Enhancement)**
**Date: 2026-08-20**

**Discovery:** The drainage arrows show direction but not slope magnitude as a percentage or degree. Landscapers would benefit from seeing "5% slope" or "3°" labels on arrows.

**Impact:** Low — direction alone is useful, but percentage adds professional value.

**Status:** Logged — arrow length is proportional to slope, which partially addresses this.

**Recommendation:** Add optional slope percentage labels on drainage arrows for professional use.

---

### D6: No "Create Swale" Tool
**Severity: Low (UX Enhancement)**
**Date: 2026-08-20**

**Discovery:** Creating a drainage swale currently requires manually painting a line of lowered terrain with the brush tool. There's no dedicated "swale" or "drainage channel" tool.

**Impact:** Low — can be done manually, but a dedicated tool would be more efficient for landscapers.

**Status:** Logged — not implemented.

**Recommendation:** Add a "drainage channel" tool that creates a V-shaped or U-shaped channel along a drawn path.

---

### D7: No Before/After Toggle for Terrain
**Severity: Low (UX Enhancement)**
**Date: 2026-08-20**

**Discovery:** While undo can revert terrain, there's no quick "before/after" toggle or split-view. Real estate agents showing hillside lots would benefit from a side-by-side or toggle comparison.

**Impact:** Low — undo works but isn't designed for rapid before/after demonstration.

**Status:** Logged — not implemented.

**Recommendation:** Add a "hold to compare" button that temporarily reverts terrain while pressed.

---

### D8: Mobile Bottom Sheet Lacks Grabber Handle
**Severity: Low (UX Polish)**
**Date: 2026-08-20**

**Discovery:** The mobile terrain controls bottom sheet doesn't have a visible grabber handle like the properties bottom sheet does. Users may not know they can dismiss it by swiping down.

**Impact:** Low — discoverability issue, not a blocker.

**Status:** Logged — not fixed in this sprint.

**Recommendation:** Add a grabber handle bar at the top of the terrain controls bottom sheet.

---

### D9: Height Legend Could Be Draggable
**Severity: Very Low (UX Polish)**
**Date: 2026-08-20**

**Discovery:** The height legend is positioned at top-left and can't be moved. On small screens it might overlap with other UI elements.

**Impact:** Very low — minor positioning issue.

**Status:** Logged.

**Recommendation:** Make the height legend draggable or collapsible.

---

### D10: Undo Stack Properly Handles Terrain Overlays
**Severity: Info (Positive Discovery)**
**Date: 2026-08-20**

**Discovery:** The undo/redo system correctly refreshes height colors and drainage arrows when undoing/redoing terrain changes. The undo callbacks include `if (terrainHeightColorsActive) applyHeightColors()` and `if (terrainDrainageActive) updateDrainageArrows()`.

**Impact:** Positive — overlays stay synchronized with terrain state during undo/redo operations.

**Status:** Working as expected.

---

### D11: Terrain Mode Exit Cleans Up Overlays
**Severity: Info (Positive Discovery)**
**Date: 2026-08-20**

**Discovery:** When exiting terrain mode, the code now properly disables and removes both height colors and drainage arrows. This prevents stale overlays from remaining visible when the user isn't in terrain editing mode.

**Impact:** Positive — clean state management.

**Status:** Implemented and verified by quality gate test T7b.

---

### D12: Brush Cursor Performance
**Severity: Info (Performance)**
**Date: 2026-08-20**

**Discovery:** The terrain-conforming brush cursor samples 48 height lookups per frame during pointer move. Each lookup uses bilinear interpolation (`getTerrainHeight`). This is computationally lightweight and should not cause performance issues even on mobile devices.

**Impact:** Neutral — performance is acceptable.

**Status:** No action needed.