#!/usr/bin/env python3
"""
build_world.py — Script maestro de construcción del Mundo Soul

Genera TODO lo necesario para que el mundo de DaemonCraft esté listo:
1. Casa-Bodygraph (El Templo de Ra) — 9 centros HD, 64 puertas
2. 6 Biomas PHS alrededor del castillo
3. Spawn de los 5 Landfolk en sus lugares designados
4. Datapack listo para copiar al servidor

Uso:
    python build_world.py
    
Salida:
    datapacks/ra_soul_world/data/ra_soul_world/functions/build.mcfunction
    datapacks/ra_soul_world/pack.mcmeta
"""

import json
import math
from pathlib import Path
from datetime import datetime

PHI = 1.618033988749
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

ROOT = Path(__file__).parent.parent
DATAPACK_DIR = ROOT / "datapacks" / "ra_soul_world"
FUNCTIONS_DIR = DATAPACK_DIR / "data" / "ra_soul_world" / "functions"

# ============================================================
# LANDFOLK DATA
# ============================================================

LANDFOLK = {
    "stevie": {
        "name": "Stevie",
        "type": "Manifestor",
        "profile": "4/6",
        "authority": "Emocional",
        "hd_env": "Valleys",
        "biome": "valley",
        "color": "yellow",
        "room": "throne_of_voice",
        "gates": [4, 9, 15, 16, 18, 21, 23, 26, 32, 39, 43, 45, 49, 55, 56, 63, 64],
        "role": "Architecta jefa",
    },
    "moss": {
        "name": "Moss",
        "type": "Projector",
        "profile": "2/4",
        "authority": "Splénico",
        "hd_env": "Kitchens",
        "biome": "kitchen",
        "color": "green",
        "room": "ajna_maps",
        "gates": [3, 5, 6, 11, 17, 18, 19, 23, 25, 26, 35, 39, 40, 42, 44, 46, 52, 58, 63, 64],
        "role": "Feng shui master",
    },
    "reed": {
        "name": "Reed",
        "type": "Reflector",
        "profile": "1/3",
        "authority": "Lunar",
        "hd_env": "Markets",
        "biome": "market",
        "color": "light_blue",
        "room": "heart_chamber",
        "gates": [1, 2, 7, 9, 11, 13, 19, 23, 32, 37, 42, 48, 51, 55, 57, 60, 62, 63],
        "role": "Mediador del grupo",
    },
    "flint": {
        "name": "Flint",
        "type": "Manifesting Generator",
        "profile": "3/5",
        "authority": "Sacral",
        "hd_env": "Valleys",
        "biome": "valley",
        "color": "red",
        "room": "sacrarium",
        "gates": [5, 7, 8, 10, 13, 15, 23, 27, 28, 29, 32, 33, 35, 42, 44, 48, 55, 60, 63, 64],
        "role": "Minero y constructor",
    },
    "ember": {
        "name": "Ember",
        "type": "Generator",
        "profile": "1/3",
        "authority": "Emocional",
        "hd_env": "Caves",
        "biome": "cave",
        "color": "orange",
        "room": "solar_garden",
        "gates": [3, 7, 13, 16, 24, 26, 32, 33, 35, 37, 40, 41, 42, 44, 52, 53, 55, 61, 62, 64],
        "role": "Jardinera y cocinera",
    },
}

# ============================================================
# HELPER: comandos Minecraft
# ============================================================

def cmd_fill(x1, y1, z1, x2, y2, z2, block):
    return f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block}"

def cmd_setblock(x, y, z, block):
    return f"setblock {x} {y} {z} {block}"

def cmd_summon(entity, x, y, z, nbt=""):
    if nbt:
        return f'summon {entity} {x} {y} {z} {nbt}'
    return f'summon {entity} {x} {y} {z}'

def cmd_tp(player, x, y, z):
    return f'tp {player} {x} {y} {z}'

