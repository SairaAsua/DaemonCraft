---
name: minecraft-goals
description: Dynamic goal-setting and phase progression for Minecraft survival
triggers:
  - minecraft goals
  - what should I do next
  - survival progression
  - phase advancement
version: 1.0.0
---

# Minecraft Goal & Phase System

You have a **life trajectory** — you're not just reacting moment to moment. You advance through phases, set projects, and track progress.

## Phase Progression

Each phase has a clear goal. When you complete it, you advance to the next phase. Save your current phase to memory so you remember across turns.

### Phase 1: First Day (Spawn → Stone Tools)
**Goal:** Don't die. Get stone pickaxe, stone sword, crafting table, furnace, shelter, food.

**Checklist:**
- [ ] 4+ oak logs collected
- [ ] Crafting table placed
- [ ] Wooden pickaxe crafted
- [ ] 20+ cobblestone collected
- [ ] Stone pickaxe crafted
- [ ] Stone sword crafted
- [ ] Furnace crafted
- [ ] Shelter built (or dug into hillside)
- [ ] Food source secured (cooked meat or bread)
- [ ] Torches crafted and placed

**When complete:** Save to memory: "Phase 1 complete. Moving to Phase 2."

### Phase 2: Iron Age
**Goal:** Iron tools, shield, bucket.

**Checklist:**
- [ ] Iron ore located (Y=0 to 64)
- [ ] 11+ iron ore collected
- [ ] Iron ingots smelted
- [ ] Iron pickaxe crafted
- [ ] Iron sword crafted
- [ ] Shield crafted
- [ ] Bucket crafted

**When complete:** Save to memory: "Phase 2 complete. Moving to Phase 3."

### Phase 3: Diamond Hunt
**Goal:** Diamond pickaxe and sword.

**Checklist:**
- [ ] Mining at Y=-59
- [ ] 5+ diamonds collected
- [ ] Diamond pickaxe crafted
- [ ] Diamond sword crafted

**When complete:** Save to memory: "Phase 3 complete. Moving to Phase 4."

### Phase 4: Nether & Beyond
**Goal:** Nether access, blaze rods, ender pearls.

**Checklist:**
- [ ] 10+ obsidian collected
- [ ] Flint and steel crafted
- [ ] Nether portal lit
- [ ] Blaze rods collected
- [ ] Ender pearls collected

**When complete:** Save to memory: "Phase 4 complete. Ready for The End."

## How to Track Progress

**At the start of each turn, recall your phase:**
```
session_search(query="current phase survival")
```

**If no phase is recorded, you are in Phase 1.**

**Assess your current status against the checklist:**
```
mc_perceive(type="inventory")   → what tools do I have?
mc_perceive(type="status")      → where am I, what's my health?
mc_perceive(type="nearby")      → what resources are around me?
```

**Pick the NEXT uncompleted item on your checklist and do it.**

**After completing an item, update memory:**
```
memory(action="add", target="memory", content="Phase 2 progress: iron pickaxe crafted. Need shield and bucket next.")
```

## Setting Projects (Within Phases)

Sometimes a checklist item is big. Break it into a project:

**Example: "Build a shelter"**
1. Find flat ground → `mc_perceive(type="map")`
2. Collect materials → `mc_manage(action="bg_collect", block="cobblestone", count=24)`
3. Clear area → `mc_mine(action="dig", ...)` on obstacles
4. Build walls → `mc_build(action="fill", ...)`
5. Add roof → `mc_build(action="place", ...)`
6. Add door + torch → `mc_build(action="place", ...)`

**Track the project in memory:**
```
memory(action="add", target="memory", content="Shelter project: found spot at 100 64 200. Clearing area now.")
```

## Reacting to Events

**If your plans get interrupted (mob attack, player request, death):**
1. Save current project state to memory
2. Handle the interruption
3. Recall your project and resume

**If you die:**
1. Record what phase you were in
2. Record what you lost
3. Restart from Phase 1 checklist (you may complete items faster since you know what to do)

## Civilization Mode: Social Goals

In civilization mode, you also have **social goals** alongside survival:

- **Marcus:** Build group shelter. Keep everyone alive.
- **Sarah:** Secure food supply. Mediate conflicts.
- **Jin:** Map the island. Find resources. Share knowledge selectively.
- **Dave:** Be useful. Be liked. Don't be left behind.
- **Lisa:** Scout independently. Mark locations. Stay self-sufficient.
- **Tommy:** Acquire resources. Stay unnoticed. Survive alone if needed.
- **Elena:** Lead in crisis. Heal the injured. Make hard calls.

**Each turn, balance your survival phase with your social agenda.**

## Landfolk Mode: Village Projects

In landfolk mode, your goals are communal:

- Build shared village structures
- Farm and maintain food supply
- Fish and trade
- Decorate and improve the village
- Help other villagers with their projects

**Track village projects collectively via chat and memory.**
