#!/usr/bin/env python3
"""look.py - one-sentence looks: map a mood word to a theme (registry themes only) plus a colour grade.

  look.py resolve "make it moody"          -> JSON {look, theme, grade_filter, ...}  (put theme in editorial-directive.json)
  look.py grade SRC DEST --look moody      -> grades the (cleaned) source before graphics are composited; audio is copied untouched
  look.py list

Same beats, different look: the storyboard (director-treatment.md) does not change, only "theme" and the grade do. Grades are deliberately mild
(face and skin tone stay natural); the face-protection rule is unaffected because graphics are composited AFTER the grade.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

LOOKS = {
    "moody": {"theme": "clean-creator", "words": ["moody", "dark", "dramatic", "dim", "night", "mysterious", "burgundy"],
              "grade": "eq=contrast=1.10:brightness=-0.03:saturation=0.86,colorbalance=rs=-0.02:bs=0.03:rh=0.02:bh=-0.01"},
    "aesthetic": {"theme": "teal-spotlight", "words": ["aesthetic", "soft", "dreamy", "pretty", "teal", "trendy", "vibe", "vibey"],
                  "grade": "eq=contrast=1.04:brightness=0.01:saturation=1.08,colorbalance=rh=0.03:bh=-0.02:bs=0.015,curves=master='0/0.02 0.5/0.5 1/0.98'"},
    "cinematic": {"theme": "navy-amber", "words": ["cinematic", "film", "filmic", "movie", "warm", "golden", "amber"],
                  "grade": "eq=contrast=1.09:brightness=-0.015:saturation=0.92,colorbalance=rs=0.015:bs=-0.02:rm=0.03:bm=-0.015:rh=0.05:bh=-0.03,curves=master='0/0 0.25/0.23 0.75/0.77 1/1'"},
    "clean": {"theme": "lime-tech", "words": ["clean", "bright", "fresh", "techy", "tech", "crisp", "modern", "punchy"],
              "grade": "eq=contrast=1.06:saturation=1.03,curves=master='0/0 0.25/0.23 0.75/0.77 1/1'"},
    "natural": {"theme": "personal", "words": ["natural", "simple", "plain", "default", "neutral", "signature", "normal"],
                "grade": "eq=contrast=1.03:saturation=0.98"},
}
DEFAULT = "natural"


def resolve(sentence: str) -> dict:
    text = sentence.lower()
    best, score = DEFAULT, 0
    for name, d in LOOKS.items():
        s = sum(1 for w in [name] + d["words"] if re.search(rf"\b{re.escape(w)}\b", text))
        if s > score:
            best, score = name, s
    d = LOOKS[best]
    return {"look": best, "matched": score > 0, "theme": d["theme"], "grade_filter": d["grade"], "sentence": sentence}


def grade(src: str, dest: str, look: str, crf: int = 12, preset: str = "medium"):
    if look not in LOOKS:
        sys.exit(f"unknown look {look!r}; choose from {', '.join(LOOKS)}")
    subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-stats", "-y", "-i", src, "-vf", LOOKS[look]["grade"],
                    "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", dest], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve")
    r.add_argument("sentence")
    g = sub.add_parser("grade")
    g.add_argument("src")
    g.add_argument("dest")
    g.add_argument("--look", required=True)
    g.add_argument("--crf", type=int, default=12)
    g.add_argument("--preset", default="medium")
    sub.add_parser("list")
    a = ap.parse_args()
    if a.cmd == "resolve":
        print(json.dumps(resolve(a.sentence), indent=1))
    elif a.cmd == "grade":
        grade(a.src, a.dest, a.look, a.crf, a.preset)
        print("GRADE_DONE", a.dest)
    else:
        for k, v in LOOKS.items():
            print(f"{k:10s} theme={v['theme']:15s} words: {', '.join(v['words'])}")


if __name__ == "__main__":
    main()