def cmd_gamerule(rule, value):
    return f'gamerule {rule} {value}'

def cmd_time_set(time):
    return f'time set {time}'

def cmd_weather(weather):
    return f'weather {weather}'

def cmd_title(player, action, text):
    return f'title {player} {action} "{text}"'

def cmd_tellraw(player, text):
    return f'tellraw {player} "{text}"'

# ============================================================
# SECCION 1: CASA-BODYGRAPH
# ============================================================

def build_castle(ox, oy, oz):
    """Genera comandos para construir el Templo de Ra."""
    cmds = []
    
    # Header
    cmds.append(f"# === El Templo de Ra ===")
    cmds.append(f"# Fecha: {datetime.now().isoformat()}")
    cmds.append(f"# Proporcion aurea φ = {PHI}")
    cmds.append(f"# 9 centros HD | 64 puertas | 5 Landfolk")
    cmds.append("")
    
    # Preparar terreno: flat area
    cmds.append("# --- Preparar terreno ---")
    cmds.append(cmd_fill(ox-50, oy-1, oz-50, ox+50, oy-1, oz+50, "grass_block"))
    cmds.append(cmd_fill(ox-50, oy, oz-50, ox+50, oy+20, oz+50, "air"))
    cmds.append("")
    
    # === PLANTA BAJA (Trigrama Inferior) ===
    cmds.append("# === PLANTA BAJA: Trigrama Inferior ===")
    cmds.append("# Lineas 1, 2, 3 = proceso personal y experimental")
    cmds.append("")
    
    # Línea 1 — Cimientos / Cripta de la Memoria (Raíz)
    cmds.append("# --- Linea 1: Cimientos (Investigator) ---")
    cmds.append("# Cripta de la Memoria - Centro Raiz")
    rx, ry, rz = ox, oy-3, oz
    cmds.append(cmd_fill(rx-10, ry, rz-6, rx+10, ry+2, rz+6, "obsidian"))
    cmds.append(cmd_fill(rx-9, ry+1, rz-5, rx+9, ry+2, rz+5, "air"))  # hollow
    cmds.append(cmd_fill(rx-10, ry+3, rz-6, rx+10, ry+3, rz+6, "deepslate"))  # ceiling
    # Ender chests = archivos
    for i in range(-8, 9, 4):
        cmds.append(cmd_setblock(rx+i, ry+1, rz-4, "ender_chest[facing=south]"))
    cmds.append(cmd_setblock(rx, ry+1, rz, "enchanting_table"))
    cmds.append("")
    
    # Línea 2 — Ventana Iluminada / Sala de las Puertas (Ajna)
    cmds.append("# --- Linea 2: Ventana Iluminada (Hermit) ---")
    cmds.append("# Sala de las Puertas - Centro Ajna")
    ax, ay, az = ox-25, oy, oz+5
    cmds.append(cmd_fill(ax-6, ay, az-4, ax+6, ay+4, az+4, "cyan_concrete"))
    cmds.append(cmd_fill(ax-5, ay+1, az-3, ax+5, ay+3, az+3, "air"))
    cmds.append(cmd_fill(ax-6, ay+5, az-4, ax+6, ay+5, az+4, "white_concrete"))
    # Cartography tables
    for i in range(-4, 5, 3):
        cmds.append(cmd_setblock(ax+i, ay+1, az-3, "cartography_table"))
    # Map walls
    cmds.append(cmd_setblock(ax-5, ay+2, az, "item_frame[facing=east]"))
    cmds.append(cmd_setblock(ax+5, ay+2, az, "item_frame[facing=west]"))
    cmds.append("")
    
    # Línea 3 — Taller de Pruebas / Sala del Sacro
    cmds.append("# --- Linea 3: Taller de Pruebas (Martyr) ---")
    cmds.append("# Sala del Sacro - Centro Sacral")
    sx, sy, sz = ox+5, oy, oz+25
    cmds.append(cmd_fill(sx-10, sy, sz-6, sx+10, sy+4, sz+6, "oak_log"))
    cmds.append(cmd_fill(sx-9, sy+1, sz-5, sx+9, sy+3, sz+5, "air"))
    cmds.append(cmd_fill(sx-10, sy+5, sz-6, sx+10, sy+5, sz+6, "jungle_planks"))
    # Crafting stations
    cmds.append(cmd_setblock(sx-8, sy+1, sz-4, "furnace[facing=south]"))
    cmds.append(cmd_setblock(sx-4, sy+1, sz-4, "crafting_table"))
    cmds.append(cmd_setblock(sx, sy+1, sz-4, "anvil"))
    cmds.append(cmd_setblock(sx+4, sy+1, sz-4, "brewing_stand"))
    cmds.append(cmd_setblock(sx+8, sy+1, sz-4, "smithing_table"))
    cmds.append("")
    
    # === PLANTA ALTA (Trigrama Superior) ===
    cmds.append("# === PLANTA ALTA: Trigrama Superior ===")
    cmds.append("# Lineas 4, 5, 6 = proceso transpersonal y social")
    cmds.append("")
    
    # Línea 4 — Piso del Segundo Nivel / Sala del Voz (Garganta)
    cmds.append("# --- Linea 4: Piso del Segundo Nivel (Opportunist) ---")
    cmds.append("# Sala del Voz (Ra) - Centro Garganta")
    tx, ty, tz = ox, oy+5, oz
    cmds.append(cmd_fill(tx-17, ty, tz-10, tx+17, ty+7, tz+10, "bricks"))
    cmds.append(cmd_fill(tx-16, ty+1, tz-9, tx+16, ty+6, tz+9, "air"))
    cmds.append(cmd_fill(tx-17, ty+8, tz-10, tx+17, ty+8, tz+10, "dark_oak_planks"))
    # Throne
    cmds.append(cmd_setblock(tx, ty+1, tz-5, "gold_block"))
    cmds.append(cmd_setblock(tx, ty+2, tz-5, "gold_block"))
    cmds.append(cmd_setblock(tx, ty+3, tz-5, "end_rod"))
    # Bell
    cmds.append(cmd_setblock(tx+10, ty+6, tz, "bell"))
    cmds.append("")
    
    # Línea 5 — Ventana del Segundo Piso / Torre del Oráculo (Corona)
    cmds.append("# --- Linea 5: Ventana del Segundo Piso (Heretic) ---")
    cmds.append("# Torre del Oraculo - Centro Corona")
    cx, cy, cz = ox+20, oy+5, oz-10
    cmds.append(cmd_fill(cx-6, cy, cz-6, cx+6, cy+10, cz+6, "amethyst_block"))
    cmds.append(cmd_fill(cx-5, cy+1, cz-5, cx+5, cy+9, cz+5, "air"))
    cmds.append(cmd_fill(cx-6, cy+11, cz-6, cx+6, cy+11, cz+6, "glass"))
    # Crystal ball = beacon
    cmds.append(cmd_setblock(cx, cy+1, cz, "beacon"))
    cmds.append(cmd_setblock(cx, cy, cz, "diamond_block"))
    # End rods = stars
    for dx, dz in [(-5,-5), (-5,5), (5,-5), (5,5)]:
        cmds.append(cmd_setblock(cx+dx, cy+10, cz+dz, "end_rod"))
    cmds.append("")
    
    # Línea 6 — Techo / Biblioteca HD (Cabeza)
    cmds.append("# --- Linea 6: Techo / Mirador (Role Model) ---")
    cmds.append("# Biblioteca HD - Centro Cabeza")
    bx, by, bz = ox-25, oy+5, oz+5
    cmds.append(cmd_fill(bx-10, by, bz-6, bx+10, by+5, bz+6, "bookshelf"))
    cmds.append(cmd_fill(bx-9, by+1, bz-5, bx+9, by+4, bz+5, "air"))
    cmds.append(cmd_fill(bx-10, by+6, bz-6, bx+10, by+6, bz+6, "spruce_planks"))
    # Lecterns
    for i in range(-8, 9, 4):
        cmds.append(cmd_setblock(bx+i, by+1, bz-4, "lectern[facing=south]"))
    cmds.append("")
    
    # === OTROS CENTROS ===
    
    # Sala del Coraje (Ego)
    cmds.append("# --- Sala del Coraje (Ego) ---")
    ex, ey, ez = ox+30, oy, oz+15
    cmds.append(cmd_fill(ex-6, ey, ez-6, ex+6, ey+4, ez+6, "yellow_terracotta"))
    cmds.append(cmd_fill(ex-5, ey+1, ez-5, ex+5, ey+3, ez+5, "air"))
    cmds.append(cmd_fill(ex-6, ey+5, ez-6, ex+6, ey+5, ez+6, "glowstone"))
    # Trophy armor stands
    for i in range(-4, 5, 4):
        cmds.append(cmd_setblock(ex+i, ey+1, ez-4, "armor_stand"))
    cmds.append("")
    
    # Cuarto del Amor (Corazón)
    cmds.append("# --- Cuarto del Amor (Corazon) ---")
    hx, hy, hz = ox-15, oy, oz+30
    cmds.append(cmd_fill(hx-6, hy, hz-10, hx+6, hy+3, hz+10, "red_nether_bricks"))
    cmds.append(cmd_fill(hx-5, hy+1, hz-9, hx+5, hy+2, hz+9, "air"))
    cmds.append(cmd_fill(hx-6, hy+4, hz-10, hx+6, hy+4, hz+10, "warped_planks"))
    # Beds
    cmds.append(cmd_setblock(hx-3, hy+1, hz-5, "red_bed[facing=south,part=head]"))
    cmds.append(cmd_setblock(hx-3, hy+1, hz-6, "red_bed[facing=south,part=foot]"))
    cmds.append(cmd_setblock(hx+3, hy+1, hz-5, "pink_bed[facing=south,part=head]"))
    cmds.append(cmd_setblock(hx+3, hy+1, hz-6, "pink_bed[facing=south,part=foot]"))
    # Jukebox
    cmds.append(cmd_setblock(hx, hy+1, hz, "jukebox"))
    cmds.append("")
    
    # Bodega (Bazo)
    cmds.append("# --- Bodega (Bazo) ---")
    px, py, pz = ox, oy-3, oz
    cmds.append(cmd_fill(px-10, py-4, pz-6, px+10, py-1, pz+6, "stone_bricks"))
    cmds.append(cmd_fill(px-9, py-3, pz-5, px+9, py-1, pz+5, "air"))
    # Chests
    for i in range(-8, 9, 3):
        for j in range(-4, 5, 3):
            cmds.append(cmd_setblock(px+i, py-3, pz+j, "chest[facing=south]"))
    cmds.append("")
    
    # Jardín Emocional (Solar Plexus)
    cmds.append("# --- Jardin Emocional (Solar Plexus) ---")
    jx, jy, jz = ox, oy, oz+45
    cmds.append(cmd_fill(jx-17, jy, jz-10, jx+17, jy, jz+10, "grass_block"))
    # Paths
    cmds.append(cmd_fill(jx, jy, jz-10, jx, jy, jz+10, "dirt_path"))
    cmds.append(cmd_fill(jx-17, jy, jz, jx+17, jy, jz, "dirt_path"))
    # Fountain center
    cmds.append(cmd_setblock(jx, jy+1, jz, "water"))
    cmds.append(cmd_setblock(jx, jy, jz, "glowstone"))
    # 8 biome sectors (colored flowers)
    colors = ["poppy", "blue_orchid", "allium", "azure_bluet", "red_tulip", 
              "orange_tulip", "white_tulip", "pink_tulip"]
    for i, color in enumerate(colors):
        angle = (2 * math.pi * i) / 8
        fx = jx + int(8 * math.cos(angle))
        fz = jz + int(8 * math.sin(angle))
        cmds.append(cmd_setblock(fx, jy+1, fz, color))
    cmds.append("")
    
    # Fachada 64 ventanas (8x8)
    cmds.append("# --- Fachada: 64 Ventanas (8x8) ---")
    cmds.append("# Una ventana por cada puerta del I Ching")
    fx_start = ox - 8
    fy_start = oy + 7
    fz_front = oz - 11
    glass_colors = [
        "red_stained_glass", "orange_stained_glass", "yellow_stained_glass",
        "lime_stained_glass", "green_stained_glass", "cyan_stained_glass",
        "light_blue_stained_glass", "blue_stained_glass", "purple_stained_glass",
        "magenta_stained_glass", "pink_stained_glass", "white_stained_glass",
        "brown_stained_glass", "gray_stained_glass", "light_gray_stained_glass", "black_stained_glass"
    ]
    gate_num = 1
    for row in range(8):
        for col in range(8):
            vx = fx_start + col * 2
            vy = fy_start + row * 3
            vz = fz_front
            color = glass_colors[(gate_num - 1) % len(glass_colors)]
            cmds.append(cmd_setblock(vx, vy, vz, color))
            gate_num += 1
    cmds.append("")
    
    return cmds


