"""P1 topbar wheel probe: shrink viewport so topbar overflows, wheel over it, check scrollLeft + camera."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":900,"height":700}).new_page()
    pg.set_default_timeout(20000)
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => document.getElementById('wp-scratch')?.click()"); pg.wait_for_timeout(900)
    st0 = pg.evaluate("""() => { const t = document.getElementById('topbar'); return { sw: t.scrollWidth, cw: t.clientWidth, sl: t.scrollLeft }; }""")
    print('topbar overflow state:', st0)
    box = pg.evaluate("() => { const r = document.getElementById('topbar').getBoundingClientRect(); return { x: r.left + r.width/2, y: r.top + r.height/2 }; }")
    pg.mouse.move(box['x'], box['y'])
    pg.mouse.wheel(0, 240)
    pg.wait_for_timeout(500)
    st1 = pg.evaluate("() => { const t = document.getElementById('topbar'); return { sl: t.scrollLeft, sw: t.scrollWidth }; }")
    print('after wheel deltaY=240 over topbar:', st1)
    cam = pg.evaluate("() => { const c = window.activeCamera; return { x: Math.round(c.position.x), y: Math.round(c.position.y), z: Math.round(c.position.z) }; }")
    print('camera after:', cam)
    b.close()