#!/usr/bin/env python3
"""
Rebuild Lobby Matrix v2 with walls, lighting, flat 2D terrain map,
no mob spawning, no day cycle, unbreakable floors.
"""

import subprocess
import time
import math
import random

LOBBY = "execute in minecraft:lobby run "
FLOOR_SIZE = 80  # -40 to +40
FLOOR_Y = [4, 24, 44, 64, 84, 104]
WALL_HEIGHT = 18


def mc_cmd(cmd):
    subprocess.run(
        ["docker", "exec", "--user", "1000", "daemoncraft-minecraft", "mc-send-to-console", cmd],
        capture_output=True, text=True
    )


def batch(cmds):
    for i in range(0, len(cmds), 12):
        batch_cmds = cmds[i:i+12]
        inner = "; ".join([f'mc-send-to-console "{c}"' for c in batch_cmds])
        subprocess.run(
            ['docker', 'exec', '--user', '1000', 'daemoncraft-minecraft', 'bash', '-c', inner],
            capture_output=True, text=True
        )
        if i % 60 == 0 and i > 0:
            print(f"  {i}/{len(cmds)}")
            time.sleep(0.2)
    print(f"Done! {len(cmds)} commands.")


def set_gamerules():
    print("Setting lobby gamerules...")
    mc_cmd(f"{LOBBY}gamerule doMobSpawning false")
    mc_cmd(f"{LOBBY}gamerule doDaylightCycle false")
    mc_cmd(f"{LOBBY}gamerule doWeatherCycle false")
    mc_cmd(f"{LOBBY}gamerule doImmediateRespawn true")
    mc_cmd(f"{LOBBY}gamerule keepInventory true")
    mc_cmd(f"{LOBBY}gamerule spawnRadius 0")
    mc_cmd(f"{LOBBY}gamerule fallDamage false")
    mc_cmd(f"{LOBBY}gamerule fireDamage false")
    mc_cmd(f"{LOBBY}gamerule drowningDamage false")
    mc_cmd(f"{LOBBY}time set day")
    mc_cmd(f"{LOBBY}weather clear")
    print("Gamerules set.")


def build_walled_floors():
    print("Building walled floors...")
    cmds = []
    half = FLOOR_SIZE // 2
    
    for y in FLOOR_Y:
        # Floor base (barrier = unbreakable)
        cmds.append(f"{LOBBY}fill {-half} {y} {-half} {half} {y} {half} barrier")
        
        # Ceiling (barrier) to enclose each room
        ceiling_y = y + WALL_HEIGHT - 1
        cmds.append(f"{LOBBY}fill {-half} {ceiling_y} {-half} {half} {ceiling_y} {half} barrier")
        
        # Walls: white_concrete with shroomlight border on top
        # North wall
        cmds.append(f"{LOBBY}fill {-half} {y+1} {-half} {half} {ceiling_y-1} {-half} white_concrete")
        # South wall
        cmds.append(f"{LOBBY}fill {-half} {y+1} {half} {half} {ceiling_y-1} {half} white_concrete")
        # West wall
        cmds.append(f"{LOBBY}fill {-half} {y+1} {-half} {-half} {ceiling_y-1} {half} white_concrete")
        # East wall
        cmds.append(f"{LOBBY}fill {half} {y+1} {-half} {half} {ceiling_y-1} {half} white_concrete")
        
        # Shroomlight/glowstone on top edge of walls for illumination
        cmds.append(f"{LOBBY}fill {-half} {ceiling_y-1} {-half} {half} {ceiling_y-1} {-half} shroomlight")
        cmds.append(f"{LOBBY}fill {-half} {ceiling_y-1} {half} {half} {ceiling_y-1} {half} shroomlight")
        cmds.append(f"{LOBBY}fill {-half} {ceiling_y-1} {-half} {-half} {ceiling_y-1} {half} shroomlight")
        cmds.append(f"{LOBBY}fill {half} {ceiling_y-1} {-half} {half} {ceiling_y-1} {half} shroomlight")
        
        # Sign at entrance
        cmds.append(f"{LOBBY}setblock 0 {y+1} {half-1} oak_sign{{Text1:'{{\"text\":\"PISO {FLOOR_Y.index(y)}\",\"color\":\"gold\",\"bold\":true}}',Text2:'{{\"text\":\"{get_floor_name(y)}\"}}'}}")
        
        # Light pillars in corners
        for cx, cz in [(-half+2, -half+2), (half-2, -half+2), (-half+2, half-2), (half-2, half-2)]:
            cmds.append(f"{LOBBY}setblock {cx} {y+1} {cz} sea_lantern")
    
    batch(cmds)


def get_floor_name(y):
    names = {
        4: "Mapa Relativo / Diseño",
        24: "Estructuras",
        44: "Mobs",
        64: "Items / Bloques",
        84: "Biomas",
        104: "Mapa del Territorio",
    }
    return names.get(y, "Showroom")


