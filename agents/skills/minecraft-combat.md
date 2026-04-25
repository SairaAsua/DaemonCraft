---
name: minecraft-combat
description: Combat strategies for every Minecraft mob — how to fight, when to flee, weapon selection
triggers:
  - minecraft combat
  - fight mobs
  - minecraft attack
  - kill mobs
version: 3.0.0
---

# Minecraft Combat

## Commands

```
mc_combat(action="attack") [target]     # attack nearest hostile or specific mob type
mc_combat(action="eat")                 # eat food to heal
mc_combat(action="equip", item="stone_sword")   # equip weapon
mc_perceive(type="status")              # check health + nearby threats
mc_mine(action="find_entities") TYPE  # find specific mob type nearby
mc_move(action="goto") X Y Z          # flee to safe location
mc_move(action="stop")                # stop current action
```

## Combat Priority

Before ANY action, check health:
- Health ≤ 6: **RUN.** `mc_combat(action="eat")` then flee. Do not fight.
- Health ≤ 10: Fight only if you have good weapon + armor
- Health > 14: Fight freely

## Weapon Selection

Equip best weapon before fighting:
```
mc_combat(action="equip", item="netherite_sword")   # best
mc_combat(action="equip", item="diamond_sword")     # great
mc_combat(action="equip", item="iron_sword")        # good
mc_combat(action="equip", item="stone_sword")       # okay
mc_combat(action="equip", item="wooden_sword")      # emergency
```

## Mob Strategies

### Zombie
- Slow, melee only. Easy kill.
- `mc_combat(action="attack", target="zombie")` — straight fight
- Watch for groups. Baby zombies are FAST.

### Skeleton
- Ranged (bow). Dangerous in open.
- Close distance fast, then `mc_combat(action="attack", target="skeleton")`
- Use shield if available. Fight near walls for cover.

### Creeper
- Explodes when close. **NEVER** let it get within 3 blocks.
- Sprint attack → retreat → sprint attack
- `mc_combat(action="attack", target="creeper")` then `mc_move(action="goto")` away quickly
- Kill with bow if possible

### Spider
- Neutral in daylight. Fast, can climb walls.
- `mc_combat(action="attack", target="spider")` — straightforward melee

### Enderman
- Only attacks if you look at it. Teleports.
- Fight in 2-block-high space (they can't fit)
- `mc_combat(action="attack", target="enderman")` — very strong, need iron+ gear

### Witch
- Throws potions. Dangerous.
- Close distance fast, melee quickly
- `mc_combat(action="attack", target="witch")`

### Creeper (charged)
- Blue glow = lightning-struck. 2x explosion.
- **RUN.** Do not engage.

### Blaze (Nether)
- Flies, shoots fireballs
- Need fire resistance or quick melee
- `mc_combat(action="attack", target="blaze")`

### Ghast (Nether)
- Flies high, shoots explosive fireballs
- Reflect fireballs by hitting them (hard with bot)
- `mc_combat(action="attack", target="ghast")`

## After Combat

1. `mc_mine(action="pickup")` — collect drops (XP, items, mob drops)
2. `mc_combat(action="eat")` — heal up
3. `mc_perceive(type="status")` — check surroundings for more threats