# ============================================================
# SECCION 2: 6 BIOMAS PHS
# ============================================================

def build_biomes(ox, oy, oz):
    """Genera comandos para construir los 6 biomas PHS alrededor del castillo."""
    cmds = []
    cmds.append("# === 6 BIOMAS PHS ===")
    cmds.append("# Entornos del Primary Health System como ecosistemas simbolicos")
    cmds.append("")
    
    # 1. CAVES (Cuevas) — Protección, control de entrada
    cmds.append("# --- 1. CAVES (Cuevas) - Proteccion, seguridad ---")
    cmds.append("# Bioma: Ember (Generator 1/3)")
    cx, cz = ox - 50, oz - 50
    cmds.append(cmd_fill(cx-8, oy-5, cz-8, cx+8, oy+5, cz+8, "stone"))
    cmds.append(cmd_fill(cx-7, oy-4, cz-7, cx+7, oy+4, cz+7, "air"))  # cave hollow
    cmds.append(cmd_setblock(cx, oy, cz, "glowstone"))
    cmds.append(cmd_setblock(cx+5, oy-1, cz+5, "chest"))
    # Portal-like entrance
    cmds.append(cmd_setblock(cx, oy+1, cz+8, "oak_door"))
    cmds.append("")
    
    # 2. MARKETS (Mercados) — Intercambio, recursos
    cmds.append("# --- 2. MARKETS (Mercados) - Intercambio, circulacion ---")
    cmds.append("# Bioma: Reed (Reflector 1/3)")
    mx, mz = ox + 50, oz + 50
    # Plaza
    cmds.append(cmd_fill(mx-15, oy-1, mz-15, mx+15, oy-1, mz+15, "smooth_stone"))
    # Stalls
    for i in range(-10, 11, 5):
        cmds.append(cmd_setblock(mx+i, oy, mz-10, "oak_planks"))
        cmds.append(cmd_setblock(mx+i, oy+1, mz-10, "oak_fence"))
        cmds.append(cmd_setblock(mx+i, oy+2, mz-10, "lantern"))
    # Central fountain
    cmds.append(cmd_setblock(mx, oy+1, mz, "water"))
    cmds.append("")
    
    # 3. KITCHENS (Cocinas) — Transformación
    cmds.append("# --- 3. KITCHENS (Cocinas) - Transformacion, mezcla ---")
    cmds.append("# Bioma: Moss (Projector 2/4)")
    kx, kz = ox - 50, oz + 50
    cmds.append(cmd_fill(kx-8, oy-1, kz-8, kx+8, oy+3, kz+8, "bricks"))
    cmds.append(cmd_fill(kx-7, oy, kz-7, kx+7, oy+2, kz+7, "air"))
    # Furnaces, smokers, campfires
    for i in range(-6, 7, 3):
        cmds.append(cmd_setblock(kx+i, oy, kz-6, "smoker[facing=south]"))
        cmds.append(cmd_setblock(kx+i, oy, kz+6, "campfire"))
    # Brewing area
    cmds.append(cmd_setblock(kx, oy+1, kz, "brewing_stand"))
    cmds.append("")
    
    # 4. MOUNTAINS (Montañas) — Altura, perspectiva
    cmds.append("# --- 4. MOUNTAINS (Montanas) - Altura, perspectiva ---")
    cmds.append("# Bioma: Observatorio universal")
    mtx, mtz = ox, oz - 80
    # Mountain peak
    for h in range(20):
        radius = 10 - h//2
        if radius > 0:
            cmds.append(cmd_fill(mtx-radius, oy+h, mtz-radius, 
                               mtx+radius, oy+h, mtz+radius, "stone"))
    # Peak lookout
    cmds.append(cmd_setblock(mtx, oy+20, mtz, "glass"))
    cmds.append(cmd_setblock(mtx, oy+21, mtz, "end_rod"))
    cmds.append("")
    
    # 5. VALLEYS (Valles) — Flujo, comunicación
    cmds.append("# --- 5. VALLEYS (Valles) - Flujo, comunicacion ---")
    cmds.append("# Bioma: Stevie (Manifestor 4/6) y Flint (MG 3/5)")
    vx, vz = ox + 80, oz
    # River
    cmds.append(cmd_fill(vx-5, oy-2, vz-30, vx+5, oy-1, vz+30, "water"))
    # Paths along river
    cmds.append(cmd_fill(vx-8, oy-1, vz-30, vx-6, oy-1, vz+30, "dirt_path"))
    cmds.append(cmd_fill(vx+6, oy-1, vz-30, vx+8, oy-1, vz+30, "dirt_path"))
    # Bridges
    for z in range(-20, 21, 10):
        cmds.append(cmd_fill(vx-2, oy-1, vz+z, vx+2, oy-1, vz+z, "oak_planks"))
    cmds.append("")
    
    # 6. SHORES (Costas) — Borde entre mundos
    cmds.append("# --- 6. SHORES (Costas) - Borde entre mundos ---")
    cmds.append("# Bioma: Umbral, transicion")
    sx, sz = ox - 80, oz
    # Beach
    cmds.append(cmd_fill(sx-10, oy-1, sz-20, sx+10, oy-1, sz+20, "sand"))
    # Water edge
    cmds.append(cmd_fill(sx-15, oy-2, sz-20, sx-11, oy-1, sz+20, "water"))
    # Pier
    cmds.append(cmd_fill(sx, oy, sz, sx, oy, sz+15, "oak_planks"))
    cmds.append(cmd_setblock(sx, oy+1, sz+15, "lantern"))
    cmds.append("")
    
    return cmds


