# Mobile Usability Discovery Log — Sprint 8, Agent 3

## Testing Environment
- Tool: Playwright (Chromium headless)
- Viewports: 375x667 (iPhone SE), 375x812 (iPhone X), 768x1024 (iPad)
- Touch: has_touch=True, is_mobile=True, device_scale_factor=2-3
- Server: Python http.server on localhost:8765

## Issues Found (Before Fixes)

### 375px (iPhone SE)

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | Topbar overflows horizontally (867px > 375px) — Layers, Cost, Walk, Share buttons off-screen | Critical | FIXED |
| 2 | Topbar scrollbar hidden (`scrollbar-width: none`) — no visual scroll affordance | High | FIXED |
| 3 | Walk mode button unreachable (off-screen at left=459, right=503, viewport=375) | Critical | FIXED |
| 4 | Cost panel button unreachable (off-screen at left=411) | Critical | FIXED |
| 5 | Layer panel button unreachable (off-screen at left=363) | Critical | FIXED |
| 6 | Share modal button unreachable (off-screen at left=507) | Critical | FIXED |
| 7 | View controls 40x40px (below 44px minimum touch target) | Medium | FIXED |
| 8 | Library category headers 31px height (below 44px touch target) | Medium | FIXED |
| 9 | Library items have small touch targets | Medium | FIXED |
| 10 | Cost panel close button 17x21px (way below 44px) | High | FIXED |
| 11 | Walk exit button 31px height (below 44px) | Medium | FIXED |
| 12 | Wizard skip button 31px height (below 44px) | Medium | FIXED |
| 13 | No long-press context menu for mobile object interaction | Enhancement | FIXED |
| 14 | Terrain painting: finger occludes brush cursor | Enhancement | FIXED |
| 15 | Walk mode hint says "WASD/Arrows" — desktop-oriented | Low | FIXED |
| 16 | Walk mode joystick 52px (could be larger for mobile) | Low | FIXED |

### 768px (iPad)

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 17 | Topbar overflows (867px > 768px) — some buttons off-screen | High | FIXED |
| 18 | Dock panels 684px wide (too wide for tablet, should be constrained) | Medium | FIXED |
| 19 | Cross-section overlay min-width 400px exceeds 375px viewport | High | FIXED |
| 20 | Cut/fill panel positioned at right:330px — off-screen on mobile | High | FIXED |
| 21 | Cost/Layer panels share top:16px right:16px — overlap | Medium | FIXED |
| 22 | Wizard skip button 31px height | Medium | FIXED |
| 23 | View controls 40px | Medium | FIXED |

### Architecture Discovery

| # | Finding | Impact |
|---|---------|--------|
| A1 | Old floating buttons (terrain-btn, excavate-btn, etc.) are hidden via `display:none !important` — replaced by Tool Dock system | Design — not a bug |
| A2 | Old floating panels (terrain-controls, excavate-panel, etc.) hidden — content moved to dock panels | Design — not a bug |
| A3 | Tool Dock has 6 tabs: Terrain, Underground, Analyze, Pro Tools, Sun, Measure | Working correctly |
| A4 | Innovation panel has 21 tools (not 12) — includes additional tools from later sprints | Not a bug |
| A5 | Innovation has progressive disclosure — advanced tools behind collapsible section | Working correctly |
| A6 | Library categories ARE collapsible (cat-section/cat-title with arrow SVG) | Working correctly |
| A7 | Touch gesture system: tap-to-select, drag-to-move, pinch-zoom via OrbitControls | Working correctly |
| A8 | Walk mode has on-screen joystick (forward/back/left/right) | Working correctly |
| A9 | Mobile properties sheet exists (#mobile-props-sheet) with bottom-sheet design | Working correctly |
| A10 | CSS inline stylesheet has 500-rule limit in Chromium — extra CSS rules are silently dropped | Fixed by separate style tag |
| A11 | IS_MOBILE detection uses UA regex + `window.innerWidth < 768` | Working correctly |
| A12 | IS_MOBILE variable is in module scope, not accessible from page evaluate | Test artifact |

## Issues Fixed

### Fix 1: Topbar Scrollable with Indicator (375px)
- Made topbar scrollable with visible thin scrollbar
- Added gradient fade indicator on right edge when buttons overflow
- JS updates `scrolled-end` class when at scroll end
- Hide disabled Undo/Redo on 375px to reduce overflow (867px → 555px)

### Fix 2: Dock Panel Width Constraint (768px)
- Added `max-width: min(340px, calc(100vw - 84px))` to dock panels
- Added `max-width: calc(100vw - 84px)` to dock panel container
- Panels now fit within viewport at both 375px and 768px

### Fix 3: Mobile-Responsive Panels
- Cost/layer panels: full width minus margins on mobile
- Cross-section overlay: `min-width: 0` instead of 400px
- Cut/fill panel: repositioned for mobile
- All panels constrained to `max-width: calc(100vw - 32px)`

### Fix 4: Touch Target Sizes (44px minimum)
- View controls: 40px → 44px
- Library category headers: 31px → 44px
- Library items: added min-height 44px
- Cost/layer close buttons: 17x21px → 44px
- Walk exit button: 31px → 44px
- Wizard skip button: 31px → 44px

### Fix 5: Long-Press Context Menu
- Added 500ms long-press detection on objects
- Shows context menu with Select/Duplicate/Rotate/Delete actions
- All menu items 44px touch targets
- Closes on tap outside

### Fix 6: Terrain Brush Offset
- On mobile touch, brush cursor offset 40px upward from finger
- Finger no longer occludes the brush position
- Uses `_getGroundPointFromScreen` with adjusted Y coordinate

### Fix 7: Walk Mode Mobile Improvements
- Mobile-specific hint ("Joystick to move - Drag to look - Tap Exit to leave")
- Larger joystick buttons (52px → 56px)
- Larger exit button (44px min)
- Walk controls and joystick verified working on mobile

### Fix 8: Separate Style Tag for Mobile CSS
- Chromium has a 500-rule limit on inline stylesheets
- Added second `<style id="mobile-usability-styles">` tag after main CSS
- All mobile-specific CSS moved to this separate tag
- Bypasses the 500-rule limit entirely

## Issues Not Fixed (By Design / Test Artifacts)

| Issue | Reason |
|-------|--------|
| Topbar still overflows at 375px (555px > 375px) | By design — scrollable with visible indicator |
| Dock panels 'analyze'/'innovate' not scrollable at 768px | They fit within viewport (no need to scroll) |
| Playwright force-click timeouts at 768px | Test artifact — works with dispatch_event |
| IS_MOBILE not accessible from page.evaluate | Module scope — test artifact only |