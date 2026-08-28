"""Find exact nesting of #properties relative to #main using html.parser."""
from html.parser import HTMLParser

html = open('/root/backyard-designer/index.html').read()

class DivTracker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []          # (tag, id_attr)
        self.props_parent = None
        self.main_close_pos = None
        self.props_start = None
        self.props_end = None
        self.in_props_depth = 0
        self.found_props_close = False

    def handle_starttag(self, tag, attrs):
        if tag not in ('div', 'main', 'header', 'section', 'aside', 'nav', 'footer'):
            return
        d = dict(attrs)
        self.stack.append((tag, d.get('id')))
        if d.get('id') == 'properties':
            self.props_start = self.getpos()
            self.props_parent = self.stack[-2][1] if len(self.stack) >= 2 else None
            print(f"#properties opens at {self.getpos()}, parent id on stack: {self.stack[-3:]}")
            self.in_props_depth = 1

    def handle_endtag(self, tag):
        if tag not in ('div', 'main', 'header', 'section', 'aside', 'nav', 'footer'):
            return
        if not self.stack:
            return
        top_tag, top_id = self.stack[-1]
        if top_tag == tag:
            popped = self.stack.pop()
            if popped[1] == 'main' and self.main_close_pos is None:
                self.main_close_pos = self.getpos()
                print(f"#main closes at {self.getpos()}; stack after close: {self.stack[-3:]}")
            if self.in_props_depth > 0:
                self.in_props_depth -= 1
                if self.in_props_depth == 0 and not self.found_props_close:
                    self.props_end = self.getpos()
                    self.found_props_close = True
                    print(f"#properties closes at {self.getpos()}; stack after close: {self.stack[-3:]}")

p = DivTracker()
p.feed(html)
print("props_start:", p.props_start, "props_end:", p.props_end)
print("main_close_pos:", p.main_close_pos)
print("props_parent id:", p.props_parent)