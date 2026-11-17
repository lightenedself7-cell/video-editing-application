"""Per-beat overlay delta inside the protected region, measured like the renderer (composite vs decoded source, no re-encode)."""
import json, sys
import numpy as np
R = "/home/dev/video-editing-application"
sys.path.insert(0, f"{R}/skills/theme-renderer")
from renderer import engine
P = f"{R}/edit/automated-job-search-spreadsheet-demo"
d = json.load(open(f"{P}/editorial-directive.json"))
ctx = engine.Context(d, P)
pr = d["protected_regions"][0]
x0, y0, x1, y1 = pr["x"], pr["y"], pr["x"] + pr["width"], pr["y"] + pr["height"]
for b in d["beats"]:
    if b["treatment"] != "OVERLAY_CARD":
        continue
    worst, wn = 0.0, 0
    for n in range(int(b["start"] * 30), int(b["end"] * 30), 3):
        dec = engine._decode(ctx, n, n + 1)
        S = np.frombuffer(dec.stdout.read(1280 * 720 * 3), np.uint8).reshape(720, 1280, 3).astype(np.float32)
        dec.stdout.close(); dec.wait()
        out, _ = engine.render_frame(ctx, n, S)
        v = float(np.abs(out - S)[y0:y1, x0:x1].max())
        if v > worst:
            worst, wn = v, n
    print(f'{b["id"]} {b["component"]:16s} max {worst:5.1f} at frame {wn} ({wn/30:.2f}s)', flush=True)