# ============================================================
# SECCION 3: SPAWN LANDFOLK
# ============================================================

def spawn_landfolk(ox, oy, oz):
    """Genera comandos /summon para los 5 Landfolk en sus lugares."""
    cmds = []
    cmds.append("# === SPAWN: Los 5 Landfolk ===")
    cmds.append("# Cada uno en su centro HD correspondiente")
    cmds.append("")
    
    spawns = {
        "stevie": (ox, oy+6, oz, "Sala del Voz - Valleys"),
        "moss": (ox-25, oy+1, oz+5, "Sala de las Puertas - Kitchens"),
        "reed": (ox-15, oy+1, oz+30, "Cuarto del Amor - Markets"),
        "flint": (ox+5, oy+1, oz+25, "Sala del Sacro - Valleys"),
        "ember": (ox, oy+1, oz+45, "Jardin Emocional - Caves"),
    }
    
    for bot_id, (x, y, z, location) in spawns.items():
        data = LANDFOLK[bot_id]
        name = data["name"]
        nbt = (
            f'{{CustomName:\'{{"text":"{name}","color":"{data["color"]}","bold":true}}\','
            f'CustomNameVisible:1b,'
            f'NoAI:0b,'
            f'PersistenceRequired:1b,'
            f'VillagerData:{{profession:"{get_villager_profession(bot_id)}",level:5}},'
            f'Tags:["landfolk","{bot_id}","hd_bot"]}}'
        )
        cmds.append(f"# {name} — {data['type']} {data['profile']} — {location}")
        cmds.append(cmd_summon("villager", x, y, z, nbt))
        # Name tag floating
        cmds.append(cmd_summon("armor_stand", x, y+2.5, z, 
            f'{{CustomName:\'{{"text":"{name} — {data["role"]}","color":"{data["color"]}","italic":true}}\','
            f'CustomNameVisible:1b,Invisible:1b,NoGravity:1b,Marker:1b}}'))
        cmds.append("")
    
    return cmds


