/**
 * Emotion Engine — Expressive body language for DaemonCraft bots
 *
 * Turns a Mineflayer bot into a character with visible emotions:
 *  - Body poses (sneak, elytra-fly, jump-dance, spin)
 *  - Particle emojis (heart, note, soul, flame, splash)
 *  - Floating display-entities (text emojis, item icons)
 *  - Reactive sounds
 *  - Movement patterns (hover, circle, bounce, spiral)
 *
 * States: idle | joy | love | anger | surprise | dance | sleep | battle | mine
 *
 * Usage:
 *   import { EmotionEngine } from './lib/emotion-engine.js';
 *   const ee = new EmotionEngine(bot, { username: 'PamPliNas' });
 *   ee.start();
 *   ee.emote('love');
 *   ee.dance();
 *   ee.mine();
 *   ee.attack();
 *   ee.stop();
 */

import { Vec3 } from 'vec3';

const EMOTION_CONFIG = {
  idle:   { particle: 'minecraft:end_rod',   sound: 'entity.allay.ambient_without_item', pitch: 1.0, swing: false, hoverJitter: 0.05 },
  joy:    { particle: 'minecraft:note',      sound: 'entity.allay.ambient_with_item',    pitch: 1.2, swing: true,  swingMs: 600, hoverJitter: 0.15 },
  love:   { particle: 'minecraft:heart',     sound: 'entity.allay.item_given',           pitch: 1.1, swing: true,  swingMs: 800, hoverJitter: 0.10 },
  anger:  { particle: 'minecraft:flame',     sound: 'entity.allay.hurt',                 pitch: 0.8, swing: true,  swingMs: 300, hoverJitter: 0.25 },
  surprise: { particle: 'minecraft:witch',   sound: 'entity.allay.ambient_without_item', pitch: 1.4, swing: true,  swingMs: 400, hoverJitter: 0.20 },
  dance:  { particle: 'minecraft:note',      sound: 'entity.allay.ambient_with_item',    pitch: 1.2, swing: true,  swingMs: 250, hoverJitter: 0.30 },
  sleep:  { particle: 'minecraft:zzz',       sound: 'entity.allay.ambient_without_item', pitch: 0.6, swing: false, hoverJitter: 0.02 },
  battle: { particle: 'minecraft:sweep_attack', sound: 'entity.allay.hurt',              pitch: 1.0, swing: true,  swingMs: 400, hoverJitter: 0.15 },
  mine:   { particle: 'minecraft:block_crack',  sound: 'entity.allay.ambient_without_item', pitch: 1.0, swing: true, swingMs: 500, hoverJitter: 0.08 },
  place:  { particle: 'minecraft:happy_villager', sound: 'block.stone.place',            pitch: 1.1, swing: true,  swingMs: 700, hoverJitter: 0.10 },
  build:  { particle: 'minecraft:happy_villager', sound: 'entity.allay.ambient_with_item', pitch: 1.2, swing: true,  swingMs: 500, hoverJitter: 0.15 },
  hurt:   { particle: 'minecraft:damage_indicator', sound: 'entity.allay.hurt',          pitch: 0.9, swing: true,  swingMs: 200, hoverJitter: 0.20 },
  jump:   { particle: 'minecraft:cloud',     sound: 'entity.allay.ambient_with_item',    pitch: 1.3, swing: true,  swingMs: 300, hoverJitter: 0.25 },
  eat:    { particle: 'minecraft:happy_villager', sound: 'entity.generic.eat',           pitch: 1.0, swing: false, hoverJitter: 0.05 },
  pickup: { particle: 'minecraft:end_rod',   sound: 'entity.allay.item_taken',           pitch: 1.2, swing: true,  swingMs: 400, hoverJitter: 0.12 },
  give:   { particle: 'minecraft:heart',     sound: 'entity.allay.item_given',           pitch: 1.1, swing: true,  swingMs: 500, hoverJitter: 0.10 },
  die:    { particle: 'minecraft:soul',      sound: 'entity.allay.death',                pitch: 0.7, swing: false, hoverJitter: 0.0  },
};

const MOVEMENT_PATTERNS = {
  hover:   async (bot, ms) => { /* default sine bob — handled in tick */ },
  circle:  async (bot, ms) => _circle(bot, ms, 2.0),
  spiral:  async (bot, ms) => _spiral(bot, ms, 2.0, 1.0),
  bounce:  async (bot, ms) => _bounce(bot, ms),
  zigzag:  async (bot, ms) => _zigzag(bot, ms),
  spin:    async (bot, ms) => _spin(bot, ms),
};

