# Backyard Designer 3D — Feature Inventory (from Sprint 5 Agent 1)

## Current UI Layout

### Top Bar (`#topbar`)
| Feature | ID | Type | Location | Notes |
|---------|-----|------|----------|-------|
| Brand logo/title | `.topbar-brand` | Text | Topbar left | "Backyard Designer 3D" |
| Undo | `#btn-undo` | Button | Topbar | Disabled by default |
| Redo | `#btn-redo` | Button | Topbar | Disabled by default |
| 3D View / Bird's-eye toggle | `#view-toggle` | Tab group | Topbar | 2-state toggle |
| Save Design | `#btn-save` | Button | Topbar | Downloads JSON |
| Load Design | `#btn-load` | Button | Topbar | File picker |
| Screenshot | `#btn-screenshot` | Button | Topbar | PNG capture |
| Help | `#btn-help` | Button | Topbar | Modal dialog |
| Layers | `#btn-layers` | Button | Topbar | Toggle panel (top-right) |
| Cost Estimator | `#btn-cost` | Button | Topbar | Toggle panel (top-right) |
| Walk Mode | `#btn-walk` | Button | Topbar | First-person mode |
| Share | `#btn-share` | Button | Topbar | QR + link modal |

### Left Sidebar (`#sidebar`)
| Feature | ID | Type | Location | Notes |
|---------|-----|------|----------|-------|
| Object Library | `#library` | Categorized list | Sidebar | Collapsible categories |

### Right Sidebar (`#properties`)
| Feature | ID | Type | Location | Notes |
|---------|-----|------|----------|-------|
| Object Properties | `#props-header`, `#props-body` | Panel | Right sidebar | Size, style, rotation, position, duplicate, delete |

### Viewport Overlays — Floating Buttons (bottom-left row)
| Feature | ID | Type | CSS Position | Problem |
|---------|-----|------|-------------|---------|
| Tape Measure | `#tape-measure-btn` | Toggle button | bottom:16px, left:200px | Floating |
| Terrain | `#terrain-btn` | Toggle button | bottom:16px, left:330px | Opens terrain panel |
| Sun & Shadow | `#sun-btn` | Toggle button | bottom:16px, left:410px | Opens sun panel |
| Excavate | `#excavate-btn` | Toggle button | bottom:16px, left:460px | Opens excavate panel |
| Analyze | `#terrain-analysis-btn` | Toggle button | bottom:16px, left:480px | Opens analysis panel |
| Innovate | `#innovation-btn` | Toggle button | bottom:16px, left:530px | Opens innovation panel |

### Viewport Overlays — Floating Panels
| Feature | ID | CSS Position | Problem |
|---------|-----|-------------|---------|
| Terrain Controls | `#terrain-controls` | bottom:56px, left:330px | Mega-panel, too many sections |
| Sun Panel | `#sun-panel` | bottom:56px, left:410px | Overlaps with terrain panel |
| Excavate Panel | `#excavate-panel` | bottom:56px, left:460px | Overlaps with analyze panel |
| Terrain Analysis Panel | `#terrain-analysis-panel` | bottom:56px, left:480px | Overlaps with excavate |
| Innovation Panel | `#innovation-panel` | bottom:56px, left:530px | MEGA-panel with 12+ tools |
| Cross-Section Panel | `#cross-section-panel` | top:16px, right:16px | Overlaps with cost/layer |
| Cost Panel | `#cost-panel` | top:16px, right:16px | Overlaps with layer panel |
| Layer Panel | `#layer-panel` | top:16px, right:16px | Overlaps with cost panel |
| Cut/Fill Panel | `#cut-fill-panel` | top:60px, right:280px | Floating, hard to find |
| Cross-Section Overlay | `#ta-cross-section-overlay` | bottom:16px, center | Appears on demand |

### Viewport Overlays — Info Displays
| Feature | ID | Position | Notes |
|---------|-----|----------|-------|
| Grid Level Badge | `#grid-level-badge` | top:16px, center | Shows when grid ≠ Y=0 |
| Depth Gauge Overlay | `#depth-gauge-overlay` | top:16px, right | Camera depth underground |
| Dimension Readout | `#dim-readout` | top:16px, left | Object dimensions |
| Safety Warnings | `#safety-warnings` | top:16px, right | Pool, fire, retaining wall |
| Context Hint | `#context-hint` | bottom:16px, center | Tooltip hint |
| Scale Bar | `#scale-bar` | bottom:16px, left | Distance reference |
| Height Legend | `#terrain-height-legend` | top:16px, left | Elevation color bar |
| Measure Readout | `#measure-readout` | follows cursor | Tape measure distance |
| Grid Labels | `#grid-labels` | inset:0 | 2D view measurements |

### View Controls (bottom-right)
| Feature | ID | Type |
|---------|-----|------|
| Zoom In | `#vc-zoom-in` | Button |
| Zoom Out | `#vc-zoom-out` | Button |
| Reset View | `#vc-reset` | Button |
| Go Underground | `#vc-underground` | Toggle button |

