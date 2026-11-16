import { mkdir, mkdtemp, realpath, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { renderIneligibleReason } from '../src/server/renderHandoff';

async function setup(directive: unknown, withRegistry = true): Promise<{ projectDir: string; skillsDir: string }> {
  const root = await realpath(await mkdtemp(join(tmpdir(), 'handoff-')));
  const projectDir = join(root, 'project');
  const skillsDir = join(root, 'skills');
  await mkdir(projectDir, { recursive: true });
  await mkdir(join(skillsDir, 'theme-renderer', 'themes', 'teal-spotlight'), { recursive: true });
  if (withRegistry) await writeFile(join(skillsDir, 'theme-renderer', 'themes', 'teal-spotlight', 'registry.json'), '{}');
  if (directive !== undefined) await writeFile(join(projectDir, 'editorial-directive.json'), JSON.stringify(directive));
  return { projectDir, skillsDir };
}

const base = () => ({
  theme: 'teal-spotlight', approval: { status: 'approved' }, source: { width: 1280, height: 720 },
  beats: [{ id: 'b1', treatment: 'OVERLAY_CARD', component: 'lower-third-tag' }, { id: 'b2', treatment: 'CLEAN_PRESENTER' }],
});

describe('render handoff eligibility', () => {
  it('accepts an approved component-only plan', async () => {
    const { projectDir, skillsDir } = await setup(base());
    expect(await renderIneligibleReason(projectDir, skillsDir)).toBeNull();
  });
  it('refuses plans the app renderer cannot draw', async () => {
    const cases: [string, (d: ReturnType<typeof base>) => void, RegExp][] = [
      ['hand-built beat', (d) => { Object.assign(d.beats[0], { component: undefined, custom_graphics: 'needs a map' }); }, /custom_graphics/],
      ['beat with nothing to draw', (d) => { delete (d.beats[0] as { component?: string }).component; }, /no component/],
      ['unapproved plan', (d) => { d.approval.status = 'pending'; }, /not approved/],
      ['different delivery size', (d) => { Object.assign(d, { delivery: { width: 3840, height: 2160 } }); }, /delivery size/],
      ['audio-only section', (d) => { Object.assign(d, { segments: [{ kind: 'voiceover' }] }); }, /Audio-only/],
    ];
    for (const [name, change, pattern] of cases) {
      const directive = base();
      change(directive);
      const { projectDir, skillsDir } = await setup(directive);
      expect(await renderIneligibleReason(projectDir, skillsDir), name).toMatch(pattern);
    }
  });
  it('refuses a theme without a registry and a missing directive', async () => {
    const noRegistry = await setup(base(), false);
    expect(await renderIneligibleReason(noRegistry.projectDir, noRegistry.skillsDir)).toMatch(/no component registry/);
    const missing = await setup(undefined);
    expect(await renderIneligibleReason(missing.projectDir, missing.skillsDir)).toMatch(/missing/);
  });
});
