# Sprint 9 — Onboarding Architect: Discovery Log

## Agent
Agent 2 (Builder) — The Onboarding Architect

## Date
2026-08-23

## Working Directory
/root/byd9-onboarding/

---

## 1. Feature Inventory Review

Read `FEATURE_INVENTORY.md` — comprehensive list of all UI elements, panels, and features.

Key findings:
- **Top bar**: Undo/Redo, View toggle, Save/Load, Screenshot, Help, Layers, Cost, Walk, Share
- **Left sidebar**: Object Library (categorized, collapsible)
- **Right sidebar**: Object Properties (size, rotation, position, duplicate, delete)
- **Tool dock**: Terrain, Tape Measure, Sun, Excavate, Analyze, Innovate (6 floating buttons)
- **Terrain controls**: 20+ controls (brush modes, presets, carving, overlays)
- **Innovation panel**: 12 advanced tools (pool wizard, ADA slope, geology, etc.)
- **Modals**: Setup wizard, Help dialog, Share/QR, Walk mode controls
- **Problem areas**: 6 floating buttons with hardcoded positions, mega-panels with no progressive disclosure, overlapping panel positions

---

## 2. Current Onboarding Audit

### What Exists (Sprint 8 and earlier)

#### Setup Wizard (`#wizard`)
- **Location**: Lines 5325-5413 in JS, line 2308 in HTML
- **Functionality**: 2-step wizard — Step 1: choose yard shape (rectangle/L-shape), Step 2: enter dimensions
- **Skip option**: "Skip — use default yard" button at bottom
- **Continue previous**: Offers to restore previous design from localStorage autosave
- **Assessment**: Functional but limited. Only covers yard setup, not the rest of the app.

#### Getting Started Hint (`#getting-started-hint`)
- **Location**: Line 1365 in HTML
- **Content**: "👋 Getting Started — Click any item below to add it to your yard. Then drag to position it."
- **Close button**: `#getting-started-close` × button
- **Auto-hide**: Hides after first object is added (line 4864)
- **Assessment**: Static text hint. Not interactive, no progressive disclosure, no tracking.

#### Help Modal (`#help-modal`)
- **Location**: Line 2414 in HTML
- **Content**: Comprehensive guide with sections: Getting Started, Camera Controls, Saving & Sharing, Terrain & Measuring, Keyboard Shortcuts, Advanced Features
- **Close**: "Got It!" button, Escape key, click outside
- **Accessibility**: `role="dialog"`, `aria-modal`, focus management
- **Assessment**: Good reference but passive — user must click Help to find it. No contextual guidance.

#### Welcome Onboarding (`showWelcomeOnboarding()`)
- **Location**: Line 5523 in JS
- **Content**: Shows a persistent hint in the context-hint element ("👋 Click an item from the left panel...") and a toast after 500ms
- **Assessment**: Minimal — just a hint and a toast. No guided tour, no tracking, no progressive disclosure.

### What's Missing

1. **No guided tour** — no sequential walkthrough of key features
2. **No contextual tooltips** — no hover tooltips explaining what buttons do
3. **No feature discovery badges** — no "New!" indicators for features the user hasn't used
4. **No "What would you like to do?" prompt** — no quick-start options (template, scratch, import)
5. **No progressive hint system** — no inactivity-based hints
6. **No "Skip tour" / "Remind me later"** — no granular dismissal options
7. **No localStorage tracking** — onboarding state not persisted across sessions
8. **No restart option** — no way to redo the tour after completing it

---

## 3. Implementation

### Architecture

Implemented a comprehensive `Onboarding` IIFE module exposed on `window.Onboarding` for Playwright test access. All state tracked in localStorage key `backyard-onboarding-state`.

### Components Implemented

#### 3.1 Welcome Prompt Modal (`#welcome-prompt`)
- **Trigger**: Appears automatically after wizard completes (MutationObserver on `#wizard` style)
- **Content**: "What would you like to do?" with 4 quick actions:
  - 📋 Start with a template — pre-made designs to customize
  - ✨ Start from scratch — empty yard, full creative control
  - 📂 Import a design — load a previously saved design file
  - 🎓 Take a guided tour — learn the basics in 2 minutes
- **Remind me later**: Dismisses prompt, resets `welcomeShown` so it can appear again
- **Escape**: Closes prompt via keyboard
- **Accessibility**: `role="dialog"`, `aria-modal`, focus management, aria-labelledby

