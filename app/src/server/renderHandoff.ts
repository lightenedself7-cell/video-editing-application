import { readFile, stat } from 'node:fs/promises';
import { join } from 'node:path';

/**
 * The app renders a job itself (no agent) when the agent says `render-by-app` and the directive uses only
 * theme components. Returns why it cannot, or null when it can.
 */
export async function renderIneligibleReason(projectDir: string, skillsDir: string): Promise<string | null> {
  let directive: Record<string, unknown>;
  try { directive = JSON.parse(await readFile(join(projectDir, 'editorial-directive.json'), 'utf8')) as Record<string, unknown>; }
  catch { return 'editorial-directive.json is missing or is not valid JSON.'; }
  const theme = directive.theme;
  if (typeof theme !== 'string' || !(await stat(join(skillsDir, 'theme-renderer', 'themes', theme, 'registry.json')).catch(() => null))) {
    return `Theme ${String(theme)} has no component registry, so the app cannot render it.`;
  }
  const approval = directive.approval as { status?: unknown } | undefined;
  if (approval?.status !== 'approved') return 'The plan is not approved yet.';
  const source = directive.source as { width?: unknown; height?: unknown } | undefined;
  const delivery = directive.delivery as { width?: unknown; height?: unknown } | undefined;
  if (delivery && (delivery.width !== source?.width || delivery.height !== source?.height)) return 'The delivery size differs from the source size, which the app renderer does not support yet.';
  const segments = directive.segments;
  if (Array.isArray(segments) && segments.some((segment) => (segment as { kind?: unknown })?.kind === 'voiceover')) return 'Audio-only sections need hand-built graphics.';
  const beats = Array.isArray(directive.beats) ? directive.beats as Record<string, unknown>[] : [];
  for (const beat of beats) {
    const id = String(beat.id ?? '?');
    if (beat.custom_graphics !== undefined) return `Beat ${id} needs hand-built graphics (custom_graphics).`;
    if (beat.treatment !== 'CLEAN_PRESENTER' && beat.component === undefined) return `Beat ${id} (${String(beat.treatment)}) has no component, so nothing would be drawn.`;
  }
  return null;
}