def build_structures():
    print("Building structure showroom...")
    cmds = []
    y = 24
    # Tower
    cmds.append(f"{LOBBY}fill 15 {y} 15 19 {y} 19 stone_bricks")
    for hy in range(y+1, y+10):
        cmds.append(f"{LOBBY}fill 15 {hy} 15 15 {hy} 19 stone_bricks")
        cmds.append(f"{LOBBY}fill 19 {hy} 15 19 {hy} 19 stone_bricks")
        cmds.append(f"{LOBBY}fill 15 {hy} 15 19 {hy} 15 stone_bricks")
        cmds.append(f"{LOBBY}fill 15 {hy} 19 19 {hy} 19 stone_bricks")
    cmds.append(f"{LOBBY}fill 15 {y+10} 15 19 {y+10} 19 stone_bricks")
    cmds.append(f"{LOBBY}setblock 17 {y+1} 17 glowstone")
    
    # House
    cmds.append(f"{LOBBY}fill -15 {y} -15 -5 {y} -5 oak_planks")
    for hy in range(y+1, y+5):
        cmds.append(f"{LOBBY}fill -15 {hy} -15 -15 {hy} -5 oak_planks")
        cmds.append(f"{LOBBY}fill -5 {hy} -15 -5 {hy} -5 oak_planks")
        cmds.append(f"{LOBBY}fill -15 {hy} -15 -5 {hy} -15 oak_planks")
        cmds.append(f"{LOBBY}fill -15 {hy} -5 -5 {hy} -5 oak_planks")
    cmds.append(f"{LOBBY}fill -16 {y+5} -16 -4 {y+5} -4 oak_stairs[facing=south,half=top]")
    cmds.append(f"{LOBBY}fill -15 {y+6} -15 -5 {y+6} -5 oak_planks")
    cmds.append(f"{LOBBY}setblock -10 {y+1} -5 oak_door[facing=south,half=lower]")
    cmds.append(f"{LOBBY}setblock -10 {y+2} -5 oak_door[facing=south,half=upper]")
    
    # Temple
    cmds.append(f"{LOBBY}fill 25 {y} -25 35 {y} -15 quartz_block")
    for hy in range(y+1, y+6):
        cmds.append(f"{LOBBY}fill 25 {hy} -25 25 {hy} -15 quartz_block")
        cmds.append(f"{LOBBY}fill 35 {hy} -25 35 {hy} -15 quartz_block")
        cmds.append(f"{LOBBY}fill 25 {hy} -25 35 {hy} -25 quartz_block")
        cmds.append(f"{LOBBY}fill 25 {hy} -15 35 {hy} -15 quartz_block")
    for x in [25, 35]:
        for z in [-25, -15]:
            cmds.append(f"{LOBBY}fill {x} {y+1} {z} {x} {y+8} {z} quartz_pillar")
    cmds.append(f"{LOBBY}fill 24 {y+9} -24 36 {y+9} -16 quartz_block")
    
    batch(cmds)


def build_mobs():
    print("Building mob showroom...")
    cmds = []
    y = 44
    cages = [
        (-10, -10, -6, -6, "zombie", "Zombie"),
        (5, 5, 9, 9, "cow", "Vaca"),
        (-10, 5, -6, 9, "villager", "Aldeano"),
        (5, -10, 9, -6, "allay", "Pixelito"),
    ]
    for x1, z1, x2, z2, mob, name in cages:
        cmds.append(f"{LOBBY}fill {x1} {y} {z1} {x2} {y+4} {z2} glass")
        cmds.append(f"{LOBBY}fill {x1+1} {y+1} {z1+1} {x2-1} {y+3} {z2-1} air")
        cx, cy, cz = (x1+x2)//2, y+1, (z1+z2)//2
        cmds.append(f"{LOBBY}setblock {cx} {cy} {cz} glowstone")
        cmds.append(f"{LOBBY}summon {mob} {cx} {cy} {cz} {{NoAI:1b,CustomName:'\"{name}\"',CustomNameVisible:1b}}")
    batch(cmds)


def build_items():
    print("Building item showroom...")
    cmds = []
    y = 64
    ores = ["coal_ore", "iron_ore", "gold_ore", "diamond_ore", "emerald_ore", "redstone_ore", "lapis_ore"]
    for i, ore in enumerate(ores):
        cmds.append(f"{LOBBY}setblock {-25 + i*3} {y} 25 {ore}")
    woods = ["oak_log", "spruce_log", "birch_log", "jungle_log", "acacia_log", "dark_oak_log", "cherry_log"]
    for i, wood in enumerate(woods):
        cmds.append(f"{LOBBY}setblock {-25 + i*3} {y} 15 {wood}")
    colors = ["white_wool", "red_wool", "blue_wool", "green_wool", "yellow_wool", "purple_wool", "orange_wool"]
    for i, color in enumerate(colors):
        cmds.append(f"{LOBBY}setblock {-25 + i*3} {y} 5 {color}")
    batch(cmds)