def get_villager_profession(bot_id):
    """Mapea cada landfolk a una profesión de aldeano de Minecraft."""
    professions = {
        "stevie": "mason",       # Constructora
        "moss": "cleric",        # Guía espiritual / feng shui
        "reed": "librarian",     # Mediador, escucha
        "flint": "toolsmith",    # Minero, herrero
        "ember": "farmer",       # Jardinera, cocinera
    }
    return professions.get(bot_id, "nitwit")


# ============================================================
# SECCION 4: SETUP MUNDO
# ============================================================

def world_setup():
    """Comandos de configuración inicial del mundo."""
    cmds = []
    cmds.append("# === CONFIGURACION DEL MUNDO ===")
    cmds.append(cmd_gamerule("doDaylightCycle", "true"))
    cmds.append(cmd_gamerule("doWeatherCycle", "true"))
    cmds.append(cmd_gamerule("keepInventory", "false"))
    cmds.append(cmd_gamerule("mobGriefing", "false"))
    cmds.append(cmd_gamerule("commandBlockOutput", "false"))
    cmds.append(cmd_time_set("day"))
    cmds.append(cmd_weather("clear"))
    cmds.append("")
    return cmds


def welcome_message():
    """Mensaje de bienvenida para Saira."""
    cmds = []
    cmds.append("# === MENSAJE DE BIENVENIDA ===")
    cmds.append(cmd_tellraw("@a", 
        "\\u00a7d[Oraculo]\\u00a7r Bienvenida al Mundo Soul, Saira."))
    cmds.append(cmd_tellraw("@a", 
        "\\u00a77El Templo de Ra aguarda. 5 almas te esperan."))
    cmds.append(cmd_tellraw("@a", 
        "\\u00a77Escribe \\u00a7e/help soul\\u00a77 para ver comandos disponibles."))
    cmds.append("")
    return cmds


