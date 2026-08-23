# Sprint 7 — Discovery Log: Social & Sharing Innovator

**Agent:** 2 (Builder — Social & Sharing Innovator)  
**Sprint:** 7  
**Date:** August 23, 2026  
**Working Directory:** /root/byd7-social-sharing/  
**Final Line Count:** 12,728 lines (up from 11,748 — added 980 lines)

---

## Features Implemented

### 1. GALLERY MODE — Community Design Gallery
**Impact:** HIGH — turns a solo design tool into a shareable community platform.

**What it does:**
- Saves designs to localStorage with auto-generated thumbnail screenshots
- Browse designs in a responsive grid with thumbnail previews
- Categorize designs: General, Pool & Water, Garden, Patio & Living, Family Yard, Modern
- Filter gallery by category
- Sort by: Most Recent, Name (A-Z), Most Objects
- Click any card to load the design instantly
- Delete designs from gallery
- Caps at 50 designs to prevent localStorage overflow
- Empty state shows placeholder message

**How it works:**
- `captureThumbnail()` renders the current scene and downscales to 200×140 JPEG
- `saveToGallery()` serializes design via existing `serializeDesign()`, stores with thumbnail + metadata in localStorage
- `renderGalleryGrid()` filters, sorts, and renders cards dynamically
- Each card has click-to-load and delete buttons

**Files modified:** index.html (CSS + HTML modal + JS)

### 2. TIME-LAPSE BUILD — Construction Animation + GIF Export
**Impact:** HIGH — the most viral potential. People love watching things being built.

**What it does:**
- Animates yard construction in 5 stages:
  1. Empty Yard (flat terrain, no objects)
  2. Terrain Sculpting (restore terrain heights)
  3. Hardscape (patios, paths, fences, structures)
  4. Planting (trees, bushes, hedges, lawn, raised beds)
  5. Finishing Touches (pools, hot tubs, fire pit, chairs, tables, grill)
- Captures each stage as a frame on canvas
- Progress bar and stage label update during animation
- After completion, "Download GIF" button appears
- Native GIF encoder (no external libraries!) using LZW compression
- GIF is 240px wide, looping, with 1s delay between frames
- Play/Stop/Replay button toggles animation state

**How it works:**
- `getObjectsByStage()` classifies objects by type into 5 categories
- `playTimelapse()` hides all objects, flattens terrain, then reveals stage by stage
- Each frame is captured via `ctx.getImageData()` and stored for GIF export
- `generateGIF()` implements a full GIF89a encoder with:
  - Color quantization (frequency-based 256-color palette)
  - LZW compression with dictionary reset at 4096 entries
  - NETSCAPE2.0 looping extension
  - Graphic Control Extension for frame delay
- `downloadTimelapseGIF()` scales frames down and generates the GIF blob

**Discovery:** The native GIF encoder was the most complex part. Implemented LZW from scratch with proper code size growth, dictionary management, and bit packing. The encoder handles the full GIF89a spec including NETSCAPE2.0 looping extension.

### 3. SOCIAL SHARING CARDS — OpenGraph-Style Preview
**Impact:** MEDIUM-HIGH — makes sharing on social media look professional.

**What it does:**
- Generates a 1200×630px image (standard OpenGraph dimensions)
- Uses the rendered 3D scene as background
- Gradient overlay for text readability (dark green at bottom)
- Green accent bar at top (brand colors)
- Editable title with word-wrap (max 2 lines, 60 chars)
- Yard dimensions displayed (e.g., "50ft × 100ft")
- Object count displayed
- "Backyard Designer 3D" branding in top-right
- "Design your dream yard" tagline
- Tree emoji badge in bottom-right
- Live preview updates as you type the title (debounced 300ms)
- Regenerate button to force a fresh render
- Download as PNG

**How it works:**
- `generateSocialCard(title)` renders the scene, draws it to canvas, then composites text/gradient/branding using Canvas 2D API
- Title input has debounced listener that regenerates card on change
- `downloadSocialCard()` uses `canvas.toDataURL('image/png')` and triggers download

---

## Discoveries & Bugs Found

### D1: Module-Scoped Variables
**Issue:** The app uses `<script type="module">` which means all variables (renderer, scene, state, CATALOG, etc.) are module-scoped, not accessible from `page.evaluate()` in Playwright tests.

