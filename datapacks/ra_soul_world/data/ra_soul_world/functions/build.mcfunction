# === CONFIGURACION DEL MUNDO ===
gamerule doDaylightCycle true
gamerule doWeatherCycle true
gamerule keepInventory false
gamerule mobGriefing false
gamerule commandBlockOutput false
time set day
weather clear

# === El Templo de Ra ===
# Fecha: 2026-05-03T04:56:34.020498
# Proporcion aurea φ = 1.618033988749
# 9 centros HD | 64 puertas | 5 Landfolk

# --- Preparar terreno ---
fill -50 63 -50 50 63 50 grass_block
fill -50 64 -50 50 84 50 air

# === PLANTA BAJA: Trigrama Inferior ===
# Lineas 1, 2, 3 = proceso personal y experimental

# --- Linea 1: Cimientos (Investigator) ---
# Cripta de la Memoria - Centro Raiz
fill -10 61 -6 10 63 6 obsidian
fill -9 62 -5 9 63 5 air
fill -10 64 -6 10 64 6 deepslate
setblock -8 62 -4 ender_chest[facing=south]
setblock -4 62 -4 ender_chest[facing=south]
setblock 0 62 -4 ender_chest[facing=south]
setblock 4 62 -4 ender_chest[facing=south]
setblock 8 62 -4 ender_chest[facing=south]
setblock 0 62 0 enchanting_table

# --- Linea 2: Ventana Iluminada (Hermit) ---
# Sala de las Puertas - Centro Ajna
fill -31 64 1 -19 68 9 cyan_concrete
fill -30 65 2 -20 67 8 air
fill -31 69 1 -19 69 9 white_concrete
setblock -29 65 2 cartography_table
setblock -26 65 2 cartography_table
setblock -23 65 2 cartography_table
setblock -30 66 5 item_frame[facing=east]
setblock -20 66 5 item_frame[facing=west]

# --- Linea 3: Taller de Pruebas (Martyr) ---
# Sala del Sacro - Centro Sacral
fill -5 64 19 15 68 31 oak_log
fill -4 65 20 14 67 30 air
fill -5 69 19 15 69 31 jungle_planks
setblock -3 65 21 furnace[facing=south]
setblock 1 65 21 crafting_table
setblock 5 65 21 anvil
setblock 9 65 21 brewing_stand
setblock 13 65 21 smithing_table

# === PLANTA ALTA: Trigrama Superior ===
# Lineas 4, 5, 6 = proceso transpersonal y social

# --- Linea 4: Piso del Segundo Nivel (Opportunist) ---
# Sala del Voz (Ra) - Centro Garganta
fill -17 69 -10 17 76 10 bricks
fill -16 70 -9 16 75 9 air
fill -17 77 -10 17 77 10 dark_oak_planks
setblock 0 70 -5 gold_block
setblock 0 71 -5 gold_block
setblock 0 72 -5 end_rod
setblock 10 75 0 bell

# --- Linea 5: Ventana del Segundo Piso (Heretic) ---
# Torre del Oraculo - Centro Corona
fill 14 69 -16 26 79 -4 amethyst_block
fill 15 70 -15 25 78 -5 air
fill 14 80 -16 26 80 -4 glass
setblock 20 70 -10 beacon
setblock 20 69 -10 diamond_block
setblock 15 79 -15 end_rod
setblock 15 79 -5 end_rod
setblock 25 79 -15 end_rod
setblock 25 79 -5 end_rod

# --- Linea 6: Techo / Mirador (Role Model) ---
# Biblioteca HD - Centro Cabeza
fill -35 69 -1 -15 74 11 bookshelf
fill -34 70 0 -16 73 10 air
fill -35 75 -1 -15 75 11 spruce_planks
setblock -33 70 1 lectern[facing=south]
setblock -29 70 1 lectern[facing=south]
setblock -25 70 1 lectern[facing=south]
setblock -21 70 1 lectern[facing=south]
setblock -17 70 1 lectern[facing=south]

# --- Sala del Coraje (Ego) ---
fill 24 64 9 36 68 21 yellow_terracotta
fill 25 65 10 35 67 20 air
fill 24 69 9 36 69 21 glowstone
setblock 26 65 11 armor_stand
setblock 30 65 11 armor_stand
setblock 34 65 11 armor_stand

# --- Cuarto del Amor (Corazon) ---
fill -21 64 20 -9 67 40 red_nether_bricks
fill -20 65 21 -10 66 39 air
fill -21 68 20 -9 68 40 warped_planks
setblock -18 65 25 red_bed[facing=south,part=head]
setblock -18 65 24 red_bed[facing=south,part=foot]
setblock -12 65 25 pink_bed[facing=south,part=head]
setblock -12 65 24 pink_bed[facing=south,part=foot]
setblock -15 65 30 jukebox

