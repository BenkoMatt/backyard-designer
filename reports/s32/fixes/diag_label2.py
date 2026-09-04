"""P1 label edit/delete: dblclick the sprite -> edit modal? rename + delete paths."""
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
    pg.wait_for_timeout(500)
    pg.evaluate("() => { document.getElementById('label-text-input').value = 'Garden'; document.getElementById('label-save-btn').click(); }")
    pg.wait_for_timeout(400)
    pos = pg.evaluate("""() => {
      let sp = null;
      window.scene.traverse(o => { if (o.type === 'Sprite' && !sp) sp = o; });
      const cam = window.activeCamera;
      const p = sp.position.clone().project(cam);
      const canvas = document.querySelector('canvas');
      const cr = canvas.getBoundingClientRect();
      return { ndc: { x: p.x, y: p.y }, w: cr.width, h: cr.height, left: cr.left, top: cr.top };
    }""")
    sx = pos['left'] + (pos['ndc']['x'] * 0.5 + 0.5) * pos['w']
    sy = pos['top'] + (-pos['ndc']['y'] * 0.5 + 0.5) * pos['h']
    print('screen:', round(sx), round(sy))
    pg.mouse.dblclick(sx, sy)
    pg.wait_for_timeout(600)
    s3 = pg.evaluate("""() => ({
        modalVisible: document.getElementById('label-edit-modal').classList.contains('visible'),
        inputVal: document.getElementById('label-text-input').value,
        deleteShown: document.getElementById('label-delete-btn').style.display
    })""")
    print('after dblclick:', s3)
    b.close()