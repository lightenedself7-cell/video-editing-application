#!/usr/bin/env python3
"""Auto-cleanup for raw presenter footage: long pauses, fillers, false starts, repeated takes, "cut cut" markers.

Two steps, with the creator's approval in between (never encode before the cut list is approved):

  plan   transcribe locally (faster-whisper, fillers kept) and write cuts.json + cuts.md
  apply  read the approved cuts.json, encode the cleaned source and a time-shifted transcript

Usage (from the repo root, inside WSL):
  .venv/bin/python skills/presenter-long-form-editor/scripts/auto_clean.py plan  RAW.mp4 --out edit/<project>/cleanup
  # read edit/<project>/cleanup/cuts.md; to keep a cut's audio, set "skip": true on it in cuts.json
  .venv/bin/python skills/presenter-long-form-editor/scripts/auto_clean.py apply RAW.mp4 --out edit/<project>/cleanup

The original file is never modified. Transcription is local only.
"""
import argparse
import json
import os
import re
import subprocess
import sys

FILLERS = {"um", "umm", "uh", "uhh", "uhm", "er", "erm", "ah", "ahh", "hmm", "mm", "mmm"}
FILLER_PROMPT = "Um, uh, so, er, I mean, uh, let me, um, start again."


# ---------- transcript ----------

def transcribe(src, model_name):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segments, info = model.transcribe(
        src, word_timestamps=True, vad_filter=True, initial_prompt=FILLER_PROMPT,
        condition_on_previous_text=False,
    )
    words = []
    for s in segments:
        for w in s.words or []:
            words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    return {"language": info.language, "duration": round(info.duration, 3), "words": words}


def norm(word):
    return re.sub(r"[^a-z0-9']", "", word.lower())


# ---------- audio envelope (for snapping cut points to quiet spots) ----------

def rms_envelope(src, hop=0.01):
    import numpy as np
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
         "-f", "s16le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    n = int(16000 * hop)
    frames = len(a) // n
    if frames == 0:
        return np.zeros(1), hop
    a = a[: frames * n].reshape(frames, n)
    return np.sqrt((a ** 2).mean(axis=1)) + 1e-9, hop


def snap(t, env, hop, lo, hi):
    """Move t to the quietest 10 ms frame within [lo, hi] (bounds never cross a kept word)."""
    if hi - lo < hop:
        return t
    i0, i1 = max(0, int(lo / hop)), min(len(env) - 1, int(hi / hop))
    if i1 <= i0:
        return t
    seg = env[i0:i1 + 1]
    return round((i0 + int(seg.argmin())) * hop + hop / 2, 3)


# ---------- detection ----------

def find_cuts(words, duration, a):
    cuts = []
    W = words
    nw = [norm(x["w"]) for x in W]

    # 1. "cut cut" marker: remove the unfinished sentence before it plus the marker itself
    i = 0
    while i < len(W) - 1:
        if nw[i] == "cut" and nw[i + 1] == "cut":
            j = i
            while j > 0:
                prev = W[j - 1]
                if W[j]["start"] - prev["end"] > a.sentence_gap or prev["w"].endswith((".", "?", "!")):
                    break
                j -= 1
            cuts.append({"start": W[j]["start"], "end": W[i + 1]["end"], "reason": "cut-cut marker", "i0": j, "i1": i + 1})
            i += 2
        else:
            i += 1

    # 2. repeated take / false start: words[i:i+k] restarted at j (keeps the LAST take)
    k = a.min_repeat
    i = 0
    while i < len(W) - k:
        hit = None
        for j in range(i + 2, min(len(W) - k + 1, i + a.max_repeat_words)):
            if W[j]["start"] - W[i]["start"] > a.max_repeat_seconds:
                break
            if nw[i:i + k] == nw[j:j + k] and all(nw[i:i + k]):
                hit = j
        if hit is not None:
            # a real false start stops mid-sentence; if the first "take" finishes a sentence it is
            # probably normal speech that repeats a phrase, so list it for review and keep it by default
            finished = any(W[x]["w"].endswith((".", "?", "!")) for x in range(i, hit))
            if finished:
                cuts.append({"start": W[i]["start"], "end": W[hit]["start"], "reason": "possible retake, check",
                             "i0": i, "i1": hit - 1, "check": True})
            else:
                cuts.append({"start": W[i]["start"], "end": W[hit]["start"], "reason": "repeated take", "i0": i, "i1": hit - 1})
            i = hit
        else:
            i += 1

    # 3. fillers, plus the silence around them down to keep_pause
    half = a.keep_pause / 2
    for i, w in enumerate(nw):
        if w in FILLERS:
            prev_end = W[i - 1]["end"] if i > 0 else 0.0
            next_start = W[i + 1]["start"] if i + 1 < len(W) else duration
            s = min(W[i]["start"], prev_end + half)
            e = max(W[i]["end"], next_start - half)
            cuts.append({"start": s, "end": e, "reason": "filler", "i0": i, "i1": i})

    # 4. long pauses (incl. head and tail of the recording): trim down to keep_pause
    edges = [(0.0, W[0]["start"] if W else duration, -1, 0)]
    edges += [(W[i]["end"], W[i + 1]["start"], i, i + 1) for i in range(len(W) - 1)]
    edges += [(W[-1]["end"] if W else 0.0, duration, len(W) - 1, len(W))]
    half = a.keep_pause / 2
    for s, e, ia, ib in edges:
        if e - s > a.max_pause:
            lead = 0.0 if ia < 0 else half
            tail = 0.0 if ib >= len(W) else half
            if e - tail - (s + lead) > 0.05:
                cuts.append({"start": s + lead, "end": e - tail, "reason": f"pause {e - s:.1f}s", "i0": None, "i1": None})
    return cuts


