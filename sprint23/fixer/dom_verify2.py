"""DOM re-verification after the #properties move (html.parser based)."""
from html.parser import HTMLParser

html = open('/root/backyard-designer/index.html').read()

class DivTracker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.results = {}

    def handle_starttag(self, tag, attrs):
        if tag not in ('div', 'main', 'header', 'section', 'aside'):
            return
        d = dict(attrs)
        self.stack.append((tag, d.get('id')))
        if d.get('id') == 'properties':
            self.results['props_parent'] = self.stack[-2] if len(self.stack) >= 2 else None
            self.results['props_line'] = self.getpos()[0]

    def handle_endtag(self, tag):
        if tag not in ('div', 'main', 'header', 'section', 'aside'):
            return
        if self.stack and self.stack[-1][0] == tag:
            popped = self.stack.pop()
            if popped[1] == 'main':
                self.results['main_close_line'] = self.getpos()[0]
                self.results['main_children_seen'] = [x[1] for x in self.stack]

p = DivTracker()
p.feed(html)
print("props opens at line:", p.results.get('props_parent'))
print("main closed at line:", p.results.get('main_close_line'))
print("stack after main close:", p.results.get('main_children_seen'))

# Also: leftover stray </div> before season-panel? Count div balance in body region
open_divs = html.count('<div')
close_divs = html.count('</div>')
print(f"total <div: {open_divs}  </div>: {close_divs}  delta: {open_divs - close_divs}")