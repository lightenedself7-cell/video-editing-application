"""Per-beat max change inside the protected region (camera overlay beats), sampled every 0.25 s."""
import json, subprocess, sys
import numpy as np
P = "/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo"
d = json.load(open(f"{P}/editorial-directive.json"))
src, mst = d["source"]["path"], f"{P}/automated-job-search-spreadsheet-demo-master.mp4"
pr = d["protected_regions"][0]
x0, y0, x1, y1 = pr["x"], pr["y"], pr["x"] + pr["width"], pr["y"] + pr["height"]


def frame(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(720, 1280, 3).astype(np.float32)


for b in d["beats"]:
    if b["treatment"] != "OVERLAY_CARD":
        continue
    worst, wt = 0.0, 0.0
    t = b["start"]
    while t < b["end"]:
        a, m = frame(src, t), frame(mst, t)
        v = float(np.abs(a - m)[y0:y1, x0:x1].max())
        if v > worst:
            worst, wt = v, t
        t += 0.25
    print(f'{b["id"]} {b["component"]:16s} {b["start"]:7.2f}-{b["end"]:7.2f} max {worst:5.1f} at {wt:.2f}  layout={b.get("layout")}')
