"""Verification for the composited master. Writes reports/checks.json and contact sheets."""
import json, subprocess, hashlib, glob, os, sys, re
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SRC = "/home/dev/videos/budget-free-website-startup-guide-clean.mp4"
MASTER = "budget-free-website-startup-guide-clean-master.mp4"
D = json.load(open("editorial-directive.json"))
FPS = 30
checks = {"master": MASTER, "source": SRC}
def sh(cmd): return subprocess.run(cmd, capture_output=True, text=True)
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def probe(p):
    j = json.loads(sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", p]).stdout)
    v = [s for s in j["streams"] if s["codec_type"] == "video"][0]; a = [s for s in j["streams"] if s["codec_type"] == "audio"][0]
    return {"width": v["width"], "height": v["height"], "r_frame_rate": v["r_frame_rate"], "nb_frames": int(v.get("nb_frames", 0)),
            "pix_fmt": v["pix_fmt"], "v_codec": v["codec_name"], "a_codec": a["codec_name"], "sample_rate": a["sample_rate"],
            "channels": a["channels"], "duration": float(j["format"]["duration"]), "v_duration": float(v["duration"]), "a_duration": float(a["duration"])}
ps, pm = probe(SRC), probe(MASTER)
checks["probe"] = {"source": ps, "master": pm}
checks["probe_match"] = all(ps[k] == pm[k] for k in ("width", "height", "r_frame_rate", "nb_frames", "a_codec", "sample_rate", "channels")) and abs(ps["duration"] - pm["duration"]) < 0.05

# full decode
r = sh(["ffmpeg", "-v", "error", "-i", MASTER, "-f", "null", "-"])
checks["full_decode"] = {"ok": r.returncode == 0 and not r.stderr.strip(), "stderr": r.stderr.strip()[:500]}

# audio identity (stream copy)
def amd5(p): return sh(["ffmpeg", "-v", "error", "-i", p, "-map", "0:a", "-c", "copy", "-f", "md5", "-"]).stdout.strip()
checks["audio_packets_identical"] = amd5(SRC) == amd5(MASTER)

# loudness
def loud(p):
    e = sh(["ffmpeg", "-nostats", "-i", p, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    s = e[e.rfind("Summary:"):]
    g = lambda k: float(re.search(k + r":\s+(-?[\d.]+)", s).group(1))
    return {"integrated_lufs": g("I"), "lra_lu": g("LRA"), "true_peak_dbfs": g("Peak")}
checks["loudness"] = {"source": loud(SRC), "master": loud(MASTER)}

# frame comparisons
def frame(p, n):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{n / FPS:.4f}", "-i", p, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(720, 1280, 3)
def psnr(a, b):
    m = np.mean((a.astype(float) - b.astype(float)) ** 2); return 99.0 if m == 0 else 10 * np.log10(255 ** 2 / m)
beats = {b["id"]: b for b in D["beats"]}
ident = []
cases = [("clean hook", 60), ("clean CTA", 21600), ("final frame", 21880)]
for bid in ("b09", "b24", "b48"):
    b = beats[bid]
    cases.append((f"{bid} inset move first frame", int(np.ceil(b["start"] * FPS))))
    cases.append((f"{bid} inset return last frame", int(np.ceil(b["end"] * FPS))))
for name, n in cases:
    ident.append({"check": name, "frame": n, "psnr_db_vs_source": round(psnr(frame(SRC, n), frame(MASTER, n)), 2)})
checks["source_identity_frames"] = ident
checks["source_identity_ok"] = all(c["psnr_db_vs_source"] >= 40 for c in ident)

# safe region (logged by the compositor on every overlay frame over camera)
safe = [json.load(open(f)) for f in sorted(glob.glob("render/chunks/*.safe.json"))]
checks["safe_region"] = {"protected_region": D["protected_regions"][0], "frames_checked": sum(s["frames_checked"] for s in safe),
                         "max_pixel_change_inside": max(s["max_overlay_delta_in_protected"] for s in safe),
                         "frames_written": sum(s["frames_written"] for s in safe)}
checks["safe_region_ok"] = checks["safe_region"]["max_pixel_change_inside"] < 1.0

# alpha assets
al = []
for f in sorted(glob.glob("assets/*.png")):
    im = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    ok = im is not None and im.ndim == 3 and im.shape[2] == 4 and im[..., 3].min() < 10 and im[..., 3].max() > 245
    al.append({"file": f, "rgba": bool(im is not None and im.ndim == 3 and im.shape[2] == 4), "alpha_range_ok": bool(ok)})
checks["alpha_assets"] = al
checks["alpha_ok"] = bool(al) and all(a["alpha_range_ok"] for a in al)

# contact sheets: every beat boundary, entrance (+0.25 s), mid, exit (-0.2 s), final frame
def sheet(frames, path, cols=6):
    tiles = []
    for lbl, n in frames:
        n = max(0, min(21880, n))
        im = cv2.cvtColor(frame(MASTER, n), cv2.COLOR_RGB2BGR)
        im = cv2.resize(im, (426, 240))
        cv2.putText(im, f"{lbl} {n / FPS:.2f}s", (6, 18), 0, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        tiles.append(im)
    while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(path, np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]))
os.makedirs("verify/contact", exist_ok=True)
fr = []
for b in D["beats"]:
    if b["treatment"] == "CLEAN_PRESENTER": continue
    s, e = int(round(b["start"] * FPS)), int(round(b["end"] * FPS))
    fr += [(b["id"] + " in", s + 8), (b["id"] + " mid", (s + e) // 2), (b["id"] + " out", e - 6)]
fr.append(("final", 21880))
paths = []
for i in range(0, len(fr), 36):
    p = f"verify/contact/sheet_{i // 36:02d}.jpg"; sheet(fr[i:i + 36], p); paths.append(p)
# edit boundaries in the source (camera<->screen cuts)
cuts = [2347, 2836, 3715, 8699, 11100, 20924]
cf = []
for c in cuts: cf += [("cut-1", c - 1), ("cut", c)]
sheet(cf, "verify/contact/source_cuts.jpg", 4); paths.append("verify/contact/source_cuts.jpg")
checks["contact_sheets"] = paths

checks["sha256"] = {"master": sha(MASTER), "source": sha(SRC), "directive": sha("editorial-directive.json")}
checks["source_unchanged"] = checks["sha256"]["source"] == D["source"]["sha256"]
checks["all_ok"] = all(checks[k] for k in ("probe_match", "audio_packets_identical", "source_identity_ok", "safe_region_ok", "alpha_ok", "source_unchanged")) and checks["full_decode"]["ok"]
json.dump(checks, open("reports/checks.json", "w"), indent=1)
print(json.dumps({k: checks[k] for k in ("probe_match", "full_decode", "audio_packets_identical", "loudness", "source_identity_ok", "safe_region", "alpha_ok", "source_unchanged", "all_ok")}, indent=1))