#### 3.2 Guided Tour (`#tour-overlay`)
- **6 steps in sequence**:
  1. Welcome — intro message
  2. Set Up Your Yard — highlights `#topbar`
  3. Add Objects — highlights `#library`
  4. Sculpt Terrain — highlights `#tool-dock`
  5. Object Properties — highlights `#properties`
  6. Save Design — highlights `#btn-save`
- **Spotlight**: CSS box-shadow creates a cutout around the target element
- **Bubble**: Positioned below/above the target with viewport clamping
- **Navigation**: Next →, Back, Skip tour, Finish ✓
- **Progress dots**: Visual indicator of current step
- **Resize handling**: Repositions on window resize
- **Completion toast**: "🎉 Tour complete! You're ready to design your backyard."
- **localStorage**: Tracks `tourCompleted` and `completedSteps[]`

#### 3.3 Contextual Tooltips (`#ctx-tooltip`)
- **12 tooltip zones** on key UI elements:
  - `#library` — "Click any item to add it to your yard"
  - `#btn-save` — "Save your design as a file"
  - `#btn-load` — "Load a previously saved design"
  - `#btn-help` — "Open the help guide for all features"
  - `#btn-screenshot` — "Capture a PNG image of your view"
  - `#btn-cost` — "See cost estimates for your design"
  - `#btn-walk` — "Explore your yard in first-person mode"
  - `#btn-share` — "Share your design via QR code or link"
  - `#btn-undo` — "Undo your last action"
  - `#btn-redo` — "Redo an undone action"
  - `#properties` — "Adjust size, rotation, and position of selected objects"
  - `#tool-dock` — "Sculpt terrain, measure, and more"
- **Trigger**: 400ms hover delay
- **Positioning**: Smart positioning with viewport clamping, arrow indicator
- **Suppression**: Hidden during active tour

#### 3.4 Feature Discovery Badges (`.discovery-badge`)
- **7 badgeable features**: Walk Mode, Share, Command Palette, Layers, Terrain Analysis, Innovation, Cross-Section
- **Badge**: Orange "New!" pill badge with pulse animation
- **Placement**: Added to the parent element of the target button
- **Removal**: Badge removed when the feature is used
- **Tracking**: `featuresUsed` object in localStorage tracks which features have been interacted with

#### 3.5 Progressive Hint System (`#progressive-hint`)
- **Trigger**: 5 seconds of inactivity (mousemove, click, keydown, touchstart, scroll)
- **Content**: 6 rotating tips:
  1. Click an item in the left panel to add it to your yard
  2. Click and drag on the ground with Terrain tools to sculpt the surface
  3. Press Ctrl+K to open the command palette and search any feature
  4. Click Walk Mode to explore your yard in first-person
  5. Use the Cost Estimator to see material costs for your design
  6. Click Save to download your design, or use Share for a QR code link
- **Dismissal**: Disappears on any interaction (mousemove, click, keydown, etc.)
- **Filtering**: Only shows tips for features the user hasn't used yet
- **Visual**: Gradient purple pill with slide-up animation

#### 3.6 Restart Button (`#onboarding-restart-btn`)
- **Visibility**: Shows after tour completes or when tour was previously completed
- **Action**: Clicking restarts the guided tour from step 1
- **Position**: Fixed bottom-right, doesn't interfere with view controls

#### 3.7 localStorage Tracking
- **Key**: `backyard-onboarding-state`
- **Schema**:
```json
{
  "completedSteps": ["welcome", "yard-setup", "add-object", ...],
  "tourCompleted": true/false,
  "welcomeShown": true/false,
  "dismissedAt": 0,
  "featuresUsed": { "library": true, "terrain": true, ... },
  "remindLaterAt": 1692806400000
}
```

---

## 4. Bugs Found & Fixed

### Bug 1: Old welcome toast interfering with new onboarding
- **Issue**: `showWelcomeOnboarding()` at line 5709 shows a toast after 500ms that interferes with the new welcome prompt
- **Fix**: Added check — if `#welcome-prompt` is visible, skip the old toast
- **Lines modified**: 5744-5749

### Bug 2: Onboarding not accessible from outside ES module
- **Issue**: `const Onboarding` was module-scoped, not on `window`, so Playwright tests couldn't access it
- **Fix**: Added `window.Onboarding = {...}` assignment in the IIFE return
- **Lines modified**: 15415-15428

### Bug 3: Welcome prompt not appearing after wizard
- **Issue**: Event delegation approach for detecting wizard completion was unreliable
- **Fix**: Replaced with `MutationObserver` on `#wizard` element's `style` attribute
- **Lines modified**: 15430-15450

---

## 5. Testing

