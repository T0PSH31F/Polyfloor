# Polyfloor 16x16 Asset Manifest

Curated master asset sheets and character walk-cycle spritesheets for GBA/DS-style corporate floor engine (`SPEC_POLYFLOOR.md`).

## Staged Assets Overview

| Asset Path                                         | Resolution (px) | Grid Size (tiles) | Role / Category                                   |
| :------------------------------------------------- | :-------------- | :---------------- | :------------------------------------------------ |
| `frontend/static/assets/room_builder.png`          | 1216 x 1744     | 76 x 109          | Structural Master Atlas (Walls, Floors, Doors)    |
| `frontend/static/assets/interiors.png`             | 256 x 17024     | 16 x 1064         | Office Furniture & Appliance Master Atlas         |
| `frontend/static/assets/characters/ceo.png`        | 768 x 288       | 48 x 18           | Executive / CEO Sprite Sheet (Formal Suit)        |
| `frontend/static/assets/characters/hr.png`         | 768 x 288       | 48 x 18           | HR Manager Sprite Sheet (Formal Blazer)           |
| `frontend/static/assets/characters/dev.png`        | 768 x 288       | 48 x 18           | Software Engineer Sprite Sheet (Casual Hoodie)    |
| `frontend/static/assets/characters/marketing.png`  | 768 x 288       | 48 x 18           | Marketing Lead Sprite Sheet (Smart Casual)        |
| `frontend/static/assets/characters/sentry.png`     | 768 x 256       | 48 x 16           | Security Sentry Sprite Sheet (Black Suit / Guard) |
| `frontend/static/assets/characters/researcher.png` | 384 x 96        | 24 x 6            | AI Researcher Sprite Sheet (Lab Coat)             |
| `frontend/static/assets/characters/executive.png`  | 768 x 288       | 48 x 18           | Board Executive Sprite Sheet (Pinstripe Suit)     |
| `frontend/static/assets/characters/intern.png`     | 768 x 288       | 48 x 18           | Engineering Intern Sprite Sheet (Casual Tee)      |
| `frontend/static/assets/characters/facilities.png` | 384 x 112       | 24 x 7            | Facilities / Ops Sprite Sheet (Work Overalls)     |

---

## Tile Grid Offsets & Key Regions

### 1. `room_builder.png` (76 x 109 tiles)

- **Walls & Pillars**: Tile X: [0..31], Tile Y: [0..39]
- **Floors & Connectors**: Tile X: [0..14], Tile Y: [40..79]
- **Borders & Shadows**: Tile X: [0..44], Tile Y: [80..89]
- **Entryways & Archways**: Tile X: [0..9], Tile Y: [90..108]

### 2. `interiors.png` (16 x 1064 tiles)

- **Generic Office Furniture** (Desks, Swivel Chairs, Computers, Water Coolers): Tile Y: [0..77] (px Y: 0..1248)
- **Library & Filing** (Bookshelves, Storage Desks): Tile Y: [286..319] (px Y: 4576..5120)
- **Conference Room** (Long Tables, Projectors, Podiums): Tile Y: [552..563] (px Y: 8832..9024)
- **Elevators & Transit Systems** (Doors, Stairs): Tile Y: [709..735] (px Y: 11344..11776)
- **Lab & Data Center Equipment** (Server Racks, Monitors, Science Desks): Tile Y: [781..890] (px Y: 12496..14256)

---

## Character Walk-Cycle Format

- **Base Grid Resolution**: 16x16 px tile base (Sprite bounding height: 32px).
- **Directional Rows**: 4 Cardinal Directions (Right, Up, Left, Down).
- **Walk Cycle Frames**: 4 to 6 walk frames per direction.
- **Action Rows**: Includes idle, walk, sit, and phone/reading variants.
