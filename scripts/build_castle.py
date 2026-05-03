#!/usr/bin/env python3
"""
build_castle.py — Construye el Bodygraph de Ra en Minecraft
Usa el blueprint JSON y genera comandos /fill y /setblock.

Principios aplicados:
- Proporción áurea (φ = 1.618) en todas las dimensiones
- 9 centros HD = 9 habitaciones principales
- 64 puertas = 64 ventanas en fachada
- Espiral áurea en el jardín central
"""

import json
import math
from pathlib import Path

PHI = 1.618033988749
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

def load_blueprint():
    bp_path = Path(__file__).parent.parent / "blueprints" / "castle_bodygraph.json"
    with open(bp_path) as f:
        return json.load(f)

def cmd_fill(x1, y1, z1, x2, y2, z2, block):
    """Genera comando /fill de Minecraft."""
    return f"/fill {x1} {y1} {z1} {x2} {y2} {z2} {block}"

def cmd_setblock(x, y, z, block):
    return f"/setblock {x} {y} {z} {block}"

def build_room(room, ox, oy, oz):
    """Genera comandos para construir una habitación."""
    cmds = []
    w, h, d = room["dimensions"]
    px, py, pz = room["position"]
    x1, y1, z1 = ox + px, oy + py, oz + pz
    x2, y2, z2 = x1 + w - 1, y1 + h - 1, z1 + d - 1
    mats = room["materials"]

    # Piso
    cmds.append(cmd_fill(x1, y1, z1, x2, y1, z2, mats.get("floor", "stone")))
    # Paredes (hollow)
    cmds.append(cmd_fill(x1, y1, z1, x2, y2, z2, mats.get("walls", "stone")))
    # Vaciar interior
    if w > 2 and h > 2 and d > 2:
        cmds.append(cmd_fill(x1+1, y1+1, z1+1, x2-1, y2-1, z2-1, "air"))
    # Techo
    cmds.append(cmd_fill(x1, y2, z1, x2, y2, z2, mats.get("ceiling", "planks")))

    # Iluminación (antorchas en esquinas)
    torch = "torch"
    for tx, tz in [(x1, z1), (x2, z1), (x1, z2), (x2, z2)]:
        cmds.append(cmd_setblock(tx, y2-1, tz, torch))

    return cmds

