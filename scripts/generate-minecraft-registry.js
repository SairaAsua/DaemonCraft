#!/usr/bin/env node
// MC_VERSION: 1.21.11
// Regenerate this file's output when bumping Minecraft version:
//   node scripts/generate-minecraft-registry.js
// This script sources canonical data from minecraft-data (PrismarineJS).

// Resolve minecraft-data from the bot's node_modules since that's where it's installed.
const fs = require('fs');
const path = require('path');
const botNodeModules = path.join(__dirname, '..', 'agents', 'bot', 'node_modules');
const mc = require(path.join(botNodeModules, 'minecraft-data'));

// ---------------------------------------------------------------------------
// MC_VERSION_SENSITIVE: 1.21.11
// Pin the Minecraft version here. When bumping, change this string and rerun.
// ---------------------------------------------------------------------------
const MINECRAFT_VERSION = '1.21.11';

const data = mc(MINECRAFT_VERSION);
if (!data) {
  console.error(`minecraft-data does not have version ${MINECRAFT_VERSION}`);
  process.exit(1);
}

// ---------------------------------------------------------------------------
// MC_VERSION_SENSITIVE: 1.21.11
// Scoreboard criteria are not exposed by minecraft-data; we maintain them
// manually because they change very rarely. When bumping version, verify
// against https://minecraft.wiki/w/Scoreboard#Criteria
// ---------------------------------------------------------------------------
const SCOREBOARD_CRITERIA = [
  { name: 'dummy', description: 'Manually set by commands' },
  { name: 'trigger', description: 'Same as dummy but enables /trigger' },
  { name: 'deathCount', description: 'Times died' },
  { name: 'playerKillCount', description: 'Players killed' },
  { name: 'totalKillCount', description: 'Mobs/players killed' },
  { name: 'health', description: 'Current health (half-hearts)' },
  { name: 'xp', description: 'Experience points' },
  { name: 'level', description: 'Experience level' },
  { name: 'food', description: 'Food level' },
  { name: 'air', description: 'Air supply (ticks)' },
  { name: 'armor', description: 'Armor value' },
  // Stat-based criteria (commonly used)
  { name: 'minecraft.mined', description: 'Blocks mined (requires block)' },
  { name: 'minecraft.crafted', description: 'Items crafted (requires item)' },
  { name: 'minecraft.used', description: 'Items used (requires item)' },
  { name: 'minecraft.broken', description: 'Items broken (requires item)' },
  { name: 'minecraft.picked_up', description: 'Items picked up (requires item)' },
  { name: 'minecraft.dropped', description: 'Items dropped (requires item)' },
  { name: 'minecraft.killed', description: 'Entity killed (requires entity)' },
  { name: 'minecraft.killed_by', description: 'Killed by entity (requires entity)' },
  { name: 'minecraft.custom', description: 'Custom stat (requires stat)' },
];

function buildRegistry() {
  const registry = {
    _meta: {
      // MC_VERSION: 1.21.11
      version: MINECRAFT_VERSION,
      generated_at: new Date().toISOString(),
      source: `minecraft-data@${require(path.join(botNodeModules, 'minecraft-data', 'package.json')).version}`,
      comment: `Regenerate with: node scripts/generate-minecraft-registry.js`,
    },
    biomes: data.biomesArray.map(b => ({
      name: b.name,
      displayName: b.displayName,
      dimension: b.dimension,
    })),
    entities: data.entitiesArray.map(e => ({
      name: e.name,
      displayName: e.displayName,
      type: e.type,        // 'mob', 'player', 'object', 'other'
      category: e.category || null,
    })),
    blocks: data.blocksArray.map(b => ({
      name: b.name,
      displayName: b.displayName,
    })),
    items: data.itemsArray.map(i => ({
      name: i.name,
      displayName: i.displayName,
    })),
    effects: data.effectsArray.map(e => ({
      name: e.name,
      displayName: e.displayName,
    })),
    scoreboard_criteria: SCOREBOARD_CRITERIA,
  };
  return registry;
}

const registry = buildRegistry();

const outPath = path.join(__dirname, '..', 'agents', 'data', 'minecraft-registry.json');
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, JSON.stringify(registry, null, 2));

console.log(`Wrote minecraft-registry.json for ${MINECRAFT_VERSION}`);
console.log(`  Biomes:    ${registry.biomes.length}`);
console.log(`  Entities:  ${registry.entities.length}`);
console.log(`  Blocks:    ${registry.blocks.length}`);
console.log(`  Items:     ${registry.items.length}`);
console.log(`  Effects:   ${registry.effects.length}`);
console.log(`  Scoreboard criteria: ${registry.scoreboard_criteria.length}`);