def merge(cuts, words, env, hop):
    """Snap to audio dips without entering kept words, then merge overlaps."""
    starts = [w["start"] for w in words]
    ends = [w["end"] for w in words]
    out = []
    for c in cuts:
        s, e = c["start"], c["end"]
        if c["i0"] is not None:
            i0, i1 = c["i0"], c["i1"]
            lo = ends[i0 - 1] if i0 > 0 else 0.0
            hi = starts[i1 + 1] if i1 + 1 < len(words) else e + 0.3
            if s >= words[i0]["start"] - 0.001:   # cut starts on a word edge: snap into the quiet before it
                s = snap(s, env, hop, max(lo, s - 0.12), s)
            if e <= words[i1]["end"] + 0.001:     # cut ends on a word edge: snap into the quiet after it
                e = snap(e, env, hop, e, min(hi, e + 0.12))
        out.append({**c, "start": round(s, 3), "end": round(e, 3)})
    out.sort(key=lambda c: c["start"])
    merged = []
    for c in out:
        if c["end"] - c["start"] < 0.06:
            continue
        if merged and c["start"] <= merged[-1]["end"] + 0.02:
            m = merged[-1]
            m["end"] = max(m["end"], c["end"])
            m["check"] = m["check"] or c.get("check", False)
            if c["reason"] not in m["reason"]:
                m["reason"] += " + " + c["reason"]
        else:
            merged.append({"start": c["start"], "end": c["end"], "reason": c["reason"], "check": c.get("check", False)})
    return merged


# ---------- reports ----------

def text_between(words, s, e):
    return " ".join(w["w"] for w in words if w["start"] >= s - 0.01 and w["end"] <= e + 0.01)


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def write_plan(out, src, tr, cuts):
    words = tr["words"]
    for n, c in enumerate(cuts, 1):
        c["id"] = n
        c["removed_text"] = text_between(words, c["start"], c["end"])
        c["skip"] = bool(c.pop("check", False))  # flagged cuts are kept unless the creator approves them
    removed = sum(c["end"] - c["start"] for c in cuts)
    plan = {"source": os.path.abspath(src), "duration": tr["duration"], "removed_s": round(removed, 2),
            "result_s": round(tr["duration"] - removed, 2), "cuts": cuts}
    json.dump(plan, open(os.path.join(out, "cuts.json"), "w"), indent=1, ensure_ascii=False)

    by = {}
    for c in cuts:
        key = c["reason"].split(" ")[0]
        by[key] = by.get(key, 0) + 1
    lines = [f"# Cut list for {os.path.basename(src)}", "",
             f"- Original: {fmt(tr['duration'])}  |  after cleanup: {fmt(plan['result_s'])}  |  removed: {removed:.1f}s in {len(cuts)} cuts",
             "- By type: " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())),
             "- To keep a cut: set `\"skip\": true` on its id in cuts.json, then run `apply`.",
             "- Rows marked KEPT are flagged for review and will NOT be cut unless you set `\"skip\": false`.", "",
             "| id | time | type | removed | context after |", "|---|---|---|---|---|"]
    for c in cuts:
        after = text_between(words, c["end"], c["end"] + 3.0)
        kind = c['reason'] + (" (KEPT)" if c["skip"] else "")
        lines.append(f"| {c['id']} | {fmt(c['start'])}-{fmt(c['end'])} | {kind} | {c['removed_text'] or '(silence)'} | {after} |")
    open(os.path.join(out, "cuts.md"), "w").write("\n".join(lines) + "\n")
    return plan


# ---------- apply ----------

def keep_segments(cuts, duration):
    segs, t = [], 0.0
    for c in sorted(cuts, key=lambda c: c["start"]):
        if c["start"] > t + 0.03:
            segs.append((t, c["start"]))
        t = max(t, c["end"])
    if duration > t + 0.03:
        segs.append((t, duration))
    return segs


