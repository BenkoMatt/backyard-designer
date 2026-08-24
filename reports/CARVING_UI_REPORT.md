# CARVING UI REPORT — Agent 3: Carving UI Overhaul (Sprint 12)

## Summary

The underground carving UI has been overhauled from a confusing multi-step wizard to a simple, intuitive paint-style brush. Users can now dig underground and fill carved areas by simply selecting a mode and clicking-dragging on the terrain — exactly like painting.

## Problem Solved

**Before**: The carving UI required selecting a shape → clicking to set center → clicking again to commit. Three separate, overlapping carving systems existed, and the simplest brush-based functions (`carveWithBrush`/`fillWithBrush`) were completely disconnected from any UI.

**After**: Two new brush modes — **Dig** and **Fill** — have been added to the terrain mode buttons. They work exactly like the existing Raise/Excavate/Smooth/Erode modes: select the mode, click and drag on the ground. A depth slider controls how deep below the surface the carving goes.

## Changes Made

### New UI Elements
| Element | Description |
|---------|-------------|
| **Dig button** | New terrain mode button (purple when active). Carves underground in real-time via click-drag. |
| **Fill button** | New terrain mode button (green when active). Fills carved areas back in via click-drag. |
| **Dig Depth slider** | Range 0-30 ft, default 5 ft. Shown only when Dig/Fill mode is active. Controls carve depth below ground surface. |
| **Depth indicator** | Height readout shows "Digging to: X ft (Y ft deep)" when in Dig mode. |
| **Advanced Carving label** | Old shape selector (Box/Cylinder/Sphere) relabeled as "Advanced Carving (shape-based)" to indicate it's optional. |

### New JavaScript Functions
| Function | Purpose |
|----------|---------|
| `applyDigFillBrush(worldX, worldZ)` | Core function — calls `carveWithBrush` or `fillWithBrush` at cursor position with current `digDepth`. |
| `updateDigDepthReadout(worldX, worldZ)` | Updates height readout to show depth below ground level when digging. |

### Modified JavaScript Functions
| Function | Change |
|----------|--------|
| `onTerrainPointerDown` | Added dig/fill branch: initializes voxels, starts painting, calls `applyDigFillBrush`. |
| `onTerrainPointerMove` | Routes to `applyDigFillBrush` during drag when in dig/fill mode. |
| `moveBrushCursor` | Shows depth readout when in dig/fill mode, normal height readout otherwise. |
| `updateExcavationHint` | Shows excavation hint for Dig mode (in addition to Excavate mode). |
| Terrain mode button handler | Shows/hides depth slider, sets hint text, initializes voxels for dig/fill modes. |

### State Variables
| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `digDepth` | number | 5 | How deep below the surface the carve goes (0-30 ft) |

### CSS Changes
- `.terrain-mode-btn.dig-btn.active` — purple (`var(--carve)`) background when active
- `.terrain-mode-btn.fill-btn.active` — green (`#2a8a3a`) background when active
- Hover states for both dig and fill buttons

## How It Works

### Dig Mode
1. User clicks the **Dig** button in terrain mode
2. The Dig Depth slider appears (0-30 ft, default 5 ft)
3. User clicks and drags on the terrain
4. `onTerrainPointerDown` → `applyDigFillBrush(worldX, worldZ)`
5. `applyDigFillBrush` gets surface height, calls `carveWithBrush(wx, surfY - digDepth/2, wz)`
6. `carveWithBrush` calls `carveShape('sphere', ...)` which modifies voxel data
7. `carveShape` calls `buildVoxelMesh()` to rebuild the mesh in real-time
8. As user drags, `onTerrainPointerMove` → `applyDigFillBrush` continues carving
9. On pointer up, undo/redo is registered via voxel snapshots

### Fill Mode
1. User clicks the **Fill** button
2. User clicks and drags over a carved area
3. Same flow as Dig, but calls `fillWithBrush(wx, surfY + digDepth/2, wz)`
4. `fillWithBrush` calls `fillShape('sphere', ...)` which restores voxel solidity
5. `buildVoxelMesh()` updates the mesh in real-time

### Advanced Carving (preserved)
The existing two-click shape-based carving system (Box/Cylinder/Sphere via `carvingShape` and the "Carving Tools" Box/Cylinder/Trench via `carvingShapeMode`) is preserved unchanged. The shape selector is now labeled "Advanced Carving (shape-based)" and the hint text recommends using the Dig brush mode for simple digging.

## Test Results

### All Tests Pass ✅

| Test | Result |
|------|--------|
| Page loads without JS errors | ✅ |
| Dig button exists | ✅ |
| Fill button exists | ✅ |
| Depth slider exists | ✅ |
| Depth row visible when Dig selected | ✅ |
| Brush mode set to "dig" on click | ✅ |
| Dig carves voxels (256 voxels) | ✅ |
| Fill restores voxels (240 voxels) | ✅ |
| Depth slider controls carving depth (deep=220 > shallow=196) | ✅ |
| Depth slider UI works (15 ft → "15 ft" display) | ✅ |
| Advanced carving label present | ✅ |
| No page errors | ✅ |

## Verification

Run: `python3 test_final.py` in `/root/byd12-carving-ui/`

```
1. Page title: "Backyard Designer 3D"
2. Dig button: True, Fill button: True
3. Depth slider: True
4. Depth row visible after Dig: True (flex)
5. Brush mode: dig
6. Dig carved 256 voxels (before=38750, after=38494)
7. Dig works: True
8. Fill restored 240 voxels (before=38494, after=38734)
9. Fill works: True
10. Deep dig (25ft): 220 voxels, Shallow dig (2ft): 196 voxels
11. Depth controls carving: True
12. Slider sets depth: 15 (display: "15 ft")
13. Slider works: True
14. Advanced label: "Advanced Carving (shape-based)"
15. Advanced label correct: True
16. No page errors: True

=== FINAL: PASS ===
```

## Constraints Met
- ✅ Did NOT break existing features (Raise/Excavate/Smooth/Erode, advanced shape carving all preserved)
- ✅ Did NOT change VOXEL_SIZE or terrainSegs
- ✅ Three.js v0.160.0 via importmap (unchanged)
- ✅ Everything in single index.html
- ✅ Max depth: 30 ft below ground (slider max=30)
- ✅ Real-time carving (buildVoxelMesh called after each carve, fast enough for drag)

## Confirmation

The carving UI is now **simple and intuitive** — like painting, not a multi-step wizard. Users select "Dig", click-drag on the ground, and underground carving happens in real-time. The depth slider controls how deep the carve goes. "Fill" works the same way to restore carved areas. The old confusing two-click commit workflow is preserved as an "Advanced" option for users who need specific shapes.