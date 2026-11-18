#!/usr/bin/env python3
"""auto_clean.py - automatic cleanup of raw talking-head footage (long-form first).

Removes silences, ums/ers, stutters, false starts and repeated takes (and anything before a spoken "cut cut"), in TWO steps so nothing is
ever cut without approval:

  1. analyze  SRC --out DIR [--script script.txt]   -> DIR/cuts.json + DIR/cuts.md  (a readable before/after list; nothing is encoded)
  2. apply    DIR --approved [--drop 3,7]            -> cleaned video + time-shifted transcript + cut-map.json

Ideas credited to Nick Saraev's public VAD jump-cut directive (min silence 0.5 s, padding, merge gap, "cut cut" restart phrase) and his voice chain.
Transcription is local faster-whisper with filler-friendly prompting; cut points are snapped to audio dips (RMS) so no cut lands mid-syllable.

Run with the repo venv (numpy + faster-whisper): .venv/bin/python skills/presenter-long-form-editor/scripts/auto_clean.py ...
"""
from __future__ import annotations

import argparse
import bisect
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

FILLERS = {"um", "umm", "uh", "uhh", "er", "erm", "ah", "hmm", "hm", "mm", "mmm", "uhm", "eh", "ehm"}
STOP1 = {"the", "a", "an", "i", "we", "you", "it", "is", "to", "and", "that", "this", "of", "in", "so", "but", "my", "our", "your", "they", "its", "its"}
FILLER_PROMPT = "Um, so, uh, I think, er, we, hmm, you know, um, let's start. Uh, okay."
REVIEW_PAUSE_S = 3.0      # pauses at least this long are flagged: the screen may be doing something while the speaker is quiet
REVIEW_WORDS = 14         # removed spans at least this many words long are flagged


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower())


def fmt_t(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


# ---------------------------------------------------------------- audio envelope
class Audio:
    """10 ms RMS envelope in dB; used to find real silences and quiet cut points."""

    def __init__(self, db):
        import numpy as np
        self.np = np
        self.db = db
        floor, speech = float(np.percentile(db, 10)), float(np.percentile(db, 90))
        self.thr = min(max(floor + 0.25 * (speech - floor), floor + 6), speech - 15)

    @classmethod
    def load(cls, src: str):
        import numpy as np
        p = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True)
        a = np.frombuffer(p.stdout, dtype=np.int16).astype(np.float32) / 32768
        n = len(a) // 160
        fr = a[: n * 160].reshape(n, 160)
        return cls(20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9))

    def silent_span(self, lo: float, hi: float):
        """Longest run of below-threshold frames between lo and hi (seconds), or None."""
        i0 = max(0, int((lo - 0.05) * 100))
        i1 = min(len(self.db), int((hi + 0.05) * 100) + 1)
        best, run_s = None, None
        for k in range(i0, i1 + 1):
            quiet = k < i1 and self.db[k] < self.thr
            if quiet and run_s is None:
                run_s = k
            elif not quiet and run_s is not None:
                if best is None or k - run_s > best[1] - best[0]:
                    best = (run_s, k)
                run_s = None
        return None if best is None else (best[0] / 100, best[1] / 100)

    def snap(self, t: float, lo: float, hi: float, window: float = 0.06) -> float:
        a, b = max(int((t - window) * 100), int(lo * 100), 0), min(int((t + window) * 100), int(hi * 100), len(self.db) - 1)
        if b <= a:
            return t
        ti = int(t * 100)
        seg = self.db[a:b + 1] + 0.02 * self.np.abs(self.np.arange(a, b + 1) - ti)
        return (a + int(seg.argmin()) + 0.5) / 100


# ---------------------------------------------------------------- transcription
def transcribe(src: str, model_name: str) -> dict:
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segs, info = model.transcribe(src, word_timestamps=True, vad_filter=True, initial_prompt=FILLER_PROMPT, condition_on_previous_text=False,
                                  vad_parameters={"min_silence_duration_ms": 500, "speech_pad_ms": 100})
    words, phrases = [], []
    for s in segs:
        phrases.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
        for w in s.words or []:
            words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    return {"language": info.language, "duration": round(info.duration, 3), "words": words, "phrases": phrases}


