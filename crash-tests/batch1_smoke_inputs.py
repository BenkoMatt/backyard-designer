"""Crash Test Batch 1 (v2): Smoke + invalid inputs. Reuse ONE browser, new pages per test."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

RESULTS = []

def rec(name, status, detail="", ss=None, errors=None):
    RESULTS.append({'test': name, 'status': status, 'detail': detail[:300], 'ss': ss, 'errors': errors or []})
    print(f"[{status}] {name}: {detail[:250]}", flush=True)

def new_page(browser):
    """Create a fresh page with console/error capture."""
    ctx = browser.new_context(viewport={'width':1280,'height':900}, device_scale_factor=1)
    page = ctx.new_page()
    state = {'console':[], 'page_errors':[], 'failed_reqs':[]}
    page.on("console", lambda m: state['console'].append({'type':m.type,'text':m.text}))
    page.on("pageerror", lambda e: state['page_errors'].append({'message':str(e),'stack':getattr(e,'stack',None)}))
    return ctx, page, state

def load(page, state, url=None):
    page.goto(url or "http://localhost:8770/index.html", wait_until='networkidle', timeout=60000)
    page.wait_for_selector('#wizard', timeout=30000)

def cerrs(state):
    out=[]
    for c in state['console']:
        if c['type'] in ('error','warning'):
            t=c['text']
            if 'swiftshader' in t.lower() or 'gpu_driver_bug' in t.lower() or 'WebGL: ' in t:
                continue
            out.append(t)
    return out

def perrs(state): return [e['message'] for e in state['page_errors']]

def finish_wizard(page, width=50, depth=100):
    page.click('#wizard-next')
    page.wait_for_selector('#wiz-width', timeout=5000)
    page.fill('#wiz-width', str(width))
    page.fill('#wiz-depth', str(depth))
    page.click('#wizard-finish')
    page.wait_for_selector('#library .lib-item', timeout=5000)
    page.wait_for_timeout(250)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox','--disable-setuid-sandbox','--disable-gpu','--use-gl=swiftshader'])
        try:
            # ---- smoke ----
            ctx, page, st = new_page(browser)
            load(page, st)
            wiz = page.query_selector('#wizard')
            rec("Page loads + wizard visible", "PASS" if wiz and wiz.is_visible() else "FAIL", "ok")
            pe = perrs(st)
            rec("Initial load clean (no pageerror)", "PASS" if not pe else "FAIL", "; ".join(pe)[:200], errors=pe)
            page.screenshot(path="/root/backyard-designer/crash-tests/screenshots/01_initial.png")

            # ---- wizard invalid dims (reuse browser, new page each) ----
            bad = ['-1','0','0.001','999999','NaN','Infinity','','abc','1e308','undefined','null',
                   '3.14159265358979','<script>alert(1)</script>']
            for val in bad:
                ctx2, page2, st2 = new_page(browser)
                try:
                    load(page2, st2)
                    page2.click('#wizard-next')
                    page2.wait_for_selector('#wiz-width', timeout=4000)
                    page2.fill('#wiz-width', val)
                    page2.fill('#wiz-depth', val)
                    page2.click('#wizard-finish')
                    page2.wait_for_timeout(700)
                    lib = page2.query_selector_all('#library .lib-item')
                    canvas = page2.query_selector('#viewport canvas')
                    pe2 = perrs(st2)
                    ce2 = cerrs(st2)
                    if pe2:
                        rec(f"Wizard dim='{val}'", "FAIL", f"pageerror: {pe2[0][:120]}", errors=pe2)
                    elif not lib or len(lib)==0:
                        rec(f"Wizard dim='{val}'", "FAIL", "no library items (editor didn't init)", errors=ce2)
                    elif not canvas:
                        rec(f"Wizard dim='{val}'", "FAIL", "no canvas")
                    else:
                        rec(f"Wizard dim='{val}'", "PASS", f"editor ok; {len(ce2)} console err(s)")
                        if ce2:
                            rec(f"  console for '{val}'", "INFO", " | ".join(ce2[:2]))
                except Exception as e:
                    rec(f"Wizard dim='{val}'", "FAIL", f"exception: {e}")
                finally:
                    ctx2.close()

            # ---- finish valid + editor ----
            finish_wizard(page)
            lib = page.query_selector_all('#library .lib-item')
            rec("Wizard completes -> editor", "PASS" if len(lib)>0 else "FAIL", f"{len(lib)} items")
            page.screenshot(path="/root/backyard-designer/crash-tests/screenshots/02_editor.png")

            # ---- localStorage corruption reload ----
            payloads = [("garbage","not json {{{"),("null","null"),("empty",""),
                        ("missing objects",json.dumps({"yard":{}})),
                        ("NaN yard",json.dumps({"objects":[],"yard":{"width":"NaN","depth":-1}})),
                        ("objects=string",json.dumps({"objects":"nope","yard":{"width":50}}))]
            for desc, pl in payloads:
                try:
                    page.evaluate(f"localStorage.setItem('backyard-design-autosave',{json.dumps(pl)})")
                    page.reload(wait_until='networkidle', timeout=60000)
                    page.wait_for_selector('#wizard', timeout=30000)
                    pe3 = perrs(st)
                    if pe3:
                        rec(f"localStorage='{desc}' reload","FAIL",f"pageerror: {pe3[0][:120]}",errors=pe3)
                    else:
                        rec(f"localStorage='{desc}' reload","PASS","no crash on reload")
                except Exception as e:
                    rec(f"localStorage='{desc}' reload","FAIL",f"exception: {e}")
            ctx.close()
        finally:
            browser.close()

    print("\n"+"="*60, flush=True)
    print(f"BATCH1: {len(RESULTS)} tests, {sum(1 for r in RESULTS if r['status']=='FAIL')} FAIL", flush=True)
    return RESULTS

if __name__=='__main__':
    run()