## Terrain Controls Panel (`#terrain-controls`)
| Feature | ID/Selector | Type | Section |
|---------|-------------|------|---------|
| Raise mode | `data-tmode="raise"` | Button | Brush modes |
| Excavate mode | `data-tmode="lower"` | Button | Brush modes |
| Smooth mode | `data-tmode="smooth"` | Button | Brush modes |
| Erode mode | `data-tmode="erode"` | Button | Brush modes |
| Brush Size | `#terrain-brush-size` | Slider | Brush settings |
| Strength | `#terrain-strength` | Slider | Brush settings |
| Precision Mode | `#precision-toggle` | Toggle | Brush settings |
| Height at cursor | `#terrain-height-readout` | Readout | Info |
| Grid Level slider | `#grid-level-slider` | Slider | Grid level |
| Ground Level display | `#grid-level-display` | Readout | Grid level |
| Depth Gauge inline | `#depth-gauge-inline` | Readout | Grid level |
| Voxel info | `#voxel-info` | Readout | Info |
| Excavation depth hint | `#excavation-depth-hint` | Text | Info |
| Carve Shape buttons | `#carve-shape-btns` | Button group | Carving |
| Carve Size | `#carve-size-slider` | Slider | Carving |
| Carve Depth | `#carve-depth-slider` | Slider | Carving |
| Carving Tools section | `.carving-section` | Section | Advanced carving |
| Carving shapes (Box/Round/Trench) | `.carving-shape-btn` | Buttons | Advanced carving |
| Carving Depth/Width/Length | `#carving-depth/width/length` | Sliders | Advanced carving |
| Carving Commit | `#carving-commit-btn` | Button | Advanced carving |
| Clear All Carvings | `#carving-clear-btn` | Button | Advanced carving |
| Terrain Presets | `.terrain-preset-btn` | Buttons | Presets (6 presets) |
| Height Colors overlay | `#terrain-toggle-height` | Toggle | Overlays |
| Drainage overlay | `#terrain-toggle-drainage` | Toggle | Overlays |
| Flatten All | `#terrain-flatten` | Button | Actions |

## Terrain Analysis Panel (`#terrain-analysis-panel`)
| Feature | ID | Type | Advanced? |
|---------|-----|------|-----------|
| Contour Lines toggle | `#ta-contour-toggle` | Toggle | No |
| Contour Interval | `#ta-contour-interval` | Number input | No |
| Slope Heatmap toggle | `#ta-slope-toggle` | Toggle | No |
| Cross-Section Profile button | `#ta-crosssection-btn` | Button | No |
| Cut/Fill Volume toggle | `#ta-cutfill-toggle` | Toggle | No |
| Water Flow Simulation toggle | `#ta-waterflow-toggle` | Toggle | Yes |
| Elevation Heatmap toggle | `#ta-elev-toggle` | Toggle | No |
| Buried Object Ghost View toggle | `#ta-ghost-toggle` | Toggle | Yes |
| Before/After Compare button | `#ta-compare-btn` | Button | Yes |

## Excavate Panel (`#excavate-panel`)
| Feature | ID | Type |
|---------|-----|------|
| Cutaway slider | `#terrain-cutaway` | Slider |
| Opacity slider | `#terrain-opacity` | Slider |
| Wireframe toggle | `#wireframe-toggle` | Button |
| Cross-Section toggle | `#cross-section-toggle` | Button |
| Buried Objects list | `#buried-objects-panel` | Panel |

## Innovation Panel (`#innovation-panel`)
| Feature | ID | Type | Advanced? |
|---------|-----|------|-----------|
| Pool Excavation Wizard | `#innov-pool-btn` | Button + sliders | No |
| Precision Flatten to Height | `#innov-flatten-btn` | Button + sliders | No |
| Elevation Markers | `#innov-marker-btn` | Button | No |
| Precision ADA Slope Tool | `#innov-slope-btn` | Button + sliders | Yes |
| Terrain Statistics Dashboard | `#innov-stats-btn` | Button | Yes |
| Auto Retaining Wall | `#innov-retwall-btn` | Button + sliders | Yes |
| Underground Structure Generator | `#innov-ugstruct-btn` | Button + sliders | Yes |
| Geological Layer Visualization | `#innov-geolayer-btn` | Button + sliders | Yes |
| Excavation Volume Calculator | `#innov-volcalc-btn` | Button | Yes |
| Exploded View | `#innov-exploded-btn` | Button + slider | Yes |
| Water Table Visualization | `#innov-watertable-btn` | Button + slider | Yes |
| Underground Ghost Preview | `#innov-ghostpreview-btn` | Button | Yes |

## Sun Panel (`#sun-panel`)
| Feature | ID | Type |
|---------|-----|------|
| Use My Location | `#sun-geo` | Button |
| Latitude | `#sun-lat` | Number input |
| Longitude | `#sun-lng` | Number input |
| City presets | `#sun-presets` | Buttons |
| Date | `#sun-date` | Date input |
| Time of day | `#sun-time` | Slider |
| Play Day Cycle | `#sun-play` | Button |
| Reset | `#sun-reset` | Button |

## Modals & Overlays
| Feature | ID | Type |
|---------|-----|------|
| Share/QR Modal | `#share-modal` | Modal |
| Walk Mode Controls | `#walk-controls` | Overlay |
| Setup Wizard | `#wizard` | Modal |
| Help Dialog | `#help-modal` | Modal |
| Toast notifications | `#toast` | Overlay |
| Mobile Properties Sheet | `#mobile-props-sheet` | Bottom sheet |

## Problem Summary
1. **6 floating buttons** at hardcoded left positions (200px, 330px, 410px, 460px, 480px, 530px) — overlap on smaller screens, no logical grouping
2. **Innovation panel** is a mega-panel with 12 tools — too long, no progressive disclosure
3. **Terrain panel** has 20+ controls mixed together — basic and advanced at same level
4. **Cost/Layer panels** share the same top:16px; right:16px position — they overlap
5. **No logical hierarchy** — all tools at same level with no grouping
6. **Advanced features** buried with no progressive disclosure
7. **Cross-section** appears in both Excavate and Analysis panel — confusing duplication
8. **Cut/Fill panel** floats at top:60px; right:280px — hard to discover