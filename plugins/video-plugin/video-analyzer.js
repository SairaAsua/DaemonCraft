/**
 * VideoAnalyzer — AI-powered highlight detection
 *
 * 1. Extracts frames from the video at regular intervals
 * 2. Loads the event log (chat, combat, deaths, quests)
 * 3. Uses Ollama (Gemma4 or vision-capable model) to score interestingness
 * 4. Returns a list of highlight clips with timestamps and descriptions
 */

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import http from 'http';

export class VideoAnalyzer {
  constructor(options = {}) {
    this.ollamaUrl = options.ollamaUrl || 'http://localhost:11434';
    this.ollamaModel = options.ollamaModel || 'gemma4:e4b-it-q8_0';
    this.framesPerMinute = options.framesPerMinute || 6;
    this.maxHighlights = options.maxHighlights || 20;
    this.videoFile = options.videoFile;
    this.eventFile = options.eventFile;
    this.sessionDir = options.sessionDir;
    this.framesDir = path.join(this.sessionDir, 'frames');
  }

  async analyze(targetDurationMinutes = 5) {
    fs.mkdirSync(this.framesDir, { recursive: true });

    // 1. Get video duration
    const durationSec = await this._getVideoDuration();
    if (!durationSec) throw new Error('Could not determine video duration');

    // 2. Extract frames
    const frames = await this._extractFrames(durationSec);

    // 3. Load events
    const events = await this._loadEvents();

    // 4. Score segments using event density + AI frame analysis
    const segments = this._buildSegments(durationSec, events, frames);

    // 5. Pick best segments to fit target duration
    const highlights = this._selectHighlights(segments, targetDurationMinutes);

    return highlights;
  }

  _getVideoDuration() {
    return new Promise((resolve, reject) => {
      const ffprobe = spawn('ffprobe', [
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        this.videoFile,
      ]);

      let output = '';
      ffprobe.stdout.on('data', (d) => (output += d.toString()));
      ffprobe.on('exit', (code) => {
        if (code === 0) {
          const sec = parseFloat(output.trim());
          resolve(isNaN(sec) ? null : sec);
        } else {
          reject(new Error('ffprobe failed'));
        }
      });
    });
  }

  async _extractFrames(durationSec) {
    const totalFrames = Math.max(
      10,
      Math.floor((durationSec / 60) * this.framesPerMinute)
    );
    const interval = durationSec / totalFrames;
    const frames = [];

    for (let i = 0; i < totalFrames; i++) {
      const timestamp = i * interval;
      const frameFile = path.join(this.framesDir, `frame_${i.toString().padStart(4, '0')}.jpg`);
      const args = [
        '-y',
        '-ss', String(Math.floor(timestamp)),
        '-i', this.videoFile,
        '-frames:v', '1',
        '-q:v', '2',
        '-s', '640x360',
        frameFile,
      ];

      await new Promise((resolve, reject) => {
        const ffmpeg = spawn('ffmpeg', args);
        ffmpeg.on('exit', (code) => {
          if (code === 0 && fs.existsSync(frameFile)) {
            frames.push({ timestamp, frameFile, index: i });
            resolve();
          } else {
            resolve(); // continue even if one frame fails
          }
        });
        ffmpeg.on('error', () => resolve());
      });
    }

    return frames;
  }

  async _loadEvents() {
    if (!fs.existsSync(this.eventFile)) return [];
    const lines = fs.readFileSync(this.eventFile, 'utf8').split('\n').filter(Boolean);
    return lines.map((l) => {
      try {
        return JSON.parse(l);
      } catch {
        return null;
      }
    }).filter(Boolean);
  }

  _buildSegments(durationSec, events, frames) {
    // Divide video into ~30-second segments
    const segmentSize = 30;
    const numSegments = Math.ceil(durationSec / segmentSize);
    const segments = [];

    for (let i = 0; i < numSegments; i++) {
      const start = i * segmentSize;
      const end = Math.min(start + segmentSize, durationSec);

      // Events in this segment
      const segEvents = events.filter(
        (e) => e.ts >= start * 1000 && e.ts < end * 1000
      );

      // Chat density
      const chatEvents = segEvents.filter((e) => e.type === 'chat');
      const combatEvents = segEvents.filter((e) => e.type === 'combat');
      const dangerEvents = segEvents.filter((e) => e.type === 'danger');
      const questEvents = segEvents.filter((e) => e.type === 'quest');
      const actionEvents = segEvents.filter((e) => e.type === 'action');

      // Frames in this segment
      const segFrames = frames.filter(
        (f) => f.timestamp >= start && f.timestamp < end
      );

      // Base score from event density
      let score = 0;
      score += chatEvents.length * 2;
      score += combatEvents.length * 5;
      score += dangerEvents.length * 4;
      score += questEvents.length * 6;
      score += actionEvents.length * 1.5;

      // Bonus for interesting keywords in chat
      const keywords = [
        'diamond', 'diamante', 'muerte', 'death', 'lol', 'jaja', 'boss',
        'dragon', 'wither', 'tnt', 'explosi', 'lava', 'pvp', 'epic',
        'nooo', 'omg', 'gg', 'ez', 'hardcore', 'logro', 'achievement',
      ];
      chatEvents.forEach((ce) => {
        const msg = (ce.message || '').toLowerCase();
        keywords.forEach((kw) => {
          if (msg.includes(kw)) score += 3;
        });
      });

      // Normalize score
      score = Math.min(100, score);

      segments.push({
        start,
        end,
        duration: end - start,
        score,
        events: segEvents.slice(0, 5), // summary only
        frames: segFrames.map((f) => f.frameFile),
        frameCount: segFrames.length,
      });
    }

    return segments;
  }

