#!/usr/bin/env python3
"""
Rebuild the Lobby Matrix correctly in the 'lobby' world.
"""

import subprocess
import time

LOBBY = "execute in minecraft:lobby run "


def mc_cmd(cmd):
    subprocess.run(
        ["docker", "exec", "--user", "1000", "daemoncraft-minecraft", "mc-send-to-console", cmd],
        capture_output=True, text=True
    )


def batch(cmds):
    for i in range(0, len(cmds), 15):
        batch_cmds = cmds[i:i+15]
        inner = "; ".join([f'mc-send-to-console "{c}"' for c in batch_cmds])
        subprocess.run(
            ['docker', 'exec', '--user', '1000', 'daemoncraft-minecraft', 'bash', '-c', inner],
            capture_output=True, text=True
        )
        if i % 60 == 0 and i > 0:
            print(f"  {i}/{len(cmds)}")
            time.sleep(0.2)
    print(f"Done! {len(cmds)} commands.")


def build_floors():
    print("Building floors...")
    cmds = []
    floors = [4, 24, 44, 64, 84]
    separators = [3, 23, 43, 63, 83]

    # White concrete floors (quarters)
    for y in floors:
        cmds.append(f"{LOBBY}fill -100 {y} -100 0 {y} 0 white_concrete")
        cmds.append(f"{LOBBY}fill 0 {y} -100 100 {y} 0 white_concrete")
        cmds.append(f"{LOBBY}fill -100 {y} 0 0 {y} 100 white_concrete")
        cmds.append(f"{LOBBY}fill 0 {y} 0 100 {y} 100 white_concrete")

    # Barrier separators
    for y in separators:
        cmds.append(f"{LOBBY}fill -100 {y} -100 0 {y} 0 barrier")
        cmds.append(f"{LOBBY}fill 0 {y} -100 100 {y} 0 barrier")
        cmds.append(f"{LOBBY}fill -100 {y} 0 0 {y} 100 barrier")
        cmds.append(f"{LOBBY}fill 0 {y} 0 100 {y} 100 barrier")

    # Lights at corners
    for y in floors:
        for cx, cz in [(-90, 90), (90, 90), (-90, -90), (90, -90)]:
            cmds.append(f"{LOBBY}setblock {cx} {y+1} {cz} glowstone")

    # Signs
    cmds.append(f"{LOBBY}setblock 0 5 0 oak_sign{{Text1:'{{\"text\":\"PISO 0\",\"color\":\"white\",\"bold\":true}}',Text2:'{{\"text\":\"Mapa Relativo\"}}'}}")
    cmds.append(f"{LOBBY}setblock 0 25 0 oak_sign{{Text1:'{{\"text\":\"PISO 1\",\"color\":\"aqua\",\"bold\":true}}',Text2:'{{\"text\":\"Estructuras\"}}'}}")
    cmds.append(f"{LOBBY}setblock 0 45 0 oak_sign{{Text1:'{{\"text\":\"PISO 2\",\"color\":\"green\",\"bold\":true}}',Text2:'{{\"text\":\"Mobs\"}}'}}")
    cmds.append(f"{LOBBY}setblock 0 65 0 oak_sign{{Text1:'{{\"text\":\"PISO 3\",\"color\":\"gold\",\"bold\":true}}',Text2:'{{\"text\":\"Items / Bloques\"}}'}}")
    cmds.append(f"{LOBBY}setblock 0 85 0 oak_sign{{Text1:'{{\"text\":\"PISO 4\",\"color\":\"light_purple\",\"bold\":true}}',Text2:'{{\"text\":\"Biomas\"}}'}}")
    cmds.append(f"{LOBBY}setblock 0 105 0 oak_sign{{Text1:'{{\"text\":\"PISO 5\",\"color\":\"red\",\"bold\":true}}',Text2:'{{\"text\":\"Mapa del Territorio\"}}'}}")

    batch(cmds)


