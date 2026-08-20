"""Shared helpers for Crash QA tests against Backyard Designer 3D."""
import os
import json
import time

BASE_URL = "http://localhost:8770/index.html"
SS_DIR = "/root/backyard-designer/crash-tests/screenshots"
os.makedirs(SS_DIR, exist_ok=True)

LAUNCH_ARGS = ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--use-gl=swiftshader']


def launch_browser(p):
    browser = p.chromium.launch(headless=True, args=LAUNCH_ARGS)
    context = browser.new_context(viewport={'width': 1280, 'height': 900},
                                  device_scale_factor=1)
    page = context.new_page()
    console_msgs = []
    page_msgs = []
    page_errors = []
    page.on("console", lambda m: console_msgs.append({
        'type': m.type, 'text': m.text, 'location': m.location
    }))
    page.on("pageerror", lambda e: page_errors.append({
        'message': str(e), 'stack': getattr(e, 'stack', None)
    }))
    page.on("requestfailed", lambda r: page_msgs.append({
        'url': r.url, 'failure': r.failure
    }))
    page.goto(BASE_URL, wait_until='networkidle', timeout=60000)
    # Wait for the wizard to appear (module loaded)
    page.wait_for_selector('#wizard', timeout=30000)
    return browser, context, page, {'console': console_msgs, 'page_errors': page_errors, 'failed_reqs': page_msgs}


def clear_console(page, state):
    state['console'].clear()
    state['page_errors'].clear()
    state['failed_reqs'].clear()


def finish_wizard(page, width=50, depth=100, shape='rectangle'):
    """Complete the onboarding wizard to get into the editor."""
    # Step 0: choose shape
    if shape == 'L':
        page.click('.shape-card[data-shape="L"]')
    page.click('#wizard-next')
    page.wait_for_selector('#wiz-width', timeout=5000)
    page.fill('#wiz-width', str(width))
    page.fill('#wiz-depth', str(depth))
    page.click('#wizard-finish')
    page.wait_for_selector('#library .lib-item', timeout=5000)
    page.wait_for_timeout(300)  # let init settle


def get_console_errors(state):
    """Return only genuine errors (exclude warnings about swiftshader, etc.)."""
    errs = []
    for c in state['console']:
        if c['type'] in ('error', 'warning'):
            txt = c['text']
            # Filter known benign swiftshader / gpu noise
            if 'swiftshader' in txt.lower() or 'gpu_driver_bug' in txt.lower():
                continue
            errs.append(txt)
    return errs


def get_page_errors(state):
    return [e['message'] for e in state['page_errors']]


def screenshot(page, name):
    path = os.path.join(SS_DIR, name + '.png')
    page.screenshot(path=path)
    return path


def add_object_by_name(page, lib_name):
    """Click the first library item whose text contains lib_name. Returns nothing."""
    # Find by text
    items = page.query_selector_all('#library .lib-item')
    for it in items:
        txt = it.inner_text().lower()
        if lib_name.lower() in txt:
            it.click()
            return True
    return False


def select_object_at_center(page):
    """Click the center of the viewport to select the object placed at origin."""
    box = page.query_selector('#viewport').bounding_box()
    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
    page.wait_for_timeout(200)


def count_objects_via_dom(page):
    """Count properties is hard; instead count via sceneObjects size using injected probe.
    Module-scoped, so we read the props panel which lists Object #N."""
    # Add a temporary object to read nextId indirectly — too invasive.
    # Instead: select none, then check #properties visibility won't tell count.
    # We use the toast/props to infer. Simpler: read the library panel state.
    return None