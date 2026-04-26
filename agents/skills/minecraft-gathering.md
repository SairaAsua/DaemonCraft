# Gathering & Resource Collection

## Core Principle

Gathering is not a single action — it's a pipeline: **find → verify → collect → verify drops → repeat**.

## Non-Solid Plants (Grass, Flowers, Tall Grass, Ferns)

These are **too small for line-of-sight raycasting**. The bot cannot "see" them the way it sees a tree or stone.

**Correct approach:**
1. **Scan:** `mc_mine(action="find_blocks", block="grass", radius=16, count=20)` — this searches by block ID, not visibility
2. **Verify:** Check the returned coordinates. Grass plants are at ground level (Y = surface).
3. **Harvest:** `mc_mine(action="dig", x=X, y=Y, z=Z)` on exact coordinates from find_blocks
4. **Pickup:** `mc_mine(action="pickup")` after breaking several
5. **Repeat:** Break 50-100 grass plants to expect 5-10 wheat_seeds (10% drop rate)

**Common mistakes:**
- ❌ `mc_mine(action="collect", block="grass", count=20)` in fair-play mode — fails because grass isn't visible to raycast
- ❌ Giving up after 10-20 blocks — with 10% drop rate, you need volume
- ❌ Breaking `grass_block` (dirt with green top) instead of `grass` (small plant) — grass_block drops dirt, not seeds

## Bulk Collection Strategy

For resources with probabilistic drops (grass → seeds, gravel → flint, leaves → saplings):

1. **Set a bulk goal:** Break 50-100 blocks before checking inventory
2. **Use background tasks:** `mc_manage(action="bg_collect", block="oak_log", count=32)` — let it run while you do other things
3. **Check progress:** `mc_perceive(type="inventory")` after the task completes
4. **Adapt:** If drops are low, collect more. Don't micro-manage every single block.

## Solid Blocks (Logs, Stone, Ores)

For solid blocks, standard collection works:
1. `mc_mine(action="collect", block="oak_log", count=16)` — finds visible blocks and mines them
2. If no blocks found: `mc_perceive(type="nearby")` to locate resources, then move closer
3. For underground: `mc_mine(action="dig", x=X, y=Y, z=Z)` on known coordinates

## Inventory Management While Gathering

- Tools break — check durability in status, craft backups before they break
- Inventory fills up — deposit at base or toss junk (dirt, cobblestone) if needed
- If full: return to base, deposit, resume gathering

## Drop Rate Reference

| Source | Drop | Rate |
|--------|------|------|
| grass | wheat_seeds | ~10% |
| tall_grass | wheat_seeds | ~10% |
| fern | wheat_seeds | ~10% |
| gravel | flint | ~10% |
| oak_leaves | oak_sapling | ~5% |
| oak_leaves | apple | ~0.5% |

**Rule of thumb:** For 10% drops, break 10x what you need. For 5% drops, break 20x.