**Fix:** Added a global exposure block at the end of the script that assigns key functions/variables to `window._byd*` properties. This is also useful for debugging.

### D2: Server Caching
**Issue:** The initial HTTP server (python3 -m http.server) was started before file edits. The cached file (11748 lines) was served instead of the updated file (12708 lines).

**Fix:** Killed the old server process and started a new one. No code changes needed — just operational awareness.

### D3: GIF Encoder LZW Complexity
**Issue:** Implementing a correct LZW encoder from scratch was non-trivial. Initial attempts had bit-packing errors that corrupted the output.

**Solution:** Implemented proper bit packing with careful handling of:
- Variable code size (starts at minCodeSize + 1, grows to 12)
- Dictionary reset at 4096 entries (emit clear code, reinitialize)
- Bit accumulation across byte boundaries
- Sub-block format for LZW data (max 255 bytes per block)

### D4: Time-Lapse Stage Timing
**Issue:** The 5-stage animation with 1-second delays per stage takes ~5 seconds total. Tests needed sufficient wait time (7s) to capture all 5 frames.

**Fix:** Increased test wait time from 5s to 7s.

### D5: Empty Gallery Re-Render
**Issue:** After clearing localStorage, the gallery grid didn't automatically re-render to show the empty state message.

**Fix:** Called `renderGalleryGrid()` explicitly after clearing localStorage in the test. In production usage, the delete button triggers re-render, and the gallery opens with `renderGalleryGrid()`.

### D6: Thumbnail Capture Requires Active Render
**Issue:** `captureThumbnail()` calls `renderer.render()` before `toDataURL()`. This works because the WebGL canvas has `preserveDrawingBuffer: true` (or the render call is synchronous).

**Note:** If `preserveDrawingBuffer` were false, the thumbnail capture would fail intermittently. The app already handles this in its screenshot function.

---

## Test Results

```
RESULTS: 58 passed, 0 failed, 58 total

Feature 1: Gallery Mode          — 18/18 tests pass
Feature 2: Time-Lapse Build       — 15/15 tests pass  
Feature 3: Social Sharing Card    — 14/14 tests pass
Existing Features Not Broken      — 10/10 tests pass
Console Errors                    — 1/1 test pass
```

### Test Coverage:
- Gallery: button existence, modal open/close, save with name+category, thumbnail generation, grid rendering, category filter, sort, count display, delete, empty state, escape key
- Time-Lapse: button existence, modal open/close, canvas, play button, progress bar, stage label, animation start, progress updates, stage label updates, frame capture (5 frames), GIF button visibility, object restoration, close button, escape key
- Social Card: button existence, modal open/close, canvas dimensions (1200×630), rendered content, title input, default value, regenerate button, download button, title change regenerates, regenerate redraws, close button, escape key, branding pixels
- Existing: Share, Save, Screenshot, Walk, Layers, Cost, Help buttons all intact. Core functions accessible. No console errors.

---

## Architecture Notes

### Integration Approach
All 3 features were added as a single self-contained block before `</script>`. This ensures:
- No modification to existing code paths
- All new CSS is in a clearly labeled section
- All new HTML modals are placed after the existing share modal
- All new JS is in one block with clear section headers
- Existing features remain untouched

### CSS Design
- Uses the app's existing CSS variables (--surface, --primary, --text, --border, --radius, etc.)
- New modals use z-index: 300 (above existing modals at z-index: 200)
- Shared button classes (.s7-btn, .s7-btn-secondary) for consistent styling
- Gallery grid is responsive with auto-fill minmax(200px, 1fr)

### Performance Considerations
- Gallery thumbnails are JPEG at 0.6 quality (small file size)
- Gallery capped at 50 designs (localStorage ~5MB limit)
- Time-lapse GIF is downscaled to 240px width for reasonable file size
- Social card canvas is 1200×630 (standard OG size, not too large)
- Title input debounced at 300ms to avoid excessive regeneration

---

## File Summary
| File | Status | Description |
|------|--------|-------------|
| index.html | Modified | +980 lines (CSS, HTML modals, JS for all 3 features) |
| sprint7_social_tests.py | Created | 58-test Playwright suite |
| DISCOVERY_LOG.md | Created | This file |

---

## Git Commits
All work committed as Caddy <caddyaibot@gmail.com>.