# ---------------------------------------------------------------- detection
def detect(words, duration, *, pause=0.5, keep=0.3, script=None, audio=None, protect=(), fillers=True, repeats=True, lead_keep=0.2, tail_keep=0.35):
    """Return a list of cut dicts (start, end, types, removed_text, before, after, ...) for the given word list. Pure apart from `audio`."""
    n = len(words)
    tok = [norm(w["w"]) for w in words]
    removed: dict[int, set] = {}

    def mark(i0, i1, reason):
        for k in range(i0, i1 + 1):
            removed.setdefault(k, set()).add(reason)

    def seq_alive():
        return [k for k in range(n) if k not in removed and tok[k]]

    if fillers:
        for k in range(n):
            if tok[k] in FILLERS:
                mark(k, k, "filler")

    # "cut cut" restart marker: drop the marker and the whole unbroken run of speech before it
    for k in range(n - 1):
        if tok[k] == "cut" and tok[k + 1] == "cut" and words[k + 1]["start"] - words[k]["end"] < 0.8:
            j = k
            while j > 0 and k - j < 45 and words[j]["start"] - words[j - 1]["end"] <= 0.7:
                j -= 1
            mark(j, k + 1, "cut-cut")

    if repeats:
        # script retakes: a script sentence heard more than once -> keep the last take
        if script:
            _script_retakes(words, tok, removed, seq_alive, script, mark)
        _stutters_and_restarts(words, tok, removed, seq_alive, mark)
        _self_retakes(words, tok, seq_alive, mark)

    cuts = []
    # word-run cuts (fillers, repeats, retakes): remove the words and the pauses around them down to `keep`
    rem = sorted(removed)
    runs, cur = [], []
    for k in rem:
        if cur and k == cur[-1] + 1:
            cur.append(k)
        else:
            if cur:
                runs.append(cur)
            cur = [k]
    if cur:
        runs.append(cur)
    for r in runs:
        i0, i1 = r[0], r[-1]
        s, e = words[i0]["start"], words[i1]["end"]
        le = words[i0 - 1]["end"] if i0 > 0 else None
        rs = words[i1 + 1]["start"] if i1 + 1 < n else None
        s2 = 0.0 if le is None else s - max(0.0, (s - le) - keep / 2)
        e2 = duration if rs is None else e + max(0.0, (rs - e) - keep / 2)
        types = sorted({t for k in r for t in removed[k]})
        cuts.append({"start": s2, "end": e2, "types": types, "review": len(r) >= REVIEW_WORDS})

    # pauses between two kept, adjacent words (pauses next to removed runs are already absorbed above)
    for k in range(n - 1):
        if k in removed or k + 1 in removed:
            continue
        gap = words[k + 1]["start"] - words[k]["end"]
        if gap < pause - 0.15:
            continue
        lo, hi = words[k]["end"], words[k + 1]["start"]
        span = audio.silent_span(lo, hi) if audio else (lo, hi)
        if not span or span[1] - span[0] < pause:
            continue
        s, e = span[0] + keep / 2, span[1] - keep / 2
        if e - s >= 0.25:
            cuts.append({"start": s, "end": e, "types": ["pause"], "review": (span[1] - span[0]) >= REVIEW_PAUSE_S})

    alive = [k for k in range(n) if k not in removed]
    if alive:
        f, l = alive[0], alive[-1]
        if f > 0 and not any(c["start"] == 0.0 for c in cuts) and words[f]["start"] > lead_keep + 0.4:
            cuts.append({"start": 0.0, "end": words[f]["start"] - lead_keep, "types": ["leading-silence"], "review": words[f]["start"] > 2.0})
        if duration - words[l]["end"] > tail_keep + 0.5 and not any(c["end"] >= duration - 1e-6 for c in cuts):
            cuts.append({"start": words[l]["end"] + tail_keep, "end": duration, "types": ["trailing-silence"], "review": duration - words[l]["end"] > 3.0})

    # protected ranges (e.g. a silent screen demo): drop pause/silence cuts that touch them
    cuts = [c for c in cuts if not (set(c["types"]) <= {"pause", "leading-silence", "trailing-silence"} and any(c["start"] < b and c["end"] > a for a, b in protect))]

    cuts = _merge(cuts)
    if audio:                                              # land every cut on a real audio dip, never mid-syllable
        for c in cuts:
            lo_s, hi_e = _neighbours(words, removed, c["start"], c["end"], duration)
            if c["start"] > 0.0:
                c["start"] = min(audio.snap(c["start"], lo_s - 0.03, c["end"] - 0.05), c["end"] - 0.05)
            if c["end"] < duration - 1e-6:
                c["end"] = max(audio.snap(c["end"], c["start"] + 0.05, hi_e + 0.03), c["start"] + 0.05)
        cuts = _merge(cuts)
    cuts = [c for c in cuts if c["end"] - c["start"] >= 0.08]

    kept_starts = [words[k]["start"] for k in alive]
    kept_ends = [words[k]["end"] for k in alive]
    out = []
    for i, c in enumerate(cuts, 1):
        s, e = c["start"], c["end"]
        gone = [words[k]["w"] for k in rem if min(e, words[k]["end"]) - max(s, words[k]["start"]) >= 0.5 * (words[k]["end"] - words[k]["start"])]
        a_i = bisect.bisect_right(kept_ends, s + 0.02)
        b_i = bisect.bisect_left(kept_starts, e - 0.02)
        before = " ".join(words[k]["w"] for k in alive[max(0, a_i - 7):a_i])
        after = " ".join(words[k]["w"] for k in alive[b_i:b_i + 7])
        types = c["types"]
        out.append({"id": i, "start": round(s, 3), "end": round(e, 3), "len": round(e - s, 2), "types": types,
                    "removed_text": " ".join(gone) if gone else f"[silence {e - s:.1f} s]", "before": before, "after": after,
                    "review": bool(c.get("review")), "approved": True})
    return out


