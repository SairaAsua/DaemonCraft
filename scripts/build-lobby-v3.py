#!/usr/bin/env python3
"""
Lobby Matrix v3 — Huge white spaces, solid walls, barrier padding,
spacious floors, solid 3D terrain map.
"""

import subprocess
import time
import math
import random

LOBBY = "execute in minecraft:lobby run "
CONTAINER_SIZE = 200   # -100 to +100
CONTAINER_HALF = 100
CONTAINER_HEIGHT = 40  # interior height
FLOOR_THICKNESS = 1
SEPARATION = 10        # barrier gap between containers
PADDING = 3            # barrier padding inside walls
FLOORS = [4, 54, 104, 154, 204, 254]

def mc_cmd(cmd):
    subprocess.run(
        ["docker", "exec", "--user", "1000", "daemoncraft-minecraft", "mc-send-to-console", cmd],
        capture_output=True, text=True
    )

def batch(cmds, batch_size=8):
    for i in range(0, len(cmds), batch_size):
        batch_cmds = cmds[i:i+batch_size]
        inner = "; ".join([f'mc-send-to-console "{c}"' for c in batch_cmds])
        subprocess.run(
            ['docker', 'exec', '--user', '1000', 'daemoncraft-minecraft', 'bash', '-c', inner],
            capture_output=True, text=True
        )
        if i % 100 == 0 and i > 0:
            print(f"  {i}/{len(cmds)}")
            time.sleep(0.2)
    print(f"Done! {len(cmds)} commands.")

def clean_lobby():
    print("Cleaning lobby area...")
    # Clear everything from Y=0 to Y=320 in a wide area
    mc_cmd(f"{LOBBY}fill -120 0 -120 120 320 120 air")
    time.sleep(2)
    print("Cleaned.")

def set_gamerules():
    print("Setting gamerules...")
    for rule in [
        "gamerule doMobSpawning false",
        "gamerule doDaylightCycle false",
        "gamerule doWeatherCycle false",
        "gamerule doImmediateRespawn true",
        "gamerule keepInventory true",
        "gamerule spawnRadius 0",
        "gamerule fallDamage false",
        "gamerule fireDamage false",
        "gamerule drowningDamage false",
        "time set day",
        "weather clear",
    ]:
        mc_cmd(f"{LOBBY}{rule}")
    print("Gamerules set.")

def build_containers():
    print("Building huge white containers...")
    cmds = []
    for y in FLOORS:
        floor_y = y
        ceiling_y = y + CONTAINER_HEIGHT - 1
        wall_inner = CONTAINER_HALF - PADDING
        wall_outer = CONTAINER_HALF
        
        # Floor: white_concrete visible, barrier underneath for protection
        cmds.append(f"{LOBBY}fill {-CONTAINER_HALF} {floor_y} {-CONTAINER_HALF} {CONTAINER_HALF} {floor_y} {CONTAINER_HALF} white_concrete")
        cmds.append(f"{LOBBY}fill {-CONTAINER_HALF} {floor_y-1} {-CONTAINER_HALF} {CONTAINER_HALF} {floor_y-1} {CONTAINER_HALF} barrier")
        
        # Ceiling: white_concrete with sea_lantern lights every 20 blocks
        cmds.append(f"{LOBBY}fill {-CONTAINER_HALF} {ceiling_y} {-CONTAINER_HALF} {CONTAINER_HALF} {ceiling_y} {CONTAINER_HALF} white_concrete")
        for lx in range(-CONTAINER_HALF + 10, CONTAINER_HALF, 20):
            for lz in range(-CONTAINER_HALF + 10, CONTAINER_HALF, 20):
                cmds.append(f"{LOBBY}setblock {lx} {ceiling_y-1} {lz} sea_lantern")
        
        # Interior walls: white_concrete (solid, opaque, bright when lit)
        cmds.append(f"{LOBBY}fill {-wall_outer} {floor_y+1} {-wall_outer} {wall_outer} {ceiling_y-1} {-wall_outer} white_concrete")
        cmds.append(f"{LOBBY}fill {-wall_outer} {floor_y+1} {wall_outer} {wall_outer} {ceiling_y-1} {wall_outer} white_concrete")
        cmds.append(f"{LOBBY}fill {-wall_outer} {floor_y+1} {-wall_outer} {-wall_outer} {ceiling_y-1} {wall_outer} white_concrete")
        cmds.append(f"{LOBBY}fill {wall_outer} {floor_y+1} {-wall_outer} {wall_outer} {ceiling_y-1} {wall_outer} white_concrete")
        
        # Barrier padding inside (invisible unbreakable layer)
        pad = wall_inner
        cmds.append(f"{LOBBY}fill {-pad} {floor_y+1} {-pad} {pad} {ceiling_y-1} {-pad} barrier")
        cmds.append(f"{LOBBY}fill {-pad} {floor_y+1} {pad} {pad} {ceiling_y-1} {pad} barrier")
        cmds.append(f"{LOBBY}fill {-pad} {floor_y+1} {-pad} {-pad} {ceiling_y-1} {pad} barrier")
        cmds.append(f"{LOBBY}fill {pad} {floor_y+1} {-pad} {pad} {ceiling_y-1} {pad} barrier")
        
        # Sign at entrance
        name = ["Mapa Relativo","Estructuras","Mobs","Items","Biomas","Territorio"][FLOORS.index(y)]
        cmds.append(f"{LOBBY}setblock 0 {floor_y+1} {pad-1} oak_sign{{Text1:'{{\"text\":\"PISO {FLOORS.index(y)}\",\"color\":\"gold\",\"bold\":true}}',Text2:'{{\"text\":\"{name}\"}}'}}")
        
        # Separation barrier below (if not first floor)
        if y > 4:
            sep_y = y - SEPARATION
            cmds.append(f"{LOBBY}fill {-CONTAINER_HALF} {sep_y} {-CONTAINER_HALF} {CONTAINER_HALF} {sep_y} {CONTAINER_HALF} barrier")
    
    batch(cmds, batch_size=6)

