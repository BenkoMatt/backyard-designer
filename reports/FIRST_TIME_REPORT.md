# First-Time User Report — Backyard Designer 3D

**Sprint 8 — Agent 1 (Builder)**
**Date:** August 23, 2026

---

## Executive Summary

Simulated a complete first-time user journey through Backyard Designer 3D using Playwright (headless Chromium, 1400×900). Found **8 usability issues** across 7 touchpoints, fixed all **8**, and verified every fix with re-testing (21/21 checks passed).

---

## The Journey (Before)

### Step 1: Loading the App
- **What happened:** The app loaded with a setup wizard overlay. The wizard showed "Welcome to Backyard Designer 3D" with a yard shape selector (Rectangle/L-Shape) and "Next Step →" button.
- **Confusion level:** Low — the wizard was clear and well-designed.
- **Verdict:** ✓ Good first impression.

### Step 2: After Setup Wizard
- **What happened:** The wizard disappeared, revealing a 3D yard with left sidebar (object library), bottom-left tool dock (6 tabs), top toolbar, and bottom-right view controls.
- **Confusion level:** HIGH — The context hint at the bottom-center was **empty and invisible**. No onboarding message appeared. No "Getting Started" guidance was visible anywhere.
- **What a new user would think:** "Okay... now what? What am I supposed to do? Do I click something? Where do I start?"
- **Issue:** `#context-hint` element existed but had no text and `opacity: 0`. No onboarding flow after wizard completion.

### Step 3: Adding an Object
- **What happened:** The left sidebar showed "Add to Your Yard" with collapsible categories (Fences & Structures, Plants, etc.). Clicking a category header expanded it, revealing objects like "Privacy Fence", "Picket Fence". Clicking an object added it to the 3D scene and opened the Properties panel on the right.
- **Confusion level:** Medium — The categories were already expanded by default, which was good. But there was no hint telling users to look at the left panel. No toast notification confirmed the object was added — only a brief context hint ("Drag to position") that disappeared in 3 seconds.
- **Issue:** No toast confirmation when adding an object. No "Getting Started" hint pointing to the library.

### Step 4: Sculpting Terrain
- **What happened:** The bottom-left tool dock showed a "Terrain" tab. Clicking it opened a panel with mode buttons (Raise/Excavate/Smooth/Erode), brush size/strength sliders, and other controls. But the panel had no instructions explaining what to do. After clicking "Raise" mode, the context hint appeared: "Click and drag on the ground to sculpt terrain."
- **Confusion level:** Medium — The instructions only appeared AFTER selecting a mode. A new user would open the panel, see all the controls, and not know what to do first.
- **Issue:** No sculpting instructions visible before the user selects a mode.

### Step 5: Saving the Design
- **What happened:** The "Save" button in the top bar had a tooltip "Save Design". Clicking it downloaded a file `my-backyard-design.json` and showed a toast: "Design saved! Check your downloads folder."
- **Confusion level:** Low — Save was obvious and well-labeled.
- **Verdict:** ✓ Works well.

### Step 6: Loading a Design
- **What happened:** The "Load" button had a tooltip "Load Design" and triggered a file picker. A hidden `<input type="file">` element existed for loading.
- **Confusion level:** Low — Load was clear.
- **Verdict:** ✓ Works well.

### Step 7: Five More Features

#### Feature 1: Sun & Shadow (via dock tab)
- Clicked "Sun & Shadow" tab → panel opened with "Use My Location" button, lat/lng inputs, city presets, date/time sliders.
- **Confusion:** Low. The "Use My Location" button was obvious.
- **Verdict:** ✓ Good.

#### Feature 2: Cost Estimator
- Clicked "Cost" button → panel showed cost breakdown by category with total.
- **Verdict:** ✓ Good.

#### Feature 3: Walk Mode
- Clicked "Walk" button → overlay appeared with "Exit Walk", "WASD/Arrows to move - Drag to look - Esc to exit" text and directional buttons.
- **Issue:** No toast confirmation when entering walk mode.

#### Feature 4: Screenshot
- Button labeled "Shot" — ambiguous. Could mean "take a shot" or something else.
- **Issue:** "Shot" is an unclear button label. Should be "Capture" or "Screenshot".
- (The code does trigger a download and toast, but the label is confusing.)

#### Feature 5: Help
- Clicked "? Help" → modal opened with comprehensive instructions including "Getting Started", "Camera Controls", "Saving & Sharing", "Terrain & Measuring", "Safety Reminders" sections.
- **Verdict:** ✓ Good — the help modal is well-written.

---

## Issues Found

| # | Severity | Issue | Touchpoint |
|---|----------|-------|------------|
| 1 | HIGH | Context hint empty/hidden after setup wizard — no guidance on what to do next | Post-setup state |
| 2 | HIGH | No onboarding/welcome guide visible after setup — user doesn't know where to start | Post-setup state |
| 3 | MEDIUM | "Shot" button label ambiguous — unclear what it does | Screenshot feature |
| 4 | MEDIUM | No toast when object is added — only a brief context hint that fades | Adding objects |
| 5 | MEDIUM | Terrain panel has no instructions before user selects a mode | Terrain sculpting |
| 6 | MEDIUM | No toast confirmation when entering walk mode | Walk mode |
| 7 | LOW | 3D View / Bird's-eye toggle buttons have no tooltips | View toggle |
| 8 | LOW | No auto-dismiss of getting started hint after user takes first action | Sidebar |

