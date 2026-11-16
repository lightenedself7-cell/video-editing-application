import { describe, expect, it } from 'vitest';
import { parseLoudnorm, preparedPromptNote } from '../src/server/prepare.js';

const stderr = `ffmpeg version 6
[Parsed_loudnorm_0 @ 0x1]
{
\t"input_i" : "-20.31",
\t"input_tp" : "-3.02",
\t"input_lra" : "5.10",
\t"input_thresh" : "-30.70",
\t"output_i" : "-24.00"
}
`;

describe('prepare', () => {
  it('reads loudnorm JSON from ffmpeg stderr', () => {
    expect(parseLoudnorm(stderr)).toEqual({ integratedLUFS: '-20.31', truePeakDBTP: '-3.02', loudnessRange: '5.10', threshold: '-30.70' });
  });

  it('returns undefined when ffmpeg printed no JSON', () => {
    expect(parseLoudnorm('Error opening input')).toBeUndefined();
  });

  it('tells the agent what is pre-computed and what to do itself', () => {
    const note = preparedPromptNote({ dir: '/p/prepared', manifest: '/p/prepared/prepared.json', sections: [
      { index: 1, path: '/a.mp4', kind: 'camera', loudness: { integratedLUFS: '-20.31', truePeakDBTP: '-3.02' }, transcript: '/p/prepared/transcripts/section-1.json', notes: [] },
      { index: 2, path: '/b.wav', kind: 'voiceover', notes: ['loudness not measured; measure it yourself'] },
    ] });
    expect(note).toContain('section-1.json');
    expect(note).toContain('-20.31 LUFS');
    expect(note).toContain('2. no transcript');
  });
});