def _merge(cuts):
    cuts = sorted(cuts, key=lambda c: (c["start"], c["end"]))
    out = []
    for c in cuts:
        if out and c["start"] <= out[-1]["end"] + 0.05:
            p = out[-1]
            p["end"] = max(p["end"], c["end"])
            p["types"] = sorted(set(p["types"]) | set(c["types"]))
            p["review"] = p.get("review") or c.get("review")
        else:
            out.append(dict(c))
    return out


def _neighbours(words, removed, s, e, duration):
    left = max((w["end"] for k, w in enumerate(words) if k not in removed and w["end"] <= s + 0.03), default=0.0)
    right = min((w["start"] for k, w in enumerate(words) if k not in removed and w["start"] >= e - 0.03), default=duration)
    return left, right


def _stutters_and_restarts(words, tok, removed, seq_alive, mark):
    seq = seq_alive()
    T = lambda k: tok[seq[k]]
    p = 0
    while p < len(seq):
        hit = None
        for m in range(8, 0, -1):                          # immediate repeats: "the plan the plan", "I I"
            if p + 2 * m <= len(seq) and all(T(p + x) == T(p + m + x) for x in range(m)):
                if m >= 2 or (T(p) in STOP1 and words[seq[p + 1]]["start"] - words[seq[p]]["end"] < 0.5 and not words[seq[p]]["w"].endswith((",", ".", ";", ":", "?", "!"))):
                    hit = (seq[p], seq[p + m - 1], p + m)
                    break
        if not hit:                                         # restarts: the opening words come back after a break
            for m in range(6, 1, -1):
                for j in range(p + m + 1, min(p + 41, len(seq) - m + 1)):
                    if not all(T(p + x) == T(j + x) for x in range(m)):
                        continue
                    if m == 2 and j - p > 5:
                        continue
                    if words[seq[j]]["start"] - words[seq[p]]["start"] > 15:
                        continue
                    prev, nxt = seq[j - 1], seq[j]
                    brk = words[nxt]["start"] - words[prev]["end"] >= 0.3 or nxt - prev > 1 or words[prev]["w"].endswith(("-", "…", "—"))
                    if brk or m >= 6:                      # a 6+ word phrase said twice is never an accident
                        hit = (seq[p], seq[j] - 1, j)
                        break
                if hit:
                    break
        if hit:
            mark(hit[0], hit[1], "repeat" if hit[2] - p <= 8 and hit[1] - hit[0] + 1 <= 8 and hit[2] == p + (hit[1] - hit[0] + 1) else "false-start")
            p = hit[2]
        else:
            p += 1