def build_biomes():
    print("Building biome showroom...")
    cmds = []
    y = 84
    cmds.append(f"{LOBBY}fill -30 {y} -30 -10 {y} -10 grass_block")
    cmds.append(f"{LOBBY}setblock -20 {y+1} -20 oak_sapling")
    cmds.append(f"{LOBBY}fill 10 {y} 10 30 {y} 30 sand")
    cmds.append(f"{LOBBY}setblock 20 {y+1} 20 cactus")
    cmds.append(f"{LOBBY}fill -30 {y} 10 -10 {y} 30 netherrack")
    cmds.append(f"{LOBBY}setblock -20 {y+1} 20 fire")
    cmds.append(f"{LOBBY}fill 10 {y} -30 30 {y} -10 end_stone")
    cmds.append(f"{LOBBY}setblock 20 {y+1} -20 chorus_plant")
    batch(cmds)


def build_flat_terrain_map():
    print("Building flat 2D terrain map...")
    random.seed(42)
    MAP_SIZE = 48
    ORIGIN_X, ORIGIN_Z, ORIGIN_Y = 180, -20, 104
    
    def noise(x, z, octaves=4):
        val = 0
        amp = 1.0
        freq = 0.05
        max_val = 0
        for _ in range(octaves):
            val += amp * math.sin(x * freq + random.random() * 100) * math.cos(z * freq + random.random() * 100)
            max_val += amp
            amp *= 0.5
            freq *= 2.0
        return val / max_val
    
    BIOME_COLORS = {
        "plains": "lime_concrete", "desert": "yellow_concrete", "river": "blue_concrete",
        "ocean": "blue_concrete", "forest": "green_concrete", "mountains": "gray_concrete",
        "snow": "white_concrete", "badlands": "red_concrete", "beach": "sand",
        "jungle": "green_wool", "savanna": "orange_concrete", "swamp": "brown_concrete",
    }
    
    def get_biome(x, z):
        temp = noise(x + 1000, z + 1000, octaves=3)
        humidity = noise(x + 2000, z + 2000, octaves=3)
        river = abs(noise(x * 0.15 + 500, z * 0.15 + 500, octaves=2))
        if river < 0.08:
            return "river"
        if temp > 0.5:
            return "desert" if humidity < -0.2 else "savanna"
        elif temp > 0.1:
            return "jungle" if humidity > 0.3 else "forest"
        elif temp > -0.3:
            return "badlands" if humidity < -0.3 else "plains"
        else:
            return "snow"
    
    cmds = []
    for mx in range(MAP_SIZE):
        for mz in range(MAP_SIZE):
            biome = get_biome(mx, mz)
            block = BIOME_COLORS.get(biome, "stone")
            cmds.append(f"{LOBBY}setblock {ORIGIN_X + mx} {ORIGIN_Y} {ORIGIN_Z + mz} {block}")
    
    # Base platform under map
    mc_cmd(f"{LOBBY}fill {ORIGIN_X} {ORIGIN_Y-1} {ORIGIN_Z} {ORIGIN_X+MAP_SIZE-1} {ORIGIN_Y-1} {ORIGIN_Z+MAP_SIZE-1} quartz_block")
    time.sleep(1)
    
    batch(cmds)
    
    # Border around map
    mc_cmd(f"{LOBBY}fill {ORIGIN_X-1} {ORIGIN_Y} {ORIGIN_Z-1} {ORIGIN_X+MAP_SIZE} {ORIGIN_Y} {ORIGIN_Z-1} quartz_block")
    mc_cmd(f"{LOBBY}fill {ORIGIN_X-1} {ORIGIN_Y} {ORIGIN_Z+MAP_SIZE} {ORIGIN_X+MAP_SIZE} {ORIGIN_Y} {ORIGIN_Z+MAP_SIZE} quartz_block")
    mc_cmd(f"{LOBBY}fill {ORIGIN_X-1} {ORIGIN_Y} {ORIGIN_Z} {ORIGIN_X-1} {ORIGIN_Y} {ORIGIN_Z+MAP_SIZE-1} quartz_block")
    mc_cmd(f"{LOBBY}fill {ORIGIN_X+MAP_SIZE} {ORIGIN_Y} {ORIGIN_Z} {ORIGIN_X+MAP_SIZE} {ORIGIN_Y} {ORIGIN_Z+MAP_SIZE-1} quartz_block")
    
    # Beacon center
    cx, cz = ORIGIN_X + MAP_SIZE // 2, ORIGIN_Z + MAP_SIZE // 2
    mc_cmd(f"{LOBBY}setblock {cx} {ORIGIN_Y+1} {cz} beacon")
    mc_cmd(f"{LOBBY}setblock {cx} {ORIGIN_Y} {cz} iron_block")
    mc_cmd(f"{LOBBY}setblock {cx} {ORIGIN_Y+2} {cz+1} oak_sign{{Text1:'{{\"text\":\"MAPA DEL TERRITORIO\",\"color\":\"gold\",\"bold\":true}}',Text2:'{{\"text\":\"Elegí dónde anclar\"}}',Text3:'{{\"text\":\"la aventura\"}}'}}")
    print("Flat terrain map complete.")


if __name__ == "__main__":
    print("=== Rebuilding Lobby Matrix v2 ===")
    set_gamerules()
    build_walled_floors()
    build_structures()
    build_mobs()
    build_items()
    build_biomes()
    build_flat_terrain_map()
    print("\n=== Done! Lobby is ready ===")
