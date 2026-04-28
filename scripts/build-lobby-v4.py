#!/usr/bin/env python3
"""
Lobby Matrix v4 — Pure structure shell only.
Huge white rooms, barrier protection, dense lighting, no content.
"""

import subprocess
import time

LOBBY = "execute in minecraft:lobby run "
CONTAINER_HALF = 100
CONTAINER_HEIGHT = 40
SEPARATION = 10
FLOORS = [4, 54, 104, 154, 204, 254]

def mc_cmd(cmd):
    subprocess.run(
        ["docker", "exec", "--user", "1000", "daemoncraft-minecraft", "mc-send-to-console", cmd],
        capture_output=True, text=True
    )

def batch(cmds, bs=6):
    for i in range(0, len(cmds), bs):
        batch = cmds[i:i+bs]
        inner = "; ".join([f'mc-send-to-console "{c}"' for c in batch])
        subprocess.run(
            ['docker', 'exec', '--user', '1000', 'daemoncraft-minecraft', 'bash', '-c', inner],
            capture_output=True, text=True
        )
        if i % 120 == 0 and i > 0:
            print(f"  {i}/{len(cmds)}")
            time.sleep(0.3)
    print(f"Done! {len(cmds)} commands.")

def clean():
    print("Cleaning lobby completely...")
    mc_cmd(f"{LOBBY}fill -120 0 -120 120 320 120 air")
    time.sleep(2)
    print("Cleaned.")

def gamerules():
    print("Setting gamerules...")
    for r in [
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
        mc_cmd(f"{LOBBY}{r}")
    print("Gamerules set.")

def build_shell():
    print("Building pure white shell...")
    cmds = []
    h = CONTAINER_HALF
    
    for floor_y in FLOORS:
        ceiling_y = floor_y + CONTAINER_HEIGHT - 1
        
        # Floor: white_concrete visible, barrier protected underneath
        cmds.append(f"{LOBBY}fill {-h} {floor_y} {-h} {h} {floor_y} {h} white_concrete")
        cmds.append(f"{LOBBY}fill {-h} {floor_y-1} {-h} {h} {floor_y-1} {h} barrier")
        
        # Ceiling: white_concrete visible, barrier protected on top
        cmds.append(f"{LOBBY}fill {-h} {ceiling_y} {-h} {h} {ceiling_y} {h} white_concrete")
        cmds.append(f"{LOBBY}fill {-h} {ceiling_y+1} {-h} {h} {ceiling_y+1} {h} barrier")
        
        # Inner walls (what you see from inside): white_concrete
        cmds.append(f"{LOBBY}fill {-h} {floor_y+1} {-h} {h} {ceiling_y-1} {-h} white_concrete")
        cmds.append(f"{LOBBY}fill {-h} {floor_y+1} {h} {h} {ceiling_y-1} {h} white_concrete")
        cmds.append(f"{LOBBY}fill {-h} {floor_y+1} {-h} {-h} {ceiling_y-1} {h} white_concrete")
        cmds.append(f"{LOBBY}fill {h} {floor_y+1} {-h} {h} {ceiling_y-1} {h} white_concrete")
        
        # Outer protection walls: barrier (one block outside white concrete)
        cmds.append(f"{LOBBY}fill {-h-1} {floor_y} {-h-1} {h+1} {ceiling_y} {-h-1} barrier")
        cmds.append(f"{LOBBY}fill {-h-1} {floor_y} {h+1} {h+1} {ceiling_y} {h+1} barrier")
        cmds.append(f"{LOBBY}fill {-h-1} {floor_y} {-h-1} {-h-1} {ceiling_y} {h+1} barrier")
        cmds.append(f"{LOBBY}fill {h+1} {floor_y} {-h-1} {h+1} {ceiling_y} {h+1} barrier")
        
        # Ceiling light grid: sea_lantern lines every 20 blocks
        for z in range(-h, h+1, 20):
            cmds.append(f"{LOBBY}fill {-h} {ceiling_y-1} {z} {h} {ceiling_y-1} {z} sea_lantern")
        for x in range(-h, h+1, 20):
            cmds.append(f"{LOBBY}fill {x} {ceiling_y-1} {-h} {x} {ceiling_y-1} {h} sea_lantern")
        
        # Wall lights: glowstone at corners and midpoints
        mid = 0
        for y in range(floor_y+5, ceiling_y-4, 15):
            for cx, cz in [(-h, -h), (-h, h), (h, -h), (h, h), (-h, 0), (h, 0), (0, -h), (0, h)]:
                cmds.append(f"{LOBBY}setblock {cx} {y} {cz} glowstone")
        
        # Floor accent: sea_lantern center + corners
        for cx, cz in [(-h+2, -h+2), (-h+2, h-2), (h-2, -h+2), (h-2, h-2), (0, 0)]:
            cmds.append(f"{LOBBY}setblock {cx} {floor_y+1} {cz} sea_lantern")
        
        # Sign
        name = ["Mapa Relativo","Estructuras","Mobs","Items","Biomas","Territorio"][FLOORS.index(floor_y)]
        cmds.append(f"{LOBBY}setblock 0 {floor_y+1} {h-2} oak_sign{{Text1:'{{\"text\":\"PISO {FLOORS.index(floor_y)}\",\"color\":\"gold\",\"bold\":true}}',Text2:'{{\"text\":\"{name}\"}}'}}")
        
        # Barrier separation between floors (if not first)
        if floor_y > 4:
            sep_bottom = floor_y - SEPARATION
            cmds.append(f"{LOBBY}fill {-h-1} {sep_bottom} {-h-1} {h+1} {floor_y-1} {h+1} barrier")
    
    batch(cmds, bs=5)

if __name__ == "__main__":
    print("=== Lobby Matrix v4 (structure only) ===")
    clean()
    gamerules()
    build_shell()
    print("\n=== Lobby v4 ready ===")
    print("6 huge white rooms, barrier-protected, densely lit, no content yet.")
