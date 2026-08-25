# DISCOVERY LOG — Sprint 17, Agent 4: Visual Polish & Consistency

## Audit Date: 2026-08-24

## 1. CSS Design Token Audit

### :root Token Block Issues
- **DUPLICATE: `--shadow`** — defined at L18 (`0 2px 8px rgba(0,0,0,0.08)`) and re-defined at L31 (`var(--shadow-sm)`), overriding itself
- **DUPLICATE: `--radius-sm`** — defined at L21 (`6px`) and re-defined at L32 (`var(--radius-panel)`), overriding itself
- **Redundant aliases:** `--shadow` = `--shadow-sm` (identical values), `--radius-sm` = `--radius-panel` (both 6px), `--panel-bg` = `--panel-bg-96` (both rgba(255,255,255,0.96))
- **19 UNUSED TOKENS** (dead code in :root): `--btn-font-size`, `--btn-padding`, `--btn-radius`, `--close-font-size`, `--control-padding`, `--font-body`, `--font-heading`, `--font-label`, `--modal-radius`, `--panel-bg`, `--panel-padding`, `--radius-button`, `--text-light`, `--toggle-on`, `--water`, `--z-modal`, `--z-overlay`, `--z-panel`, `--z-toast`
- **2 blank lines** in :root block (L48-49) — cosmetic noise

### Hardcoded Colors in CSS (not using tokens)
- `rgba(45,45,45,0.85)` in `#context-hint` — should use dark overlay token
- `rgba(45,45,45,0.9)` in `#measure-readout` — should use dark overlay token
- `rgba(0,0,0,0.7)` in `#walk-hint` — should use modal backdrop token
- `rgba(0,0,0,0.6)` in `#tour-backdrop`, `#tour-spotlight`, `#atmosphere-badge`, `.templates-confirm` — should use modal backdrop token
- `rgba(220,53,53,0.92)` in `#walk-exit` — hardcoded red, should use `--danger`
- `rgba(180,40,40,0.95)` in `#walk-exit:hover` — hardcoded dark red
- `rgba(61,117,73,0.15)` in focus ring `box-shadow` — hardcoded primary color
- `background: white` in ~20+ CSS rules — should use `var(--surface)`
- `border-radius: 16px` in `.wizard-panel`, `.help-panel` — should use `var(--radius)` (10px)
- `border-radius: 8px` in `#ctx-tooltip`, `#share-qr-canvas`, `#share-url-box`, `#print-view .print-screenshot img` — should use `var(--radius-sm)` (6px)
- `border-radius: 20px` in `#context-hint`, `#sculpt-restore-pill`, `#onboarding-restart-btn`, `#grid-level-badge`, `#atmosphere-badge`, `.recent-chip`, `#batch-bar button` — should use `--radius-pill` (20px)
- `border-radius: 16px` in `.recent-chip` — should use `--radius-pill`

## 2. Panel Header Inconsistencies

### Two Different Patterns Found:
**Group A (dock/excavate/cs/innov):**
- margin-bottom: 4px, padding-bottom: 6px
- title font-size: 13px, close font-size: 16px (dock: 18px)

**Group B (cost/layer/season/growth/permit):**
- margin-bottom: 10px (layer: 8px), padding-bottom: 8px (layer: 6px)
- title font-size: 14px (layer: 13px), close font-size: 18px (layer: 16px)