# --- Bodega (Bazo) ---
fill -10 57 -6 10 60 6 stone_bricks
fill -9 58 -5 9 60 5 air
setblock -8 58 -4 chest[facing=south]
setblock -8 58 -1 chest[facing=south]
setblock -8 58 2 chest[facing=south]
setblock -5 58 -4 chest[facing=south]
setblock -5 58 -1 chest[facing=south]
setblock -5 58 2 chest[facing=south]
setblock -2 58 -4 chest[facing=south]
setblock -2 58 -1 chest[facing=south]
setblock -2 58 2 chest[facing=south]
setblock 1 58 -4 chest[facing=south]
setblock 1 58 -1 chest[facing=south]
setblock 1 58 2 chest[facing=south]
setblock 4 58 -4 chest[facing=south]
setblock 4 58 -1 chest[facing=south]
setblock 4 58 2 chest[facing=south]
setblock 7 58 -4 chest[facing=south]
setblock 7 58 -1 chest[facing=south]
setblock 7 58 2 chest[facing=south]

# --- Jardin Emocional (Solar Plexus) ---
fill -17 64 35 17 64 55 grass_block
fill 0 64 35 0 64 55 dirt_path
fill -17 64 45 17 64 45 dirt_path
setblock 0 65 45 water
setblock 0 64 45 glowstone
setblock 8 65 45 poppy
setblock 5 65 50 blue_orchid
setblock 0 65 53 allium
setblock -5 65 50 azure_bluet
setblock -8 65 45 red_tulip
setblock -5 65 40 orange_tulip
setblock 0 65 37 white_tulip
setblock 5 65 40 pink_tulip

# --- Fachada: 64 Ventanas (8x8) ---
# Una ventana por cada puerta del I Ching
setblock -8 71 -11 red_stained_glass
setblock -6 71 -11 orange_stained_glass
setblock -4 71 -11 yellow_stained_glass
setblock -2 71 -11 lime_stained_glass
setblock 0 71 -11 green_stained_glass
setblock 2 71 -11 cyan_stained_glass
setblock 4 71 -11 light_blue_stained_glass
setblock 6 71 -11 blue_stained_glass
setblock -8 74 -11 purple_stained_glass
setblock -6 74 -11 magenta_stained_glass
setblock -4 74 -11 pink_stained_glass
setblock -2 74 -11 white_stained_glass
setblock 0 74 -11 brown_stained_glass
setblock 2 74 -11 gray_stained_glass
setblock 4 74 -11 light_gray_stained_glass
setblock 6 74 -11 black_stained_glass
setblock -8 77 -11 red_stained_glass
setblock -6 77 -11 orange_stained_glass
setblock -4 77 -11 yellow_stained_glass
setblock -2 77 -11 lime_stained_glass
setblock 0 77 -11 green_stained_glass
setblock 2 77 -11 cyan_stained_glass
setblock 4 77 -11 light_blue_stained_glass
setblock 6 77 -11 blue_stained_glass
setblock -8 80 -11 purple_stained_glass
setblock -6 80 -11 magenta_stained_glass
setblock -4 80 -11 pink_stained_glass
setblock -2 80 -11 white_stained_glass
setblock 0 80 -11 brown_stained_glass
setblock 2 80 -11 gray_stained_glass
setblock 4 80 -11 light_gray_stained_glass
setblock 6 80 -11 black_stained_glass
setblock -8 83 -11 red_stained_glass
setblock -6 83 -11 orange_stained_glass
setblock -4 83 -11 yellow_stained_glass
setblock -2 83 -11 lime_stained_glass
setblock 0 83 -11 green_stained_glass
setblock 2 83 -11 cyan_stained_glass
setblock 4 83 -11 light_blue_stained_glass
setblock 6 83 -11 blue_stained_glass
setblock -8 86 -11 purple_stained_glass
setblock -6 86 -11 magenta_stained_glass
setblock -4 86 -11 pink_stained_glass
setblock -2 86 -11 white_stained_glass
setblock 0 86 -11 brown_stained_glass
setblock 2 86 -11 gray_stained_glass
setblock 4 86 -11 light_gray_stained_glass
setblock 6 86 -11 black_stained_glass
setblock -8 89 -11 red_stained_glass
setblock -6 89 -11 orange_stained_glass
setblock -4 89 -11 yellow_stained_glass
setblock -2 89 -11 lime_stained_glass
setblock 0 89 -11 green_stained_glass
setblock 2 89 -11 cyan_stained_glass
setblock 4 89 -11 light_blue_stained_glass
setblock 6 89 -11 blue_stained_glass
setblock -8 92 -11 purple_stained_glass
setblock -6 92 -11 magenta_stained_glass
setblock -4 92 -11 pink_stained_glass
setblock -2 92 -11 white_stained_glass
setblock 0 92 -11 brown_stained_glass
setblock 2 92 -11 gray_stained_glass
setblock 4 92 -11 light_gray_stained_glass
setblock 6 92 -11 black_stained_glass