const DISPLAY_EMOJIS = {
  heart:    { text: '❤️',  color: '#ff3366' },
  note:     { text: '🎵',  color: '#ffcc00' },
  star:     { text: '⭐',   color: '#ffdd44' },
  skull:    { text: '💀',  color: '#aaaaaa' },
  fire:     { text: '🔥',  color: '#ff6600' },
  water:    { text: '💧',  color: '#3399ff' },
  zap:      { text: '⚡',   color: '#ffff66' },
  diamond:  { item: 'minecraft:diamond', scale: 1.5 },
  emerald:  { item: 'minecraft:emerald', scale: 1.5 },
  sword:    { item: 'minecraft:iron_sword', scale: 1.2 },
  pickaxe:  { item: 'minecraft:iron_pickaxe', scale: 1.2 },
};

export class EmotionEngine {
  constructor(bot, opts = {}) {
    this.bot = bot;
    this.username = opts.username || bot.username;
    this.tickMs = opts.tickMs || 200;
    this.enabled = false;
    this.currentEmotion = 'idle';
    this.swingTimer = 0;
    this.hoverPhase = 0;
    this.lastSound = 0;
    this.tickInterval = null;
    this.movementPromise = null;
    this.armToggle = false;
    this.displayEntities = []; // track spawned display entities
  }

  start() {
    if (this.enabled) return;
    this.enabled = true;
    this._enterHoverMode();
    this.tickInterval = setInterval(() => this._tick(), this.tickMs);
    console.log(`[emotion] Engine started for ${this.username}`);
  }

  stop() {
    this.enabled = false;
    if (this.tickInterval) clearInterval(this.tickInterval);
    this._exitHoverMode();
    this._killAllDisplays();
    console.log(`[emotion] Engine stopped for ${this.username}`);
  }

  // ─────────────────────────────────────────────────────────────────
  // High-level expressive actions (callable by agent tools)
  // ─────────────────────────────────────────────────────────────────

  emote(emotion) {
    if (!EMOTION_CONFIG[emotion]) {
      console.warn(`[emotion] Unknown emotion "${emotion}"`);
      return;
    }
    this.currentEmotion = emotion;
    this.swingTimer = 0;
    console.log(`[emotion] ${this.username} feels ${emotion}`);

    // Immediate burst
    this._particleBurst(8);
    this._playSound(1.0);
  }

  /** Express joy — bouncing + notes */
  joy() { this.emote('joy'); this._movePattern('bounce', 1500); }

  /** Express love — hearts + gentle hover */
  love() { this.emote('love'); this._showDisplay('heart', 2000); }

  /** Express anger — flames + aggressive swing */
  anger() { this.emote('anger'); this._showDisplay('fire', 1500); }

  /** Express surprise — witch particles + spin */
  surprise() { this.emote('surprise'); this._movePattern('spin', 1000); }

  /** Dance! — note particles + circular movement */
  dance() { this.emote('dance'); this._movePattern('circle', 3000); }

  /** Sleep — zzz particles + descend */
  sleep() { this.emote('sleep'); this._descend(0.5); }

  /** Battle stance — sweep particles + ready pose */
  battle() { this.emote('battle'); this._showDisplay('sword', 2000); }

  /** Mining — block crack + tool display */
  mine() { this.emote('mine'); this._showDisplay('pickaxe', 2000); }

  /** Place a block — happy villager particles */
  place() { this.emote('place'); }

  /** Build structure — creative joy */
  build() { this.emote('build'); this._showDisplay('emerald', 2000); }

  /** Hurt / damaged — red particles + recoil */
  hurt() { this.emote('hurt'); this._movePattern('bounce', 500); }

  /** Jump / leap — cloud particles */
  jump() { this.emote('jump'); }

  /** Eat food */
  eat() { this.emote('eat'); }

  /** Pick up item — sparkle */
  pickup() { this.emote('pickup'); this._showDisplay('emerald', 1500); }

  /** Give item to player — hearts */
  give() { this.emote('give'); this._showDisplay('heart', 2000); }

  /** Death / respawn — soul particles */
  die() { this.emote('die'); }

  /** Attack — lunge forward + hurt sound */
  attack() {
    this.emote('battle');
    this._lunge();
    this._playSound(1.0);
  }

  /** React to chat — show text emoji floating */
  react(emojiKey, durationMs = 2000) {
    this._showDisplay(emojiKey, durationMs);
  }

  /** Show a floating text message above the bot */
  sayAbove(text, durationMs = 3000) {
    this._spawnTextDisplay(text, durationMs);
  }

  // ─────────────────────────────────────────────────────────────────
  // Tick loop
  // ─────────────────────────────────────────────────────────────────

