# Sprint 16 — Desktop UX Polish Discovery Log (Agent 3)

## File Structure
- Single `index.html` file, 16,942 lines (after changes), Three.js v0.160.0
- CSS variables defined at top (`--sidebar-w`, `--topbar-h`, etc.)
- Multiple `@media` breakpoints: 768px (mobile), 768px+500px (small mobile), tablet

## Key Code Locations (after changes)
| Feature | Line Range | Notes |
|---------|-----------|-------|
| CSS variables | 43-62 | `--sidebar-w: 280px` |
| `#tool-dock` CSS | 157-162 | `bottom: 32px` (was 16px) |
| `.td-tab` CSS | 163-168 | `padding: 8px 12px` (was 8px 10px) |
| `.td-tab .td-label` CSS | 174 | `font-weight: 600; font-size: 11px` |
| `#dock-panel-container` CSS | 181-184 | `bottom: 32px` |
| `.dock-panel` CSS | 186-191 | `min-width: 320px; max-width: 400px` |
| `#status-bar` CSS | 220-227 | Fixed bottom, 24px height |
| `#scale-bar` CSS | 133 | `bottom: 32px` |
| `#tape-measure-btn` CSS | 139 | `bottom: 32px` |
| `#terrain-btn` CSS | 143 | `bottom: 32px` |
| `#terrain-controls` CSS | 147 | `bottom: 72px` |
| `#terrain-analysis-btn` CSS | 269 | `bottom: 32px` |
| `#innovation-btn` CSS | 747 | `bottom: 32px` |
| `#view-controls` CSS | 126 | `bottom: 32px` |
| `updateCanvasCursor()` | ~6608 | Cursor feedback function |
| `updateStatusBar()` | ~6618 | Status bar update function |
| Status bar variables | ~6601 | `_statusFPS`, `_statusFrameCount`, etc. |
| Keyboard shortcuts | ~6712-6760 | 1-6, [, ], X handlers |
| `animate()` FPS tracking | ~4478-4486 | FPS counter in render loop |
| Mouse world position tracking | ~5312-5330 | `mousemove` listener on viewport |
| Terrain button click handler | ~6955 | Toggles terrainMode, calls updateCanvasCursor |
| Command palette items | ~6157-6177 | CMD_ITEMS array with terrain brush shortcuts |
| Status bar HTML | ~16935 | `#status-bar` with sb-tool, sb-brush, sb-height, sb-fps |
| Window exports | ~16921-16929 | Getters for testing (terrainMode, terrainBrushMode, etc.) |

## Architecture Notes
- `terrainMode`, `terrainBrushMode`, `terrainBrushSize` are `let` variables in script scope
- `isDragging`, `dragObject`, `dragStartPos` manage object drag state
- `tapeMeasureActive` controls tape measure tool
- `cmdPaletteOpen` tracks command palette state
- Exposed live values via `Object.defineProperty(window, ...)` getters for testing
- `showToast()` function used for all keyboard shortcut feedback
- `showHint()` shows transient context hints
- The `animate()` loop runs continuously via `requestAnimationFrame`
- FPS calculated by counting frames per 1000ms window

## Pitfalls Found
1. **Multiple `terrainBtn` declarations** — The variable `terrainBtn` is declared in multiple IIFE scopes. Using `document.getElementById('terrain-btn')` in the keydown handler avoids scope issues.
2. **Duplicate code blocks** — Mobile touch handlers and desktop pointer handlers share similar code, making targeted patches require extra context for uniqueness.
3. **Server port conflicts** — Another agent's HTTP server was running on port 8199 from a different directory. Had to kill it and restart.
4. **`let` scope in Playwright** — `let` variables in script scope aren't accessible via `page.evaluate()`. Used `Object.defineProperty` with getters to expose live values.