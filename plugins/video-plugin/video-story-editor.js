/**
 * VideoStoryEditor — Narrative-driven highlight editing
 *
 * Takes a recorded session + a story template and produces a cinematic
 * output that follows the narrative beats of the adventure.
 *
 * Usage:
 *   const editor = new VideoStoryEditor({ sessionDir, templateFile });
 *   await editor.edit({ outputFile, sourceVideo });
 */

import fs from 'fs';
import path from 'path';
import { VideoEditor } from './video-editor.js';

export class VideoStoryEditor {
  constructor(options = {}) {
    this.sessionDir = options.sessionDir;
    this.templateFile = options.templateFile;
    this.template = null;
    this.events = [];
    this.sessionMeta = null;
  }

  async load() {
    // Load template
    if (!fs.existsSync(this.templateFile)) {
      throw new Error(`Template not found: ${this.templateFile}`);
    }
    this.template = JSON.parse(fs.readFileSync(this.templateFile, 'utf8'));

    // Load session metadata
    const metaPath = path.join(this.sessionDir, 'meta.json');
    if (fs.existsSync(metaPath)) {
      this.sessionMeta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    }

    // Load events
    const eventFile = path.join(this.sessionDir, 'events.jsonl');
    if (fs.existsSync(eventFile)) {
      const lines = fs.readFileSync(eventFile, 'utf8').split('\n').filter(Boolean);
      this.events = lines.map((l) => {
        try { return JSON.parse(l); } catch { return null; }
      }).filter(Boolean);
    }

    return this;
  }

  /**
   * Map each template segment to a real timestamp in the video.
   * Uses event matching first, falls back to estimated positions.
   */
  mapSegmentsToTimestamps() {
    const sessionStartMs = this.sessionMeta?.startedAt || Date.now();
    const sessionDurationSec = this.sessionMeta?.durationSec || 2400; // default 40min
    const segments = this.template.segments;

    const mapped = [];
    let fallbackCursor = 30; // start 30s in

    for (const seg of segments) {
      const detect = seg.detect_by;
      let foundTs = null;

      // Try to find matching events
      if (detect && this.events.length > 0) {
        const candidates = this.events.filter((e) => {
          // Match event type
          if (detect.event_types && !detect.event_types.includes(e.type)) return false;
          // Match keywords in message/note
          const text = `${e.message || ''} ${e.note || ''} ${e.from || ''}`.toLowerCase();
          if (detect.keywords) {
            return detect.keywords.some((kw) => text.includes(kw.toLowerCase()));
          }
          return true;
        });

        if (candidates.length > 0) {
          // Use the first matching event timestamp
          const ev = candidates[0];
          let relSec = 0;
          if (ev.time && ev.time > 1000000000000) {
            relSec = (ev.time - sessionStartMs) / 1000;
          } else if (ev.relTs) {
            relSec = ev.relTs;
          } else if (ev.ts) {
            relSec = typeof ev.ts === 'number' && ev.ts > 1000000000000
              ? (ev.ts - sessionStartMs) / 1000
              : ev.ts;
          }
          if (relSec > 0 && relSec < sessionDurationSec) {
            foundTs = relSec;
          }
        }
      }

      // Fallback strategies
      if (foundTs == null) {
        if (detect?.fallback_seconds_from_start != null) {
          foundTs = detect.fallback_seconds_from_start;
        } else if (detect?.fallback_seconds_after_prev != null && mapped.length > 0) {
          foundTs = mapped[mapped.length - 1].start + detect.fallback_seconds_after_prev;
        } else {
          foundTs = fallbackCursor;
        }
      }

      // Clamp
      const maxStart = sessionDurationSec - seg.target_duration_sec;
      if (foundTs > maxStart) foundTs = Math.max(0, maxStart);
      if (foundTs < 0) foundTs = 0;

      // Calculate end (with a little buffer to pick best part)
      const searchWindow = seg.target_duration_sec + 8;
      let endTs = foundTs + searchWindow;
      if (endTs > sessionDurationSec) endTs = sessionDurationSec;

      mapped.push({
        ...seg,
        start: foundTs,
        end: endTs,
        searchWindow,
      });

      fallbackCursor = endTs + 10;
    }

    return mapped;
  }

