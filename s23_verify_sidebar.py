from playwright.sync_api import sync_playwright
URL = "http://localhost:8095/index.html"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    ctx = b.new_context(viewport={"width": 1280, "height": 800})
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(600)
    if pg.is_visible("#wizard"):
        pg.click("#wizard-skip")
        pg.wait_for_timeout(300)
    if pg.is_visible("#welcome-prompt"):
        pg.click("#wp-remind-later")
        pg.wait_for_timeout(300)
    # scroll sidebar fully down via mouse wheel over sidebar (real events)
    pg.hover("#sidebar")
    for _ in range(30):
        pg.mouse.wheel(0, 240)
        pg.wait_for_timeout(30)
    m = pg.evaluate("""()=>{
      const sb = document.getElementById('sidebar');
      const bar = document.getElementById('status-bar');
      const items = sb.querySelectorAll('.lib-item');
      const last = items[items.length-1];
      // also last category title (some categories may sit below last lib-item)
      const titles = sb.querySelectorAll('.cat-title');
      const lastTitle = titles[titles.length-1];
      const barTop = bar.getBoundingClientRect().top;
      const lr = last.getBoundingClientRect();
      const tr = lastTitle.getBoundingClientRect();
      return {barTop: Math.round(barTop), lastItemBottom: Math.round(lr.bottom), lastItemTop: Math.round(lr.top),
              lastTitleBottom: Math.round(tr.bottom), scrollTop: sb.scrollTop, scrollHeight: sb.scrollHeight,
              clientH: sb.clientHeight, padBottom: getComputedStyle(sb).paddingBottom,
              itemClearsBar: lr.bottom <= barTop, fullyVisible: lr.bottom <= Math.min(barTop, window.innerHeight)};
    }""")
    print(m)
    b.close()