# === 6 BIOMAS PHS ===
# Entornos del Primary Health System como ecosistemas simbolicos

# --- 1. CAVES (Cuevas) - Proteccion, seguridad ---
# Bioma: Ember (Generator 1/3)
fill -58 59 -58 -42 69 -42 stone
fill -57 60 -57 -43 68 -43 air
setblock -50 64 -50 glowstone
setblock -45 63 -45 chest
setblock -50 65 -42 oak_door

# --- 2. MARKETS (Mercados) - Intercambio, circulacion ---
# Bioma: Reed (Reflector 1/3)
fill 35 63 35 65 63 65 smooth_stone
setblock 40 64 40 oak_planks
setblock 40 65 40 oak_fence
setblock 40 66 40 lantern
setblock 45 64 40 oak_planks
setblock 45 65 40 oak_fence
setblock 45 66 40 lantern
setblock 50 64 40 oak_planks
setblock 50 65 40 oak_fence
setblock 50 66 40 lantern
setblock 55 64 40 oak_planks
setblock 55 65 40 oak_fence
setblock 55 66 40 lantern
setblock 60 64 40 oak_planks
setblock 60 65 40 oak_fence
setblock 60 66 40 lantern
setblock 50 65 50 water

# --- 3. KITCHENS (Cocinas) - Transformacion, mezcla ---
# Bioma: Moss (Projector 2/4)
fill -58 63 42 -42 67 58 bricks
fill -57 64 43 -43 66 57 air
setblock -56 64 44 smoker[facing=south]
setblock -56 64 56 campfire
setblock -53 64 44 smoker[facing=south]
setblock -53 64 56 campfire
setblock -50 64 44 smoker[facing=south]
setblock -50 64 56 campfire
setblock -47 64 44 smoker[facing=south]
setblock -47 64 56 campfire
setblock -44 64 44 smoker[facing=south]
setblock -44 64 56 campfire
setblock -50 65 50 brewing_stand

# --- 4. MOUNTAINS (Montanas) - Altura, perspectiva ---
# Bioma: Observatorio universal
fill -10 64 -90 10 64 -70 stone
fill -10 65 -90 10 65 -70 stone
fill -9 66 -89 9 66 -71 stone
fill -9 67 -89 9 67 -71 stone
fill -8 68 -88 8 68 -72 stone
fill -8 69 -88 8 69 -72 stone
fill -7 70 -87 7 70 -73 stone
fill -7 71 -87 7 71 -73 stone
fill -6 72 -86 6 72 -74 stone
fill -6 73 -86 6 73 -74 stone
fill -5 74 -85 5 74 -75 stone
fill -5 75 -85 5 75 -75 stone
fill -4 76 -84 4 76 -76 stone
fill -4 77 -84 4 77 -76 stone
fill -3 78 -83 3 78 -77 stone
fill -3 79 -83 3 79 -77 stone
fill -2 80 -82 2 80 -78 stone
fill -2 81 -82 2 81 -78 stone
fill -1 82 -81 1 82 -79 stone
fill -1 83 -81 1 83 -79 stone
setblock 0 84 -80 glass
setblock 0 85 -80 end_rod

# --- 5. VALLEYS (Valles) - Flujo, comunicacion ---
# Bioma: Stevie (Manifestor 4/6) y Flint (MG 3/5)
fill 75 62 -30 85 63 30 water
fill 72 63 -30 74 63 30 dirt_path
fill 86 63 -30 88 63 30 dirt_path
fill 78 63 -20 82 63 -20 oak_planks
fill 78 63 -10 82 63 -10 oak_planks
fill 78 63 0 82 63 0 oak_planks
fill 78 63 10 82 63 10 oak_planks
fill 78 63 20 82 63 20 oak_planks

# --- 6. SHORES (Costas) - Borde entre mundos ---
# Bioma: Umbral, transicion
fill -90 63 -20 -70 63 20 sand
fill -95 62 -20 -91 63 20 water
fill -80 64 0 -80 64 15 oak_planks
setblock -80 65 15 lantern

# === SPAWN: Los 5 Landfolk ===
# Cada uno en su centro HD correspondiente