def _units(words, tok, seq):
    units, cur = [], []
    for k in seq:
        cur.append(k)
        if words[k]["w"].endswith((".", "?", "!")):
            units.append(cur)
            cur = []
    if cur:
        units.append(cur)
    return units


def _self_retakes(words, tok, seq_alive, mark):
    """Without a script: a sentence said again (>= 80 % similar) within the next four sentences means the earlier one was a retake."""
    seq = seq_alive()
    units = [u for u in _units(words, tok, seq) if len(u) >= 4]
    k = 0
    while k < len(units):
        a = [tok[x] for x in units[k]]
        hit = None
        for l in range(k + 1, min(k + 5, len(units))):
            if words[units[l][0]]["start"] - words[units[k][0]]["start"] > 60:
                break
            if difflib.SequenceMatcher(None, a, [tok[x] for x in units[l]]).ratio() >= 0.8:
                hit = l
                break
        if hit is not None:
            mark(units[k][0], units[hit][0] - 1, "retake")
            k = hit
        else:
            k += 1


def _script_retakes(words, tok, removed, seq_alive, script, mark):
    """With a script: every script sentence heard more than once keeps only its LAST take."""
    seq = seq_alive()
    toks = [tok[k] for k in seq]
    for sent in re.split(r"(?<=[.!?])\s+|\n+", script):
        st = [norm(w) for w in sent.split() if norm(w)]
        if len(st) < 5:
            continue
        sset, m = set(st), len(st)
        cands = []
        for p in range(0, len(toks) - m + 1):
            win = toks[p:p + m]
            if len(sset & set(win)) < 0.6 * len(sset):
                continue
            r = difflib.SequenceMatcher(None, st, win).ratio()
            if r >= 0.75:
                cands.append((r, p))
        chosen = []
        for r, p in sorted(cands, reverse=True):
            if all(abs(p - q) >= m for _, q in chosen):
                chosen.append((r, p))
        pos = sorted(p for _, p in chosen)
        for a, b in zip(pos, pos[1:]):
            mark(seq[a], seq[b] - 1, "retake")


# ---------------------------------------------------------------- time map + transcript shifting
def make_T(removed):
    """T(x): original time -> cleaned time, for removed = [[a, b], ...] on the original timeline."""
    removed = sorted((float(a), float(b)) for a, b in removed)

    def T(x: float) -> float:
        return round(x - sum(max(0.0, min(x, b) - a) for a, b in removed), 3)
    return T


def shift_transcript(raw: dict, removed) -> dict:
    T = make_T(removed)
    inside = lambda s, e: any(s >= a - 0.01 and e <= b + 0.01 for a, b in removed)
    words = []
    for w in raw["words"]:
        if inside(w["start"], w["end"]):
            continue
        s, e = T(w["start"]), T(w["end"])
        if e - s > 0.01:
            words.append({**w, "start": s, "end": e})
    phrases = []
    for ph in raw["phrases"]:
        kept = [w for w in raw["words"] if ph["start"] - 0.01 <= w["start"] <= ph["end"] + 0.01 and not inside(w["start"], w["end"])]
        if kept:
            phrases.append({"start": round(T(kept[0]["start"]), 2), "end": round(T(kept[-1]["end"]), 2), "text": " ".join(w["w"] for w in kept)})
    return {**raw, "duration": round(T(raw["duration"]), 2), "words": words, "phrases": phrases, "cut": {"removed": [[a, b] for a, b in removed]}}