def build_structures():
    print("Building structure showroom...")
    cmds = []
    # Tower
    cmds.append(f"{LOBBY}fill 20 24 20 24 24 24 stone_bricks")
    for y in range(25, 35):
        cmds.append(f"{LOBBY}fill 20 {y} 20 20 {y} 24 stone_bricks")
        cmds.append(f"{LOBBY}fill 24 {y} 20 24 {y} 24 stone_bricks")
        cmds.append(f"{LOBBY}fill 20 {y} 20 24 {y} 20 stone_bricks")
        cmds.append(f"{LOBBY}fill 20 {y} 24 24 {y} 24 stone_bricks")
    cmds.append(f"{LOBBY}fill 20 35 20 24 35 24 stone_bricks")
    cmds.append(f"{LOBBY}setblock 22 25 22 glowstone")

    # House
    cmds.append(f"{LOBBY}fill -20 24 -20 -10 24 -10 oak_planks")
    for y in range(25, 29):
        cmds.append(f"{LOBBY}fill -20 {y} -20 -20 {y} -10 oak_planks")
        cmds.append(f"{LOBBY}fill -10 {y} -20 -10 {y} -10 oak_planks")
        cmds.append(f"{LOBBY}fill -20 {y} -20 -10 {y} -20 oak_planks")
        cmds.append(f"{LOBBY}fill -20 {y} -10 -10 {y} -10 oak_planks")
    cmds.append(f"{LOBBY}fill -21 29 -21 -9 29 -9 oak_stairs[facing=south,half=top]")
    cmds.append(f"{LOBBY}fill -20 30 -20 -10 30 -10 oak_planks")
    cmds.append(f"{LOBBY}setblock -15 25 -10 oak_door[facing=south,half=lower]")
    cmds.append(f"{LOBBY}setblock -15 26 -10 oak_door[facing=south,half=upper]")

    # Temple
    cmds.append(f"{LOBBY}fill 30 24 -30 40 24 -20 quartz_block")
    for y in range(25, 30):
        cmds.append(f"{LOBBY}fill 30 {y} -30 30 {y} -20 quartz_block")
        cmds.append(f"{LOBBY}fill 40 {y} -30 40 {y} -20 quartz_block")
        cmds.append(f"{LOBBY}fill 30 {y} -30 40 {y} -30 quartz_block")
        cmds.append(f"{LOBBY}fill 30 {y} -20 40 {y} -20 quartz_block")
    for x in [30, 40]:
        for z in [-30, -20]:
            cmds.append(f"{LOBBY}fill {x} 25 {z} {x} 32 {z} quartz_pillar")
    cmds.append(f"{LOBBY}fill 29 33 -29 41 33 -21 quartz_block")

    batch(cmds)


def build_mobs():
    print("Building mob showroom...")
    cmds = []
    cages = [
        (-10, 44, -10, -6, 48, -6, "zombie", "Zombie"),
        (5, 44, 5, 9, 48, 9, "cow", "Vaca"),
        (-10, 44, 5, -6, 48, 9, "villager", "Aldeano"),
        (5, 44, -10, 9, 48, -6, "allay", "Pixelito"),
    ]
    for x1, y1, z1, x2, y2, z2, mob, name in cages:
        cmds.append(f"{LOBBY}fill {x1} {y1} {z1} {x2} {y2} {z2} glass")
        cmds.append(f"{LOBBY}fill {x1+1} {y1+1} {z1+1} {x2-1} {y2-1} {z2-1} air")
        cx, cy, cz = (x1+x2)//2, y1+1, (z1+z2)//2
        cmds.append(f"{LOBBY}setblock {cx} {cy} {cz} glowstone")
        cmds.append(f"{LOBBY}summon {mob} {cx} {cy} {cz} {{NoAI:1b,CustomName:'\"{name}\"',CustomNameVisible:1b}}")
    batch(cmds)


def build_items():
    print("Building item showroom...")
    cmds = []
    ores = ["coal_ore", "iron_ore", "gold_ore", "diamond_ore", "emerald_ore", "redstone_ore", "lapis_ore"]
    for i, ore in enumerate(ores):
        cmds.append(f"{LOBBY}setblock {-30 + i*3} 65 30 {ore}")
    woods = ["oak_log", "spruce_log", "birch_log", "jungle_log", "acacia_log", "dark_oak_log", "cherry_log"]
    for i, wood in enumerate(woods):
        cmds.append(f"{LOBBY}setblock {-30 + i*3} 65 20 {wood}")
    colors = ["white_wool", "red_wool", "blue_wool", "green_wool", "yellow_wool", "purple_wool", "orange_wool"]
    for i, color in enumerate(colors):
        cmds.append(f"{LOBBY}setblock {-30 + i*3} 65 10 {color}")
    batch(cmds)