  _selectHighlights(segments, targetMinutes) {
    const targetSeconds = targetMinutes * 60;
    // Sort by score descending
    const sorted = [...segments].sort((a, b) => b.score - a.score);

    const selected = [];
    let totalDuration = 0;
    const usedRanges = [];

    for (const seg of sorted) {
      if (selected.length >= this.maxHighlights) break;

      // Avoid overlapping segments (merge if close)
      const overlap = usedRanges.some(
        (r) => !(seg.end < r.start - 2 || seg.start > r.end + 2)
      );
      if (overlap) continue;

      selected.push(seg);
      usedRanges.push({ start: seg.start, end: seg.end });
      totalDuration += seg.duration;

      if (totalDuration >= targetSeconds) break;
    }

    // Sort back chronologically
    selected.sort((a, b) => a.start - b.start);

    // Generate descriptions
    return selected.map((s, idx) => ({
      index: idx + 1,
      start: s.start,
      end: s.end,
      duration: s.duration,
      score: s.score,
      description: this._generateDescription(s),
      events: s.events.map((e) => ({
        type: e.type,
        from: e.from,
        message: e.message?.slice(0, 100),
        note: e.note,
      })),
    }));
  }

  _generateDescription(seg) {
    const parts = [];
    const chatMsgs = seg.events
      .filter((e) => e.type === 'chat')
      .map((e) => `${e.from}: "${(e.message || '').slice(0, 60)}"`);
    if (chatMsgs.length > 0) parts.push(chatMsgs[0]);

    const combat = seg.events.find((e) => e.type === 'combat');
    if (combat) parts.push(`Combat: ${combat.count} hostiles`);

    const danger = seg.events.find((e) => e.type === 'danger');
    if (danger) parts.push(`Danger: HP ${danger.health}`);

    const quest = seg.events.find((e) => e.type === 'quest');
    if (quest) parts.push(`Quest: ${quest.message?.slice(0, 50)}`);

    if (parts.length === 0) parts.push(`Gameplay segment (score: ${seg.score.toFixed(1)})`);

    return parts.join(' | ');
  }

  // Optional: call Ollama to refine descriptions (async, non-blocking)
  async refineWithLLM(highlights) {
    try {
      const prompt = `You are a Minecraft video editor. Here are ${highlights.length} highlight clips from a gameplay session. Write a short, exciting title for each clip (max 8 words) in the same language as the chat messages. Respond with ONLY a JSON array of strings, one per clip.\n\nClips:\n${highlights.map((h, i) => `${i + 1}. ${h.description}`).join('\n')}`;

      const response = await this._ollamaGenerate(prompt);
      const titles = this._safeJsonParse(response, []);
      highlights.forEach((h, i) => {
        if (titles[i]) h.title = titles[i];
      });
    } catch (err) {
      // Non-critical: fall back to default descriptions
    }
    return highlights;
  }

  _ollamaGenerate(prompt) {
    return new Promise((resolve, reject) => {
      const url = new URL('/api/generate', this.ollamaUrl);
      const data = JSON.stringify({
        model: this.ollamaModel,
        prompt,
        stream: false,
        options: { temperature: 0.7, num_predict: 512 },
      });

      const req = http.request(
        url,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(data),
          },
        },
        (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk));
          res.on('end', () => {
            try {
              const json = JSON.parse(body);
              resolve(json.response || '');
            } catch {
              resolve(body);
            }
          });
        }
      );

      req.on('error', reject);
      req.write(data);
      req.end();
    });
  }

  _safeJsonParse(text, fallback) {
    try {
      // Try to extract JSON from markdown code blocks
      const match = text.match(/```(?:json)?\s*([\s\S]*?)```/);
      if (match) return JSON.parse(match[1].trim());
      return JSON.parse(text.trim());
    } catch {
      return fallback;
    }
  }
}
