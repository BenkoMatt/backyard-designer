"""Line-range splice: replace V04 Escape block between exact marker lines."""
path = '/root/backyard-designer/index.html'
lines = open(path).read().split('\n')

start = None
for i, ln in enumerate(lines):
    if "} else if (e.key === 'Escape') {" in ln and i + 1 < len(lines) and 'Sprint 23 fix (S23-V04)' in lines[i + 1]:
        start = i
        break
assert start is not None, 'start marker not found'

end = None
for j in range(start, len(lines)):
    if 'deselectObject(); clearMultiSelect(); hideContextMenu();' in lines[j]:
        end = j
        break
assert end is not None, 'end marker not found'

print('start line (1-idx):', start + 1, repr(lines[start]))
print('end line (1-idx):', end + 1, repr(lines[end]))

new_block = """} else if (e.key === 'Escape') {
// Sprint 23 fix (S23-V04): close only the TOPMOST layer per Escape press
// (array order = z-order; the first open layer closes, everything else stays).
let modalClosed = false;
const escapeLayers = [
['help-modal', 'class', () => closeModal('help-modal')],
['shortcuts-modal', 'class', () => closeModal('shortcuts-modal')],
['share-modal', 'class', () => closeModal('share-modal')],
['templates-modal', 'display', () => { document.getElementById('templates-modal').style.display = 'none'; }],
['gallery-modal', 'display', () => { document.getElementById('gallery-modal').style.display = 'none'; }],
['timelapse-modal', 'display', () => { document.getElementById('timelapse-modal').style.display = 'none'; }],
['socialcard-modal', 'display', () => { document.getElementById('socialcard-modal').style.display = 'none'; }],
['label-edit-modal', 'display', () => { document.getElementById('label-edit-modal').style.display = 'none'; }],
['export-menu', 'display', () => { document.getElementById('export-menu').style.display = 'none'; }],
];
for (const [layerId, kind, closer] of escapeLayers) {
const el = document.getElementById(layerId);
const open = kind === 'class' ? (el && el.classList.contains('visible'))
: (el && getComputedStyle(el).display !== 'none');
if (open) { closer(); modalClosed = true; break; }
}
if (!modalClosed) {
// Close dock panels
if (typeof window._dockClosePanel === 'function' && window._dockActiveTab && window._dockActiveTab()) {
window._dockClosePanel();
modalClosed = true;
}
}
if (!modalClosed) {
// Close right-side floating panels (use exposed close functions for IIFE-scoped panels)
const floatingPanelIds = [
'season-panel', 'growth-panel', 'permit-panel',
'cost-panel', 'layer-panel', 'cross-section-panel', 'cut-fill-panel', 'ta-cross-section-overlay'
];
for (const fpId of floatingPanelIds) {
const el = document.getElementById(fpId);
if (el && el.classList.contains('visible')) {
if (fpId === 'season-panel' && window._closeSeasonPanel) { window._closeSeasonPanel(); }
else if (fpId === 'growth-panel' && window._closeGrowthPanel) { window._closeGrowthPanel(); }
else if (fpId === 'permit-panel' && window._closePermitPanel) { window._closePermitPanel(); }
else {
el.classList.remove('visible');
if (fpId === 'cost-panel') { document.getElementById('btn-cost')?.classList.remove('active'); if (typeof costPanelVisible !== 'undefined') costPanelVisible = false; }
if (fpId === 'layer-panel') { document.getElementById('btn-layers')?.classList.remove('active'); if (typeof layerPanelVisible !== 'undefined') layerPanelVisible = false; }
}
modalClosed = true;
break; // Sprint 23 fix (S23-V04): topmost layer only
}
}
}
if (!modalClosed) { deselectObject(); clearMultiSelect(); hideContextMenu(); }"""

lines[start:end + 1] = new_block.split('\n')
open(path, 'w').write('\n'.join(lines))
print('spliced OK; new line count:', len(lines))