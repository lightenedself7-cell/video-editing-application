import json, subprocess, sys, numpy as np
from multiprocessing import Pool
sys.path.insert(0, 'scripts')
from bubble_lib import rim_score
SRC = "/home/dev/videos/hiringcafe-hidden-job-board.mp4"
raw = json.load(open('reports/bubble_raw.json'))
# greedy clustering in time order
segs = []
for t, c in raw:
    if c is None or c[3] < 0.55: continue
    if segs:
        s = segs[-1]; m = np.median(np.array(s['c'])[:, :3], 0)
        if abs(c[0] - m[0]) < 18 and abs(c[1] - m[1]) < 18 and abs(c[2] - m[2]) < 9 and t - s['t'][-1] < 6:
            s['c'].append(c); s['t'].append(t); continue
    segs.append({'c': [c], 't': [t]})
segs = [s for s in segs if len(s['c']) >= 4]
# merge neighbours whose medians agree
merged = []
for s in segs:
    m = np.median(np.array(s['c'])[:, :3], 0)
    if merged:
        pm = np.median(np.array(merged[-1]['c'])[:, :3], 0)
        if abs(m[0] - pm[0]) < 14 and abs(m[1] - pm[1]) < 14 and abs(m[2] - pm[2]) < 6:
            merged[-1]['c'] += s['c']; merged[-1]['t'] += s['t']; continue
    merged.append(s)
out = []
for s in merged:
    m = np.median(np.array(s['c'])[:, :3], 0)
    out.append({'start': s['t'][0], 'end': s['t'][-1], 'n': len(s['c']), 'circle': [round(float(x), 1) for x in m]})
json.dump(out, open('reports/bubble_layouts.json', 'w'), indent=1)
for o in out: print(o)
