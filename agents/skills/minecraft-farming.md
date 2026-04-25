---
name: minecraft-farming
description: Food production in Minecraft — crop farming, animal breeding, cooking, food sources
triggers:
  - minecraft farm
  - grow food minecraft
  - minecraft food
  - breed animals
version: 3.1.0
---

# Minecraft Farming

## Commands

```
mc_manage(action="bg_collect", block="CROP", count=N)     # harvest crops
mc_build(action="place", block="SEEDS", x=X, y=Y, z=Z)    # plant seeds
mc_craft(action="craft", item="ITEM")                      # craft farming tools
mc_manage(action="smelt", item="RAW_FOOD")                 # cook food in furnace
mc_combat(action="attack", target="ANIMAL")                # kill for meat
mc_perceive(type="nearby")                                  # find farmland, water, crops
mc_build(action="place", block="hoe", x=X, y=Y, z=Z)      # use hoe on dirt (via interact)
mc_build(action="place", block="bonemeal", x=X, y=Y, z=Z) # bone meal crops
```

## Quick Food (Early Game)

Fastest way to not starve:

1. Kill animals: `mc_combat(action="attack", target="cow")`, `mc_combat(action="attack", target="pig")`, `mc_combat(action="attack", target="chicken")`
2. `mc_mine(action="pickup")` — collect raw meat
3. `mc_manage(action="smelt", item="raw_beef")` (or raw_porkchop, raw_chicken)
4. Cooked steak = 8 food points (best common food)

## Crop Farming

### Setup
1. Craft hoe: `mc_craft(action="craft", item="stone_hoe")`
2. Find water or place water bucket near dirt
3. Till dirt near water: equip hoe, interact on dirt blocks
4. Get seeds: break grass with hand → wheat seeds
5. Plant: `mc_build(action="place", block="wheat_seeds", x=X, y=Y, z=Z)` on farmland

### Harvest
- Wheat grows in ~20 minutes. Fully grown = golden color.
- `mc_manage(action="bg_collect", block="wheat", count=N)` — harvest mature wheat
- `mc_craft(action="craft", item="bread")` — 3 wheat → 1 bread (6 food points)

### Best Crops
- **Wheat**: bread (6 food) — easy, found everywhere
- **Carrots**: eat raw (3 food) or golden carrot (6 food + saturation)
- **Potatoes**: bake in furnace (5 food) — excellent
- **Beetroot**: beetroot soup (6 food) — decent

## Animal Farming

### Breeding
1. Build fenced enclosure: `mc_craft(action="craft", item="oak_fence")`
2. Lure animals with food (wheat for cows/sheep, seeds for chickens, carrots for pigs)
3. Feed two of same animal to breed

### Animal Products
- **Cow**: raw beef (cook it), leather
- **Pig**: raw porkchop (cook it)
- **Chicken**: raw chicken (cook it), feathers, eggs
- **Sheep**: wool (shear or kill), raw mutton

## Food Rankings (food points + saturation)

```
Golden carrot:     6 food, 14.4 sat  (best overall)
Cooked steak:      8 food, 12.8 sat  (best farmable)
Cooked porkchop:   8 food, 12.8 sat  (tied with steak)
Baked potato:      5 food, 6.0 sat   (easy to mass produce)
Bread:             5 food, 6.0 sat   (easy early game)
Cooked chicken:    6 food, 7.2 sat   (decent)
Apple:             4 food, 2.4 sat   (oak tree drops)
```
