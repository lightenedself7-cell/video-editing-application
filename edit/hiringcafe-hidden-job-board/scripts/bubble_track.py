import subprocess, numpy as np, json, sys
from multiprocessing import Pool
sys.path.insert(0, 'scripts')
from bubble_lib import candidate
SRC = "/home/dev/videos/hiringcafe-hidden-job-board.mp4"
SCREENS = [(88.8, 176.13), (204.27, 508.63), (515.77, 582.23)]
FPS = 2
def work(a):
    t0, t1 = a
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(t1 - t0), "-i", SRC, "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 720, 1280, 3)
    return [(round(t0 + i / FPS, 2), candidate(f)) for i, f in enumerate(fr)]
if __name__ == "__main__":
    chunks = []
    for a, b in SCREENS:
        t = a
        while t < b: chunks.append((t, min(t + 20, b))); t += 20
    with Pool(8) as p: res = [x for r in p.map(work, chunks) for x in r]
    json.dump(res, open("reports/bubble_raw.json", "w"))
    print(len(res), "samples;", sum(1 for _, c in res if c is None), "none;", sum(1 for _, c in res if c and c[3] < 0.5), "weak")
    runs = []
    for t, c in res:
        key = None if c is None or c[3] < 0.5 else c
        if runs and runs[-1]["c"] is not None and key is not None and max(abs(key[k] - runs[-1]["c"][k]) for k in range(3)) <= 8 and t - runs[-1]["end"] < 1.1:
            runs[-1]["end"] = t + 1 / FPS; runs[-1]["n"] += 1
        elif runs and key is None and runs[-1]["c"] is None and t - runs[-1]["end"] < 1.1:
            runs[-1]["end"] = t + 1 / FPS; runs[-1]["n"] += 1
        else: runs.append({"start": t, "end": t + 1 / FPS, "n": 1, "c": key})
    for r in runs:
        if r["n"] >= 3: print(f'{r["start"]:7.1f}-{r["end"]:7.1f} n={r["n"]:3d} {r["c"]}')