# ============================================================
# SECCION 5: SIGNPOSTS / CARTELES
# ============================================================

def build_signposts(ox, oy, oz):
    """Carteles indicadores en cada bioma."""
    cmds = []
    cmds.append("# === CARTELES INDICADORES ===")
    
    signs = [
        (ox, oy+1, oz-15, "Cripta de la Memoria", "Centro Raiz"),
        (ox-25, oy+1, oz, "Sala de las Puertas", "Centro Ajna - Moss"),
        (ox+5, oy+1, oz+15, "Sala del Sacro", "Centro Sacral - Flint"),
        (ox-10, oy+1, oz+30, "Cuarto del Amor", "Centro Corazon - Reed"),
        (ox+20, oy+1, oz-5, "Torre del Oraculo", "Centro Corona"),
        (ox-20, oy+1, oz+5, "Biblioteca HD", "Centro Cabeza"),
        (ox+30, oy+1, oz+10, "Sala del Coraje", "Centro Ego"),
        (ox, oy+1, oz+35, "Jardin Emocional", "Centro Solar Plexus - Ember"),
        (ox, oy+6, oz-5, "Sala del Voz", "Centro Garganta - Stevie"),
    ]
    
    for x, y, z, line1, line2 in signs:
        nbt = f'{{Text1:\'{{"text":"{line1}"}}\',Text2:\'{{"text":"{line2}","color":"gray"}}\'}}'
        cmds.append(cmd_setblock(x, y, z, f"oak_sign{[nbt]}"))
    
    cmds.append("")
    return cmds