# ---------------------------------------------------------------- reports
def write_report(d: Path, src: str, duration: float, cuts: list, params: dict):
    total = sum(c["end"] - c["start"] for c in cuts)
    (d / "cuts.json").write_text(json.dumps({"source": src, "duration": duration, "params": params, "removed_s": round(total, 2),
                                             "cleaned_duration": round(duration - total, 2), "cuts": cuts}, indent=1, ensure_ascii=False))
    by = {}
    for c in cuts:
        for t in c["types"]:
            by[t] = by.get(t, 0) + 1
    lines = [f"# Cut list: {Path(src).name}", "",
             f"Original {fmt_t(duration)} -> cleaned **{fmt_t(duration - total)}** (removes {total:.1f} s in {len(cuts)} cuts: " + ", ".join(f"{v} {k}" for k, v in sorted(by.items())) + ")", "",
             "Nothing is encoded until you approve. To skip a cut, tell me its number (or set `approved` to false in cuts.json). Cuts marked ⚠ need a look: a long quiet stretch may be a screen demo, or a large span of speech.", "",
             "| # | time (orig) | len | type | removed | context |", "|---|---|---|---|---|---|"]
    for c in cuts:
        ctx = f"…{c['before']} **[CUT]** {c['after']}…".replace("|", "/")
        lines.append(f"| {c['id']}{' ⚠' if c['review'] else ''} | {fmt_t(c['start'])}-{fmt_t(c['end'])} | {c['len']:.1f}s | {'+'.join(c['types'])} | {c['removed_text'].replace('|', '/')} | {ctx} |")
    (d / "cuts.md").write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------- encode
def probe_fps(src: str) -> str:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    return out or "30"


VOICE_CHAIN = "highpass=f=80,lowpass=f=12000,equalizer=f=200:t=q:w=1:g=-1,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-18dB:ratio=2.5:attack=20:release=250"


def encode(src: str, removed, dest: Path, *, preset="veryfast", crf=12, voice_chain=False, fade=0.015):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout)
    removed = sorted((max(0.0, a), min(dur, b)) for a, b in removed)
    keep, t = [], 0.0
    for a, b in removed:
        if a - t > 0.02:
            keep.append((t, a))
        t = max(t, b)
    if dur - t > 0.02:
        keep.append((t, dur))
    parts, labels = [], ""
    for i, (a, b) in enumerate(keep):
        fin = f",afade=t=in:st=0:d={fade}" if a > 0.0 else ""
        fout = f",afade=t=out:st={max(0.0, b - a - fade):.3f}:d={fade}" if b < dur - 0.01 else ""
        parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS{fin}{fout}[a{i}]")
        labels += f"[v{i}][a{i}]"
    tail = f"[ao];[ao]{VOICE_CHAIN}[a]" if voice_chain else "[a]"
    graph = ";\n".join(parts) + f";\n{labels}concat=n={len(keep)}:v=1:a=1[v]{tail}"
    script = dest.with_suffix(".filtergraph.txt")
    script.write_text(graph)
    fps = probe_fps(src)
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-stats", "-y", "-i", src, "-filter_complex_script", str(script), "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", fps, "-c:a", "aac", "-b:a", "256k", "-ar", "44100", "-movflags", "+faststart", str(dest)]
    subprocess.run(cmd, check=True)
    script.unlink(missing_ok=True)
    return keep


