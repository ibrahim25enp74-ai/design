# Architecture

## Concept and form

This file applies to every building type and scale: houses, housing, schools, hospitals, mosques, offices, retail, hotels, cultural buildings, interiors, landscape and urban design, competitions and student projects. Project-specific facts belong in `projects.md`, not here.

Start from the site, the climate and the program. A form that responds to them is specific by default.

### Climate

| Climate | Start from |
|---|---|
| Hot, dry (Iraq, the Gulf, North Africa) | Shade first. Thermal mass, courtyards, cross-ventilation, deep reveals, small openings on east and west. |
| Hot, humid | Airflow first. Raised floors, deep roof overhangs, permeable walls, cross-ventilation. Avoid materials that rust or trap water. |
| Temperate | Daylight and seasonal sun. Openable facades, winter sun with summer shading. |
| Cold | Compactness and insulation. Collect the low sun, give entrances a protected threshold. |

- **Orientation** (northern hemisphere): south facades get horizontal shading. East and west facades get vertical fins or smaller openings. North facades can open up. If every facade looks the same, the building is ignoring the sun.

### Context

- **Heritage**: borrow principles, not ornaments. The mashrabiya means filtered light, privacy and airflow. Build those with perforated brick, timber screens or operable shutters, not a laser-cut pattern on a glass box. A courtyard is something you design in section, not a logo. Use an arch only where it actually spans something. The same applies to any local tradition.
- **Local materials**: use what the place builds with (in Mosul, for example, brick, Mosul marble, juss and stone). Use them honestly and let them set the palette of the drawings and boards too.

### Program

The concept usually comes from the program's own logic:
- **Retail and markets**: movement, shop rhythm, thresholds, shade.
- **Schools**: the in-between spaces where children actually spend their time.
- **Housing**: privacy gradients, from street to threshold to court to room.
- **Healthcare**: daylight and the shortest routes.
- **Mosques**: the qibla axis, light and the transition from street to prayer.

Ask what this program does that no other program does, and design that.

### Generic tells (architecture)

- Parametric fins or Voronoi skins with no climatic, structural or program reason
- A glass box in a hot climate
- Arches, domes or geometric patterns stuck on as heritage stickers
- A dramatic cantilever with no program reason
- Shuffled "pixel" windows
- White render + timber cladding + green roof on every project
- A facade composed only in elevation: everything flush, no depth or shadow
- Plans where the room shapes are driven by a facade gesture, or corridors lead nowhere

## Drawings (CAD / DXF)

### Line weight hierarchy (plotted, mm)

| Element | Weight |
|---|---|
| Cut walls and structure | 0.50–0.70 |
| Cut lighter elements (partitions, frames) | 0.35 |
| Projection and elevation edges | 0.25 |
| Beyond, furniture, fixtures | 0.18 |
| Hatch, dimensions, grids, hidden lines | 0.09–0.13 |

Every drawing needs at least three distinguishable weights: cut, then projection, then beyond. If everything plots at the same weight, the drawing reads flat.

### Rules

- Set line weights and colours by layer, not per entity. Follow the file's existing layer scheme rather than inventing a second one.
- **Poché**: use a solid fill for cut walls at 1:100 and smaller, and hatch patterns at 1:50 and larger. Use no more than three hatch patterns per sheet, always lighter than the lines around them.
- **Colour**: plot in black and greys. Use one accent colour, and only for the message: new versus existing, circulation, the intervention. No ACI rainbow plots.
- **Text at A3, 100%**: sheet titles 5–7 mm, drawing titles 3.5–5 mm, labels 2.5 mm, notes at least 1.8 mm. Use one font family and named text styles, not ad-hoc heights.
- **Dimensions**: one dimension style per scale, with strings aligned. Presentation sheets are not over-dimensioned.
- **Symbols**: north arrow, scale bar and section marks are small, share one style family and stay the same on every sheet. No clip-art north arrows.
- **Furniture and people**: simple line blocks at 0.13–0.18. No detailed pseudo-3D blocks in plan.
- **Trees**: light canopy outlines, one consistent symbol. No heavy clip art.

## Sheet layout (A3 / A1 sets)

- One hero drawing per sheet. Supporting drawings are smaller and aligned to the same grid.
- Margins, title block position and the baseline of drawing titles are identical on every sheet.
- Drawing titles sit at the same offset from their drawings everywhere.
- Leave roughly 25–35% of the sheet empty, because empty space is part of the composition. A lone small drawing floating in a large empty sheet is not restraint: scale it up or pair it.
- Order the set logically (site, plans, sections, elevations, details) and number the sheets sequentially.
- The title block is quiet, small and grey. The drawing is the hero, not the logo.
- Images on sheets (aerials, renders, photos) get one shared treatment across the set: either all full-bleed or all framed, with one colour grade.
- Check one sheet plotted at 100% and read the smallest text.

## Boards, diagrams and renders

- One story per board. Each diagram answers one question: sun, wind, circulation, program, structure or phasing.
- Diagrams share one arrow style, one line weight set, one accent colour and one axonometric angle across the set.
- Renders show the light and season that are true to the place: high, hard sun and deep shadows for Mosul, not a Nordic overcast sky. Show materials that will really be built, and people dressed for the place doing what people actually do there.
- No lens flare, no oversaturated sunset, no stock supercars, no clip-art birds or balloons.
- Prefer one strong drawing (section perspective, axonometric, detail) over yet another eye-level render.
- Give every image in a set the same colour grade.

## Checklist

- [ ] Concept traces back to a fact about the site, climate or program
- [ ] At least three line weights visible: cut > projection > beyond
- [ ] At most three hatch patterns per sheet, lighter than the lines
- [ ] One accent colour, used for meaning
- [ ] Same margins, title block and title baseline on every sheet
- [ ] Smallest plotted text is at least 1.8 mm
- [ ] No heritage stickers and no unjustified parametric skins
- [ ] Any Arabic text checked against `arabic-type.md`