def build_structures():
    print("Building structures...")
    cmds = []
    y = FLOORS[1]  # Piso 1
    pad = CONTAINER_HALF - PADDING - 2
    
    # Tower
    cmds.append(f"{LOBBY}fill 20 {y} 20 24 {y} 24 stone_bricks")
    for hy in range(y+1, y+11):
        cmds.append(f"{LOBBY}fill 20 {hy} 20 20 {hy} 24 stone_bricks")
        cmds.append(f"{LOBBY}fill 24 {hy} 20 24 {hy} 24 stone_bricks")
        cmds.append(f"{LOBBY}fill 20 {hy} 20 24 {hy} 20 stone_bricks")
        cmds.append(f"{LOBBY}fill 20 {hy} 24 24 {hy} 24 stone_bricks")
    cmds.append(f"{LOBBY}fill 20 {y+11} 20 24 {y+11} 24 stone_bricks")
    cmds.append(f"{LOBBY}setblock 22 {y+1} 22 glowstone")
    
    # House
    cmds.append(f"{LOBBY}fill -20 {y} -20 -10 {y} -10 oak_planks")
    for hy in range(y+1, y+5):
        cmds.append(f"{LOBBY}fill -20 {hy} -20 -20 {hy} -10 oak_planks")
        cmds.append(f"{LOBBY}fill -10 {hy} -20 -10 {hy} -10 oak_planks")
        cmds.append(f"{LOBBY}fill -20 {hy} -20 -10 {hy} -20 oak_planks")
        cmds.append(f"{LOBBY}fill -20 {hy} -10 -10 {hy} -10 oak_planks")
    cmds.append(f"{LOBBY}fill -21 {y+5} -21 -9 {y+5} -9 oak_stairs[facing=south,half=top]")
    cmds.append(f"{LOBBY}fill -20 {y+6} -20 -10 {y+6} -10 oak_planks")
    cmds.append(f"{LOBBY}setblock -15 {y+1} -10 oak_door[facing=south,half=lower]")
    cmds.append(f"{LOBBY}setblock -15 {y+2} -10 oak_door[facing=south,half=upper]")
    
    # Temple
    cmds.append(f"{LOBBY}fill 30 {y} -30 40 {y} -20 quartz_block")
    for hy in range(y+1, y+6):
        cmds.append(f"{LOBBY}fill 30 {hy} -30 30 {hy} -20 quartz_block")
        cmds.append(f"{LOBBY}fill 40 {hy} -30 40 {hy} -20 quartz_block")
        cmds.append(f"{LOBBY}fill 30 {hy} -30 40 {hy} -30 quartz_block")
        cmds.append(f"{LOBBY}fill 30 {hy} -20 40 {hy} -20 quartz_block")
    for x in [30, 40]:
        for z in [-30, -20]:
            cmds.append(f"{LOBBY}fill {x} {y+1} {z} {x} {y+8} {z} quartz_pillar")
    cmds.append(f"{LOBBY}fill 29 {y+9} -29 41 {y+9} -21 quartz_block")
    
    batch(cmds, batch_size=8)

def build_mobs():
    print("Building mob showroom...")
    cmds = []
    y = FLOORS[2]
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
    batch(cmds, batch_size=8)

