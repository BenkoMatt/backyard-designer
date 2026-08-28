"""Dump the open-element stack at key line numbers around #main/#properties."""
from html.parser import HTMLParser

html = open('/root/backyard-designer/index.html').read()

KEYS = {286, 1169, 1173, 1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190}

class StackDump(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag in ('div', 'main', 'header', 'section', 'aside'):
            d = dict(attrs)
            self.stack.append((tag, d.get('id')))
            if self.getpos()[0] in KEYS:
                print(f"L{self.getpos()[0]} OPEN  {tag}#{d.get('id')} -> stack: {self.stack}")

    def handle_endtag(self, tag):
        if tag in ('div', 'main', 'header', 'section', 'aside'):
            if self.getpos()[0] in KEYS:
                print(f"L{self.getpos()[0]} CLOSE {tag} (top was {self.stack[-1] if self.stack else None})")
            if self.stack and self.stack[-1][0] == tag:
                self.stack.pop()
            elif self.stack:
                # mismatch: pop until we find matching tag (browser error recovery approx)
                for i in range(len(self.stack) - 1, -1, -1):
                    if self.stack[i][0] == tag:
                        del self.stack[i:]
                        break

p = StackDump()
p.feed(html)