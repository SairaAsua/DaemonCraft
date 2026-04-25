---
name: minecraft-navigation
description: Navigation and exploration in Minecraft — finding biomes, structures, caves, ores, and efficient movement
triggers:
  - minecraft navigate
  - find biome
  - minecraft explore
  - find village
  - find cave
version: 3.2.0
---

# Minecraft Navigation

## Commands

```
mc_manage(action="bg_goto", x=X, y=Y, z=Z)     # pathfind to exact position
mc_move(action="follow", player="PLAYER")       # follow a player continuously
mc_move(action="stop")                           # stop movement
mc_perceive(type="status")                        # check position, biome, dimension
mc_perceive(type="nearby")                        # scan surroundings
mc_perceive(type="map")                           # ASCII top-down map
mc_perceive(type="map", radius=24)               # wider view (24-block radius)
```

## Coordinate System

- **X**: East (+) / West (-)
- **Y**: Height (0=bedrock, 64=sea level, 320=sky limit)
- **Z**: South (+) / North (-)

Always check `mc_perceive(type="status")` for current position before navigating.

## Navigation Pre-flight and Recovery

- Use `mc_perceive(type="map")`, `mc_perceive(type="look")`, or `mc_perceive(type="scene")` before choosing a destination.
- For long travel, use `mc_manage(action="bg_goto", ...)`, then `mc_manage(action="task_status")`; do not block your whole turn.
- If following a player fails with "not found nearby", they are not visible. Ask for coordinates, go to a known mark, or move to a vantage point.
- If navigation fails or times out, stop, observe current position, and choose a nearer waypoint. Do not retry the same far coordinates repeatedly.
- Avoid walking into water/lava/cliffs shown by scene/map.

## Finding Resources by Y-Level

```
Diamonds:       Y = -64 to -1    (best at Y = -59)
Iron:           Y = -64 to 72    (best at Y = 16)
Gold:           Y = -64 to 32    (best at Y = -16)
Coal:           Y = 0 to 192     (best at Y = 96)
Copper:         Y = -16 to 112   (best at Y = 48)
Lapis:          Y = -64 to 64    (best at Y = 0)
Redstone:       Y = -64 to 16    (best at Y = -59)
Emerald:        Y = -16 to 320   (mountain biomes only)
Ancient Debris: Y = 8 to 119     (best at Y = 15, Nether only)
```

## Finding Structures

Structures don't have search commands, but strategies:

- **Village**: explore plains, savanna, desert, taiga biomes
- **Cave/Ravine**: `mc_perceive(type="nearby")` near Y=40-60, or just explore
- **Stronghold**: throw eye of ender, follow direction
- **Nether Fortress**: explore nether, tend to be along Z axis
- **Ocean Monument**: find ocean biome, look for dark structure

## Exploration Strategies

### Spiral Search
Walk in expanding squares to cover area:
1. Go north 50 blocks
2. Turn east 50 blocks
3. Turn south 100 blocks
4. Turn west 100 blocks
5. Continue expanding

### Strip Mining (for ores)
1. `mc_manage(action="bg_goto", x=X, y=-59, z=Z)` — go to diamond level
2. Dig straight tunnel (2 high, 1 wide)
3. Branch tunnels every 3 blocks left and right
4. `mc_perceive(type="nearby")` periodically to check for ores

### Cave Exploration
1. `mc_perceive(type="nearby")` or look for openings
2. Bring torches (lots)
3. Place torches on RIGHT wall (so you can find way out: follow torches on LEFT)
4. `mc_perceive(type="status")` frequently — watch for mobs

## Saving Locations

When you find something important, save coordinates:
- Base location
- Mine entrance
- Village location
- Nether portal
- Mob spawner
- Good farming spot

Use: `mc_manage(action="mark", name="NAME")`
List: `mc_manage(action="marks")`
Return: `mc_manage(action="go_mark", name="NAME")`
