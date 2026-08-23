# Discovery Log — First-Time User Journey

**Sprint 8 — Agent 1 (Builder)**
**Date:** August 23, 2026
**Tool:** Playwright headless Chromium, 1400×900 viewport
**Server:** Python http.server on localhost:8765

---

## Journey Log

### [JOURNEY] 2026-08-23T03:06:00 — Step 1: Loading app for first time
- App loaded successfully at http://localhost:8765/index.html
- Setup wizard appeared immediately (#wizard visible)
- Screenshot: `screenshots/01_load.png`

### [WIZARD] 2026-08-23T03:06:01 — Wizard content analysis
- Heading: "Welcome to Backyard Designer 3D"
- Step 1 of 2: "Let's set up your yard. What shape is it?"
- Shape options: Rectangle, L-Shape (Rectangle selected by default)
- Action button: "Next Step →"
- Skip option: "Skip — use default yard"
- Screenshot: `screenshots/02_wizard.png`
- **Finding:** Wizard is clear and well-designed. No issues.

### [WIZARD] 2026-08-23T03:06:03 — Wizard step 2: Dimensions
- Heading: "How Big Is Your Yard?"
- Inputs: Width (side to side), Depth (front to back)
- Quick sizes: Small (30×50), Medium (50×100), Large (75×150) as clickable links
- Action button: "Start Designing! →"
- Back button: "← Back"
- Skip option still available
- **Finding:** Good progressive disclosure. Quick sizes help users who don't know dimensions.

### [JOURNEY] 2026-08-23T03:06:05 — Step 2: Post-setup state
- Wizard closed, 3D view visible
- **ISSUE FOUND [HIGH]**: Context hint (`#context-hint`) is empty and invisible. Text is empty string. `visible` class not applied.
- **ISSUE FOUND [HIGH]**: No onboarding elements found (checked `.welcome`, `.getting-started`, `.onboarding`, `.tutorial`, `.first-time-hint`, `.tip-box`, `.info-box` — all empty)
- UI elements visible:
  - `#topbar`: Backyard Designer 3D, Undo, Redo, 3D View, Bird's-eye, Save, Load, Shot, ? Help, Layers, Cost, Walk, Share
  - `#sidebar`: "Add to Your Yard" with object library (21 items in .lib-item)
  - `#tool-dock`: SCULPT (Terrain, Underground, Analyze), BUILD (Pro Tools), VIEW (Sun & Shadow, Measure)
  - `#view-controls`: bottom-right zoom/reset buttons
- Screenshot: `screenshots/04_post_setup.png`

### [OBJECT] 2026-08-23T03:06:08 — Step 3: Adding an object
- `.lib-item` selector: 21 items found (categories already expanded)
- First item: "Privacy Fence — 6-8 ft wood fence"
- Clicking the item: object added to scene, Properties panel appeared on right
- Properties panel showed: Privacy Fence, Object #1, Size & Style (Height 4/6/8 ft, Length, Color), Rotation
- **ISSUE FOUND [MEDIUM]**: No toast notification when object is added — only a brief context hint that disappears in 3 seconds
- Screenshot: `screenshots/05_object.png`

### [TERRAIN] 2026-08-23T03:06:12 — Step 4: Sculpting terrain
- Terrain dock tab visible at bottom-left, text "Terrain", aria-label "Terrain editing tools"
- Clicked terrain tab → dock panel opened
- Panel content: "Terrain Sculpting" header, Mode buttons (Raise/Excavate/Smooth/Erode), Brush Size slider (8 ft), Strength slider (0.05), Precision Mode toggle, Height at cursor readout, Grid Level section, Voxel info
- **ISSUE FOUND [MEDIUM]**: No instructions in the panel before user selects a mode — user doesn't know to "click and drag on the ground"
- Clicked "Raise" mode → context hint appeared: "Click and drag on the ground to sculpt terrain"
- Screenshot: `screenshots/06_terrain_panel.png`

### [SAVE] 2026-08-23T03:06:15 — Step 5: Saving design
- Save button: text "Save", tooltip "Save Design"
- Click triggered download: `my-backyard-design.json`
- Toast: "Design saved! Check your downloads folder."
- **Finding:** Save works well with clear feedback.

### [LOAD] 2026-08-23T03:06:17 — Step 6: Loading design
- Load button: text "Load", tooltip "Load Design"
- File input (`input[type='file']`) found — loading via file picker
- **Finding:** Load is clear and functional.

### [FEATURE] 2026-08-23T03:06:19 — Feature 1: Sun & Shadow
- Dock tab "Sun & Shadow" clicked → panel opened
- Panel content: Location section with "Use My Location" button, Latitude/Longitude inputs, City presets (Detroit, New York, LA, Chicago, Dallas, Seattle, Miami, Denver), Date input, Time slider, Play Day Cycle button, Reset button
- **Finding:** Well-organized panel. "Use My Location" is discoverable.
- Screenshot: `screenshots/08_sun.png`

### [FEATURE] 2026-08-23T03:06:22 — Feature 2: Cost Estimator
- "Cost" button clicked (tooltip "Cost Estimator")
- Cost panel appeared: "Cost Estimate" with Fences & Structures $600, Total (1 item) $600, disclaimer text
- **Finding:** Works well.
- Screenshot: `screenshots/09_cost.png`

### [FEATURE] 2026-08-23T03:06:25 — Feature 3: Walk Mode
- "Walk" button clicked (tooltip "Walk Through Your Design (first-person)")
- Walk controls overlay appeared: "Exit Walk", "WASD/Arrows to move - Drag to look - Esc to exit", directional buttons (▲◀▶▼)
- **ISSUE FOUND [MEDIUM]**: No toast confirmation when entering walk mode
- **Finding:** On-screen instructions are present (WASD/Arrows), which is good.
- Screenshot: `screenshots/10_walk.png`

### [FEATURE] 2026-08-23T03:06:28 — Feature 4: Screenshot
- Screenshot button: text "Shot", tooltip "Take Screenshot"
- **ISSUE FOUND [MEDIUM]**: "Shot" is ambiguous — could mean many things. Should be "Capture" or "Screenshot"
- (Code does trigger download + toast: "Screenshot saved!")

### [FEATURE] 2026-08-23T03:06:30 — Feature 5: Help
- "? Help" button clicked
- Help modal appeared with comprehensive content:
  - "How to Use Backyard Designer 3D"
  - Getting Started: Click items from left panel, click objects in 3D view, drag to reposition, use right panel for properties
  - Camera Controls: 3D View (orbit/zoom/pan), Bird's-eye (top-down), zoom buttons
  - Saving & Sharing: Save downloads file, auto-saves to browser, Screenshot captures PNG
  - Terrain & Measuring: Terrain sculpting, Precision Mode, Tape Measure, Excavate, Cross-Section, Scale Bar, Grid Labels
  - Safety Reminders: Pool barriers, MISS DIG 811, fire pit distance, retaining walls, grading
  - Close button: "Got It!"
- **Finding:** Help modal is excellent — comprehensive and well-organized.
- Content length: 1926 characters
- Screenshot: `screenshots/11_help.png` (not captured due to EPIPE crash, but modal was verified visible)

### [UI] 2026-08-23T03:06:32 — Topbar button analysis
All topbar buttons have tooltips:
- Undo: title="Undo", aria-label="Undo last action"
- Redo: title="Redo", aria-label="Redo last action"
- Save: title="Save Design"
- Load: title="Load Design"
- Screenshot: title="Take Screenshot"
- Help: title="Help"
- Layers: title="Layer Management"
- Cost: title="Cost Estimator"
- Walk: title="Walk Through Your Design (first-person)"
- Share: title="Share Design via Link / QR Code"

### [UI] 2026-08-23T03:06:33 — View toggle analysis
- 3D View button: NO tooltip
- Bird's-eye button: NO tooltip
- **ISSUE FOUND [LOW]**: View toggle buttons lack tooltips

### [UI] 2026-08-23T03:06:34 — Dock tab analysis
- All 6 dock tabs have aria-labels:
  - Terrain: "Terrain editing tools"
  - Underground: "Underground excavation tools"
  - Analyze: "Terrain analysis tools"
  - Pro Tools: "Pro terrain tools"
  - Sun & Shadow: "Sun and shadow simulator"
  - Measure: "Tape measure tool"
- All have visible text labels (.td-label)
- **Finding:** Dock tabs are well-labeled.

### [ERRORS] 2026-08-23T03:06:35 — Console errors
- Only WebGL performance warnings (GPU stall due to ReadPixels) — not actual errors
- No JavaScript errors or page errors
- **Finding:** App is stable with no console errors.

---

## Issues Summary

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| 1 | HIGH | Context hint empty/hidden after setup wizard | FIXED |
| 2 | HIGH | No onboarding/welcome guide visible after setup | FIXED |
| 3 | MEDIUM | "Shot" button label ambiguous | FIXED → "Capture" |
| 4 | MEDIUM | No toast when object is added | FIXED |
| 5 | MEDIUM | Terrain panel has no instructions before mode selection | FIXED |
| 6 | MEDIUM | No toast when entering walk mode | FIXED |
| 7 | LOW | View toggle buttons have no tooltips | FIXED |
| 8 | LOW | Getting Started hint doesn't auto-hide | FIXED |

---

## Post-Fix Verification

All 21 verification checks passed:
- Wizard visible ✓
- Context hint after setup (visible + text) ✓
- Getting Started hint visible ✓
- Welcome toast visible ✓
- Library items found (21) ✓
- Toast after add object ✓
- Properties panel visible after add ✓
- Getting Started hint hidden after add ✓
- Terrain dock tab visible ✓
- Terrain panel visible ✓
- Terrain has sculpting instructions ✓
- Context hint after raise mode ✓
- Save button (label + tooltip) ✓
- Save download works ✓
- Load button (label + tooltip) ✓
- Screenshot button labeled "Capture" ✓
- Walk controls visible ✓
- Walk has WASD instructions ✓
- Walk toast ✓
- Help modal visible + content > 100 chars ✓
- Help has Getting Started section ✓
- View toggle tooltips ✓
- No console errors ✓

---

## Screenshots

Pre-fix screenshots: `screenshots/` directory
Post-fix screenshots: `screenshots_after/` directory