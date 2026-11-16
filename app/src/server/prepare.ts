import { appendFile, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import type { JobSettings } from '../shared/types.js';
import { runCommand } from './process.js';

// Mechanical work done by the app before the agent starts, so the model spends its
// tokens on editorial decisions instead of probing, measuring and transcribing.
// Everything here is best-effort: a failure is recorded and the agent does that step itself.

const WHISPER = `
import json, sys, os
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
model = WhisperModel(os.environ.get("VIDEO_WHISPER_MODEL", "small"), device="auto", compute_type="auto")
segments, info = model.transcribe(src, word_timestamps=True, vad_filter=True)
words, phrases = [], []
for s in segments:
    phrases.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    for w in s.words or []:
        words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
json.dump({"language": info.language, "duration": round(info.duration, 2), "words": words, "phrases": phrases}, open(out, "w"), ensure_ascii=False)
`;

export interface PreparedSection { index: number; path: string; kind: string; loudness?: Record<string, string>; transcript?: string; notes: string[] }
export interface Prepared { sections: PreparedSection[]; dir: string; manifest: string }

async function progress(projectDir: string, phase: string, percent: number, message: string, skipped = false): Promise<void> {
  const line = { t: new Date().toISOString(), phase, percent, message, ...(skipped ? { skipped: true } : {}) };
  await appendFile(join(projectDir, 'ui-progress.jsonl'), `${JSON.stringify(line)}\n`).catch(() => undefined);
}

export function parseLoudnorm(stderr: string): Record<string, string> | undefined {
  const start = stderr.lastIndexOf('{');
  const end = stderr.lastIndexOf('}');
  if (start < 0 || end < start) return undefined;
  try {
    const value = JSON.parse(stderr.slice(start, end + 1)) as Record<string, unknown>;
    const pick = (key: string): string | undefined => typeof value[key] === 'string' ? value[key] as string : undefined;
    const result: Record<string, string> = {};
    for (const [from, to] of [['input_i', 'integratedLUFS'], ['input_tp', 'truePeakDBTP'], ['input_lra', 'loudnessRange'], ['input_thresh', 'threshold']] as const) {
      const v = pick(from);
      if (v !== undefined) result[to] = v;
    }
    return Object.keys(result).length ? result : undefined;
  } catch { return undefined; }
}

export async function prepareJob(settings: JobSettings, projectDir: string, python: string, workspace: string, isCancelled: () => boolean): Promise<Prepared> {
  const dir = join(projectDir, 'prepared');
  await mkdir(join(dir, 'transcripts'), { recursive: true });
  const sections: PreparedSection[] = [];
  const transcribe = !settings.allowRemoteUpload;
  const total = settings.sections.length;
  for (const [i, section] of settings.sections.entries()) {
    if (isCancelled()) break;
    const entry: PreparedSection = { index: i + 1, path: section.path, kind: section.kind, notes: [] };
    await progress(projectDir, 'intake', Math.round(i / total * 100), `Measuring loudness, section ${i + 1}/${total}`);
    const loud = await runCommand('ffmpeg', ['-hide_banner', '-nostdin', '-i', section.path, '-vn', '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], { cwd: workspace, timeoutMs: 15 * 60_000 });
    entry.loudness = loud.code === 0 ? parseLoudnorm(loud.stderr) : undefined;
    if (!entry.loudness) entry.notes.push('loudness not measured; measure it yourself');
    sections.push(entry);
  }
  if (transcribe) {
    for (const [i, entry] of sections.entries()) {
      if (isCancelled()) break;
      await progress(projectDir, 'transcribe', Math.round(i / total * 100), `Transcribing locally, section ${i + 1}/${total}`);
      const out = join(dir, 'transcripts', `section-${entry.index}.json`);
      const result = await runCommand(python, ['-c', WHISPER, entry.path, out], { cwd: workspace, timeoutMs: 60 * 60_000, maxOutput: 64 * 1024 });
      if (result.code === 0) entry.transcript = out;
      else entry.notes.push(`local transcription failed (${result.stderr.trim().split('\n').pop()?.slice(0, 160) ?? 'unknown error'}); transcribe it yourself`);
    }
    if (sections.length && sections.every((s) => s.transcript)) await progress(projectDir, 'transcribe', 100, 'Transcripts ready');
  }
  const manifest = join(dir, 'prepared.json');
  await writeFile(manifest, `${JSON.stringify({ createdAt: new Date().toISOString(), whisperModel: process.env.VIDEO_WHISPER_MODEL ?? 'small', sections }, null, 2)}\n`);
  return { sections, dir, manifest };
}

export function preparedPromptNote(prepared: Prepared): string {
  const lines = prepared.sections.map((s) => `  ${s.index}. ${s.transcript ? `transcript ${s.transcript}` : 'no transcript'}${s.loudness ? `; integrated ${s.loudness.integratedLUFS} LUFS, true peak ${s.loudness.truePeakDBTP} dBTP` : ''}`);
  return `\nPre-computed by the app before you started (read ${prepared.manifest}; reuse these, do not redo them):
${lines.join('\n')}
Transcript files hold {"words":[{"w","start","end"}],"phrases":[{"start","end","text"}]} from local faster-whisper, with word-level timestamps in seconds. Use them in place of your own transcription step. If a section lists a note, or a transcript looks wrong, do that one step yourself. Skip re-measuring loudness for sections that report a value.`;
}