# ============================================================
# MAIN
# ============================================================

def main():
    ox, oy, oz = 0, 64, 0
    
    all_cmds = []
    all_cmds.extend(world_setup())
    all_cmds.extend(build_castle(ox, oy, oz))
    all_cmds.extend(build_biomes(ox, oy, oz))
    all_cmds.extend(spawn_landfolk(ox, oy, oz))
    all_cmds.extend(build_signposts(ox, oy, oz))
    all_cmds.extend(welcome_message())
    
    # Guardar como mcfunction
    FUNCTIONS_DIR.mkdir(parents=True, exist_ok=True)
    func_path = FUNCTIONS_DIR / "build.mcfunction"
    with open(func_path, "w") as f:
        f.write("\n".join(all_cmds))
    
    # pack.mcmeta
    pack_meta = {
        "pack": {
            "pack_format": 15,
            "description": "El Mundo Soul — Casa-Bodygraph de Ra Uru Hu con 5 Landfolk HD"
        }
    }
    with open(DATAPACK_DIR / "pack.mcmeta", "w") as f:
        json.dump(pack_meta, f, indent=2)
    
    # README
    readme = f"""# Datapack: ra_soul_world

## Instalación
1. Copia esta carpeta a tu mundo: `saves/<tu_mundo>/datapacks/`
2. En Minecraft: `/reload`
3. Ejecuta: `/function ra_soul_world:build`

## Qué construye
- **El Templo de Ra**: Casa-Bodygraph con 9 centros HD
  - Planta baja (Líneas 1-3): Cripta, Sala de Puertas, Sala del Sacro
  - Planta alta (Líneas 4-6): Sala del Voz, Torre del Oráculo, Biblioteca
- **6 Biomas PHS**: Caves, Markets, Kitchens, Mountains, Valleys, Shores
- **5 Landfolk**: Villagers con nombres y profesiones HD

## Landfolk
| Nombre | Tipo HD | Perfil | Bioma | Centro |
|--------|---------|--------|-------|--------|
| Stevie | Manifestor | 4/6 | Valleys | Garganta |
| Moss | Projector | 2/4 | Kitchens | Ajna |
| Reed | Reflector | 1/3 | Markets | Corazón |
| Flint | Man. Generator | 3/5 | Valleys | Sacral |
| Ember | Generator | 1/3 | Caves | Solar Plexus |

## Comandos útiles
- `/function ra_soul_world:build` — Reconstruye todo
- `/tp @s 0 70 0` — Ir al Templo de Ra
- `/kill @e[tag=landfolk]` — Eliminar landfolk

PULSE STATUS: ALIVE | STRONG | ETERNAL
"""
    with open(DATAPACK_DIR / "README.md", "w") as f:
        f.write(readme)
    
    print(f"Generados {len(all_cmds)} comandos")
    print(f"Datapack guardado en: {DATAPACK_DIR}")
    print(f"Funcion: {func_path}")
    print(f"\nPara instalar:")
    print(f"  1. cp -r {DATAPACK_DIR} ~/minecraft/saves/<mundo>/datapacks/")
    print(f"  2. En Minecraft: /reload")
    print(f"  3. /function ra_soul_world:build")
    
    return len(all_cmds)


if __name__ == "__main__":
    main()