### Playwright Test Suite (`test_onboarding.py`)
- **29 tests**, all passing
- **Fresh browser context** for each test (no localStorage = first-time user)
- **Test coverage**:
  - Page loads without JS errors ✅
  - Setup wizard appears ✅
  - Wizard can be skipped ✅
  - Welcome prompt appears after wizard ✅
  - Welcome prompt has 4 quick actions ✅
  - Quick action labels correct ✅
  - Tour overlay appears ✅
  - Tour shows step indicator ✅
  - Tour has title text ✅
  - Tour advances through all 6 steps ✅
  - Tour completion shows confirmation ✅
  - Tour overlay hidden after completion ✅
  - Restart tour button visible after completion ✅
  - localStorage tracks tour completion ✅
  - Contextual tooltip element exists ✅
  - Progressive hint element exists ✅
  - Restart tour button reopens tour ✅
  - Skip tour button exists ✅
  - Skip tour closes overlay ✅
  - Progressive hint system initialized ✅
  - Back button visible on step 2+ ✅
  - Back button returns to previous step ✅
  - Feature discovery badges present ✅
  - "Remind me later" button exists ✅
  - "Remind me later" closes welcome prompt ✅
  - "Remind me later" shows helpful toast ✅
  - Progressive hint can be triggered ✅
  - Progressive hint disappears on interaction ✅
  - Contextual tooltip appears on hover ✅

---

## 6. Files Modified

| File | Lines | Change |
|------|-------|--------|
| index.html | 1230-1369 | Added ~140 lines of CSS for onboarding components |
| index.html | 1385-1434 | Added ~50 lines of HTML for onboarding overlay elements |
| index.html | 5744-5749 | Fixed old welcome toast to not conflict with new onboarding |
| index.html | 14854-15461 | Added ~610 lines of JS for complete onboarding system |
| test_onboarding.py | new | 29-test Playwright suite |
| debug_onboarding.py | new | Debug script (not part of deliverables) |

**Total lines added to index.html**: ~800 lines (CSS + HTML + JS)
**Final index.html size**: 15,464 lines (was 14,663)

---

## 7. Onboarding Flow Summary

### First-Time User Experience (60-second path)

1. **Page loads** → Setup wizard appears (yard shape + dimensions)
2. **Wizard completes** (click "Start Designing!" or "Skip") → Welcome prompt appears
3. **User chooses**:
   - **Template** → Toast guides to wizard, progressive hints start
   - **From scratch** → Toast "Your empty yard is ready!", progressive hints start
   - **Import** → File picker opens, toast guides
   - **Tour** → 6-step guided tour begins
   - **Remind me later** → Toast, progressive hints start
4. **After tour** → Completion toast, restart button appears, progressive hints start
5. **During use** → Contextual tooltips on hover, progressive hints after 5s inactivity
6. **Feature discovery** → "New!" badges on unused features, removed on first use

### Return User Experience

- **Tour completed before** → Restart button visible, no welcome prompt
- **Tour not completed** → Welcome prompt may appear again (if "Remind me later" was used)
- **Progressive hints** → Only shows tips for unused features
- **Badges** → Only shows for unused features

---

## 8. Accessibility

- All onboarding elements have appropriate ARIA roles (`dialog`, `tooltip`, `status`)
- `aria-modal` on welcome prompt and tour overlay
- `aria-hidden` management on show/hide
- `aria-live="polite"` on tour bubble and progressive hint
- `aria-label` on discovery badges and restart button
- Keyboard support: Escape closes all onboarding overlays
- Focus management: Welcome prompt focuses first action button
- `prefers-reduced-motion`: Disables animations for reduced motion users
- Mobile responsive: Adjusted padding, max-width for small screens

---

## 9. Constraints Met

- ✅ Work only in `/root/byd9-onboarding/`
- ✅ Didn't break existing features (all existing onboarding preserved, just enhanced)
- ✅ Three.js v0.160.0 via importmap (unchanged)
- ✅ Single index.html (all code inline)
- ✅ Git commits as Caddy <caddyaibot@gmail.com>

---

## 10. Notes

- The old `showWelcomeOnboarding()` function is still called but now checks if the new welcome prompt is visible before showing its toast
- The old getting-started hint is preserved as a secondary onboarding cue
- The help modal is preserved as a comprehensive reference
- The setup wizard is preserved as the yard configuration tool
- All new onboarding code is namespaced under the `Onboarding` module
- Progressive hints use a 5-second inactivity timer (per spec)
- Feature tracking is non-intrusive (uses `{ once: true }` event listeners where possible)