# ---------------------------------------------------------------- CLI
def cmd_analyze(a):
    d = Path(a.out)
    d.mkdir(parents=True, exist_ok=True)
    raw_path = d / "raw-transcript.json"
    if raw_path.exists() and not a.retranscribe and raw_path.stat().st_mtime >= Path(a.src).stat().st_mtime:
        raw = json.loads(raw_path.read_text())
        print("reusing", raw_path)
    else:
        print("transcribing locally (faster-whisper, fillers kept) ...", flush=True)
        raw = transcribe(a.src, a.model)
        raw_path.write_text(json.dumps(raw, ensure_ascii=False))
    print("reading audio envelope ...", flush=True)
    audio = Audio.load(a.src)
    script = Path(a.script).read_text() if a.script else None
    protect = [tuple(float(x) for x in r.split("-")) for r in a.protect.split(",") if r] if a.protect else []
    cuts = detect(raw["words"], raw["duration"], pause=a.pause, keep=a.keep, script=script, audio=audio, protect=protect, fillers=not a.no_fillers, repeats=not a.no_repeats)
    params = {"pause": a.pause, "keep": a.keep, "script": a.script, "protect": a.protect, "model": a.model}
    write_report(d, str(Path(a.src).resolve()), raw["duration"], cuts, params)
    total = sum(c["end"] - c["start"] for c in cuts)
    print(f"{len(cuts)} cuts, {total:.1f} s removed ({fmt_t(raw['duration'])} -> {fmt_t(raw['duration'] - total)}). Review {d / 'cuts.md'} then run: apply {d} --approved")


def cmd_apply(a):
    d = Path(a.dir)
    if not a.approved:
        sys.exit("Refusing to encode: cuts must be approved first. Show cuts.md to the user, then re-run with --approved (and --drop N,N for any cut they rejected).")
    data = json.loads((d / "cuts.json").read_text())
    drop = {int(x) for x in a.drop.split(",") if x} if a.drop else set()
    removed = [[c["start"], c["end"]] for c in data["cuts"] if c.get("approved", True) and c["id"] not in drop]
    src = data["source"]
    dest = Path(a.output) if a.output else Path(src).with_name(Path(src).stem + "-cut.mp4")
    keep = encode(src, removed, dest, preset=a.preset, crf=a.crf, voice_chain=a.voice_chain)
    raw = json.loads((d / "raw-transcript.json").read_text())
    shifted = shift_transcript(raw, removed)
    (d / "transcript-cut.json").write_text(json.dumps(shifted, ensure_ascii=False))
    (d / "transcript-cut.txt").write_text("".join(f"[{p['start']:.2f}-{p['end']:.2f}] {p['text']}\n" for p in shifted["phrases"]))
    (d / "cut-map.json").write_text(json.dumps({"source": src, "cleaned": str(dest), "removed": removed, "keep": keep, "old_duration": data["duration"], "new_duration": shifted["duration"]}, indent=1))
    h = hashlib.sha256()
    with open(dest, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    (d / "source-cut.sha256").write_text(f"{h.hexdigest()}  {dest}\n")
    print(f"CLEAN_DONE {dest} ({fmt_t(data['duration'])} -> {fmt_t(shifted['duration'])}); transcript {d / 'transcript-cut.json'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze")
    a.add_argument("src")
    a.add_argument("--out", required=True)
    a.add_argument("--script", help="text file with the intended script; repeated takes of a script sentence keep only the last")
    a.add_argument("--pause", type=float, default=0.5, help="silence at least this long is shortened (default 0.5 s)")
    a.add_argument("--keep", type=float, default=0.3, help="silence left behind after a cut (default 0.3 s)")
    a.add_argument("--protect", default="", help="comma list of 'start-end' seconds where silence must NOT be cut (silent screen demos)")
    a.add_argument("--model", default="small")
    a.add_argument("--no-fillers", action="store_true")
    a.add_argument("--no-repeats", action="store_true")
    a.add_argument("--retranscribe", action="store_true")
    a.set_defaults(fn=cmd_analyze)
    b = sub.add_parser("apply")
    b.add_argument("dir")
    b.add_argument("--approved", action="store_true", help="required: the user has approved cuts.md")
    b.add_argument("--drop", default="", help="comma list of cut ids the user rejected")
    b.add_argument("--output")
    b.add_argument("--preset", default="veryfast", help="x264 preset; the cleaned file is an intermediate the renderer re-encodes, so veryfast at CRF 12 is visually lossless and ~2x faster than slow")
    b.add_argument("--crf", type=int, default=12)
    b.add_argument("--voice-chain", action="store_true", help="highpass 80, lowpass 12k, EQ, gentle compression (final loudness is set later)")
    b.set_defaults(fn=cmd_apply)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