def build_biomes():
    print("Building biome showroom...")
    cmds = []
    cmds.append(f"{LOBBY}fill -40 84 -40 -20 84 -20 grass_block")
    cmds.append(f"{LOBBY}setblock -30 85 -30 oak_sapling")
    cmds.append(f"{LOBBY}fill 20 84 20 40 84 40 sand")
    cmds.append(f"{LOBBY}setblock 30 85 30 cactus")
    cmds.append(f"{LOBBY}fill -40 84 20 -20 84 40 netherrack")
    cmds.append(f"{LOBBY}setblock -30 85 30 fire")
    cmds.append(f"{LOBBY}fill 20 84 -40 40 84 -20 end_stone")
    cmds.append(f"{LOBBY}setblock 30 85 -30 chorus_plant")
    batch(cmds)


def build_terrain_map():
    print("Building demo terrain map...")
    import math
    import random

    random.seed(42)
    MAP_SIZE = 32
    ORIGIN_X, ORIGIN_Z, ORIGIN_Y = 200, 0, 104

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

    def get_biome_height(x, z):
        h = noise(x, z, octaves=5)
        height = int(64 + h * 40)
        temp = noise(x + 1000, z + 1000, octaves=3)
        humidity = noise(x + 2000, z + 2000, octaves=3)
        river = abs(noise(x * 0.15 + 500, z * 0.15 + 500, octaves=2))
        if river < 0.08:
            return "river", 62
        if height > 95:
            return "snow" if temp < -0.3 else "mountains", height
        if height < 50:
            return "beach" if temp > 0.4 else "swamp", height
        if temp > 0.5:
            return "desert" if humidity < -0.2 else "savanna", height
        elif temp > 0.1:
            return "jungle" if humidity > 0.3 else "forest", height
        elif temp > -0.3:
            return "badlands" if humidity < -0.3 else "plains", height
        else:
            return "snow" if height > 80 else "plains", height

    cmds = []
    for mx in range(MAP_SIZE):
        for mz in range(MAP_SIZE):
            biome, height = get_biome_height(mx, mz)
            block = BIOME_COLORS.get(biome, "stone")
            ly = ORIGIN_Y + max(0, (height - 64) // 3)
            cmds.append(f"{LOBBY}setblock {ORIGIN_X + mx} {ly} {ORIGIN_Z + mz} {block}")

    # Base platform
    mc_cmd(f"{LOBBY}fill {ORIGIN_X} {ORIGIN_Y-1} {ORIGIN_Z} {ORIGIN_X+MAP_SIZE-1} {ORIGIN_Y-1} {ORIGIN_Z+MAP_SIZE-1} white_concrete")
    time.sleep(1)

    batch(cmds)

    # Beacon center
    cx, cz = ORIGIN_X + MAP_SIZE // 2, ORIGIN_Z + MAP_SIZE // 2
    mc_cmd(f"{LOBBY}setblock {cx} {ORIGIN_Y} {cz} beacon")
    mc_cmd(f"{LOBBY}setblock {cx} {ORIGIN_Y-1} {cz} iron_block")
    mc_cmd(f"{LOBBY}setblock {cx} {ORIGIN_Y+1} {cz+1} oak_sign{{Text1:'{{\"text\":\"MAPA DEL TERRITORIO\",\"color\":\"gold\",\"bold\":true}}',Text2:'{{\"text\":\"Elegí dónde anclar\"}}',Text3:'{{\"text\":\"la aventura\"}}'}}")


if __name__ == "__main__":
    print("=== Rebuilding Lobby Matrix ===")
    build_floors()
    build_structures()
    build_mobs()
    build_items()
    build_biomes()
    build_terrain_map()
    print("\n=== Lobby Matrix rebuild complete! ===")