def build_items():
    print("Building item showroom...")
    cmds = []
    y = FLOORS[3]
    ores = ["coal_ore", "iron_ore", "gold_ore", "diamond_ore", "emerald_ore", "redstone_ore", "lapis_ore"]
    for i, ore in enumerate(ores):
        cmds.append(f"{LOBBY}setblock {-30 + i*3} {y} 30 {ore}")
    woods = ["oak_log", "spruce_log", "birch_log", "jungle_log", "acacia_log", "dark_oak_log", "cherry_log"]
    for i, wood in enumerate(woods):
        cmds.append(f"{LOBBY}setblock {-30 + i*3} {y} 20 {wood}")
    colors = ["white_wool", "red_wool", "blue_wool", "green_wool", "yellow_wool", "purple_wool", "orange_wool"]
    for i, color in enumerate(colors):
        cmds.append(f"{LOBBY}setblock {-30 + i*3} {y} 10 {color}")
    batch(cmds, batch_size=8)

def build_biomes():
    print("Building biome showroom...")
    cmds = []
    y = FLOORS[4]
    cmds.append(f"{LOBBY}fill -40 {y} -40 -20 {y} -20 grass_block")
    cmds.append(f"{LOBBY}setblock -30 {y+1} -30 oak_sapling")
    cmds.append(f"{LOBBY}fill 20 {y} 20 40 {y} 40 sand")
    cmds.append(f"{LOBBY}setblock 30 {y+1} 30 cactus")
    cmds.append(f"{LOBBY}fill -40 {y} 20 -20 {y} 40 netherrack")
    cmds.append(f"{LOBBY}setblock -30 {y+1} 30 fire")
    cmds.append(f"{LOBBY}fill 20 {y} -40 40 {y} -20 end_stone")
    cmds.append(f"{LOBBY}setblock 30 {y+1} -30 chorus_plant")
    batch(cmds, batch_size=8)

def build_solid_terrain_map():
    print("Building solid 3D terrain map...")
    random.seed(42)
    MAP_SIZE = 64
    ORIGIN_X, ORIGIN_Z = -30, -30
    BASE_Y = FLOORS[5]
    
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
            h = noise(mx, mz, octaves=5)
            height = int(BASE_Y + max(0, (h * 20)))  # 0 to +20 blocks above base
            
            # Solid column from base_y to height
            if height > BASE_Y:
                cmds.append(f"{LOBBY}fill {ORIGIN_X + mx} {BASE_Y} {ORIGIN_Z + mz} {ORIGIN_X + mx} {height} {ORIGIN_Z + mz} {block}")
            else:
                cmds.append(f"{LOBBY}setblock {ORIGIN_X + mx} {BASE_Y} {ORIGIN_Z + mz} {block}")
    
    batch(cmds, batch_size=4)
    
    # Border
    mc_cmd(f"{LOBBY}fill {ORIGIN_X-1} {BASE_Y} {ORIGIN_Z-1} {ORIGIN_X+MAP_SIZE} {BASE_Y} {ORIGIN_Z-1} quartz_block")
    mc_cmd(f"{LOBBY}fill {ORIGIN_X-1} {BASE_Y} {ORIGIN_Z+MAP_SIZE} {ORIGIN_X+MAP_SIZE} {BASE_Y} {ORIGIN_Z+MAP_SIZE} quartz_block")
    mc_cmd(f"{LOBBY}fill {ORIGIN_X-1} {BASE_Y} {ORIGIN_Z} {ORIGIN_X-1} {BASE_Y} {ORIGIN_Z+MAP_SIZE-1} quartz_block")
    mc_cmd(f"{LOBBY}fill {ORIGIN_X+MAP_SIZE} {BASE_Y} {ORIGIN_Z} {ORIGIN_X+MAP_SIZE} {BASE_Y} {ORIGIN_Z+MAP_SIZE-1} quartz_block")
    
    # Beacon center
    cx, cz = ORIGIN_X + MAP_SIZE // 2, ORIGIN_Z + MAP_SIZE // 2
    mc_cmd(f"{LOBBY}setblock {cx} {BASE_Y} {cz} beacon")
    mc_cmd(f"{LOBBY}setblock {cx} {BASE_Y-1} {cz} iron_block")
    print("Terrain map complete.")

if __name__ == "__main__":
    print("=== Lobby Matrix v3 ===")
    clean_lobby()
    set_gamerules()
    build_containers()
    build_structures()
    build_mobs()
    build_items()
    build_biomes()
    build_solid_terrain_map()
    print("\n=== Lobby v3 ready ===")
