#!/usr/bin/env python3
"""Verify a master rendered by render_directive.py and write <project>/reports/checks.json.

  verify_master.py <project-dir> [--directive FILE] [--master FILE]

The file format is {"results": [{"check", "pass", "detail"}]}, which the app reads. Exit code 0 means every check passed.
Checks: full decode, size, frame rate, duration, audio loudness against the source, and that overlays stayed out of the protected region.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

DURATION_TOL_S = 0.10
LOUDNESS_TOL_LU = 0.2
PROTECTED_TOL = 4.0  # pixel levels of 255; a card's soft glow may reach a few levels in


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path: str) -> dict:
    r = _run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    return json.loads(r.stdout or "{}")


def loudness(path: str):
    r = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"])
    text = r.stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", text)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", text)
    return (float(i[-1]) if i else None), (float(p[-1]) if p else None)


def verify(project: Path, directive: dict, master: Path) -> list[dict]:
    results = []

    def add(name, ok, detail):
        results.append({"check": name, "pass": bool(ok), "detail": detail})

    src = directive["source"]
    if not master.is_file():
        add("master exists", False, f"{master} not found")
        return results
    dec = _run(["ffmpeg", "-v", "error", "-i", str(master), "-f", "null", "-"])
    add("full decode", dec.returncode == 0 and not dec.stderr.strip(), dec.stderr.strip()[:200] or "decoded without errors")
    info = probe(str(master))
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
    size = (int(v.get("width", 0)), int(v.get("height", 0)))
    add("frame size", size == (int(src["width"]), int(src["height"])), f"{size[0]}x{size[1]} (source {src['width']}x{src['height']})")
    try:
        fps = Fraction(v.get("r_frame_rate", "0/1"))
    except ZeroDivisionError:
        fps = Fraction(0)
    add("frame rate", fps == Fraction(str(src["fps"])), f"{float(fps):.3f} (source {float(Fraction(str(src['fps']))):.3f})")
    dur = float(info.get("format", {}).get("duration", 0) or 0)
    add("duration", abs(dur - float(src["duration_s"])) <= DURATION_TOL_S, f"{dur:.3f}s (source {float(src['duration_s']):.3f}s)")
    if a is None:
        add("audio present", False, "no audio stream in the master")
    else:
        m_lufs, m_peak = loudness(str(master))
        s_lufs, _ = loudness(src["path"])
        ok = m_lufs is not None and s_lufs is not None and abs(m_lufs - s_lufs) <= LOUDNESS_TOL_LU
        add("audio matches source", ok, f"{m_lufs} LUFS, true peak {m_peak} dBFS (source {s_lufs} LUFS)")
    safe_path = project / "render" / "safe.json"
    if safe_path.is_file():
        safe = json.loads(safe_path.read_text())
        d = safe.get("max_overlay_delta_in_protected", 0.0)
        add("protected region untouched", d <= PROTECTED_TOL, f"max change {d:.1f}/255 over {safe.get('frames_checked', 0)} overlay frames")
    else:
        add("protected region untouched", False, "render/safe.json is missing")
    return results


def write_checks(project: Path, directive: dict, master: Path) -> list[dict]:
    results = verify(project, directive, master)
    out = project / "reports"
    out.mkdir(exist_ok=True)
    (out / "checks.json").write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--directive", type=Path)
    ap.add_argument("--master", type=Path)
    args = ap.parse_args()
    project = args.project.resolve()
    directive = json.loads((args.directive or project / "editorial-directive.json").read_text(encoding="utf-8"))
    master = args.master or project / f"{directive.get('project', project.name)}-master.mp4"
    results = write_checks(project, directive, master)
    for r in results:
        print(("PASS " if r["pass"] else "FAIL ") + f"{r['check']}: {r['detail']}")
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
