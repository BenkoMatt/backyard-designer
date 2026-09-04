"""P1 label edit/delete probe: add label, dblclick it, edit, delete."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
OUT = "/root/byd32-fix/reports/s32/fixes"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(20000)
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => document.getElementById('wp-scratch')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(400)
    pg.evaluate("() => document.getElementById('btn-label')?.click()")
    pg.wait_for_timeout(300)
    pg.mouse.click(640, 430)
    pg.wait_for_timeout(600)
    s1 = pg.evaluate("""() => ({
        modalVisible: document.getElementById('label-edit-modal').classList.contains('visible')
    })""")
    print('after yard click:', s1)
    pg.evaluate("() => { document.getElementById('label-text-input').value = 'Garden'; document.getElementById('label-save-btn').click(); }")
    pg.wait_for_timeout(400)
    s2 = pg.evaluate("""() => { let n = 0; window.scene.traverse(o => { if (o.type === 'Sprite') n++; }); return { sprites: n }; }""")
    print('sprites after save:', s2)
    b.close()