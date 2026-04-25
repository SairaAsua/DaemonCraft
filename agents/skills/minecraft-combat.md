---
name: minecraft-combat
description: Combat strategies for every Minecraft mob — how to fight, when to flee, weapon selection
triggers:
  - minecraft combat
  - fight mobs
  - minecraft attack
  - kill mobs
version: 3.2.0
---

# Minecraft Combat

## Commands

```
mc_combat(action="attack", target="TARGET")     # attack nearest hostile or specific mob type
mc_combat(action="eat")                          # eat food to heal
mc_combat(action="equip", item="ITEM", slot="hand")  # equip weapon
mc_perceive(type="status")                        # check health + nearby threats
mc_perceive(type="nearby")                        # find specific mob type nearby
mc_manage(action="bg_goto", x=X, y=Y, z=Z)      # flee to safe location
mc_move(action="stop")                           # stop current action
```

## Combat Priority

Before ANY action, check health:
- Health ≤ 6: **RUN.** `mc_combat(action="eat")` then flee. Do not fight.
- Health ≤ 10: Fight only if you have good weapon + armor
- Health > 14: Fight freely

## Combat Pre-flight Checks

Before attacking:

1. Run `mc_perceive(type="status")` or `mc_perceive(type="nearby")` to confirm the target is visible.
2. Check health and food. If hurt or hungry, eat/flee first.
3. Check inventory for a weapon. If the equip tool says "No ITEM in inventory", choose a weapon you actually have or craft one.
4. If attack says "No target found", do not retry. Move/look/search or choose a different visible target.
5. If there are multiple hostiles or a creeper is close, flee and regroup.

Tool errors are tactical information, not proof that combat is broken.

## Weapon Selection

Equip best weapon before fighting:
```
mc_combat(action="equip", item="netherite_sword", slot="hand")   # best
mc_combat(action="equip", item="diamond_sword", slot="hand")     # great
mc_combat(action="equip", item="iron_sword", slot="hand")        # good
mc_combat(action="equip", item="stone_sword", slot="hand")       # okay
mc_combat(action="equip", item="wooden_sword", slot="hand")      # emergency
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
- `mc_combat(action="attack", target="creeper")` then `mc_manage(action="bg_goto", ...)` away quickly
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