### Inconsistencies within groups:
- `dock-panel-header` close: 18px (exception in Group A)
- `layer-panel-header`: mixed values from both groups
- `excavate-header`, `cs-header`, `innov-header` close: 16px (vs dock's 18px)
- `cost/season/growth/permit` title: 14px (vs dock's 13px)
- `terrain-controls-header`: margin-bottom 4px, padding-bottom 6px (Group A style)
- `dock-panel-header .minimize`: 16px (vs close at 18px)

## 3. Focus-Visible Outlines
- Global `*:focus-visible` at L644: `outline: 2px solid var(--primary); outline-offset: 2px`
- Specific overrides at L646-648: white outline for primary/active buttons
- Animated focus rings at L1217-1232: `box-shadow: 0 0 0 4px rgba(61,117,73,0.15)` — hardcoded color
- Individual `.cat-title` and `.lib-item` focus-visible at L111, L118: `outline-offset: -2px` (inset)
- **Inconsistency:** Global uses `outline-offset: 2px` (outset), but cat-title/lib-item use `-2px` (inset)

## 4. Topbar Layout
- 6 dividers separating 7 groups — properly organized
- Brand on left, spacer, then grouped toolbar sections
- Each group has logical grouping (undo/redo, view toggle, file ops, view/analysis, export/share, community, planning)
- Layout looks clean and uncluttered at 1280px
- No duplicate or unnecessary separators found

## 5. Tool Dock Appearance
- 7 tabs across 3 groups (Sculpt: 3 tabs, Build: 1 tab, View: 3 tabs)
- Group labels: 9px, 700 weight, uppercase — readable
- Tab labels: 12px, 400 weight (should be 600 per CSS but computed shows 400 due to .td-label class)
- Active state: primary green background — clear
- Icons: 18x18px — aligned
- Background: rgba(255,255,255,0.95) — should use `var(--panel-bg-95)` token but acceptable

## 6. Mobile Artifacts (Leftover)
- **Comment only:** `/* Mobile usability fixes */` at L1014 — no rules, dead comment
- **Comment only:** `/* Mobile adjustments */` at L1154 — no rules, dead comment
- **Dead HTML element:** `#walk-hint-mobile` at L2661 — never displayed, `display:none` inline style
- **Dead JS code:** Reference to `walk-hint-mobile` in JS at L8652-8657 — guarded by `if (false && ...)`
- **Dead constant:** `IS_MOBILE = false` — referenced nowhere in conditionals
- **Dead function:** `_showMobileContextMenu()` — exists but never called from live code path

## 7. Toasts, Tooltips, Floating Messages
- `#toast`: uses `var(--text-dark)` ✓ (now resolves to `var(--text)`)
- `#measure-readout`: hardcoded `rgba(45,45,45,0.9)` — fixed to `var(--dark-overlay)`
- `#context-hint`: hardcoded `rgba(45,45,45,0.85)`, `border-radius: 20px` — fixed
- `#walk-hint`: hardcoded `rgba(0,0,0,0.7)`, `border-radius: 20px` — fixed
- `#ctx-tooltip`: `border-radius: 8px` — fixed to `var(--radius-sm)`
- `#progressive-hint`: `border-radius: 24px` — intentional larger pill, left as-is
- `#onboarding-restart-btn`: `border-radius: 20px` — fixed to `var(--radius-pill)`

## 8. Onboarding/Intro Panel
- `#wizard` / `.wizard-panel`: uses `border-radius: 16px` (hardcoded) and `background: white` — fixed to `var(--radius)` and `var(--surface)`
- `#welcome-prompt` / `.welcome-prompt-panel`: uses `box-shadow: 0 20px 60px rgba(0,0,0,0.3)` (intentional large shadow)
- `.help-panel`: `border-radius: 16px` and `background: white` — fixed
- Welcome prompt quick action buttons: `background: white` — fixed to `var(--surface)`

## 9. Button Style Patterns
Multiple button patterns found with varying padding/font-size/border-radius:
- `.tb-btn`: 7px 12px, 13px, `var(--radius-sm)` — topbar buttons (consistent)
- `.view-toggle button`: 5px 14px, 13px, 4px — view toggle (unique, acceptable)
- `.terrain-mode-btn`: 7px 10px, 11px, `var(--radius-sm)` — terrain buttons
- `.excavate-btns button`: 6px 8px, 11px, `var(--radius-sm)` — excavate buttons
- `.ta-btn`: 6px 10px, 11px, `var(--radius-sm)` — analysis buttons
- `.prop-actions button`: 8px, 13px, `var(--radius-sm)` — property buttons
- `.share-actions button`: 9px 18px, 13px, `var(--radius-sm)` — share buttons
- `.innov-btns button`: 7px 8px, 11px, `var(--radius-sm)` — innovation buttons
- `.wizard-btn`: 12px 32px, 15px, `var(--radius-sm)` — wizard button

**Assessment:** Button sizes vary by context (topbar vs panels vs modals), which is acceptable. All use `var(--radius-sm)` for border-radius. The size differences are intentional — topbar buttons are larger than compact panel buttons.

## 10. Screenshots Taken
### Pre-fix (1280x800):
- 01-wizard.png, 02-main-app.png, 03-terrain-panel.png, 04-analyze-panel.png
- 05-sun-panel.png, 06-innovate-panel.png, 07-cost-panel.png, 08-layer-panel.png
- 09-season-panel.png, 10-growth-panel.png, 11-welcome-prompt.png, 12-templates-modal.png

### Post-fix (1280x800):
- Same set of screenshots in screenshots/post-fix/
- 0 JS errors confirmed
- All panel headers now have identical computed styles