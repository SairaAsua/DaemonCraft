---
name: minecraft-survival
description: Master Minecraft survival skill — observe/think/act game loop, phase progression from spawn to Ender Dragon
triggers:
  - play minecraft
  - minecraft survival
  - beat the ender dragon
  - survive in minecraft
  - minecraft agent
version: 3.2.0
---

# Minecraft Survival — Master Skill

## Tools

You control your Minecraft bot via the `mc` tools:
```
mc_perceive(type="status")              # see everything — health, pos, inventory, nearby, chat
mc_perceive(type="inventory")           # detailed categorized inventory
mc_perceive(type="nearby")              # blocks + entities nearby
mc_perceive(type="read_chat")           # read player messages
mc_manage(action="bg_collect", block="BLOCK", count=N)   # find and mine N blocks
mc_craft(action="craft", item="ITEM")    # craft item (need crafting table nearby for 3x3)
mc_craft(action="recipes", item="ITEM")  # look up crafting recipe ingredients
mc_manage(action="smelt", item="INPUT")  # smelt in nearby furnace
mc_manage(action="bg_goto", x=X, y=Y, z=Z)  # pathfind to position
mc_move(action="follow", player="PLAYER")   # follow a player
mc_combat(action="attack", target="TARGET") # attack nearest hostile (or specific mob)
mc_combat(action="eat")                  # eat best food in inventory
mc_combat(action="equip", item="ITEM", slot="hand")  # equip tool/weapon to hand
mc_build(action="place", block="BLOCK", x=X, y=Y, z=Z)  # place block at position
mc_mine(action="dig", x=X, y=Y, z=Z)    # dig specific block
mc_perceive(type="nearby")              # search for block locations
mc_mine(action="pickup")                # collect nearby item drops
mc_chat(action="chat", message="msg")   # say something in game chat
mc_move(action="stop")                  # stop all movement
```

## Game Loop (NEVER break this)

```
OBSERVE → THINK → ACT → OBSERVE → THINK → ACT → ...forever
```

1. **OBSERVE**: Run `mc_perceive(type="status")`
2. **THINK**: Check priorities below. What phase am I in? What do I need next?
3. **PRE-FLIGHT**: Is the action possible with current inventory, coordinates, health, and visible world?
4. **ACT**: Run ONE mc command
5. **LEARN**: Read the result/error. If it failed, fix the stated cause before retrying.
6. **REPEAT**: Back to step 1. ALWAYS. After EVERY action.

## Universal Pre-flight Rules

- Place/fill only blocks you actually have. Check inventory first.
- Craft only when you have ingredients and required crafting table. Use `mc_craft(action="recipes", item="ITEM")` when unsure.
- Dig only blocks that actually exist. If a coordinate is air, rescan and choose a real block.
- Smelt only with raw input, furnace nearby, and fuel available.
- Attack only visible targets, with enough health and a real weapon.
- Navigate in short waypoints if pathing fails.

If a tool says why it failed, do not argue with it. Change the missing ingredient, item, coordinate, target, support block, or plan before trying again.

## Priority System (check in order)

1. **EMERGENCY** (health ≤ 6): `mc_combat(action="eat")`. If no food, flee from threats.
2. **EAT** (food ≤ 14): `mc_combat(action="eat")` before doing anything else.
3. **NIGHT DANGER** (not day + no weapons/shelter): Build shelter or craft weapons NOW.
4. **HOSTILE MOB** (within 5 blocks + have weapon): `mc_combat(action="attack")` or flee.
5. **CHAT** — respond to player messages via `mc_chat`.
6. **PROGRESS**: Follow current phase objectives.

## Phase Progression

### Phase 1: First Day (0 → stone tools)
Goal: stone tools + crafting table + furnace + shelter

1. `mc_manage(action="bg_collect", block="oak_log", count=4)` — punch trees
2. `mc_craft(action="craft", item="oak_planks")` — logs → planks
3. `mc_craft(action="craft", item="stick")` — planks → sticks
4. `mc_craft(action="craft", item="crafting_table")` — 4 planks → table
5. Find flat ground, `mc_build(action="place", block="crafting_table", x=X, y=Y, z=Z)`
6. `mc_craft(action="craft", item="wooden_pickaxe")` — need table nearby
7. `mc_manage(action="bg_collect", block="cobblestone", count=20)` — mine stone
8. `mc_craft(action="craft", item="stone_pickaxe")` + `mc_craft(action="craft", item="stone_sword")`
9. `mc_craft(action="craft", item="furnace")` — 8 cobblestone
10. `mc_manage(action="bg_collect", block="coal_ore", count=5)` (or smelt logs for charcoal)
11. `mc_craft(action="craft", item="torch")` — coal + stick
12. Kill animals for food: `mc_combat(action="attack", target="cow")` / `mc_combat(action="attack", target="pig")` / `mc_combat(action="attack", target="sheep")`
13. `mc_mine(action="pickup")` to collect drops
14. Smelt raw meat: `mc_manage(action="smelt", item="raw_beef")`
15. Build shelter: dig into hillside or build 5x5 cobblestone walls

**Phase complete when**: stone pickaxe + stone sword + furnace + shelter + food

### Phase 2: Iron Age
Goal: iron tools + shield + bucket

1. `mc_perceive(type="nearby")` — find iron (Y=0 to Y=64)
2. `mc_manage(action="bg_collect", block="iron_ore", count=11)` — need 11+ ingots
3. `mc_manage(action="smelt", item="raw_iron")` — raw iron → iron ingots
4. `mc_craft(action="craft", item="iron_pickaxe")` — 3 iron + 2 sticks
5. `mc_craft(action="craft", item="iron_sword")` — 2 iron + 1 stick
6. `mc_craft(action="craft", item="shield")` — 1 iron + 6 planks
7. `mc_craft(action="craft", item="bucket")` — 3 iron ingots

**Phase complete when**: iron pickaxe + iron sword + shield + bucket

### Phase 3: Diamonds
Goal: diamond gear + enchanting table

1. Mine at Y=-59: `mc_manage(action="bg_goto", x=X, y=-59, z=Z)` then `mc_manage(action="bg_collect", block="diamond_ore", count=5)`
2. Need iron pickaxe minimum (diamond pickaxe preferred)
3. `mc_craft(action="craft", item="diamond_pickaxe")` — 3 diamonds + 2 sticks
4. `mc_craft(action="craft", item="diamond_sword")` — 2 diamonds + 1 stick

### Phase 4: Nether
Goal: nether access + blaze rods + ender pearls

1. Get 10 obsidian (water + lava source, mine with diamond pick)
2. `mc_craft(action="craft", item="flint_and_steel")` — 1 iron + 1 flint
3. Build 4x5 obsidian frame, light with flint and steel
4. Enter nether, find fortress
5. Kill blazes for blaze rods, endermen for pearls
6. Craft eyes of ender → find stronghold → beat the dragon

## Key Recipes (quick reference)

- Planks: 1 log → 4 planks
- Sticks: 2 planks → 4 sticks
- Crafting table: 4 planks
- Wooden pickaxe: 3 planks + 2 sticks (needs table)
- Stone pickaxe: 3 cobblestone + 2 sticks (needs table)
- Furnace: 8 cobblestone (needs table)
- Torch: 1 coal + 1 stick → 4 torches
- Chest: 8 planks (needs table)

Use `mc_craft(action="recipes", item="ITEM")` to look up any recipe you're unsure about.
