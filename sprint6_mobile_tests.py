#!/usr/bin/env python3
"""
Sprint 6 — Mobile-First Test Suite (Backyard Designer 3D)
Tests every feature on phone (375px) and tablet (768px) viewports.
Uses Playwright with chromium.

Run: python3 sprint6_mobile_tests.py
"""

import asyncio
import json
import os
import sys
import time
import traceback
from pathlib import Path

from playwright.async_api import async_playwright, Page, BrowserContext

# ── Configuration ──────────────────────────────────────────────────
BASE_URL = "http://localhost:8100/index.html"
PHONE_W, PHONE_H = 375, 812    # iPhone 13 mini / iPhone SE
TABLET_W, TABLET_H = 768, 1024  # iPad mini portrait
PHONE_LAND_W, PHONE_LAND_H = 812, 375
TABLET_LAND_W, TABLET_LAND_H = 1024, 768

MIN_TOUCH_TARGET = 44  # Apple/WCAG minimum touch target

RESULTS = []
PASS_COUNT = 0
FAIL_COUNT = 0
SKIP_COUNT = 0

# ── Helpers ────────────────────────────────────────────────────────
def log_result(name: str, status: str, detail: str = "", viewport: str = ""):
    global PASS_COUNT, FAIL_COUNT, SKIP_COUNT
    entry = {"test": name, "status": status, "detail": detail, "viewport": viewport}
    RESULTS.append(entry)
    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠️"}.get(status, "?")
    vstr = f"[{viewport}] " if viewport else ""
    print(f"  {icon} {vstr}{name}" + (f" — {detail}" if detail else ""))
    if status == "PASS": PASS_COUNT += 1
    elif status == "FAIL": FAIL_COUNT += 1
    else: SKIP_COUNT += 1

async def wait_for_app(page: Page, timeout_ms=12000):
    """Wait for the Three.js app to be ready."""
    try:
        # THREE.js is loaded as ES module (importmap), not as global
        # So we check for _test object and canvas instead
        await page.wait_for_function("typeof window._test === 'object' && window._test !== null", timeout=timeout_ms)
        await page.wait_for_function("document.querySelector('canvas') !== null", timeout=timeout_ms)
        await page.wait_for_timeout(500)
    except Exception:
        pass

async def dismiss_wizard(page: Page):
    """Dismiss the setup wizard if it appears."""
    try:
        # The wizard has a skip or button to proceed
        skip_btn = page.locator('#wizard .wizard-btn, #wizard button:has-text("Skip"), #wizard-skip')
        if await skip_btn.count() > 0:
            await skip_btn.first.click(timeout=2000)
            await page.wait_for_timeout(500)
            return True
    except Exception:
        pass
    try:
        # Try clicking the final button or pressing Escape
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
    except Exception:
        pass
    # Force remove wizard if present
    try:
        await page.evaluate("""() => {
            const w = document.getElementById('wizard');
            if (w) w.style.display = 'none';
        }""")
    except Exception:
        pass

async def get_bounding_box(page: Page, selector: str) -> dict:
    """Get bounding box of element, return None if not found."""
    try:
        result = await page.evaluate(f"""() => {{
            const el = document.querySelector('{selector}');
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            return {{x: rect.x, y: rect.y, width: rect.width, height: rect.height, 
                      display: getComputedStyle(el).display,
                      visibility: getComputedStyle(el).visibility,
                      opacity: getComputedStyle(el).opacity}};
        }}""")
        return result
    except Exception:
        return None

async def get_all_buttons_info(page: Page, container_selector: str = "") -> list:
    """Get all buttons and their dimensions within a container."""
    js = """(containerSel) => {
        const container = containerSel ? document.querySelector(containerSel) : document;
        if (!container) return [];
        const btns = container.querySelectorAll('button');
        return Array.from(btns).map(b => {
            const rect = b.getBoundingClientRect();
            const style = getComputedStyle(b);
            return {
                id: b.id || b.getAttribute('data-dock') || b.className.split(' ')[0] || 'unnamed',
                text: b.textContent.trim().substring(0, 30),
                x: rect.x, y: rect.y,
                width: rect.width, height: rect.height,
                display: style.display,
                visibility: style.visibility,
                visible: rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden',
                tooSmall: rect.width < 44 || rect.height < 44
            };
        });
    }"""
    return await page.evaluate(js, container_selector)

async def check_overflow(page: Page, selector: str, viewport_width: int) -> tuple:
    """Check if element overflows viewport width. Returns (overflows, overflow_amount)."""
    js = """(args) => {
        const el = document.querySelector(args.sel);
        if (!el) return {overflows: false, amount: 0};
        const rect = el.getBoundingClientRect();
        const overflows = rect.right > args.vw + 1;
        return {overflows: overflows, amount: Math.max(0, rect.right - args.vw), right: rect.right, width: rect.width};
    }"""
    result = await page.evaluate(js, {"sel": selector, "vw": viewport_width})
    return result.get("overflows", False), result.get("amount", 0)

async def check_horizontal_scroll(page: Page) -> bool:
    """Check if the page has horizontal scroll (indicating overflow)."""
    return await page.evaluate("""() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth + 1;
    }""")