def shift_transcript(tr, cuts):
    C = sorted((c["start"], c["end"]) for c in cuts)

    def T(x):
        return round(x - sum(min(b, x) - a for a, b in C if x > a), 3)

    words = [dict(w, start=T(w["start"]), end=T(w["end"])) for w in tr["words"]
             if not any(w["start"] >= a - 0.01 and w["end"] <= b + 0.01 for a, b in C)]
    return {**tr, "duration": T(tr["duration"]), "words": words, "cut": {"removed": C}}


def apply(a):
    plan = json.load(open(os.path.join(a.out, "cuts.json")))
    cuts = [c for c in plan["cuts"] if not c.get("skip")]
    duration = plan["duration"]
    segs = keep_segments(cuts, duration)
    fade = 0.015
    parts, labels = [], []
    for n, (s, e) in enumerate(segs):
        d = e - s
        parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{n}];")
        af = f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS"
        if n > 0:
            af += f",afade=t=in:st=0:d={fade}"
        if n < len(segs) - 1:
            af += f",afade=t=out:st={max(0, d - fade):.3f}:d={fade}"
        parts.append(af + f"[a{n}];")
        labels.append(f"[v{n}][a{n}]")
    graph = "".join(parts) + "".join(labels) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    gpath = os.path.join(a.out, "cut-graph.txt")
    open(gpath, "w").write(graph)

    base = os.path.splitext(os.path.basename(a.src))[0]
    dst = a.output or os.path.join(a.out, f"{base}-clean.mp4")
    if os.path.abspath(dst) == os.path.abspath(a.src):
        sys.exit("refusing to overwrite the original footage")
    venc = ["-c:v", "h264_nvenc", "-preset", "p6", "-cq", "16"] if a.nvenc else ["-c:v", "libx264", "-preset", a.preset, "-crf", "12"]
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y", "-i", a.src,
           "-filter_complex_script", gpath, "-map", "[v]", "-map", "[a]", *venc, "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", dst]
    subprocess.run(cmd, check=True)

    tpath = os.path.join(a.out, "transcript.json")
    if os.path.exists(tpath):
        json.dump(shift_transcript(json.load(open(tpath)), cuts), open(os.path.join(a.out, "transcript-clean.json"), "w"),
                  ensure_ascii=False)
    got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst],
                               capture_output=True, text=True).stdout.strip())
    expect = sum(e - s for s, e in segs)
    print(f"cleaned: {dst}\n  {len(cuts)} cuts applied, {len(segs)} segments, duration {got:.2f}s (expected {expect:.2f}s)")
    if abs(got - expect) > 0.5:
        print("  WARNING: duration differs from the plan by more than 0.5 s, check the edit boundaries")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", choices=["plan", "apply"])
    p.add_argument("src")
    p.add_argument("--out", required=True, help="working folder, e.g. edit/<project>/cleanup")
    p.add_argument("--transcript", help="reuse an existing word-level transcript JSON instead of transcribing")
    p.add_argument("--model", default=os.environ.get("VIDEO_WHISPER_MODEL", "small"))
    p.add_argument("--max-pause", type=float, default=0.6, help="pauses longer than this get trimmed (s)")
    p.add_argument("--keep-pause", type=float, default=0.3, help="pause length left after trimming (s)")
    p.add_argument("--min-repeat", type=int, default=3, help="words that must match to call it a retake")
    p.add_argument("--max-repeat-words", type=int, default=40)
    p.add_argument("--max-repeat-seconds", type=float, default=25.0)
    p.add_argument("--sentence-gap", type=float, default=0.7)
    p.add_argument("--output", help="cleaned video path (default: <out>/<name>-clean.mp4)")
    p.add_argument("--nvenc", action="store_true", help="encode on the NVIDIA GPU (check: ffmpeg -encoders | grep nvenc)")
    p.add_argument("--preset", default="medium", help="x264 preset when not using --nvenc")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.step == "apply":
        return apply(a)

    tpath = os.path.join(a.out, "transcript.json")
    if a.transcript:
        tr = json.load(open(a.transcript))
    else:
        print("transcribing locally ...")
        tr = transcribe(a.src, a.model)
    if not tr.get("duration"):
        tr["duration"] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                               a.src], capture_output=True, text=True).stdout.strip())
    json.dump(tr, open(tpath, "w"), ensure_ascii=False)
    env, hop = rms_envelope(a.src)
    cuts = merge(find_cuts(tr["words"], tr["duration"], a), tr["words"], env, hop)
    plan = write_plan(a.out, a.src, tr, cuts)
    print(f"plan: {len(cuts)} cuts, {plan['removed_s']}s removed, {fmt(tr['duration'])} -> {fmt(plan['result_s'])}")
    print(f"review {os.path.join(a.out, 'cuts.md')}, then run: apply")


if __name__ == "__main__":
    main()
