# Basic Mode Report — Sprint 17

## Summary

Implemented a **Basic Mode** for Backyard Designer 3D — a simplified interface for beginners that shows only essential tools. The mode is toggled via a Basic/Advanced switch in the topbar and persists to localStorage.

## What Was Built

### 1. Mode Toggle UI
- Added a two-button toggle switch (`Basic` / `Advanced`) in the topbar, positioned between the brand and the spacer
- Active button is highlighted with the primary color
- Uses ARIA roles (`role="tablist"`, `role="tab"`, `aria-selected`)
- Defaults to **Basic** on first visit

### 2. CSS-Driven Show/Hide
- Added `body.byd-basic-mode` and `body.byd-advanced-mode` body classes
- All visibility changes are CSS-driven via `display: none !important` rules
- No JS DOM manipulation needed for hiding/showing elements
- ~165 lines of CSS rules targeting specific elements by ID, class, and data attributes

### 3. JavaScript `setMode()` Function
- `window.setMode(mode)` — sets mode ('basic' or 'advanced'), updates body class, saves to localStorage
- Validates input, defaults to 'basic' if invalid
- Auto-switches to Terrain tab if an advanced dock tab is active when switching to basic
- Closes any open advanced panels when switching to basic
- Blocks Ctrl+K (command palette) in basic mode via capture-phase listener
- Click handler for `.mode-toggle-btn` buttons
- Reads saved preference from `localStorage.getItem('byd-mode')` on page load

### 4. localStorage Persistence
- Key: `byd-mode`
- Values: `'basic'` or `'advanced'`
- Default: `'basic'` (first visit)

## What Basic Mode Shows

| Feature | Basic Mode | Advanced Mode |
|---------|-----------|----------------|
| Terrain tab (Raise, Lower, Smooth, Dig, Fill, Flatten) | ✅ | ✅ |
| Erode brush | ❌ Hidden | ✅ |
| Terrain presets (Hill, Valley, etc.) | ❌ Hidden | ✅ |
| Terrain overlays (Height Colors, Drainage) | ❌ Hidden | ✅ |
| Precision mode | ❌ Hidden | ✅ |
| Grid level section | ❌ Hidden | ✅ |
| Carving section | ❌ Hidden | ✅ |
| Underground tab | ❌ Hidden | ✅ |
| Analyze tab | ❌ Hidden | ✅ |
| Pro Tools tab | ❌ Hidden | ✅ |
| Atmosphere tab | ❌ Hidden | ✅ |
| Measure tab | ❌ Hidden | ✅ |
| Sun & Shadow tab | ✅ | ✅ |
| Undo / Redo | ✅ | ✅ |
| Save / Load / Screenshot / Help | ✅ | ✅ |
| 3D / Bird's-eye toggle | ✅ | ✅ |
| Layers button | ❌ Hidden | ✅ |
| Cost button | ❌ Hidden | ✅ |
| Walk button | ❌ Hidden | ✅ |
| Share button | ❌ Hidden | ✅ |
| Export dropdown | ❌ Hidden | ✅ |
| Gallery / Time-Lapse / Card | ❌ Hidden | ✅ |
| Season / Growth / Permits / Templates / Label / Print | ❌ Hidden | ✅ |
| Object sidebar | ✅ | ✅ |
| Properties panel | ✅ | ✅ |
| Status bar | Simplified (tool only) | Full (tool, brush, height, FPS) |
| Command palette (Ctrl+K) | ❌ Blocked | ✅ |
| Terrain height legend | ❌ Hidden | ✅ |

## Files Modified

### `index.html`
- **CSS** (after line 1553): Added ~165 lines of `body.byd-basic-mode` CSS rules
- **HTML** (after line 1772): Added 4 lines for mode toggle UI (`#mode-toggle`)
- **JavaScript** (before closing `</script>`): Added ~96 lines for `setupBasicMode()` IIFE

### New Files
- `test_basic_mode.js` — Playwright test suite (22 tests)
- `DISCOVERY_LOG.md` — Discovery and exploration log
- `BASIC_MODE_REPORT.md` — This report

## Testing Results

**22/22 tests passing** ✅

```
✅ Default to Basic mode
✅ Mode toggle buttons exist
✅ Advanced dock tabs hidden in Basic mode
✅ Terrain & Sun tabs visible in Basic mode
✅ Erode brush hidden in Basic mode
✅ Required terrain brushes visible
✅ Advanced topbar buttons hidden
✅ Essential topbar buttons visible
✅ View toggle visible
✅ Status bar simplified (1 item)
✅ Command palette hidden
✅ Switch to Advanced mode
✅ All dock tabs visible in Advanced mode
✅ Advanced buttons visible in Advanced mode
✅ Erode brush visible in Advanced mode
✅ localStorage saved as advanced
✅ Mode persists on reload
✅ localStorage saved as basic
✅ Ctrl+K blocked in basic mode
✅ window.setMode function exists
✅ No JS errors on load
✅ Mode toggle button click works
```

## How to Test

1. Start HTTP server: `python3 -m http.server 8172`
2. Open `http://localhost:8172/index.html` in a browser
3. Verify Basic mode is active by default (toggle shows "Basic" highlighted)
4. Verify advanced features are hidden
5. Click "Advanced" — verify all features appear
6. Reload page — verify mode persists
7. Run automated tests: `node test_basic_mode.js`

## Design Notes

- **CSS-first approach**: All visibility toggling is done via CSS classes on `<body>`, not JS DOM manipulation. This is performant, maintainable, and avoids timing issues.
- **Graceful degradation**: If localStorage is unavailable, the app defaults to basic mode silently.
- **No feature removal**: Advanced features are hidden, not removed. Switching to Advanced mode instantly restores everything without page reload.
- **Beginner safety**: Ctrl+K (command palette) is explicitly blocked in basic mode via a capture-phase keyboard listener, preventing accidental activation.