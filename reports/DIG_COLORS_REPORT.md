# Sprint 19 — Dig Color Enhancement Report

## Problem

When digging/excavating terrain below 0ft, the geological layer colors were applied but visually indistinct:
- All 4 geological layers were muted browns/grays that blended together
- The 25% brightness boost was insufficient for underground visibility
- No depth-based color banding was visible during active digging — holes looked uniformly brown
- The grass-to-earth transition band was only 0.5ft, too abrupt
- The `EXCAVATION_EARTH_COLOR` (0x5C4033) didn't match the geological layer palette

When raising terrain above 0ft, the grass→dirt→rock slope-based coloring was clear and visually distinct. Digging lacked this same clarity.

## Changes Made

### 1. Enhanced Geological Layer Colors (line ~7159)

| Layer | Before | After | Change |
|-------|--------|-------|--------|
| Topsoil (0 to -2ft) | 0x3b2818 (dark brown) | 0x4a301e (rich dark brown) | Slightly richer, more saturated |
| Subsoil (-2 to -6ft) | 0x8b6f47 (lighter brown) | 0x9b7a4f (warm brown) | Brighter, clearly lighter than topsoil |
| Clay (-6 to -12ft) | 0xa0553a (reddish) | 0xb85530 (clearly red/orange) | More saturated red, very distinct from subsoil |
| Bedrock (-12 to -15ft) | 0x707072 (gray) | 0x606068 (clearly gray) | Cooler gray, more distinct from clay |

### 2. Increased Brightness Boost: 25% → 45% (lines ~4386, ~7431)

- `applyTerrainVertexColors()`: boost changed from 1.25 to 1.45
- `buildSolidEarth()`: `UNDERGROUND_BRIGHTNESS_BOOST` changed from 0.25 to 0.45
- Makes underground colors clearly visible in the 3D scene

### 3. Widened Transition Band: 0.5ft → 1.5ft (line ~4379)

- `TRANSITION_BAND` changed from 0.5 to 1.5 feet
- The grass-to-earth transition at y=0 is now smoother but still clearly visible
- Uses the existing smoothstep blend function

### 4. Depth Band Stripes Every 2ft (lines ~4392-4398, ~7452-7456)

- Added subtle darker stripes at the top of every 2ft depth band
- `bandPhase = (depthBelowSurface % 2) / 2` — when bandPhase < 0.12, colors are darkened by 15%
- Applied to both surface terrain mesh and solid earth interior walls
- Creates visible "layer lines" during active digging, similar to geological strata

### 5. Layer Transition Width: 0.5ft → 0.75ft (line ~7165)

- `GEO_LAYER_TRANSITION_WIDTH` widened from 0.5 to 0.75 feet
- Smoother blends between named geological layers at boundaries

### 6. Updated EXCAVATION_EARTH_COLOR (line ~7125)

- Changed from 0x5C4033 to 0x6b4a2e
- Now matches the boosted topsoil/subsoil color range more closely
- Interior earth walls show the same layered coloring as the surface via `buildSolidEarth()`

## Verification

### Playwright Color Sampling

Dug a 30-radius hole to -15ft and sampled vertex colors across all 4 depth ranges:

| Layer | Avg RGB (normalized) | Visual |
|-------|---------------------|--------|
| Topsoil (0 to -2ft) | (0.343, 0.246, 0.166) | Rich dark brown ✓ |
| Subsoil (-2 to -6ft) | (0.835, 0.628, 0.403) | Warm lighter brown ✓ |
| Clay (-6 to -12ft) | (0.938, 0.490, 0.295) | Clearly red/orange ✓ |
| Bedrock (-12 to -15ft) | (0.596, 0.525, 0.537) | Clearly gray ✓ |

All 4 layers are visually distinct — bedrock has R≈G≈B (gray), clay is very red-dominant, subsoil is the lightest, and topsoil is the darkest.

### Quality Gate

- **Sprint 17 Quality Gate: 81/81 tests PASS, 0 failures**
- No console errors introduced
- No regressions in mode toggle, keyboard shortcuts, rendering, or FPS

## Files Modified

- `index.html` — 4 patches applied:
  1. Geological layer color definitions + transition width (line ~7156)
  2. `EXCAVATION_EARTH_COLOR` constant (line ~7125)
  3. `applyTerrainVertexColors()` — transition band, brightness boost, depth bands (line ~4376)
  4. `buildSolidEarth()` — brightness boost, depth bands (line ~7414)