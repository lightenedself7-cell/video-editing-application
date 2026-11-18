"""Classify every frame as camera (pink wall) or screen (white UI); find presenter-bubble corner on screens.
Writes reports/shots.json with runs and reports/frames_class.json."""
import json, subprocess, numpy as np
SRC = "/home/dev/videos/hiringcafe-hidden-job-board.mp4"
W, H = 320, 180; FS = W * H * 3
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
cls = []; n = 0
while True:
    b = p.stdout.read(FS)
    if len(b) < FS: break
    f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
    # camera: magenta/pink wall dominates the top-left and top-right strips
    strip = np.concatenate([f[10:120, 0:50].reshape(-1, 3), f[10:120, 270:320].reshape(-1, 3)])
    r, g, bl = strip[:, 0].mean(), strip[:, 1].mean(), strip[:, 2].mean()
    pink = (r - g) > 40 and (bl - g) > 20
    white_frac = float(((f[20:160, 60:260] > 225).all(-1)).mean())
    # bubble corners: skin-ish/darker blob in bottom corners while the rest is white UI
    bl_c = f[120:180, 0:60]; br_c = f[110:180, 255:320]
    def blobby(c): return float((c.mean(-1) < 170).mean())
    cls.append([n, "camera" if pink and white_frac < 0.25 else "screen", round(white_frac, 3), round(blobby(bl_c), 3), round(blobby(br_c), 3)])
    n += 1
json.dump(cls, open("reports/frames_class.json", "w"))
runs = []
for k, c, *_ in cls:
    if runs and runs[-1][2] == c and k == runs[-1][1]: runs[-1][1] = k + 1
    else: runs.append([k, k + 1, c])
# merge flicker shorter than 6 frames
merged = []
for a, b, c in runs:
    if merged and (b - a < 6 or merged[-1][2] == c):
        merged[-1][1] = b
    else: merged.append([a, b, c])
for r in merged:
    seg = [x for x in cls if r[0] <= x[0] < r[1]]
    r.append(round(float(np.mean([x[3] for x in seg])), 2)); r.append(round(float(np.mean([x[4] for x in seg])), 2))
json.dump(merged, open("reports/shots.json", "w"), indent=0)
for a, b, c, l, rr in merged:
    print(f"{a/30:7.2f}-{b/30:7.2f}s  {c:6s}  dark-BL {l:.2f}  dark-BR {rr:.2f}")
print("frames", n)
