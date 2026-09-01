cd /root/byd23-toast-hygiene
python3 - << 'PYEOF'
p = '/root/byd23-toast-hygiene/index.html'
s = open(p, encoding='utf-8').read()
# Hide the empty "Recently Used" section until it has chips (basic-mode first
# load shows header + nothing — vision flags as lost content).
old = ("const sidebar = document.getElementById('library');\n"
       "if (sidebar) {\n"
       "const recentDiv = document.createElement('div');\n"
       "recentDiv.className = 'recent-section';\n"
       "recentDiv.innerHTML = '<div class=\"recent-title\">Recently Used</div><div id=\"recent-items\"></div>';\n"
       "sidebar.parentNode.insertBefore(recentDiv, sidebar);\n"
       "}")
new = ("const sidebar = document.getElementById('library');\n"
       "if (sidebar) {\n"
       "const recentDiv = document.createElement('div');\n"
       "recentDiv.className = 'recent-section';\n"
       "recentDiv.style.display = 'none';  // Sprint 23: hidden until first use (empty header read as broken)\n"
       "recentDiv.innerHTML = '<div class=\"recent-title\">Recently Used</div><div id=\"recent-items\"></div>';\n"
       "sidebar.parentNode.insertBefore(recentDiv, sidebar);\n"
       "// sprint 23 hygiene: reveal 'Recently Used' only when a chip is added\n"
       "const _revealRecent = () => { recentDiv.style.display = ''; };\n"
       "if (typeof window !== 'undefined') window._revealRecent = _revealRecent;\n"
       "}")
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('recent-section gated.')
PYEOF
grep -n "recent-items" /root/byd23-toast-hygiene/index.html | head -4