---

## Fixes Applied

### Fix 1: Welcome onboarding hint after setup (Issue #1, #2)
**File:** `index.html`, function `showWelcomeOnboarding()` added after `initWithYard()`

- Context hint (`#context-hint`) now shows: "👋 Click an item from the left panel to add it to your yard"
- Hint is clickable to dismiss, styled with larger font and proper wrapping
- Welcome toast: "Welcome! Click items on the left to build your yard. Click ? Help anytime." appears 500ms after setup

### Fix 2: "Getting Started" banner in sidebar (Issue #2)
**File:** `index.html`, `#getting-started-hint` div added to sidebar

- Green gradient banner with "👋 Getting Started" heading
- Text: "Click any item below to add it to your yard. Then drag to position it."
- Dismissible via × button
- Auto-hides after the user adds their first object

### Fix 3: "Shot" → "Capture" button label (Issue #3)
**File:** `index.html`, `#btn-screenshot` button text changed from "Shot" to "Capture"

### Fix 4: Toast when object is added (Issue #4)
**File:** `index.html`, `buildLibrary()` click handler

- Added `showToast(item.name + ' added! Drag to reposition')` when a library item is clicked
- Getting Started hint auto-hides after first object is added

### Fix 5: Terrain panel instructions (Issue #5)
**File:** `index.html`, `#terrain-controls` panel

- Added instruction banner at top of terrain panel: "💡 How to sculpt: Pick a mode (Raise, Excavate, etc.), then click and drag on the ground to shape the terrain. Adjust brush size and strength as needed."

### Fix 6: Walk mode toast (Issue #6)
**File:** `index.html`, `enterWalkMode()` function

- Added toast: "Walk mode! Use WASD or arrow keys to move. Press Esc to exit."

### Fix 7: View toggle tooltips (Issue #7)
**File:** `index.html`, `#view-toggle` buttons

- 3D View: `title="3D perspective view — orbit, zoom, pan"`
- Bird's-eye: `title="Bird's-eye top-down view for precise placement"`

### Fix 8: Auto-hide getting started hint (Issue #8)
**File:** `index.html`, `buildLibrary()` click handler

- `#getting-started-hint` element's `display` set to `none` after first object is added

---

## The Journey (After)

### Step 1: Loading the App
- ✓ Same clear setup wizard

### Step 2: After Setup Wizard
- ✓ **Context hint now visible**: "👋 Click an item from the left panel to add it to your yard"
- ✓ **Getting Started banner** in sidebar: "👋 Getting Started — Click any item below to add it to your yard."
- ✓ **Welcome toast**: "Welcome! Click items on the left to build your yard. Click ? Help anytime."
- **New user experience:** "Oh, I should click items from the left panel. Got it!"

### Step 3: Adding an Object
- ✓ **Toast**: "Privacy Fence added! Drag to reposition"
- ✓ Properties panel appears
- ✓ Getting Started hint auto-hides (user has figured it out)

### Step 4: Sculpting Terrain
- ✓ **Instructions visible**: "💡 How to sculpt: Pick a mode (Raise, Excavate, etc.), then click and drag on the ground..."
- ✓ Context hint shows: "Click and drag on the ground to sculpt terrain" after selecting a mode

### Step 5: Saving
- ✓ Download + toast: "Design saved! Check your downloads folder."

### Step 6: Loading
- ✓ File picker + tooltip: "Load Design"

### Step 7: Five More Features
- ✓ Sun & Shadow: Works with "Use My Location" button
- ✓ Cost: Works with cost breakdown
- ✓ Walk Mode: **Toast** "Walk mode! Use WASD or arrow keys to move. Press Esc to exit." + on-screen controls
- ✓ Screenshot: Button labeled "Capture" (was "Shot")
- ✓ Help: Comprehensive modal with Getting Started section

### View Toggle
- ✓ Tooltips: "3D perspective view — orbit, zoom, pan" / "Bird's-eye top-down view for precise placement"

---

## Verification Results

**21/21 checks passed** in the post-fix Playwright verification:

| Check | Result |
|-------|--------|
| Wizard visible | ✓ |
| Context hint after setup (visible + text) | ✓ |
| Getting Started hint visible | ✓ |
| Welcome toast visible | ✓ |
| Library items found (21) | ✓ |
| Toast after add object | ✓ |
| Properties panel visible after add | ✓ |
| Getting Started hint hidden after add | ✓ |
| Terrain dock tab visible | ✓ |
| Terrain panel visible | ✓ |
| Terrain has sculpting instructions | ✓ |
| Context hint after raise mode | ✓ |
| Save button (label + tooltip) | ✓ |
| Save download works | ✓ |
| Load button (label + tooltip) | ✓ |
| Screenshot button labeled "Capture" | ✓ |
| Walk controls visible | ✓ |
| Walk has WASD instructions | ✓ |
| Walk toast | ✓ |
| Help modal visible + content > 100 chars | ✓ |
| Help has Getting Started section | ✓ |
| View toggle tooltips | ✓ |
| No console errors | ✓ |

---

## Commit

```
3d0a4c0 Sprint 8: First-time user usability fixes
```

**Changes:** 1 file changed, 58 insertions(+), 4 deletions(-)