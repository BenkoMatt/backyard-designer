"""Dump live terrain, simulate marchContourLevel + ribbon build in Python, find the degeneracy."""
import json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8380/index.html"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--enable-unsafe-swiftshader","--use-gl=swiftshader","--disable-gpu-sandbox","--no-sandbox"])
    pg = b.new_context(viewport={"width":1280,"height":800}).new_page()
    pg.set_default_timeout(20000)
    pg.goto(BASE, wait_until="load", timeout=60000); pg.wait_for_timeout(2200)
    pg.evaluate("() => document.getElementById('wizard-skip')?.click()"); pg.wait_for_timeout(900)
    pg.evaluate("() => window.setMode('advanced')"); pg.wait_for_timeout(400)
    pg.evaluate("""() => {
      const T = window._test;
      T.ensureTerrainArray();
      for (let iz = 60; iz <= 100; iz++) for (let ix = 70; ix <= 110; ix++) {
        const dx = (ix-85)/25, dz = (iz-80)/20;
        const d = Math.sqrt(dx*dx+dz*dz);
        if (d < 1) T.state.terrain[iz*201+ix] = -15*(1-d)*(1-d);
      }
      T.applyTerrainToMesh();
    }""")
    pg.wait_for_timeout(1500)
    ter = pg.evaluate("() => Array.from(window._test.state.terrain)")
    json.dump(ter, open('/tmp/terrain_live.json','w'))
    print('terrain len:', len(ter), 'min:', min(ter), 'max:', max(ter))
    b.close()
# simulate in python
segs = 200; halfW = 25; halfD = 50; cellW = 0.25; cellD = 0.5
level = -14.95
def h(ix, iz):
    v = ter[iz*(segs+1)+ix]
    return v if v else 0
pts = []
for iz in range(segs):
    for ix in range(segs):
        h00, h10, h11, h01 = h(ix,iz), h(ix+1,iz), h(ix+1,iz+1), h(ix,iz+1)
        x0, x1 = ix*cellW-halfW, (ix+1)*cellW-halfW
        z0, z1 = iz*cellD-halfD, (iz+1)*cellD-halfD
        def interp(ha, hb, xa, xb, za, zb):
            if hb == ha: return None
            t = (level-ha)/(hb-ha)
            if t < 0 or t > 1: return None
            return (xa+t*(xb-xa), level+0.05, za+t*(zb-za))
        e = [interp(h00,h10,x0,x1,z0,z0), interp(h10,h11,x1,x1,z0,z1), interp(h01,h11,x0,x1,z1,z1), interp(h00,h01,x0,x0,z0,z1)]
        v = [p for p in e if p is not None]
        if len(v) == 2:
            pts.extend(v[0]); pts.extend(v[1])
        elif len(v) == 4:
            pts.extend(v[0]); pts.extend(v[1]); pts.extend(v[2]); pts.extend(v[3])
print('segments:', len(pts)/6)
print('first 18:', [round(v,2) for v in pts[:18]])
# check degeneracy: consecutive pairs equal?
degen = sum(1 for i in range(0, len(pts)-5, 6) if pts[i]==pts[i+3] and pts[i+1]==pts[i+4] and pts[i+2]==pts[i+5])
print('degenerate pairs:', degen)