def build_corridor(room1, room2, rooms_dict, ox, oy, oz):
    """Genera pasillo entre dos habitaciones."""
    cmds = []
    r1 = rooms_dict[room1["from"]]
    r2 = rooms_dict[room2["to"]]

    # Centro de cada habitación
    w1, h1, d1 = r1["dimensions"]
    w2, h2, d2 = r2["dimensions"]
    p1 = r1["position"]
    p2 = r2["position"]

    c1 = (p1[0] + w1//2, p1[1] + 1, p1[2] + d1//2)
    c2 = (p2[0] + w2//2, p2[1] + 1, p2[2] + d2//2)

    # Construir pasillo simple (interpolación lineal)
    width = room2.get("width", 3)
    height = room2.get("height", 3)
    material = "oak_planks"

    dx = abs(c2[0] - c1[0])
    dz = abs(c2[2] - c1[2])

    if dx > dz:
        # Horizontal en X
        x_start, x_end = min(c1[0], c2[0]), max(c1[0], c2[0])
        z = c1[2]
        cmds.append(cmd_fill(ox+x_start, oy+c1[1], oz+z-width//2,
                             ox+x_end, oy+c1[1]+height-1, oz+z+width//2, material))
    else:
        # Horizontal en Z
        z_start, z_end = min(c1[2], c2[2]), max(c1[2], c2[2])
        x = c1[0]
        cmds.append(cmd_fill(ox+x-width//2, oy+c1[1], oz+z_start,
                             ox+x+width//2, oy+c1[1]+height-1, oz+z_end, material))

    return cmds

def build_fibonacci_garden(ox, oy, oz, max_radius=21):
    """Construye jardín en espiral áurea de Fibonacci."""
    cmds = []
    # Cuadrados de Fibonacci en espiral
    squares = [
        (0, 0, 1),    # 1×1
        (1, 0, 1),    # 1×1
        (0, 1, 2),    # 2×2
        (-2, -1, 3),  # 3×3
        (-2, 2, 5),   # 5×5
        (3, -3, 8),   # 8×8
    ]

    biomes = ["cactus", "bamboo", "azalea", "oak_sapling", "spruce_sapling",
              "birch_sapling", "dark_oak_sapling", "jungle_sapling"]

    for i, (dx, dz, size) in enumerate(squares):
        x1 = ox + dx * 3
        z1 = oz + dz * 3
        x2 = x1 + size * 3 - 1
        z2 = z1 + size * 3 - 1
        # Borde de piedra
        cmds.append(cmd_fill(x1, oy, z1, x2, oy, z2, "grass_block"))
        # Centro con planta característica
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        plant = biomes[i % len(biomes)]
        cmds.append(cmd_setblock(cx, oy+1, cz, plant))

    # Fuente central
    cmds.append(cmd_setblock(ox, oy+1, oz, "water"))
    cmds.append(cmd_setblock(ox, oy, oz, "glowstone"))

    return cmds

def build_gates_fascade(ox, oy, oz):
    """Construye la fachada con 64 ventanas (8×8) representando las 64 puertas."""
    cmds = []
    # Fachada frontal: 64 ventanas en 8 filas × 8 columnas
    # Cada ventana es 2 bloques de alto × 1 de ancho, separadas por 1 bloque
    start_x = ox - 8
    start_y = oy + 2
    start_z = oz - 1

    colors = [
        "red_stained_glass", "orange_stained_glass", "yellow_stained_glass",
        "lime_stained_glass", "green_stained_glass", "cyan_stained_glass",
        "light_blue_stained_glass", "blue_stained_glass", "purple_stained_glass",
        "magenta_stained_glass", "pink_stained_glass", "white_stained_glass"
    ]

    gate_num = 1
    for row in range(8):
        for col in range(8):
            vx = start_x + col * 2
            vy = start_y + row * 3
            vz = start_z
            color = colors[(gate_num - 1) % len(colors)]
            # Marco de piedra
            cmds.append(cmd_fill(vx, vy, vz, vx, vy+1, vz, "stone_bricks"))
            # Ventana de cristal coloreado
            cmds.append(cmd_setblock(vx, vy, vz+1, color))
            gate_num += 1

    return cmds

def main():
    bp = load_blueprint()
    ox, oy, oz = bp["origin"]
    rooms = bp["rooms"]
    rooms_dict = {r["id"]: r for r in rooms}

    all_cmds = []
    all_cmds.append("# === El Bodygraph de Ra ===")
    all_cmds.append(f"# Proporción áurea φ = {PHI}")
    all_cmds.append(f"# 9 centros HD | 64 puertas | Espiral áurea")
    all_cmds.append("")

    # Construir habitaciones
    for room in rooms:
        all_cmds.append(f"# --- {room['name']} ({room['center_hd']}) ---")
        all_cmds.extend(build_room(room, ox, oy, oz))
        all_cmds.append("")

    # Construir pasillos
    all_cmds.append("# --- Pasillos (Canales) ---")
    for corr in bp["corridors"]:
        all_cmds.extend(build_corridor(corr, corr, rooms_dict, ox, oy, oz))
    all_cmds.append("")

    # Jardín Fibonacci
    all_cmds.append("# --- Jardín Espiral Áurea ---")
    garden = rooms_dict.get("solar_garden")
    if garden:
        gx = ox + garden["position"][0]
        gy = oy + garden["position"][1]
        gz = oz + garden["position"][2]
        all_cmds.extend(build_fibonacci_garden(gx, gy, gz))
    all_cmds.append("")

    # Fachada 64 ventanas
    all_cmds.append("# --- Fachada 64 Puertas ---")
    throne = rooms_dict.get("throne_of_voice")
    if throne:
        tx = ox + throne["position"][0] + throne["dimensions"][0] // 2
        ty = oy + throne["position"][1]
        tz = oz + throne["position"][2]
        all_cmds.extend(build_gates_fascade(tx, ty, tz))

    # Guardar archivo de comandos
    out_path = Path(__file__).parent.parent / "blueprints" / "castle_commands.mcfunction"
    with open(out_path, "w") as f:
        f.write("\n".join(all_cmds))

    print(f"Generados {len(all_cmds)} comandos")
    print(f"Guardado en: {out_path}")
    print(f"\nPara ejecutar en Minecraft:")
    print(f"  1. Copia el archivo a tu datapack: data/ra_castle/functions/build.mcfunction")
    print(f"  2. Ejecuta: /function ra_castle:build")
    print(f"  3. O pega los comandos uno por uno en consola")

if __name__ == "__main__":
    main()