  _tick() {
    if (!this.enabled || !this.bot.entity) return;
    const cfg = EMOTION_CONFIG[this.currentEmotion];

    // Hover bobbing
    this._hoverBob();

    // Arm swing
    if (cfg.swing && cfg.swingMs > 0) {
      this.swingTimer += this.tickMs;
      if (this.swingTimer >= cfg.swingMs) {
        this.swingTimer = 0;
        this.armToggle = !this.armToggle;
        this._swing(this.armToggle ? 'right' : 'left');
      }
    }

    // Ambient particles (probabilistic)
    if (Math.random() < 0.15) {
      this._emitParticle(1);
    }

    // Ambient sounds (very sparse)
    if (Math.random() < 0.02) {
      this._playSound(0.6);
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // Primitives
  // ─────────────────────────────────────────────────────────────────

  _swing(arm) {
    try { this.bot.swingArm(arm, true); } catch {}
  }

  _hoverBob() {
    if (!this.bot.entity) return;
    this.hoverPhase += 0.12;
    const jitter = EMOTION_CONFIG[this.currentEmotion]?.hoverJitter ?? 0.05;
    const offset = Math.sin(this.hoverPhase) * jitter;
    if (this.bot.physics) this.bot.physics.gravity = 0;
    if (this.bot.entity.velocity) this.bot.entity.velocity = new Vec3(0, 0, 0);
    this.bot.entity.position.y += offset * 0.02; // subtle
  }

  _enterHoverMode() {
    if (this.bot.physics) {
      this._normalGravity = this.bot.physics.gravity;
      this.bot.physics.gravity = 0;
    }
  }

  _exitHoverMode() {
    if (this.bot.physics && this._normalGravity != null) {
      this.bot.physics.gravity = this._normalGravity;
    }
  }

  _emitParticle(count = 1) {
    const cfg = EMOTION_CONFIG[this.currentEmotion];
    const pos = this.bot.entity.position;
    const cmd = `/particle ${cfg.particle} ${pos.x.toFixed(1)} ${(pos.y + 1).toFixed(1)} ${pos.z.toFixed(1)} 0.3 0.3 0.3 0.02 ${count} force`;
    this._safeChat(cmd);
  }

  _particleBurst(count) {
    const cfg = EMOTION_CONFIG[this.currentEmotion];
    const pos = this.bot.entity.position;
    const cmd = `/particle ${cfg.particle} ${pos.x.toFixed(1)} ${(pos.y + 1.5).toFixed(1)} ${pos.z.toFixed(1)} 0.5 0.5 0.5 0.1 ${count} force`;
    this._safeChat(cmd);
  }

  _playSound(volume = 0.6) {
    const now = Date.now();
    if (now - this.lastSound < 2000) return;
    this.lastSound = now;
    const cfg = EMOTION_CONFIG[this.currentEmotion];
    const pos = this.bot.entity.position;
    const pitch = (cfg.pitch + (Math.random() * 0.2 - 0.1)).toFixed(2);
    const cmd = `/playsound ${cfg.sound} ambient @a ${pos.x.toFixed(1)} ${pos.y.toFixed(1)} ${pos.z.toFixed(1)} ${volume} ${pitch}`;
    this._safeChat(cmd);
  }

  _safeChat(cmd) {
    try { if (this.bot.chat) this.bot.chat(cmd); } catch {}
  }

  // ─────────────────────────────────────────────────────────────────
  // Display Entities (emojis flotantes)
  // ─────────────────────────────────────────────────────────────────

  _showDisplay(key, durationMs) {
    const def = DISPLAY_EMOJIS[key];
    if (!def) return;
    if (def.text) {
      this._spawnTextDisplay(def.text, durationMs, def.color);
    } else if (def.item) {
      this._spawnItemDisplay(def.item, durationMs, def.scale);
    }
  }

  _spawnTextDisplay(text, durationMs = 2000, color = '#ffffff') {
    const pos = this.bot.entity.position;
    const uuid = this._randomTag();
    const cmd = `/summon minecraft:text_display ${pos.x.toFixed(2)} ${(pos.y + 2.2).toFixed(2)} ${pos.z.toFixed(2)} {text:'{"text":"${text}","color":"${color}"}',billboard:"center",see_through:1b,Tags:["dc_${this.username}","${uuid}"],transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.5f,1.5f,1.5f]}}`;
    this._safeChat(cmd);
    this.displayEntities.push(uuid);
    setTimeout(() => this._killDisplay(uuid), durationMs);
  }

  _spawnItemDisplay(itemId, durationMs = 2000, scale = 1.0) {
    const pos = this.bot.entity.position;
    const uuid = this._randomTag();
    const cmd = `/summon minecraft:item_display ${pos.x.toFixed(2)} ${(pos.y + 2.0).toFixed(2)} ${pos.z.toFixed(2)} {item:{id:"${itemId}",Count:1b},billboard:"center",Tags:["dc_${this.username}","${uuid}"],transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[${scale}f,${scale}f,${scale}f]}}`;
    this._safeChat(cmd);
    this.displayEntities.push(uuid);
    setTimeout(() => this._killDisplay(uuid), durationMs);
  }

  _killDisplay(uuid) {
    this._safeChat(`/kill @e[type=minecraft:text_display,tag=${uuid}]`);
    this._safeChat(`/kill @e[type=minecraft:item_display,tag=${uuid}]`);
    this.displayEntities = this.displayEntities.filter(id => id !== uuid);
  }

  _killAllDisplays() {
    this._safeChat(`/kill @e[type=minecraft:text_display,tag=dc_${this.username}]`);
    this._safeChat(`/kill @e[type=minecraft:item_display,tag=dc_${this.username}]`);
    this.displayEntities = [];
  }

  _randomTag() {
    return 'd' + Math.random().toString(36).slice(2, 8);
  }

  // ─────────────────────────────────────────────────────────────────
  // Movement primitives (async, fire-and-forget)
  // ─────────────────────────────────────────────────────────────────

  async _movePattern(patternName, ms) {
    if (this.movementPromise) return; // one at a time
    const fn = MOVEMENT_PATTERNS[patternName];
    if (!fn) return;
    this.movementPromise = fn(this.bot, ms).catch(() => {}).finally(() => {
      this.movementPromise = null;
    });
  }

  async _lunge() {
    if (!this.bot.entity) return;
    const yaw = this.bot.entity.yaw;
    const forward = new Vec3(-Math.sin(yaw), 0, -Math.cos(yaw)).scaled(1.5);
    const dest = this.bot.entity.position.plus(forward);
    if (this.bot.creative?.flyTo) {
      try { await this.bot.creative.flyTo(dest); } catch {}
    } else {
      this.bot.entity.position.add(forward.scaled(0.3));
    }
  }

  async _descend(amount) {
    if (!this.bot.entity) return;
    this.bot.entity.position.y -= amount;
  }
}

// ─────────────────────────────────────────────────────────────────
// Movement pattern implementations
// ─────────────────────────────────────────────────────────────────

async function _circle(bot, ms, radius) {
  const steps = Math.floor(ms / 100);
  const center = bot.entity.position.clone();
  for (let i = 0; i < steps; i++) {
    const angle = (i / steps) * Math.PI * 2;
    const dest = center.offset(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
    if (bot.creative?.flyTo) {
      try { await bot.creative.flyTo(dest); } catch { break; }
    } else {
      bot.entity.position = dest;
    }
    await sleep(100);
  }
}

async function _spiral(bot, ms, radius, rise) {
  const steps = Math.floor(ms / 100);
  const center = bot.entity.position.clone();
  for (let i = 0; i < steps; i++) {
    const angle = (i / steps) * Math.PI * 4;
    const y = center.y + (i / steps) * rise;
    const dest = new Vec3(center.x + Math.cos(angle) * radius, y, center.z + Math.sin(angle) * radius);
    if (bot.creative?.flyTo) {
      try { await bot.creative.flyTo(dest); } catch { break; }
    } else {
      bot.entity.position = dest;
    }
    await sleep(100);
  }
}

async function _bounce(bot, ms) {
  const steps = Math.floor(ms / 150);
  const base = bot.entity.position.y;
  for (let i = 0; i < steps; i++) {
    bot.entity.position.y = base + Math.abs(Math.sin((i / steps) * Math.PI * 4)) * 0.8;
    await sleep(150);
  }
  bot.entity.position.y = base;
}

async function _zigzag(bot, ms) {
  const steps = Math.floor(ms / 200);
  const base = bot.entity.position.clone();
  for (let i = 0; i < steps; i++) {
    const offset = (i % 2 === 0 ? 1 : -1) * 0.8;
    bot.entity.position.x = base.x + offset;
    await sleep(200);
  }
  bot.entity.position.x = base.x;
}

async function _spin(bot, ms) {
  const steps = Math.floor(ms / 50);
  const startYaw = bot.entity.yaw;
  for (let i = 0; i < steps; i++) {
    bot.entity.yaw = startYaw + (i / steps) * Math.PI * 4;
    await sleep(50);
  }
  bot.entity.yaw = startYaw;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

export default EmotionEngine;