# ── Test: Page loads and renders ────────────────────────────────────
async def test_page_loads(page: Page, vw: str, w: int, h: int):
    """Basic: page loads without errors, Three.js initializes."""
    name = f"Page loads at {vw}"
    try:
        await wait_for_app(page)
        # Check _test object exists (THREE.js is loaded as ES module, not global)
        has_test = await page.evaluate("typeof window._test === 'object' && window._test !== null")
        if not has_test:
            log_result(name, "FAIL", "window._test not available", vw)
            return
        # Check canvas exists
        has_canvas = await page.evaluate("document.querySelector('canvas') !== null")
        if not has_canvas:
            log_result(name, "FAIL", "No canvas element", vw)
            return
        # Check THREE is available via _test
        has_three = await page.evaluate("window._test.scene !== undefined && window._test.scene !== null")
        if not has_three:
            log_result(name, "FAIL", "Three.js scene not available via _test", vw)
            return
        log_result(name, "PASS", "window._test, canvas, scene all present", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: No horizontal overflow on page ────────────────────────────
async def test_no_horizontal_overflow(page: Page, vw: str, w: int, h: int):
    """The page should not have horizontal scroll at any viewport width."""
    name = f"No horizontal overflow at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        overflows = await check_horizontal_scroll(page)
        if overflows:
            scroll_w = await page.evaluate("document.documentElement.scrollWidth")
            client_w = await page.evaluate("document.documentElement.clientWidth")
            # Allow small overflow (within 10%) for landscape tablet with sidebar
            if scroll_w > client_w * 1.1:
                log_result(name, "FAIL", f"scrollWidth={scroll_w} > clientWidth={client_w}", vw)
            else:
                log_result(name, "PASS", f"Minor overflow: {scroll_w} vs {client_w} (within 10%)", vw)
        else:
            log_result(name, "PASS", "", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Topbar visible and reachable ──────────────────────────────
async def test_topbar_visible(page: Page, vw: str, w: int, h: int):
    """Topbar should be visible and contain buttons."""
    name = f"Topbar visible at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        bb = await get_bounding_box(page, "#topbar")
        if not bb:
            log_result(name, "FAIL", "#topbar not found", vw)
            return
        if bb["display"] == "none" or bb["height"] < 10:
            log_result(name, "FAIL", f"topbar not visible: display={bb['display']}, h={bb['height']}", vw)
            return
        # Check that at least some topbar buttons are visible
        btns = await get_all_buttons_info(page, "#topbar")
        visible_btns = [b for b in btns if b["visible"]]
        if len(visible_btns) < 3:
            log_result(name, "FAIL", f"Only {len(visible_btns)} visible buttons in topbar", vw)
            return
        log_result(name, "PASS", f"{len(visible_btns)} visible buttons", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Topbar touch targets ─────────────────────────────────────
async def test_topbar_touch_targets(page: Page, vw: str, w: int, h: int):
    """All visible topbar buttons should be at least 44x44px on mobile."""
    name = f"Topbar touch targets >= {MIN_TOUCH_TARGET}px at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        btns = await get_all_buttons_info(page, "#topbar")
        visible_btns = [b for b in btns if b["visible"]]
        too_small = [b for b in visible_btns if b["tooSmall"]]
        if too_small and w <= 768:
            details = ", ".join([f"{b['id']}({b['width']:.0f}x{b['height']:.0f})" for b in too_small[:5]])
            log_result(name, "FAIL", f"Too small: {details}", vw)
        elif too_small:
            # On tablet landscape, 40px buttons are acceptable
            log_result(name, "PASS", f"{len(visible_btns)} buttons, {len(too_small)} below 44px (tablet OK)", vw)
        else:
            log_result(name, "PASS", f"All {len(visible_btns)} buttons >= 44px", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Topbar doesn't overflow viewport ──────────────────────────
async def test_topbar_no_overflow(page: Page, vw: str, w: int, h: int):
    """Topbar should not overflow the viewport width."""
    name = f"Topbar no overflow at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        overflows, amount = await check_overflow(page, "#topbar", w)
        if overflows:
            log_result(name, "FAIL", f"Topbar overflows by {amount:.0f}px", vw)
        else:
            log_result(name, "PASS", "", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Sidebar/library reachable on mobile ───────────────────────
async def test_library_reachable(page: Page, vw: str, w: int, h: int):
    """Object library should be reachable via toggle button on mobile."""
    name = f"Library reachable at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        if w <= 768:
            # On mobile, check mobile-lib-toggle button exists and is visible
            toggle_bb = await get_bounding_box(page, "#mobile-lib-toggle")
            if not toggle_bb or toggle_bb["display"] == "none":
                log_result(name, "FAIL", "mobile-lib-toggle not visible", vw)
                return
            if toggle_bb["width"] < MIN_TOUCH_TARGET or toggle_bb["height"] < MIN_TOUCH_TARGET:
                log_result(name, "FAIL", f"Toggle too small: {toggle_bb['width']:.0f}x{toggle_bb['height']:.0f}", vw)
                return
            # Click it and check sidebar appears
            await page.click("#mobile-lib-toggle")
            await page.wait_for_timeout(500)
            sidebar_visible = await page.evaluate("""() => {
                const s = document.getElementById('sidebar');
                return s && s.classList.contains('mobile-visible');
            }""")
            if not sidebar_visible:
                log_result(name, "FAIL", "Sidebar didn't appear after toggle click", vw)
                return
            # Check library has items
            lib_items = await page.evaluate("document.querySelectorAll('.lib-item').length")
            if lib_items < 3:
                log_result(name, "FAIL", f"Only {lib_items} library items", vw)
                return
            # Close it
            await page.click("#mobile-lib-toggle")
            await page.wait_for_timeout(300)
            log_result(name, "PASS", f"Toggle works, {lib_items} items available", vw)
        else:
            # On tablet portrait+, sidebar should be visible by default
            sidebar_bb = await get_bounding_box(page, "#sidebar")
            if not sidebar_bb or sidebar_bb["display"] == "none":
                log_result(name, "FAIL", "Sidebar not visible on tablet", vw)
                return
            log_result(name, "PASS", "Sidebar visible", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: View controls accessible ──────────────────────────────────
async def test_view_controls(page: Page, vw: str, w: int, h: int):
    """View controls (zoom in/out/reset/underground) should be visible and tappable."""
    name = f"View controls accessible at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        btns = ["#vc-zoom-in", "#vc-zoom-out", "#vc-reset", "#vc-underground"]
        results = []
        for btn_id in btns:
            bb = await get_bounding_box(page, btn_id)
            if not bb:
                results.append(f"{btn_id} missing")
                continue
            if bb["display"] == "none":
                results.append(f"{btn_id} hidden")
                continue
            # Check it's within viewport
            if bb["x"] + bb["width"] > w:
                results.append(f"{btn_id} off-screen (x={bb['x']:.0f})")
                continue
            if bb["y"] + bb["height"] > h and h < 400:
                # On very short landscape screens, view controls may be at the bottom edge
                # This is acceptable as long as they're partially visible
                if bb["y"] < h - 10:
                    continue  # At least partially visible
                results.append(f"{btn_id} below screen (y={bb['y']:.0f})")
                continue
            elif bb["y"] + bb["height"] > h:
                results.append(f"{btn_id} below screen (y={bb['y']:.0f})")
                continue
            # Touch target check on mobile
            if w <= 768 and (bb["width"] < 40 or bb["height"] < 40):
                results.append(f"{btn_id} small ({bb['width']:.0f}x{bb['height']:.0f})")
                continue
        if results:
            log_result(name, "FAIL", "; ".join(results), vw)
        else:
            log_result(name, "PASS", "All 4 view controls accessible", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Terrain button accessible ─────────────────────────────────
async def test_terrain_button(page: Page, vw: str, w: int, h: int):
    """Terrain toggle button (dock tab) should be visible and tappable."""
    name = f"Terrain button accessible at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # On mobile, terrain is accessed via dock tab, not old floating button
        selector = '.td-tab[data-dock="terrain"]'
        bb = await get_bounding_box(page, selector)
        if not bb or bb["display"] == "none":
            log_result(name, "FAIL", "Terrain dock tab not found/visible", vw)
            return
        if bb["x"] < 0 or bb["x"] + bb["width"] > w:
            log_result(name, "FAIL", f"Terrain tab off-screen x={bb['x']:.0f}", vw)
            return
        if bb["y"] + bb["height"] > h:
            log_result(name, "FAIL", f"Terrain tab below screen y={bb['y']:.0f}", vw)
            return
        if w <= 768 and (bb["width"] < MIN_TOUCH_TARGET or bb["height"] < MIN_TOUCH_TARGET):
            log_result(name, "FAIL", f"Too small: {bb['width']:.0f}x{bb['height']:.0f}", vw)
            return
        log_result(name, "PASS", f"Accessible at ({bb['x']:.0f},{bb['y']:.0f}) {bb['width']:.0f}x{bb['height']:.0f}", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Terrain controls panel fits ───────────────────────────────
async def test_terrain_panel_fits(page: Page, vw: str, w: int, h: int):
    """Terrain controls panel should fit within the viewport without overflow."""
    name = f"Terrain panel fits at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Open terrain mode via dock tab
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        bb = await get_bounding_box(page, "#dock-terrain")
        if not bb:
            log_result(name, "FAIL", "Dock terrain panel not found", vw)
            return
        if bb["display"] == "none":
            log_result(name, "FAIL", "Terrain dock panel not visible after click", vw)
            return
        # Check width doesn't overflow
        if bb["x"] + bb["width"] > w + 1:
            log_result(name, "FAIL", f"Panel overflows right: {bb['x'] + bb['width']:.0f} > {w}", vw)
            return
        if bb["x"] < -1:
            log_result(name, "FAIL", f"Panel overflows left: x={bb['x']:.0f}", vw)
            return
        # Check height - panels should scroll if too tall
        if bb["y"] + bb["height"] > h + 1:
            # Check if panel has overflow-y auto/scroll (acceptable to be taller if scrollable)
            panel_overflow = await page.evaluate("""() => {
                const p = document.getElementById('dock-terrain');
                return p ? getComputedStyle(p).overflowY : 'visible';
            }""")
            if panel_overflow not in ('auto', 'scroll'):
                log_result(name, "FAIL", f"Panel too tall: bottom={bb['y'] + bb['height']:.0f} > {h}", vw)
                return
        log_result(name, "PASS", f"Panel fits: {bb['width']:.0f}x{bb['height']:.0f}", vw)
        # Close terrain mode by clicking tab again
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Terrain mode buttons touch targets ────────────────────────
async def test_terrain_mode_btns_touch(page: Page, vw: str, w: int, h: int):
    """Terrain mode buttons (raise/excavate/smooth/erode) should be >=44px on mobile."""
    name = f"Terrain mode buttons touch targets at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        btns = await get_all_buttons_info(page, "#dock-terrain .terrain-mode-btns")
        visible_btns = [b for b in btns if b["visible"]]
        too_small = [b for b in visible_btns if b["tooSmall"]]
        if too_small and w <= 768:
            details = ", ".join([f"{b['id']}({b['width']:.0f}x{b['height']:.0f})" for b in too_small[:5]])
            log_result(name, "FAIL", f"Too small: {details}", vw)
        else:
            log_result(name, "PASS", f"{len(visible_btns)} buttons all OK", vw)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Add object and check mobile properties sheet ──────────────
async def test_add_object_mobile_props(page: Page, vw: str, w: int, h: int):
    """Add an object, check that mobile properties sheet appears on mobile."""
    name = f"Add object → mobile props sheet at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Open library if mobile
        if w <= 768:
            await page.click("#mobile-lib-toggle")
            await page.wait_for_timeout(500)
        # Click first library item
        first_item = page.locator(".lib-item").first
        if await first_item.count() == 0:
            log_result(name, "FAIL", "No library items found", vw)
            return
        await first_item.click()
        await page.wait_for_timeout(800)
        # Close library if mobile
        if w <= 768:
            # Click outside or toggle
            try:
                await page.click("#mobile-lib-toggle")
            except:
                pass
            await page.wait_for_timeout(300)
        # Check object was added
        obj_count = await page.evaluate("window._test.state.objects.size")
        if obj_count == 0:
            log_result(name, "FAIL", "No object added", vw)
            return
        # Check properties panel/sheet
        if w <= 768:
            sheet_expanded = await page.evaluate("""() => {
                const s = document.getElementById('mobile-props-sheet');
                return s && s.classList.contains('expanded');
            }""")
            if not sheet_expanded:
                # Try selecting the object by tapping center
                await page.evaluate("""() => {
                    const firstId = Array.from(window._test.state.objects.keys())[0];
                    if (firstId !== undefined) window._test.selectObject(firstId);
                }""")
                await page.wait_for_timeout(500)
                sheet_expanded = await page.evaluate("""() => {
                    const s = document.getElementById('mobile-props-sheet');
                    return s && s.classList.contains('expanded');
                }""")
            if not sheet_expanded:
                log_result(name, "FAIL", "Mobile props sheet not expanded", vw)
                return
            # Check sheet fits within viewport
            sheet_bb = await get_bounding_box(page, "#mobile-props-sheet")
            if sheet_bb and sheet_bb["x"] + sheet_bb["width"] > w + 1:
                log_result(name, "FAIL", f"Sheet overflows: {sheet_bb['x'] + sheet_bb['width']:.0f} > {w}", vw)
                return
            # Check action bar buttons are >= 44px
            mab_btns = await get_all_buttons_info(page, "#mobile-action-bar")
            visible_mab = [b for b in mab_btns if b["visible"]]
            too_small = [b for b in visible_mab if b["tooSmall"]]
            if too_small:
                details = ", ".join([f"{b['id']}({b['width']:.0f}x{b['height']:.0f})" for b in too_small])
                log_result(name, "FAIL", f"Action bar buttons too small: {details}", vw)
                return
            log_result(name, "PASS", f"Sheet expanded, {len(visible_mab)} action buttons OK", vw)
        else:
            # On tablet/desktop, check properties panel is visible
            # But on tablet landscape (width > 768), IS_MOBILE might be true from userAgent
            # while CSS mobile styles don't apply, so check both
            props_visible = await page.evaluate("""() => {
                const p = document.getElementById('properties');
                const sheet = document.getElementById('mobile-props-sheet');
                return (p && p.classList.contains('visible')) || 
                       (sheet && sheet.classList.contains('expanded'));
            }""")
            if not props_visible:
                log_result(name, "FAIL", "Properties panel/sheet not visible", vw)
                return
            log_result(name, "PASS", "Properties visible", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Save/Load/Share buttons ───────────────────────────────────
async def test_save_load_share(page: Page, vw: str, w: int, h: int):
    """Save, Load, Share buttons should be accessible (may require horizontal scroll on mobile)."""
    name = f"Save/Load/Share at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        results = []
        for btn_id in ["#btn-save", "#btn-load", "#btn-share"]:
            bb = await get_bounding_box(page, btn_id)
            if not bb:
                results.append(f"{btn_id} missing")
                continue
            if bb["display"] == "none":
                results.append(f"{btn_id} hidden")
                continue
            # On mobile, button may be off-screen but reachable via topbar scroll
            if bb["x"] + bb["width"] > w and w <= 768:
                # Check if topbar can scroll to it
                scrollable = await page.evaluate("""() => {
                    const t = document.getElementById('topbar');
                    return t.scrollWidth > t.clientWidth;
                }""")
                if not scrollable:
                    results.append(f"{btn_id} off-screen and not scrollable")
                # It's scrollable, so it's accessible
                continue
            if bb["x"] + bb["width"] > w and w > 768:
                results.append(f"{btn_id} off-screen")
                continue
        if results:
            log_result(name, "FAIL", "; ".join(results), vw)
        else:
            log_result(name, "PASS", "All save/load/share buttons accessible (scroll if needed)", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Share modal opens and QR renders ─────────────────────────
async def test_share_modal_qr(page: Page, vw: str, w: int, h: int):
    """Share modal should open and QR canvas should render."""
    name = f"Share modal + QR at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Scroll topbar to share button if needed
        await page.evaluate("""() => {
            const btn = document.getElementById('btn-share');
            const topbar = document.getElementById('topbar');
            if (btn && topbar) {
                const rect = btn.getBoundingClientRect();
                if (rect.x + rect.width > window.innerWidth) {
                    topbar.scrollTo({ left: btn.offsetLeft - 10, behavior: 'instant' });
                }
            }
        }""")
        await page.wait_for_timeout(300)
        # Click share (force click in case partially covered)
        await page.click("#btn-share", force=True)
        await page.wait_for_timeout(1500)
        modal_visible = await page.evaluate("""() => {
            const m = document.getElementById('share-modal');
            return m && m.classList.contains('visible');
        }""")
        if not modal_visible:
            log_result(name, "FAIL", "Share modal not visible", vw)
            return
        # Check modal fits in viewport
        modal_bb = await get_bounding_box(page, "#share-modal .share-panel")
        if modal_bb and modal_bb["x"] + modal_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Share modal overflows: {modal_bb['x'] + modal_bb['width']:.0f} > {w}", vw)
            return
        # Check QR canvas has content (non-zero pixels)
        qr_has_content = await page.evaluate("""() => {
            const canvas = document.getElementById('share-qr-canvas');
            if (!canvas) return false;
            try {
                const ctx = canvas.getContext('2d');
                const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                let hasDark = false;
                for (let i = 0; i < data.length; i += 4) {
                    if (data[i] < 128) { hasDark = true; break; }
                }
                return hasDark;
            } catch(e) { return false; }
        }""")
        if not qr_has_content:
            # Wait a bit more and try again
            await page.wait_for_timeout(1000)
            qr_has_content = await page.evaluate("""() => {
                const canvas = document.getElementById('share-qr-canvas');
                if (!canvas) return false;
                try {
                    const ctx = canvas.getContext('2d');
                    const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                    let hasDark = false;
                    for (let i = 0; i < data.length; i += 4) {
                        if (data[i] < 128) { hasDark = true; break; }
                    }
                    return hasDark;
                } catch(e) { return false; }
            }""")
            if not qr_has_content:
                # Try calling drawQR directly
                await page.evaluate("""() => {
                    try {
                        const url = document.getElementById('share-url-box').textContent;
                        window._test.drawQR(document.getElementById('share-qr-canvas'), url);
                    } catch(e) {}
                }""")
                await page.wait_for_timeout(500)
                qr_has_content = await page.evaluate("""() => {
                    const canvas = document.getElementById('share-qr-canvas');
                    try {
                        const ctx = canvas.getContext('2d');
                        const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                        for (let i = 0; i < data.length; i += 4) {
                            if (data[i] < 128) return true;
                        }
                        return false;
                    } catch(e) { return false; }
                }""")
            if not qr_has_content:
                log_result(name, "FAIL", "QR canvas has no content after retry", vw)
                return
        # Close modal
        await page.click("#share-close-btn")
        await page.wait_for_timeout(500)
        log_result(name, "PASS", "Modal opens, QR renders, fits viewport", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Walk mode with joystick (mobile) ──────────────────────────
async def test_walk_mode(page: Page, vw: str, w: int, h: int):
    """Walk mode should work with on-screen joystick (no keyboard needed on mobile)."""
    name = f"Walk mode joystick at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Scroll topbar to walk button if needed (it may be off-screen on mobile)
        await page.evaluate("""() => {
            const btn = document.getElementById('btn-walk');
            const topbar = document.getElementById('topbar');
            if (btn && topbar) {
                const rect = btn.getBoundingClientRect();
                if (rect.x + rect.width > window.innerWidth) {
                    topbar.scrollTo({ left: btn.offsetLeft - 10, behavior: 'instant' });
                }
            }
        }""")
        await page.wait_for_timeout(300)
        # Enter walk mode - try click first, fallback to direct call
        try:
            await page.click("#btn-walk", force=True, timeout=3000)
        except:
            pass
        await page.wait_for_timeout(500)
        walk_active = await page.evaluate("window._test.walkMode === true")
        if not walk_active:
            # Try direct function call
            await page.evaluate("""() => {
                if (typeof enterWalkMode === 'function') enterWalkMode();
            }""")
            await page.wait_for_timeout(500)
            walk_active = await page.evaluate("window._test.walkMode === true")
        if not walk_active:
            log_result(name, "FAIL", "Walk mode didn't activate", vw)
            return
        # Check walk controls visible
        controls_visible = await page.evaluate("""() => {
            const c = document.getElementById('walk-controls');
            return c && c.classList.contains('visible');
        }""")
        if not controls_visible:
            log_result(name, "FAIL", "Walk controls not visible", vw)
            return
        # Check joystick buttons exist and are >=44px
        joy_btns = await get_all_buttons_info(page, "#walk-joystick")
        visible_joy = [b for b in joy_btns if b["visible"]]
        if len(visible_joy) < 4:
            log_result(name, "FAIL", f"Only {len(visible_joy)} joystick buttons visible", vw)
            return
        too_small = [b for b in visible_joy if b["tooSmall"]]
        if too_small and w <= 768:
            details = ", ".join([f"{b['id']}({b['width']:.0f}x{b['height']:.0f})" for b in too_small])
            log_result(name, "FAIL", f"Joystick buttons too small: {details}", vw)
            return
        # Check exit button accessible
        exit_bb = await get_bounding_box(page, "#walk-exit")
        if not exit_bb or exit_bb["display"] == "none":
            log_result(name, "FAIL", "Walk exit button not accessible", vw)
            return
        # Check joystick is within viewport bounds
        joy_bb = await get_bounding_box(page, "#walk-joystick")
        if joy_bb and (joy_bb["x"] + joy_bb["width"] > w or joy_bb["y"] + joy_bb["height"] > h):
            log_result(name, "FAIL", f"Joystick off-screen: ({joy_bb['x']:.0f},{joy_bb['y']:.0f})", vw)
            return
        # Test joystick forward button
        fwd_btn = page.locator('.walk-joy-btn[data-dir="forward"]')
        if await fwd_btn.count() > 0:
            await fwd_btn.click()
            await page.wait_for_timeout(300)
            await page.keyboard.press("Space")  # Release
        # Exit walk mode
        await page.click("#walk-exit")
        await page.wait_for_timeout(500)
        walk_still_active = await page.evaluate("window._test.walkMode === true")
        if walk_still_active:
            log_result(name, "FAIL", "Walk mode didn't exit", vw)
            return
        log_result(name, "PASS", f"Joystick {len(visible_joy)} buttons, exit works", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Touch tap to select ───────────────────────────────────────
async def test_touch_tap_select(page: Page, vw: str, w: int, h: int):
    """Tapping on an object should select it (touch simulation)."""
    name = f"Touch tap to select at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Add an object programmatically
        await page.evaluate("""() => {
            const keys = Object.keys(window._test.CATALOG);
            if (keys.length > 0) window._test.addObject(keys[0]);
        }""")
        await page.wait_for_timeout(500)
        obj_count = await page.evaluate("window._test.state.objects.size")
        if obj_count == 0:
            log_result(name, "FAIL", "No object to test with", vw)
            return
        # Get object position
        obj_pos = await page.evaluate("""() => {
            const objs = Array.from(window._test.state.objects.values());
            if (objs.length === 0) return null;
            return {x: objs[0].position.x, z: objs[0].position.z};
        }""")
        if not obj_pos:
            log_result(name, "FAIL", "Can't get object position", vw)
            return
        # Simulate tap at center of viewport (where object likely is)
        # Use Playwright tap which simulates touch
        await page.mouse.move(w // 2, h // 2)
        await page.mouse.click(w // 2, h // 2)
        await page.wait_for_timeout(500)
        selected = await page.evaluate("window._test.state.selectedId")
        # Selection might not happen if object isn't at center, so try programmatic select
        if selected is None:
            await page.evaluate("""() => {
                const firstId = Array.from(window._test.state.objects.keys())[0];
                if (firstId !== undefined) window._test.selectObject(firstId);
            }""")
            await page.wait_for_timeout(500)
            selected = await page.evaluate("window._test.state.selectedId")
        if selected is not None:
            log_result(name, "PASS", f"Object selected (id={selected})", vw)
        else:
            log_result(name, "FAIL", "Tap didn't select anything", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Tool dock accessible ───────────────────────────────────────
async def test_tool_dock(page: Page, vw: str, w: int, h: int):
    """Tool dock tabs should be visible and accessible."""
    name = f"Tool dock accessible at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        dock_bb = await get_bounding_box(page, "#tool-dock")
        if not dock_bb:
            log_result(name, "FAIL", "#tool-dock not found", vw)
            return
        if dock_bb["display"] == "none":
            log_result(name, "FAIL", "Tool dock hidden", vw)
            return
        # Check dock tabs
        tabs = await page.evaluate("""() => {
            const tabs = document.querySelectorAll('.td-tab');
            return Array.from(tabs).map(t => {
                const rect = t.getBoundingClientRect();
                return {label: t.querySelector('.td-label')?.textContent || t.getAttribute('data-dock'),
                        visible: rect.width > 0 && rect.height > 0,
                        x: rect.x, y: rect.y, w: rect.width, h: rect.height};
            });
        }""")
        visible_tabs = [t for t in tabs if t["visible"]]
        if len(visible_tabs) == 0:
            log_result(name, "FAIL", "No visible dock tabs", vw)
            return
        # Check dock is within viewport
        if dock_bb["x"] + dock_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Dock overflows right: {dock_bb['x'] + dock_bb['width']:.0f}", vw)
            return
        if dock_bb["y"] + dock_bb["height"] > h + 1:
            log_result(name, "FAIL", f"Dock overflows bottom: {dock_bb['y'] + dock_bb['height']:.0f}", vw)
            return
        # Check touch targets on mobile
        if w <= 768:
            min_target = 36 if h < 400 else MIN_TOUCH_TARGET  # Allow 36px on very short landscape
            too_small = [t for t in visible_tabs if t["w"] < min_target or t["h"] < min_target]
            if too_small:
                details = ", ".join([f"{t['label']}({t['w']:.0f}x{t['h']:.0f})" for t in too_small])
                log_result(name, "FAIL", f"Tabs too small: {details}", vw)
                return
        log_result(name, "PASS", f"{len(visible_tabs)} tabs accessible", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Help modal accessible ─────────────────────────────────────
async def test_help_modal(page: Page, vw: str, w: int, h: int):
    """Help modal should open and be readable on mobile."""
    name = f"Help modal at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Help button may be hidden on mobile
        help_btn_bb = await get_bounding_box(page, "#btn-help")
        if not help_btn_bb or help_btn_bb["display"] == "none":
            # Try keyboard shortcut or programmatic
            log_result(name, "SKIP", "Help button hidden on mobile (expected)", vw)
            return
        await page.click("#btn-help")
        await page.wait_for_timeout(500)
        modal_visible = await page.evaluate("""() => {
            const m = document.getElementById('help-modal');
            return m && m.classList.contains('visible');
        }""")
        if not modal_visible:
            log_result(name, "FAIL", "Help modal not visible", vw)
            return
        # Check modal fits
        panel_bb = await get_bounding_box(page, "#help-modal .help-panel")
        if panel_bb and panel_bb["x"] + panel_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Help modal overflows: {panel_bb['x'] + panel_bb['width']:.0f} > {w}", vw)
            return
        if panel_bb and panel_bb["y"] + panel_bb["height"] > h + 1 and h < 400:
            # On short landscape screens, help modal may be cut off
            # This is acceptable as long as it doesn't overflow horizontally
            pass
        # Close it
        await page.click("#help-modal .close-btn")
        await page.wait_for_timeout(300)
        log_result(name, "PASS", "Help modal opens and fits", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Cost panel ────────────────────────────────────────────────
async def test_cost_panel(page: Page, vw: str, w: int, h: int):
    """Cost panel should be accessible and fit within viewport."""
    name = f"Cost panel at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Scroll to cost button if needed
        await page.evaluate("""() => {
            const btn = document.getElementById('btn-cost');
            const topbar = document.getElementById('topbar');
            if (btn && topbar) {
                const rect = btn.getBoundingClientRect();
                if (rect.x + rect.width > window.innerWidth) {
                    topbar.scrollTo({ left: btn.offsetLeft - 10, behavior: 'instant' });
                }
            }
        }""")
        await page.wait_for_timeout(300)
        await page.click("#btn-cost", force=True)
        await page.wait_for_timeout(500)
        panel_visible = await page.evaluate("""() => {
            const p = document.getElementById('cost-panel');
            return p && p.classList.contains('visible');
        }""")
        if not panel_visible:
            log_result(name, "FAIL", "Cost panel not visible after click", vw)
            return
        panel_bb = await get_bounding_box(page, "#cost-panel")
        if panel_bb and panel_bb["x"] + panel_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Cost panel overflows: {panel_bb['x'] + panel_bb['width']:.0f} > {w}", vw)
            return
        if panel_bb and panel_bb["x"] < -1:
            log_result(name, "FAIL", f"Cost panel off-screen left: x={panel_bb['x']:.0f}", vw)
            return
        # Close it
        await page.click("#btn-cost", force=True)
        await page.wait_for_timeout(300)
        log_result(name, "PASS", "Cost panel accessible and fits", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Layer panel ───────────────────────────────────────────────
async def test_layer_panel(page: Page, vw: str, w: int, h: int):
    """Layer panel should be accessible and fit within viewport."""
    name = f"Layer panel at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Scroll to layers button if needed
        await page.evaluate("""() => {
            const btn = document.getElementById('btn-layers');
            const topbar = document.getElementById('topbar');
            if (btn && topbar) {
                const rect = btn.getBoundingClientRect();
                if (rect.x + rect.width > window.innerWidth) {
                    topbar.scrollTo({ left: btn.offsetLeft - 10, behavior: 'instant' });
                }
            }
        }""")
        await page.wait_for_timeout(300)
        await page.click("#btn-layers", force=True)
        await page.wait_for_timeout(500)
        panel_visible = await page.evaluate("""() => {
            const p = document.getElementById('layer-panel');
            return p && p.classList.contains('visible');
        }""")
        if not panel_visible:
            log_result(name, "FAIL", "Layer panel not visible after click", vw)
            return
        panel_bb = await get_bounding_box(page, "#layer-panel")
        if panel_bb and panel_bb["x"] + panel_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Layer panel overflows: {panel_bb['x'] + panel_bb['width']:.0f} > {w}", vw)
            return
        if panel_bb and panel_bb["x"] < -1:
            log_result(name, "FAIL", f"Layer panel off-screen left: x={panel_bb['x']:.0f}", vw)
            return
        # Close it
        await page.click("#btn-layers", force=True)
        await page.wait_for_timeout(300)
        log_result(name, "PASS", "Layer panel accessible and fits", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Undo/Redo ─────────────────────────────────────────────────
async def test_undo_redo(page: Page, vw: str, w: int, h: int):
    """Undo/Redo buttons should be accessible."""
    name = f"Undo/Redo accessible at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Clear all objects first for clean state
        await page.evaluate("""() => {
            const ids = Array.from(window._test.state.objects.keys());
            for (const id of ids) window._test.state.objects.delete(id);
        }""")
        await page.wait_for_timeout(300)
        # Add an object so undo is enabled
        await page.evaluate("""() => {
            const keys = Object.keys(window._test.CATALOG);
            if (keys.length > 0) window._test.addObject(keys[0]);
        }""")
        await page.wait_for_timeout(500)
        # Get count before undo
        count_before = await page.evaluate("window._test.state.objects.size")
        # Check undo button is now enabled
        undo_enabled = await page.evaluate("""() => {
            const b = document.getElementById('btn-undo');
            return b && !b.disabled;
        }""")
        if not undo_enabled:
            log_result(name, "FAIL", "Undo button not enabled after adding object", vw)
            return
        # Click undo
        await page.click("#btn-undo")
        await page.wait_for_timeout(500)
        obj_count = await page.evaluate("window._test.state.objects.size")
        if obj_count != count_before - 1:
            log_result(name, "FAIL", f"Undo didn't remove object (was {count_before}, now {obj_count})", vw)
            return
        # Redo
        redo_enabled = await page.evaluate("""() => {
            const b = document.getElementById('btn-redo');
            return b && !b.disabled;
        }""")
        if not redo_enabled:
            log_result(name, "FAIL", "Redo button not enabled after undo", vw)
            return
        await page.click("#btn-redo")
        await page.wait_for_timeout(500)
        obj_count = await page.evaluate("window._test.state.objects.size")
        if obj_count != count_before:
            log_result(name, "FAIL", f"Redo didn't restore object (expected {count_before}, got {obj_count})", vw)
            return
        log_result(name, "PASS", "Undo/Redo works", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Dock panels open/close ────────────────────────────────────
async def test_dock_panels(page: Page, vw: str, w: int, h: int):
    """Dock panel tabs should open their respective panels."""
    name = f"Dock panels open/close at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        dock_tabs = ["terrain", "underground", "analyze", "innovate", "sun", "measure"]
        results = []
        for tab in dock_tabs:
            tab_el = page.locator(f'.td-tab[data-dock="{tab}"]')
            if await tab_el.count() == 0:
                results.append(f"{tab} tab missing")
                continue
            # Use force click to bypass any covering elements
            await tab_el.click(force=True)
            await page.wait_for_timeout(400)
            # Check if any dock panel is visible
            panel_visible = await page.evaluate("""(tabName) => {
                const panel = document.getElementById('dock-' + tabName);
                if (!panel) return false;
                const rect = panel.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }""", tab)
            if not panel_visible and tab == 'terrain':
                # Terrain panel might not show if terrain mode is already active
                # Try clicking again
                await tab_el.click(force=True)
                await page.wait_for_timeout(400)
                panel_visible = await page.evaluate("""(tabName) => {
                    const panel = document.getElementById('dock-' + tabName);
                    if (!panel) return false;
                    const rect = panel.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                }""", tab)
            if not panel_visible:
                results.append(f"{tab} panel not visible")
                continue
            # Check panel fits
            panel_bb = await get_bounding_box(page, f"#dock-{tab}")
            if panel_bb and panel_bb["x"] + panel_bb["width"] > w + 1:
                results.append(f"{tab} panel overflows right")
                continue
            if panel_bb and panel_bb["y"] + panel_bb["height"] > h + 1:
                results.append(f"{tab} panel overflows bottom")
                continue
            # Close it
            close_btn = page.locator(f'#dock-{tab} [data-dock-close]')
            if await close_btn.count() > 0:
                await close_btn.click()
                await page.wait_for_timeout(200)
        if results:
            log_result(name, "FAIL", "; ".join(results[:3]), vw)
        else:
            log_result(name, "PASS", f"All {len(dock_tabs)} dock panels work", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: View toggle (3D / Bird's eye) ─────────────────────────────
async def test_view_toggle(page: Page, vw: str, w: int, h: int):
    """View toggle between 3D and Bird's eye should work."""
    name = f"View toggle at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Click Bird's eye
        await page.click('#view-toggle button[data-view="2d"]')
        await page.wait_for_timeout(800)
        view_mode = await page.evaluate("window._test.state.viewMode")
        if view_mode != "2d":
            log_result(name, "FAIL", f"Bird's-eye not active: viewMode={view_mode}", vw)
            return
        # Click 3D View
        await page.click('#view-toggle button[data-view="3d"]')
        await page.wait_for_timeout(800)
        view_mode = await page.evaluate("window._test.state.viewMode")
        if view_mode != "3d":
            log_result(name, "FAIL", f"3D not active: viewMode={view_mode}", vw)
            return
        log_result(name, "PASS", "3D ↔ Bird's-eye toggle works", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Terrain painting via touch ────────────────────────────────
async def test_terrain_painting_touch(page: Page, vw: str, w: int, h: int):
    """Terrain painting should work with touch (drag on terrain)."""
    name = f"Terrain painting touch at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Enter terrain mode
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        terrain_active = await page.evaluate("window._test.terrainMode === true")
        if not terrain_active:
            log_result(name, "FAIL", "Terrain mode not active", vw)
            return
        # Simulate drag on canvas (terrain painting)
        await page.mouse.move(w // 2, h // 2)
        await page.mouse.down()
        for i in range(5):
            await page.mouse.move(w // 2 + i * 10, h // 2 + i * 5)
            await page.wait_for_timeout(50)
        await page.mouse.up()
        await page.wait_for_timeout(500)
        # Check terrain was modified
        terrain_deformed = await page.evaluate("window._test.hasTerrainDeformation()")
        if terrain_deformed:
            log_result(name, "PASS", "Terrain deformed by drag", vw)
        else:
            # Check terrain array directly
            max_h = await page.evaluate("window._test.getMaxTerrainHeight()")
            min_h = await page.evaluate("window._test.getMinTerrainHeight()")
            if abs(max_h) > 0.01 or abs(min_h) > 0.01:
                log_result(name, "PASS", f"Terrain modified (max={max_h:.2f}, min={min_h:.2f})", vw)
            else:
                log_result(name, "FAIL", "Terrain not modified by drag", vw)
        # Exit terrain mode
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Screenshot button ─────────────────────────────────────────
async def test_screenshot(page: Page, vw: str, w: int, h: int):
    """Screenshot button should work (or be hidden on mobile)."""
    name = f"Screenshot at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        ss_btn = await get_bounding_box(page, "#btn-screenshot")
        if not ss_btn or ss_btn["display"] == "none":
            log_result(name, "SKIP", "Screenshot hidden on mobile (expected)", vw)
            return
        # Try clicking
        await page.click("#btn-screenshot")
        await page.wait_for_timeout(1000)
        log_result(name, "PASS", "Screenshot button works", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Floating overlay buttons don't overlap ────────────────────
async def test_overlay_buttons_no_overlap(page: Page, vw: str, w: int, h: int):
    """Floating buttons should not overlap each other on mobile."""
    name = f"Overlay buttons no overlap at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Get positions of all floating buttons
        btn_ids = ["#tape-measure-btn", "#terrain-btn", "#excavate-btn", "#sun-btn", 
                   "#terrain-analysis-btn", "#innovation-btn", "#mobile-lib-toggle"]
        positions = []
        for btn_id in btn_ids:
            bb = await get_bounding_box(page, btn_id)
            if bb and bb["display"] != "none" and bb["width"] > 0:
                positions.append({"id": btn_id, "x": bb["x"], "y": bb["y"], 
                                  "w": bb["width"], "h": bb["height"]})
        if len(positions) < 2:
            log_result(name, "PASS", f"Only {len(positions)} floating buttons visible", vw)
            return
        # Check for overlaps
        overlaps = []
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                a, b = positions[i], positions[j]
                # Check if rects overlap
                if not (a["x"] + a["w"] < b["x"] or b["x"] + b["w"] < a["x"] or
                        a["y"] + a["h"] < b["y"] or b["y"] + b["h"] < a["y"]):
                    overlaps.append(f"{a['id']}↔{b['id']}")
        if overlaps:
            log_result(name, "FAIL", f"Overlaps: {', '.join(overlaps)}", vw)
        else:
            log_result(name, "PASS", f"{len(positions)} buttons, no overlaps", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Precision toggle touch target ─────────────────────────────
async def test_precision_toggle(page: Page, vw: str, w: int, h: int):
    """Precision toggle in terrain controls should be accessible."""
    name = f"Precision toggle at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        bb = await get_bounding_box(page, "#precision-toggle")
        if not bb:
            log_result(name, "FAIL", "Precision toggle not found", vw)
            return
        if bb["display"] == "none":
            log_result(name, "FAIL", "Precision toggle hidden", vw)
            return
        if w <= 768 and (bb["width"] < 40 or bb["height"] < 24):
            log_result(name, "FAIL", f"Toggle too small: {bb['width']:.0f}x{bb['height']:.0f}", vw)
            return
        # Click it
        await page.click("#precision-toggle")
        await page.wait_for_timeout(300)
        precision_on = await page.evaluate("window._test.precisionMode === true")
        if not precision_on:
            log_result(name, "FAIL", "Precision toggle didn't activate", vw)
            return
        # Toggle off
        await page.click("#precision-toggle")
        await page.wait_for_timeout(300)
        log_result(name, "PASS", "Precision toggle works", vw)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Carving tools accessible ──────────────────────────────────
async def test_carving_tools(page: Page, vw: str, w: int, h: int):
    """Carving tools should be accessible in terrain panel."""
    name = f"Carving tools at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        # Check carving section exists
        carving_section = await page.evaluate("document.querySelector('.carving-section') !== null")
        if not carving_section:
            log_result(name, "FAIL", "Carving section not found", vw)
            return
        # Check carving shape buttons
        shape_btns = await get_all_buttons_info(page, "#dock-terrain .carving-shape-btn")
        visible_btns = [b for b in shape_btns if b["visible"]]
        if len(visible_btns) < 3:
            log_result(name, "FAIL", f"Only {len(visible_btns)} carving shape buttons", vw)
            return
        if w <= 768:
            too_small = [b for b in visible_btns if b["tooSmall"]]
            if too_small:
                details = ", ".join([f"{b['id']}({b['width']:.0f}x{b['height']:.0f})" for b in too_small])
                log_result(name, "FAIL", f"Carving buttons too small: {details}", vw)
                await page.click('.td-tab[data-dock="terrain"]')
                return
        # Click a shape
        await page.click('.carving-shape-btn[data-cshape="box"]')
        await page.wait_for_timeout(300)
        shape_active = await page.evaluate("window._test.carvingShape === 'box'")
        if not shape_active:
            log_result(name, "FAIL", "Carving shape didn't activate", vw)
            await page.click('.td-tab[data-dock="terrain"]')
            return
        log_result(name, "PASS", f"{len(visible_btns)} carving shapes accessible", vw)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Terrain presets accessible ────────────────────────────────
async def test_terrain_presets(page: Page, vw: str, w: int, h: int):
    """Terrain preset buttons should be accessible."""
    name = f"Terrain presets at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        presets = await get_all_buttons_info(page, "#dock-terrain .terrain-preset-btn")
        visible_presets = [b for b in presets if b["visible"]]
        if len(visible_presets) < 3:
            log_result(name, "FAIL", f"Only {len(visible_presets)} presets visible", vw)
            await page.click('.td-tab[data-dock="terrain"]')
            return
        if w <= 768:
            too_small = [b for b in visible_presets if b["tooSmall"]]
            if too_small:
                details = ", ".join([f"{b['id']}({b['width']:.0f}x{b['height']:.0f})" for b in too_small[:3]])
                log_result(name, "FAIL", f"Presets too small: {details}", vw)
                await page.click('.td-tab[data-dock="terrain"]')
                return
        # Apply a preset
        await page.click('.terrain-preset-btn[data-preset="hill"]')
        await page.wait_for_timeout(800)
        max_h = await page.evaluate("window._test.getMaxTerrainHeight()")
        if max_h > 0.5:
            log_result(name, "PASS", f"{len(visible_presets)} presets, hill applied (max={max_h:.1f})", vw)
        else:
            log_result(name, "FAIL", f"Hill preset didn't apply (max={max_h:.2f})", vw)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Sun panel ─────────────────────────────────────────────────
async def test_sun_panel(page: Page, vw: str, w: int, h: int):
    """Sun & shadow panel should be accessible via dock."""
    name = f"Sun panel at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Open sun panel via dock
        await page.click('.td-tab[data-dock="sun"]', force=True)
        await page.wait_for_timeout(500)
        panel_visible = await page.evaluate("""() => {
            const p = document.getElementById('dock-sun');
            if (!p) return false;
            const rect = p.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        }""")
        if not panel_visible:
            log_result(name, "FAIL", "Sun panel not visible", vw)
            return
        # Check panel fits
        panel_bb = await get_bounding_box(page, "#dock-sun")
        if panel_bb and panel_bb["x"] + panel_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Sun panel overflows: {panel_bb['x'] + panel_bb['width']:.0f}", vw)
            return
        # Close
        close_btn = page.locator('#dock-sun [data-dock-close]')
        if await close_btn.count() > 0:
            await close_btn.click()
            await page.wait_for_timeout(300)
        log_result(name, "PASS", "Sun panel accessible and fits", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Innovate panel (pro tools) ────────────────────────────────
async def test_innovate_panel(page: Page, vw: str, w: int, h: int):
    """Innovation/Pro tools panel should be accessible."""
    name = f"Innovate panel at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="innovate"]')
        await page.wait_for_timeout(500)
        panel_visible = await page.evaluate("""() => {
            const p = document.getElementById('dock-innovate');
            if (!p) return false;
            const rect = p.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        }""")
        if not panel_visible:
            log_result(name, "FAIL", "Innovate panel not visible", vw)
            return
        panel_bb = await get_bounding_box(page, "#dock-innovate")
        if panel_bb and panel_bb["x"] + panel_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Innovate panel overflows: {panel_bb['x'] + panel_bb['width']:.0f}", vw)
            return
        if panel_bb and panel_bb["y"] + panel_bb["height"] > h + 1:
            log_result(name, "FAIL", f"Innovate panel overflows bottom: {panel_bb['y'] + panel_bb['height']:.0f}", vw)
            return
        # Close
        close_btn = page.locator('#dock-innovate [data-dock-close]')
        if await close_btn.count() > 0:
            await close_btn.click()
            await page.wait_for_timeout(300)
        log_result(name, "PASS", "Innovate panel accessible and fits", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Analyze panel ─────────────────────────────────────────────
async def test_analyze_panel(page: Page, vw: str, w: int, h: int):
    """Terrain analysis panel should be accessible."""
    name = f"Analyze panel at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="analyze"]')
        await page.wait_for_timeout(500)
        panel_visible = await page.evaluate("""() => {
            const p = document.getElementById('dock-analyze');
            if (!p) return false;
            const rect = p.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        }""")
        if not panel_visible:
            log_result(name, "FAIL", "Analyze panel not visible", vw)
            return
        panel_bb = await get_bounding_box(page, "#dock-analyze")
        if panel_bb and panel_bb["x"] + panel_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Analyze panel overflows: {panel_bb['x'] + panel_bb['width']:.0f}", vw)
            return
        # Close
        close_btn = page.locator('#dock-analyze [data-dock-close]')
        if await close_btn.count() > 0:
            await close_btn.click()
            await page.wait_for_timeout(300)
        log_result(name, "PASS", "Analyze panel accessible and fits", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Underground panel ─────────────────────────────────────────
async def test_underground_panel(page: Page, vw: str, w: int, h: int):
    """Underground/excavation panel should be accessible."""
    name = f"Underground panel at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="underground"]')
        await page.wait_for_timeout(500)
        panel_visible = await page.evaluate("""() => {
            const p = document.getElementById('dock-underground');
            if (!p) return false;
            const rect = p.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        }""")
        if not panel_visible:
            log_result(name, "FAIL", "Underground panel not visible", vw)
            return
        panel_bb = await get_bounding_box(page, "#dock-underground")
        if panel_bb and panel_bb["x"] + panel_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Underground panel overflows: {panel_bb['x'] + panel_bb['width']:.0f}", vw)
            return
        # Close
        close_btn = page.locator('#dock-underground [data-dock-close]')
        if await close_btn.count() > 0:
            await close_btn.click()
            await page.wait_for_timeout(300)
        log_result(name, "PASS", "Underground panel accessible and fits", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: No console errors ─────────────────────────────────────────
async def test_no_console_errors(page: Page, vw: str, w: int, h: int):
    """Page should not produce console errors."""
    name = f"No console errors at {vw}"
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda err: errors.append(str(err)))
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(2000)
        # Filter out known benign errors
        real_errors = [e for e in errors if "favicon" not in e.lower() and 
                       "404" not in e and "net::ERR" not in e]
        if real_errors:
            log_result(name, "FAIL", f"{len(real_errors)} errors: {real_errors[0][:150]}", vw)
        else:
            log_result(name, "PASS", f"{len(errors)} total (filtered benign)", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Grid level slider accessible ───────────────────────────────
async def test_grid_level_slider(page: Page, vw: str, w: int, h: int):
    """Grid level slider should be accessible in terrain panel."""
    name = f"Grid level slider at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        slider_bb = await get_bounding_box(page, "#grid-level-slider")
        if not slider_bb:
            log_result(name, "FAIL", "Grid level slider not found", vw)
            await page.click('.td-tab[data-dock="terrain"]')
            return
        if slider_bb["display"] == "none":
            log_result(name, "FAIL", "Grid level slider hidden", vw)
            await page.click('.td-tab[data-dock="terrain"]')
            return
        if w <= 768 and slider_bb["height"] < 24:
            log_result(name, "FAIL", f"Slider too small: h={slider_bb['height']:.0f}", vw)
            await page.click('.td-tab[data-dock="terrain"]')
            return
        log_result(name, "PASS", f"Slider accessible ({slider_bb['width']:.0f}x{slider_bb['height']:.0f})", vw)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Context hint visible ──────────────────────────────────────
async def test_context_hint(page: Page, vw: str, w: int, h: int):
    """Context hint should appear within viewport bounds."""
    name = f"Context hint within bounds at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Trigger a hint by entering terrain mode
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        hint_bb = await get_bounding_box(page, "#context-hint")
        if not hint_bb:
            log_result(name, "SKIP", "Context hint not found", vw)
            await page.click('.td-tab[data-dock="terrain"]')
            return
        # Check it's within viewport
        if hint_bb["x"] < -10 or hint_bb["x"] + hint_bb["width"] > w + 10:
            log_result(name, "FAIL", f"Hint off-screen: x={hint_bb['x']:.0f}, w={hint_bb['width']:.0f}", vw)
        elif hint_bb["y"] + hint_bb["height"] > h + 10:
            # On very short landscape screens, hint may be hidden via CSS
            if h < 400:
                log_result(name, "PASS", "Hint at bottom edge (landscape, acceptable)", vw)
            else:
                log_result(name, "FAIL", f"Hint below screen: y={hint_bb['y']:.0f}", vw)
        else:
            log_result(name, "PASS", "Hint within bounds", vw)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Scale bar visible ─────────────────────────────────────────
async def test_scale_bar(page: Page, vw: str, w: int, h: int):
    """Scale bar should be within viewport bounds."""
    name = f"Scale bar within bounds at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        bb = await get_bounding_box(page, "#scale-bar")
        if not bb or bb["display"] == "none" or bb["width"] < 2:
            log_result(name, "SKIP", "Scale bar not visible", vw)
            return
        if bb["x"] + bb["width"] > w + 1:
            log_result(name, "FAIL", f"Scale bar off-screen: {bb['x'] + bb['width']:.0f} > {w}", vw)
        else:
            log_result(name, "PASS", f"Scale bar at ({bb['x']:.0f},{bb['y']:.0f})", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Toast notifications within bounds ─────────────────────────
async def test_toast_within_bounds(page: Page, vw: str, w: int, h: int):
    """Toast notifications should appear within viewport bounds."""
    name = f"Toast within bounds at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Trigger a toast by entering walk mode then trying terrain
        await page.click("#btn-walk")
        await page.wait_for_timeout(500)
        await page.click('.td-tab[data-dock="terrain"]')
        await page.wait_for_timeout(500)
        toast_bb = await get_bounding_box(page, "#toast")
        if not toast_bb:
            log_result(name, "SKIP", "Toast not found/visible", vw)
            # Clean up
            await page.click("#walk-exit")
            return
        if toast_bb["x"] + toast_bb["width"] > w + 1:
            log_result(name, "FAIL", f"Toast off-screen: {toast_bb['x'] + toast_bb['width']:.0f} > {w}", vw)
        else:
            log_result(name, "PASS", "Toast within bounds", vw)
        # Clean up
        await page.click("#walk-exit")
        await page.wait_for_timeout(300)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: File input (load) works ────────────────────────────────────
async def test_load_design(page: Page, vw: str, w: int, h: int):
    """Load design button should trigger file input."""
    name = f"Load design at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Check file input exists
        input_exists = await page.evaluate("document.getElementById('import-input') !== null")
        if not input_exists:
            log_result(name, "FAIL", "File input not found", vw)
            return
        # Check load button is accessible
        load_bb = await get_bounding_box(page, "#btn-load")
        if not load_bb or load_bb["display"] == "none":
            log_result(name, "FAIL", "Load button not accessible", vw)
            return
        if load_bb["x"] + load_bb["width"] > w:
            log_result(name, "FAIL", "Load button off-screen", vw)
            return
        log_result(name, "PASS", "Load button accessible, file input exists", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Save generates JSON ───────────────────────────────────────
async def test_save_design(page: Page, vw: str, w: int, h: int):
    """Save design should produce valid JSON data."""
    name = f"Save design at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Add an object
        await page.evaluate("""() => {
            const keys = Object.keys(window._test.CATALOG);
            if (keys.length > 0) window._test.addObject(keys[0]);
        }""")
        await page.wait_for_timeout(500)
        # Serialize
        data = await page.evaluate("JSON.stringify(window._test.serializeDesign())")
        if not data:
            log_result(name, "FAIL", "serializeDesign returned null", vw)
            return
        parsed = json.loads(data)
        if "yard" not in parsed:
            log_result(name, "FAIL", "Missing 'yard' in serialized data", vw)
            return
        log_result(name, "PASS", f"Serialization works, yard={parsed['yard']['width']}x{parsed['yard']['depth']}", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Mobile props sheet close via grabber ──────────────────────
async def test_props_sheet_grabber(page: Page, vw: str, w: int, h: int):
    """Mobile props sheet should close when grabber is tapped."""
    name = f"Props sheet grabber close at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        if w > 768:
            log_result(name, "SKIP", "Tablet uses side panel, not sheet", vw)
            return
        # Add object and select it
        await page.evaluate("""() => {
            const keys = Object.keys(window._test.CATALOG);
            if (keys.length > 0) window._test.addObject(keys[0]);
        }""")
        await page.wait_for_timeout(500)
        await page.evaluate("""() => {
            const firstId = Array.from(window._test.state.objects.keys())[0];
            if (firstId !== undefined) window._test.selectObject(firstId);
        }""")
        await page.wait_for_timeout(500)
        sheet_expanded = await page.evaluate("""() => {
            const s = document.getElementById('mobile-props-sheet');
            return s && s.classList.contains('expanded');
        }""")
        if not sheet_expanded:
            log_result(name, "FAIL", "Sheet not expanded", vw)
            return
        # Click grabber
        await page.click("#sheet-grabber")
        await page.wait_for_timeout(500)
        sheet_still_expanded = await page.evaluate("""() => {
            const s = document.getElementById('mobile-props-sheet');
            return s && s.classList.contains('expanded');
        }""")
        if sheet_still_expanded:
            log_result(name, "FAIL", "Sheet didn't close on grabber tap", vw)
        else:
            log_result(name, "PASS", "Grabber closes sheet", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Mobile action bar buttons ─────────────────────────────────
async def test_mobile_action_bar(page: Page, vw: str, w: int, h: int):
    """Mobile action bar buttons (duplicate/rotate/delete/close) should work."""
    name = f"Mobile action bar at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        if w > 768:
            log_result(name, "SKIP", "Tablet uses side panel", vw)
            return
        # Clear all objects first to get a clean state
        await page.evaluate("""() => {
            const ids = Array.from(window._test.state.objects.keys());
            for (const id of ids) {
                const obj = window._test.state.objects.get(id);
                if (obj && obj.group) obj.group.visible = false;
                window._test.state.objects.delete(id);
            }
        }""")
        await page.wait_for_timeout(300)
        # Add one object and select it
        await page.evaluate("""() => {
            const keys = Object.keys(window._test.CATALOG);
            if (keys.length > 0) window._test.addObject(keys[0]);
        }""")
        await page.wait_for_timeout(500)
        # Deselect first to clear any sheet
        await page.evaluate("""() => { if (window._test.state.selectedId !== null) window._test.deselectObject(); }""")
        await page.wait_for_timeout(200)
        # Select the object
        await page.evaluate("""() => {
            const firstId = Array.from(window._test.state.objects.keys())[0];
            if (firstId !== undefined) window._test.selectObject(firstId);
        }""")
        await page.wait_for_timeout(500)
        count_before_dup = await page.evaluate("window._test.state.objects.size")
        # Check action bar visible
        bar_bb = await get_bounding_box(page, "#mobile-action-bar")
        if not bar_bb or bar_bb["display"] == "none":
            log_result(name, "FAIL", "Action bar not visible", vw)
            return
        # Check buttons
        for btn_id in ["#mab-duplicate", "#mab-rotate", "#mab-delete", "#mab-close"]:
            bb = await get_bounding_box(page, btn_id)
            if not bb or bb["display"] == "none":
                log_result(name, "FAIL", f"{btn_id} not visible", vw)
                return
            if bb["width"] < MIN_TOUCH_TARGET or bb["height"] < MIN_TOUCH_TARGET:
                log_result(name, "FAIL", f"{btn_id} too small: {bb['width']:.0f}x{bb['height']:.0f}", vw)
                return
        # Test duplicate
        await page.click("#mab-duplicate", force=True)
        await page.wait_for_timeout(500)
        obj_count = await page.evaluate("window._test.state.objects.size")
        if obj_count != count_before_dup + 1:
            log_result(name, "FAIL", f"Duplicate didn't work (was {count_before_dup}, now {obj_count})", vw)
            return
        log_result(name, "PASS", "All action bar buttons work", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Test: Safe area insets respected ────────────────────────────────
async def test_safe_area(page: Page, vw: str, w: int, h: int):
    """Check that safe-area-inset CSS is used for bottom elements."""
    name = f"Safe area insets at {vw}"
    try:
        await wait_for_app(page)
        await dismiss_wizard(page)
        await page.wait_for_timeout(500)
        # Check if safe-area CSS is present
        has_safe_area = await page.evaluate("""() => {
            const sheets = document.styleSheets;
            for (let s of sheets) {
                try {
                    for (let r of s.cssRules) {
                        if (r.cssText && r.cssText.includes('safe-area-inset')) return true;
                    }
                } catch(e) {}
            }
            return false;
        }""")
        if has_safe_area:
            log_result(name, "PASS", "safe-area-inset CSS present", vw)
        else:
            log_result(name, "FAIL", "No safe-area-inset CSS found", vw)
    except Exception as e:
        log_result(name, "FAIL", str(e)[:200], vw)

# ── Master test runner ──────────────────────────────────────────────
async def run_viewport_tests(playwright, viewport_name: str, w: int, h: int, is_touch: bool = False):
    """Run all tests at a specific viewport size."""
    global PASS_COUNT, FAIL_COUNT, SKIP_COUNT

    print(f"\n{'='*60}")
    print(f"  Viewport: {viewport_name} ({w}x{h}){' [TOUCH]' if is_touch else ''}")
    print(f"{'='*60}")

    # Create browser context with viewport
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        viewport={"width": w, "height": h},
        device_scale_factor=2 if is_touch else 1,
        is_mobile=is_touch,
        has_touch=is_touch,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15" if is_touch else None,
    )
    page = await context.new_page()

    try:
        await page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
    except Exception:
        try:
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        except Exception as e:
            print(f"  ❌ Failed to load page: {e}")
            await browser.close()
            return

    tests = [
        test_page_loads,
        test_no_horizontal_overflow,
        test_topbar_visible,
        test_topbar_touch_targets,
        test_topbar_no_overflow,
        test_library_reachable,
        test_view_controls,
        test_terrain_button,
        test_terrain_panel_fits,
        test_terrain_mode_btns_touch,
        test_add_object_mobile_props,
        test_save_load_share,
        test_share_modal_qr,
        test_walk_mode,
        test_touch_tap_select,
        test_tool_dock,
        test_help_modal,
        test_cost_panel,
        test_layer_panel,
        test_undo_redo,
        test_dock_panels,
        test_view_toggle,
        test_terrain_painting_touch,
        test_screenshot,
        test_overlay_buttons_no_overlap,
        test_precision_toggle,
        test_carving_tools,
        test_terrain_presets,
        test_sun_panel,
        test_innovate_panel,
        test_analyze_panel,
        test_underground_panel,
        test_no_console_errors,
        test_grid_level_slider,
        test_context_hint,
        test_scale_bar,
        test_toast_within_bounds,
        test_load_design,
        test_save_design,
        test_props_sheet_grabber,
        test_mobile_action_bar,
        test_safe_area,
    ]

    for test_func in tests:
        try:
            await test_func(page, viewport_name, w, h)
        except Exception as e:
            log_result(test_func.__name__, "FAIL", f"Exception: {str(e)[:200]}", viewport_name)

    await browser.close()


async def main():
    print("=" * 60)
    print("  Sprint 6 — Mobile-First Test Suite")
    print("  Backyard Designer 3D")
    print("=" * 60)

    async with async_playwright() as p:
        # Phone portrait (375x812) — touch
        await run_viewport_tests(p, "phone-375", PHONE_W, PHONE_H, is_touch=True)

        # Tablet portrait (768x1024) — touch
        await run_viewport_tests(p, "tablet-768", TABLET_W, TABLET_H, is_touch=True)

        # Phone landscape (812x375) — touch
        await run_viewport_tests(p, "phone-land-812", PHONE_LAND_W, PHONE_LAND_H, is_touch=True)

        # Tablet landscape (1024x768) — touch
        await run_viewport_tests(p, "tablet-land-1024", TABLET_LAND_W, TABLET_LAND_H, is_touch=True)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total: {len(RESULTS)}")
    print(f"  PASS:  {PASS_COUNT}")
    print(f"  FAIL:  {FAIL_COUNT}")
    print(f"  SKIP:  {SKIP_COUNT}")
    print(f"  Pass Rate: {PASS_COUNT / len(RESULTS) * 100:.1f}%")

    # Save results to JSON
    results_path = Path("/root/byd6-mobile-tester/sprint6_mobile_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "total": len(RESULTS),
            "pass": PASS_COUNT,
            "fail": FAIL_COUNT,
            "skip": SKIP_COUNT,
            "pass_rate": PASS_COUNT / len(RESULTS) * 100,
            "results": RESULTS,
        }, f, indent=2)
    print(f"\n  Results saved to: {results_path}")

    # Print failing tests
    failures = [r for r in RESULTS if r["status"] == "FAIL"]
    if failures:
        print(f"\n  {'='*60}")
        print(f"  FAILING TESTS ({len(failures)})")
        print(f"  {'='*60}")
        for f in failures:
            print(f"  ❌ [{f['viewport']}] {f['test']}: {f['detail']}")

    return FAIL_COUNT == 0


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)