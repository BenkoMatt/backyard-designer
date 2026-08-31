"""Verify innovate dock: single header, zero overlaps; re-run audit matrix."""
from playwright.sync_api import sync_playwright
from s23a_common import load_app, to_advanced
import s23a_common
s23a_common.URL = "http://localhost:8092/index.html"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox", "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1280, "height": 800})
    load_app(pg)
    to_advanced(pg)
    pg.click('.td-tab[data-dock="innovate"]')
    pg.wait_for_timeout(600)
    r = pg.evaluate("""() => {
        const inner = document.getElementById('dock-innovate-content').querySelector('.innov-header');
        const innerDisp = inner ? getComputedStyle(inner).display : 'absent';
        const dk = document.getElementById('dock-innovate').getBoundingClientRect();
        const td = document.getElementById('tool-dock').getBoundingClientRect();
        const bar = document.getElementById('bottom-left-toolbar').getBoundingClientRect();
        const inter = (a, c) => Math.max(0, Math.min(a.right, c.right) - Math.max(a.left, c.left)) *
                                Math.max(0, Math.min(a.bottom, c.bottom) - Math.max(a.top, c.top));
        return { innerHeaderDisplay: innerDisp, dock_vs_tooldock: Math.round(inter(dk, td)),
                 dock_vs_toolbar: Math.round(inter(dk, bar)) };
    }""")
    print(r)
    pg.screenshot(path="reports/sprint23_panel_audit/after2_innovate.png")
    b.close()