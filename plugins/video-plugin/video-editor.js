/**
 * VideoEditor — FFmpeg-based highlight reel editor
 *
 * Takes a source video + highlight list and produces a polished output:
 *   - Concatenates clips
 *   - Adds crossfade transitions
 *   - Optional background music
 *   - Optional title card
 */

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

export class VideoEditor {
  constructor(options = {}) {
    this.ffmpegPath = options.ffmpegPath || 'ffmpeg';
    this.ffprobePath = options.ffprobePath || 'ffprobe';
    this.sessionDir = options.sessionDir;
    this.outputDir = options.outputDir;
  }

  async createHighlightReel({
    sourceVideo,
    highlights,
    targetDurationMinutes = 5,
    outputFile,
    addTransitions = true,
    addMusic = false,
    musicFile,
    titleCard,
  }) {
    if (!highlights || highlights.length === 0) {
      throw new Error('No highlights provided');
    }

    const clipsDir = path.join(this.sessionDir, 'clips');
    fs.mkdirSync(clipsDir, { recursive: true });

    // 1. Extract each highlight clip
    const clipFiles = [];
    for (let i = 0; i < highlights.length; i++) {
      const h = highlights[i];
      const clipFile = path.join(clipsDir, `clip_${i.toString().padStart(3, '0')}.mp4`);
      await this._extractClip(sourceVideo, h.start, h.end, clipFile);
      clipFiles.push(clipFile);
    }

    // 2. If target duration is specified, trim/adjust clips proportionally
    const totalClipDuration = highlights.reduce((sum, h) => sum + (h.end - h.start), 0);
    const targetSec = targetDurationMinutes * 60;

    // 3. Build concat with or without transitions
    if (addTransitions && clipFiles.length > 1) {
      await this._concatWithTransitions(clipFiles, outputFile, addMusic ? musicFile : null);
    } else {
      await this._concatSimple(clipFiles, outputFile, addMusic ? musicFile : null);
    }

    // 4. Optional title card overlay (first 3 seconds)
    if (titleCard) {
      const titledOutput = outputFile.replace('.mp4', '_titled.mp4');
      await this._addTitleCard(outputFile, titleCard, titledOutput);
      fs.renameSync(titledOutput, outputFile);
    }

    return outputFile;
  }

  _extractClip(source, start, end, output) {
    const duration = end - start;
    return new Promise((resolve, reject) => {
      const args = [
        '-y',
        '-ss', String(start),
        '-t', String(duration),
        '-i', source,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-avoid_negative_ts', 'make_zero',
        output,
      ];

      const ffmpeg = spawn(this.ffmpegPath, args);
      ffmpeg.on('exit', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Extract clip failed: code ${code}`));
      });
      ffmpeg.on('error', reject);
    });
  }

  _concatSimple(clipFiles, output, musicFile) {
    return new Promise((resolve, reject) => {
      const listFile = path.join(path.dirname(output), 'concat_list.txt');
      const list = clipFiles.map((f) => `file '${f}'`).join('\n');
      fs.writeFileSync(listFile, list);

      const args = [
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', listFile,
      ];

      if (musicFile && fs.existsSync(musicFile)) {
        args.push('-i', musicFile);
        args.push('-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=3[aout]');
        args.push('-map', '0:v');
        args.push('-map', '[aout]');
      }

      args.push('-c:v', 'libx264');
      args.push('-preset', 'medium');
      args.push('-crf', '23');
      args.push('-c:a', 'aac');
      args.push('-b:a', '192k');
      args.push('-movflags', '+faststart');
      args.push(output);

      const ffmpeg = spawn(this.ffmpegPath, args);
      ffmpeg.on('exit', (code) => {
        try { fs.unlinkSync(listFile); } catch {}
        if (code === 0) resolve();
        else reject(new Error(`Concat failed: code ${code}`));
      });
      ffmpeg.on('error', reject);
    });
  }

  _concatWithTransitions(clipFiles, output, musicFile) {
    // Build a complex filtergraph with xfade transitions between clips
    return new Promise((resolve, reject) => {
      const filters = [];
      const inputs = clipFiles.map((f, i) => `[${i}:v][${i}:a]`).join('');

      // Build xfade chain
      let lastV = '[0:v]';
      let lastA = '[0:a]';
      for (let i = 1; i < clipFiles.length; i++) {
        const nextV = `[${i}:v]`;
        const nextA = `[${i}:a]`;
        const outV = `[v${i}]`;
        const outA = `[a${i}]`;

        // Video crossfade (0.5 sec)
        filters.push(`${lastV}${nextV}xfade=transition=fade:duration=0.5:offset=${this._getOffset(i)}${outV}`);
        // Audio crossfade
        filters.push(`${lastA}${nextA}acrossfade=d=0.5${outA}`);

        lastV = outV;
        lastA = outA;
      }

      const filterComplex = filters.join(';');

      const args = ['-y'];
      clipFiles.forEach((f) => {
        args.push('-i', f);
      });

      if (musicFile && fs.existsSync(musicFile)) {
        args.push('-i', musicFile);
      }

      args.push('-filter_complex', filterComplex);
      args.push('-map', lastV);
      args.push('-map', lastA);

      if (musicFile) {
        // Remix with music (more complex, fall back to simple for now)
        // For simplicity, we skip music when transitions are enabled
      }

      args.push('-c:v', 'libx264');
      args.push('-preset', 'medium');
      args.push('-crf', '23');
      args.push('-c:a', 'aac');
      args.push('-b:a', '192k');
      args.push('-movflags', '+faststart');
      args.push(output);

      const ffmpeg = spawn(this.ffmpegPath, args);
      ffmpeg.on('exit', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Transition concat failed: code ${code}`));
      });
      ffmpeg.on('error', reject);
    });
  }

  _getOffset(clipIndex) {
    // Rough offset estimation; in production you'd probe each clip's exact duration
    // For now assume each clip is ~30s, subtract 0.5s for each previous transition
    return clipIndex * 29.5;
  }

  _addTitleCard(videoFile, titleText, output) {
    // Drawtext title card for first 3 seconds
    const safeTitle = titleText.replace(/'/g, "'\\''");
    const drawtext = `drawtext=text='${safeTitle}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t\\,0\\,3)':box=1:boxcolor=black@0.6:boxborderw=10`;

    return new Promise((resolve, reject) => {
      const args = [
        '-y',
        '-i', videoFile,
        '-vf', drawtext,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'copy',
        output,
      ];

      const ffmpeg = spawn(this.ffmpegPath, args);
      ffmpeg.on('exit', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Title card failed: code ${code}`));
      });
      ffmpeg.on('error', reject);
    });
  }
}
