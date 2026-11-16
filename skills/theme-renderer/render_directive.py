#!/usr/bin/env python3
"""Render an editorial directive with its theme's components.

  render_directive.py <project-dir>                      full render: validate, chunks in parallel, concat, audio copied from source
  render_directive.py <project-dir> --png 120 480        write those frames as PNGs to <project-dir>/render/frames
  render_directive.py <project-dir> --chunk 0 900 out.mp4   one video-only chunk (used by the parallel runner)

The directive is <project-dir>/editorial-directive.json (or --directive). Output defaults to
<project-dir>/<project>-master.mp4. Original media is never modified.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from renderer import engine  # noqa: E402


def progress(project: Path, percent: float, message: str, phase: str = "composite") -> None:
    line = {"t": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "phase": phase, "percent": int(percent), "message": message}
    with open(project / "ui-progress.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line) + "\n")


def validate(directive: Path) -> None:
    validator = HERE.parent / "presenter-long-form-editor" / "scripts" / "validate_directive.py"
    r = subprocess.run([sys.executable, str(validator), str(directive)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        raise SystemExit("directive failed validation; nothing rendered")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--directive", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 2))
    ap.add_argument("--png", nargs="+", type=int)
    ap.add_argument("--chunk", nargs=3, metavar=("FIRST", "LAST_EXCL", "OUT"))
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args()

    project = args.project.resolve()
    dpath = args.directive or project / "editorial-directive.json"
    directive = json.loads(dpath.read_text(encoding="utf-8"))
    if not args.chunk:
        validate(dpath)
    ctx = engine.Context(directive, str(project))

    if args.png:
        for p in engine.render_pngs(ctx, args.png, str(project / "render" / "frames")):
            print(p)
        return 0
    if args.chunk:
        engine.render_chunk(ctx, int(args.chunk[0]), int(args.chunk[1]), args.chunk[2])
        return 0

    n = int(round(ctx.duration * ctx.fps))
    k = max(1, args.workers)
    step = -(-n // k)
    chunks_dir = project / "render" / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    procs, outs = [], []
    for i in range(k):
        a, b = i * step, min(n, (i + 1) * step)
        if a >= b:
            break
        out = chunks_dir / f"c{i}.mp4"
        outs.append((out, b - a))
        procs.append(subprocess.Popen([sys.executable, __file__, str(project), "--directive", str(dpath), "--chunk", str(a), str(b), str(out)]))
    last = 0.0
    while any(p.poll() is None for p in procs):
        time.sleep(5)
        if time.time() - last >= 60:
            done = sum(int(Path(str(o) + ".progress").read_text() or 0) for o, _ in outs if Path(str(o) + ".progress").exists())
            progress(project, 100 * done / n, f"Rendered about {done} of {n} frames")
            last = time.time()
    if any(p.returncode for p in procs):
        raise SystemExit("a render chunk failed")
    listing = chunks_dir / "concat.txt"
    listing.write_text("".join(f"file '{o}'\n" for o, _ in outs))
    master = args.out or project / f"{directive.get('project', project.name)}-master.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing)]
    if args.no_audio:
        cmd += ["-c", "copy", str(master)]
    else:
        cmd += ["-i", ctx.src_path, "-map", "0:v:0", "-map", "1:a:0?", "-c", "copy", "-shortest", str(master)]
    subprocess.run(cmd, check=True)
    safe = {"max_overlay_delta_in_protected": 0.0, "frames_checked": 0}
    for o, _ in outs:
        s = json.loads(Path(str(o) + ".safe.json").read_text())
        safe["max_overlay_delta_in_protected"] = max(safe["max_overlay_delta_in_protected"], s["max_overlay_delta_in_protected"])
        safe["frames_checked"] += s["frames_checked"]
    (project / "render" / "safe.json").write_text(json.dumps(safe, indent=2))
    progress(project, 100, "Render complete")
    print(master)
    from verify_master import write_checks  # noqa: E402
    results = write_checks(project, directive, Path(master))
    failed = [r for r in results if not r["pass"]]
    for r in results:
        print(("PASS " if r["pass"] else "FAIL ") + f"{r['check']}: {r['detail']}")
    progress(project, 100, "All checks pass" if not failed else f"{len(failed)} check(s) failed", "verify")
    progress(project, 100, "Master and checks written to the project folder", "deliver")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
