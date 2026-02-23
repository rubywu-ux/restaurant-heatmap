# Heatmap Views Implementation Plan

## Inspiration Analysis

### Pin References Studied
| # | Reference | Key Takeaway |
|---|-----------|-------------|
| 1 | Landscapes of the Northeast Megaregion — Jeff Ferzoco | Warm earthy multi-color gradient on muted natural base tiles |
| 2 | Feltron — Finland Population Change | Ultra-minimal, monochrome blue on dark background, grid-like precision |
| 3 | Vietnam War Bombing Missions (USDOD) | Glowing dots on pure black — no heat blur, raw dot density tells the story |
| 4 | Austin Tree Density Map | Light clean background, organic green dots varying in size, nature palette |
| 5 | Urban Design Map Analysis | Soft green/yellow transparent overlay on desaturated base, analytical feel |

---

## 5 Views to Implement

### View 1: "Classic Heat" (current default)
- **Tiles**: CartoDB Positron (light gray)
- **Palette**: Red → Yellow gradient
- **Markers**: Tiny red dots (3-4px)
- **Vibe**: Standard clean data viz
- **Status**: ✅ Already implemented

### View 2: "Dark Neon"
- **Tiles**: CartoDB Dark Matter (black)
- **Palette**: Cyan → Magenta → Yellow (electric neon gradient)
- **Markers**: Tiny glowing cyan dots with subtle glow
- **Vibe**: Feltron + Vietnam pin mashup — dramatic, editorial, cinematic
- **Implementation**:
  - [ ] Swap tile layer to `CartoDB dark_matter`
  - [ ] Custom Leaflet heatmap gradient: `{0.2: '#0ff', 0.5: '#f0f', 0.8: '#ff0', 1.0: '#fff'}`
  - [ ] Cyan CircleMarkers with `0.7` opacity
  - [ ] Increase heatmap `radius` and `blur` for glow effect

### View 3: "Dot Density"
- **Tiles**: Stadia.AlidadeSmoothDark (dark muted)
- **Palette**: No heatmap layer at all
- **Markers**: Each visit = 1 glowing orange dot (like bombing map)
- **Vibe**: Raw data, every single visit plotted as its own dot — visceral density
- **Implementation**:
  - [ ] Hide HeatMap layer entirely
  - [ ] Plot 1 CircleMarker per visit (not per restaurant) for true density
  - [ ] Small radius (2px), warm orange (`#ff6b35`), low opacity so overlap creates brightness
  - [ ] Dark tile layer for contrast

### View 4: "Minimal Blue"
- **Tiles**: CartoDB Positron (light)
- **Palette**: Monochrome blue gradient (`#e8f4fd → #1a73e8 → #0d47a1`)
- **Markers**: Blue dots, size scaled by visit count
- **Vibe**: Feltron — clean, corporate, data-journalism
- **Implementation**:
  - [ ] Blue heatmap gradient: `{0.3: '#e8f4fd', 0.6: '#64b5f6', 0.8: '#1a73e8', 1.0: '#0d47a1'}`
  - [ ] Blue CircleMarkers with thin stroke
  - [ ] Slightly larger radius for high-visit spots

### View 5: "Terrain Green"
- **Tiles**: Stadia.AlidadeSmooth or OpenTopoMap (earthy/natural)
- **Palette**: Green gradient (`#c8e6c9 → #4caf50 → #1b5e20`)
- **Markers**: Green dots, organic feel, size = count
- **Vibe**: Austin tree density + urban green analysis — nature/environment
- **Implementation**:
  - [ ] Green heatmap gradient: `{0.2: '#c8e6c9', 0.5: '#66bb6a', 0.8: '#2e7d32', 1.0: '#1b5e20'}`
  - [ ] Green CircleMarkers
  - [ ] Earthy tile layer to complement palette

---

## UI: View Switcher

**Position**: Top-left, below zoom controls (or top-right near search)  
**Design**: Pill-shaped segmented control, glassmorphism style matching existing UI  
**Behavior**: Clicking a view instantly swaps tiles + heatmap gradient + marker colors  

```
┌──────────────────────────────────────────────────────┐
│  Classic  │  Dark Neon  │  Dots  │  Blue  │  Green   │
└──────────────────────────────────────────────────────┘
```

### Technical Approach
1. **All in JS (client-side switching)** — no Python rebuild needed per view
2. Pre-define all 5 configurations as JS objects
3. On view switch:
   - Swap `L.tileLayer` 
   - Remove old heatmap, add new one with different `gradient` option
   - Restyle all CircleMarkers (color, radius, opacity)
4. Persist selected view in `localStorage`

---

## Implementation Checklist

- [ ] **Phase 1**: Build the view switcher UI (HTML/CSS in `get_top5_js`)
- [ ] **Phase 2**: Define 5 view config objects in JS
- [ ] **Phase 3**: Implement tile layer swapping
- [ ] **Phase 4**: Implement heatmap gradient swapping  
- [ ] **Phase 5**: Implement marker restyling
- [ ] **Phase 6**: Wire up click handlers + localStorage persistence
- [ ] **Phase 7**: Apply to both HTML files (global + Seattle)
- [ ] **Phase 8**: Test all views, commit and push

---

## File Changes
| File | Change |
|------|--------|
| `build_heatmap.py` | Add view switcher HTML/CSS/JS to `get_top5_js()`, change marker/heatmap creation to support dynamic restyling |
| `restaurant_heatmap.html` | Auto-generated |
| `restaurant_heatmap_seattle.html` | Auto-generated |