  /**
   * Score sub-intervals within each segment's window to find the best clip.
   * Uses event density to pick the most interesting N seconds.
   */
  scoreSubIntervals(mappedSegments) {
    const highlights = [];

    for (const seg of mappedSegments) {
      const targetDur = seg.target_duration_sec;
      const windowEvents = this.events.filter((e) => {
        let relSec = 0;
        if (e.time && e.time > 1000000000000) {
          const startMs = this.sessionMeta?.startedAt || Date.now();
          relSec = (e.time - startMs) / 1000;
        } else if (e.relTs != null) {
          relSec = e.relTs;
        } else if (e.ts != null) {
          relSec = e.ts;
        }
        return relSec >= seg.start && relSec <= seg.end;
      });

      // Divide window into 3-second slots and score them
      const slotSize = 3;
      const numSlots = Math.floor((seg.end - seg.start) / slotSize);
      let bestSlotStart = seg.start;
      let bestScore = -1;

      for (let i = 0; i <= numSlots - Math.ceil(targetDur / slotSize); i++) {
        const slotStart = seg.start + i * slotSize;
        const slotEnd = slotStart + targetDur;
        const slotEvents = windowEvents.filter((e) => {
          let relSec = 0;
          if (e.time && e.time > 1000000000000) {
            const startMs = this.sessionMeta?.startedAt || Date.now();
            relSec = (e.time - startMs) / 1000;
          } else if (e.relTs != null) {
            relSec = e.relTs;
          } else if (e.ts != null) {
            relSec = e.ts;
          }
          return relSec >= slotStart && relSec <= slotEnd;
        });

        let score = 0;
        score += slotEvents.filter((e) => e.type === 'chat').length * 2;
        score += slotEvents.filter((e) => e.type === 'quest').length * 6;
        score += slotEvents.filter((e) => e.type === 'combat').length * 5;
        score += slotEvents.filter((e) => e.type === 'danger').length * 4;
        score += slotEvents.filter((e) => e.type === 'action').length * 1.5;

        // Bonus for keywords
        const keywords = seg.detect_by?.keywords || [];
        slotEvents.forEach((ev) => {
          const text = `${ev.message || ''} ${ev.note || ''}`.toLowerCase();
          keywords.forEach((kw) => {
            if (text.includes(kw.toLowerCase())) score += 5;
          });
        });

        if (score > bestScore) {
          bestScore = score;
          bestSlotStart = slotStart;
        }
      }

      // If no events scored, just take the middle of the window
      if (bestScore <= 0 && (seg.end - seg.start) > targetDur) {
        bestSlotStart = seg.start + (seg.end - seg.start - targetDur) / 2;
      }

      const finalEnd = Math.min(bestSlotStart + targetDur, seg.end);

      highlights.push({
        index: seg.id,
        start: Math.round(bestSlotStart * 10) / 10,
        end: Math.round(finalEnd * 10) / 10,
        duration: Math.round((finalEnd - bestSlotStart) * 10) / 10,
        score: bestScore,
        description: `${seg.video_label} | ${seg.description}`,
        events: windowEvents.slice(0, 3).map((e) => ({
          type: e.type,
          from: e.from,
          message: e.message?.slice(0, 80),
        })),
        editing: seg.editing,
      });
    }

    return highlights;
  }

  /**
   * Main entry point: load, map, score, edit.
   */
  async edit({ sourceVideo, outputFile, musicFile }) {
    await this.load();

    const mapped = this.mapSegmentsToTimestamps();
    const highlights = this.scoreSubIntervals(mapped);

    // Save narrative highlights
    const highlightsFile = path.join(this.sessionDir, 'highlights-narrative.json');
    fs.writeFileSync(highlightsFile, JSON.stringify(highlights, null, 2));

    // Use VideoEditor to produce final output
    const editor = new VideoEditor({
      ffmpegPath: 'ffmpeg',
      ffprobePath: 'ffprobe',
      sessionDir: this.sessionDir,
      outputDir: path.dirname(outputFile),
    });

    const global = this.template.global_settings || {};
    const titleCard = this.template.title_card
      ? `${this.template.title_card.text}\n${this.template.title_card.subtitle || ''}`
      : null;

    await editor.createHighlightReel({
      sourceVideo,
      highlights,
      targetDurationMinutes: Math.ceil((this.template.target_duration_seconds || 120) / 60),
      outputFile,
      addTransitions: global.add_transitions !== false,
      addMusic: Boolean(musicFile),
      musicFile,
      titleCard,
    });

    // If end card requested, append a black hold with text (simplified: just note it)
    if (this.template.end_card) {
      console.log(`[StoryEditor] End card requested: "${this.template.end_card.text}"`);
      // In a full implementation, we'd render the end card with FFmpeg drawtext + black frame
    }

    return {
      ok: true,
      outputFile,
      highlights,
      template: this.template.template_id,
    };
  }
}

/**
 * CLI helper: run narrative edit from command line
 * Usage: node video-story-editor.js <sessionDir> <templateFile> [outputFile] [musicFile]
 */
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const sessionDir = process.argv[2];
  const templateFile = process.argv[3];
  const outputFile = process.argv[4] || path.join(sessionDir, 'output-narrative.mp4');
  const musicFile = process.argv[5] || null;

  if (!sessionDir || !templateFile) {
    console.error('Usage: node video-story-editor.js <sessionDir> <templateFile> [outputFile] [musicFile]');
    process.exit(1);
  }

  const metaPath = path.join(sessionDir, 'meta.json');
  if (!fs.existsSync(metaPath)) {
    console.error('Session metadata not found');
    process.exit(1);
  }
  const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
  const sourceVideo = path.join(sessionDir, meta.videoFile);

  const storyEditor = new VideoStoryEditor({ sessionDir, templateFile });
  storyEditor.edit({ sourceVideo, outputFile, musicFile })
    .then((result) => {
      console.log('Narrative edit complete:', result.outputFile);
      process.exit(0);
    })
    .catch((err) => {
      console.error('Narrative edit failed:', err.message);
      process.exit(1);
    });
}
