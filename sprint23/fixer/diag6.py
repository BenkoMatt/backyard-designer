"""V01: is the pointer even reaching the canvas now? and V04: is wizard actually under guide?"""
from playwright.sync_api import sync_playwright
import json

BASE = "http://localhost:8304/index.html"

with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---- V01 full trace ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    page.keyboard.press("Escape"); page.wait_for_timeout(400)
    wp = page.locator("#wp-scratch")
    print("wp-scratch count:", wp.count(), "visible:", wp.is_visible() if wp.count() else None)
    if wp.count() > 0 and wp.is_visible():
        wp.click(); page.wait_for_timeout(300)
    print("welcome-prompt still visible:", page.evaluate("() => document.getElementById('welcome-prompt')?.classList.contains('visible')"))
    # instrument BEFORE placing object
    page.evaluate("""() => {
        window.__ptr = [];
        const vp = document.getElementById('viewport');
        ['pointerdown','pointermove','pointerup'].forEach(t =>
            vp.addEventListener(t, e => window.__ptr.push({t, x: Math.round(e.clientX), y: Math.round(e.clientY)})));
    }""")
    page.evaluate("() => { const i = document.querySelectorAll('.lib-item')[0]; if (i) i.click(); }")
    page.wait_for_timeout(600)
    screen = page.evaluate("""() => {
        const g = window._bydSceneObjects.get(1);
        const v = g.position.clone();
        v.project(window._bydActiveCamera);
        const vp = document.getElementById('viewport').getBoundingClientRect();
        return { x: vp.left + (v.x + 1) / 2 * vp.width, y: vp.top + (1 - v.y) / 2 * vp.height };
    }""")
    hit = page.evaluate("""([x, y]) => { const el = document.elementFromPoint(x, y);
        return el ? el.tagName + '#' + (el.id || el.className.toString().slice(0,30)) : 'none'; }""", [screen["x"], screen["y"]])
    print("hit at object center:", hit)
    page.mouse.move(screen["x"], screen["y"])
    page.mouse.down()
    page.mouse.move(screen["x"] + 80, screen["y"] + 40, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    print("vp events:", page.evaluate("() => window.__ptr"))
    print("pos:", page.evaluate("() => window._bydState.objects.get(1)?.position"))
    ctx.close()

    # ---- V04: which handler closed the wizard? add trace ----
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(BASE, timeout=30000)
    page.wait_for_timeout(1800)
    # instrument the wizard display setter
    page.evaluate("""() => {
        window.__wizLog = [];
        const wiz = document.getElementById('wizard');
        const obs = new MutationObserver(() => window.__wizLog.push('mutation:' + wiz.style.display));
        obs.observe(wiz, {attributes: true, attributeFilter: ['style']});
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') window.__wizLog.push('esc-seen target=' + e.target.tagName + ' defaultPrevented=' + e.defaultPrevented);
        }, true);
    }""")
    page.keyboard.press("F1"); page.wait_for_timeout(300)
    page.keyboard.press("Escape"); page.wait_for_timeout(300)
    print("V04 wizLog:", page.evaluate("() => window.__wizLog"))
    print("V04 final:", page.evaluate("""() => ({wiz: document.getElementById('wizard').style.display, guide: document.getElementById('shortcuts-modal').classList.contains('visible')})"""))
    ctx.close()
    browser.close()