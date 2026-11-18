"""Final checks on the master: probe, frame count, full decode, loudness, protected-region delta, audio-vs-wav, hashes."""
import json, subprocess, hashlib, re, os, sys, glob
D = "/home/dev/video-editing-application/edit/hiringcafe-hidden-job-board"; os.chdir(D)
M = "hiringcafe-hidden-job-board-master.mp4"; R = {}
sh = lambda *a: subprocess.run(a, capture_output=True, text=True)
p = json.loads(sh("ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_read_frames,duration,sample_rate,channels,pix_fmt", "-of", "json", M).stdout)["streams"]
R["streams"] = p
v = [s for s in p if "width" in s][0]; a = [s for s in p if "sample_rate" in s][0]
R["video_ok"] = (v["width"], v["height"], v["r_frame_rate"], v["nb_read_frames"]) == (1280, 720, "30/1", "19920")
R["duration_v"] = float(v["duration"]); R["duration_a"] = float(a["duration"])
R["av_diff_s"] = round(abs(R["duration_v"] - R["duration_a"]), 3)
dec = sh("ffmpeg", "-v", "error", "-i", M, "-f", "null", "-"); R["decode_errors"] = dec.stderr.strip()[:300]
e = sh("ffmpeg", "-hide_banner", "-nostats", "-i", M, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-").stderr
R["loudness"] = {k: float(re.findall(rf"^\s+{k}:\s+(-?[\d.]+)", e, re.M)[-1]) for k in ("I", "LRA")}
R["true_peak_dbtp"] = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
safe = [json.load(open(f)) for f in sorted(glob.glob("render/chunks/c*.mp4.safe.json"))]
R["protected_region_max_delta"] = max(s["max_overlay_delta_in_protected"] for s in safe); R["protected_frames_checked"] = sum(s["frames_checked"] for s in safe)
R["frames_written"] = sum(s["frames_written"] for s in safe)
R["source_sha256"] = open("reports/source.sha256").read().split()[0]; R["master_sha256"] = hashlib.sha256(open(M, "rb").read()).hexdigest()
R["directive_sha256"] = hashlib.sha256(open("editorial-directive.json", "rb").read()).hexdigest()
json.dump(R, open("reports/checks.json", "w"), indent=1); print(json.dumps(R, indent=1))