# Stevie — Manifestor 4/6 — Sala del Voz - Valleys
summon villager 0 70 0 {CustomName:'{"text":"Stevie","color":"yellow","bold":true}',CustomNameVisible:1b,NoAI:0b,PersistenceRequired:1b,VillagerData:{profession:"mason",level:5},Tags:["landfolk","stevie","hd_bot"]}
summon armor_stand 0 72.5 0 {CustomName:'{"text":"Stevie — Architecta jefa","color":"yellow","italic":true}',CustomNameVisible:1b,Invisible:1b,NoGravity:1b,Marker:1b}

# Moss — Projector 2/4 — Sala de las Puertas - Kitchens
summon villager -25 65 5 {CustomName:'{"text":"Moss","color":"green","bold":true}',CustomNameVisible:1b,NoAI:0b,PersistenceRequired:1b,VillagerData:{profession:"cleric",level:5},Tags:["landfolk","moss","hd_bot"]}
summon armor_stand -25 67.5 5 {CustomName:'{"text":"Moss — Feng shui master","color":"green","italic":true}',CustomNameVisible:1b,Invisible:1b,NoGravity:1b,Marker:1b}

# Reed — Reflector 1/3 — Cuarto del Amor - Markets
summon villager -15 65 30 {CustomName:'{"text":"Reed","color":"light_blue","bold":true}',CustomNameVisible:1b,NoAI:0b,PersistenceRequired:1b,VillagerData:{profession:"librarian",level:5},Tags:["landfolk","reed","hd_bot"]}
summon armor_stand -15 67.5 30 {CustomName:'{"text":"Reed — Mediador del grupo","color":"light_blue","italic":true}',CustomNameVisible:1b,Invisible:1b,NoGravity:1b,Marker:1b}

# Flint — Manifesting Generator 3/5 — Sala del Sacro - Valleys
summon villager 5 65 25 {CustomName:'{"text":"Flint","color":"red","bold":true}',CustomNameVisible:1b,NoAI:0b,PersistenceRequired:1b,VillagerData:{profession:"toolsmith",level:5},Tags:["landfolk","flint","hd_bot"]}
summon armor_stand 5 67.5 25 {CustomName:'{"text":"Flint — Minero y constructor","color":"red","italic":true}',CustomNameVisible:1b,Invisible:1b,NoGravity:1b,Marker:1b}

# Ember — Generator 1/3 — Jardin Emocional - Caves
summon villager 0 65 45 {CustomName:'{"text":"Ember","color":"orange","bold":true}',CustomNameVisible:1b,NoAI:0b,PersistenceRequired:1b,VillagerData:{profession:"farmer",level:5},Tags:["landfolk","ember","hd_bot"]}
summon armor_stand 0 67.5 45 {CustomName:'{"text":"Ember — Jardinera y cocinera","color":"orange","italic":true}',CustomNameVisible:1b,Invisible:1b,NoGravity:1b,Marker:1b}

# === CARTELES INDICADORES ===
setblock 0 65 -15 oak_sign['{Text1:\'{"text":"Cripta de la Memoria"}\',Text2:\'{"text":"Centro Raiz","color":"gray"}\'}']
setblock -25 65 0 oak_sign['{Text1:\'{"text":"Sala de las Puertas"}\',Text2:\'{"text":"Centro Ajna - Moss","color":"gray"}\'}']
setblock 5 65 15 oak_sign['{Text1:\'{"text":"Sala del Sacro"}\',Text2:\'{"text":"Centro Sacral - Flint","color":"gray"}\'}']
setblock -10 65 30 oak_sign['{Text1:\'{"text":"Cuarto del Amor"}\',Text2:\'{"text":"Centro Corazon - Reed","color":"gray"}\'}']
setblock 20 65 -5 oak_sign['{Text1:\'{"text":"Torre del Oraculo"}\',Text2:\'{"text":"Centro Corona","color":"gray"}\'}']
setblock -20 65 5 oak_sign['{Text1:\'{"text":"Biblioteca HD"}\',Text2:\'{"text":"Centro Cabeza","color":"gray"}\'}']
setblock 30 65 10 oak_sign['{Text1:\'{"text":"Sala del Coraje"}\',Text2:\'{"text":"Centro Ego","color":"gray"}\'}']
setblock 0 65 35 oak_sign['{Text1:\'{"text":"Jardin Emocional"}\',Text2:\'{"text":"Centro Solar Plexus - Ember","color":"gray"}\'}']
setblock 0 70 -5 oak_sign['{Text1:\'{"text":"Sala del Voz"}\',Text2:\'{"text":"Centro Garganta - Stevie","color":"gray"}\'}']

# === MENSAJE DE BIENVENIDA ===
tellraw @a "\u00a7d[Oraculo]\u00a7r Bienvenida al Mundo Soul, Saira."
tellraw @a "\u00a77El Templo de Ra aguarda. 5 almas te esperan."
tellraw @a "\u00a77Escribe \u00a7e/help soul\u00a77 para ver comandos disponibles."
