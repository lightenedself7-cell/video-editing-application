"""Render an editorial directive with a theme's components.

The directive says what appears when; the theme's components draw it. No per-video drawing code.
Step 1 scope: source and delivery have the same size; beats without a `component` stay clean presenter.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

from . import registry as reg
from .gfx import Kit, icon_sprite


class Context:
    def __init__(self, directive: dict, project_dir: str, theme_dir: Path | None = None):
        self.directive = directive
        self.project_dir = project_dir
        self.theme = directive.get("theme", "clean-creator")
        self.theme_dir = Path(theme_dir) if theme_dir else reg.theme_dir(self.theme)
        src = directive["source"]
        self.src_path = src["path"]
        self.W, self.H = int(src["width"]), int(src["height"])
        dl = directive.get("delivery") or {}
        if dl and (int(dl.get("width", self.W)), int(dl.get("height", self.H))) != (self.W, self.H):
            raise SystemExit("theme-renderer step 1 needs delivery size equal to source size")
        self.fps = float(Fraction(str(src["fps"])))
        self.duration = float(src["duration_s"])
        self.tokens = json.loads((self.theme_dir / "tokens.json").read_text(encoding="utf-8"))
        self.registry = reg.load_registry(self.theme)
        self.kit = Kit(self.tokens, str(self.theme_dir), self.W, self.H)
        self.beats = sorted(directive["beats"], key=lambda b: b["start"])
        prot = directive.get("protected_regions") or []
        self.protected = prot[0] if prot else None
        self._icons: dict = {}
        self._ground = None
        self.components = _load_components(self.theme_dir)
        missing = set(self.registry["components"]) ^ set(self.components)
        if missing:
            raise SystemExit(f"registry and components.py disagree for: {sorted(missing)}")

    def icon(self, rel_path: str, size: int, tile: bool = False):
        key = (rel_path, size, tile)
        if key not in self._icons:
            self._icons[key] = icon_sprite(os.path.join(self.project_dir, rel_path), self.kit.px(size), tile)
        return self._icons[key]

    def ground(self):
        if self._ground is None:
            self._ground = self.kit.make_ground()
        return self._ground.copy()  # callers draw on it; never hand out the cached image itself

    def beat_at(self, t: float):
        for b in self.beats:
            if b["start"] <= t < b["end"]:
                return b
        return None


def _load_components(theme_dir: Path) -> dict:
    spec = importlib.util.spec_from_file_location(f"theme_components_{theme_dir.name}", theme_dir / "components.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(reg.SKILL_DIR))  # so components can `from renderer.gfx import ...`
    spec.loader.exec_module(mod)
    return mod.COMPONENTS


def render_frame(ctx: Context, n: int, S: np.ndarray):
    """Returns (frame, reference). `reference` is the untouched source when the component must not alter the protected region."""
    t = n / ctx.fps
    base = S.copy()
    b = ctx.beat_at(t)
    if b is None or not b.get("component"):
        return base, None
    spec = ctx.registry["components"][b["component"]]
    out = ctx.components[b["component"]](ctx, b, b.get("props", {}), t, base, S)
    return out, (None if spec.get("touches_presenter") else S)


def _decode(ctx: Context, f0: int, f1: int):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f0 / ctx.fps:.6f}", "-i", ctx.src_path, "-frames:v", str(f1 - f0),
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)


def render_pngs(ctx: Context, frames: list[int], out_dir: str) -> list[str]:
    import cv2
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for n in frames:
        dec = _decode(ctx, n, n + 1)
        buf = dec.stdout.read(ctx.W * ctx.H * 3)
        dec.stdout.close()
        dec.wait()
        S = np.frombuffer(buf, np.uint8).reshape(ctx.H, ctx.W, 3).astype(np.float32)
        out, _ = render_frame(ctx, n, S)
        p = os.path.join(out_dir, f"f{n:05d}.png")
        cv2.imwrite(p, cv2.cvtColor(np.clip(out + 0.5, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        paths.append(p)
    return paths


def render_chunk(ctx: Context, f0: int, f1: int, out_path: str, crf: int = 16, threads: int = 2) -> dict:
    """Render frames [f0, f1) to an H.264 file (no audio). Returns the protected-region safety numbers."""
    dec = _decode(ctx, f0, f1)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ctx.W}x{ctx.H}", "-r", f"{ctx.fps:g}",
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-threads", str(threads),
                            "-x264-params", f"keyint={int(round(ctx.fps * 2))}:min-keyint={int(round(ctx.fps * 2))}:scenecut=0", out_path], stdin=subprocess.PIPE)
    FS = ctx.W * ctx.H * 3
    safe = {"max_overlay_delta_in_protected": 0.0, "frames_checked": 0}
    pr = ctx.protected
    n = f0
    while n < f1:
        buf = dec.stdout.read(FS)
        if len(buf) < FS:
            break
        S = np.frombuffer(buf, np.uint8).reshape(ctx.H, ctx.W, 3).astype(np.float32)
        out, ref = render_frame(ctx, n, S)
        if ref is not None and pr:
            px, py, pw, ph = pr["x"], pr["y"], pr["width"], pr["height"]
            d = float(np.abs(out[py:py + ph, px:px + pw] - ref[py:py + ph, px:px + pw]).max())
            safe["max_overlay_delta_in_protected"] = max(safe["max_overlay_delta_in_protected"], d)
            safe["frames_checked"] += 1
        enc.stdin.write(np.clip(out + 0.5, 0, 255).astype(np.uint8).tobytes())
        n += 1
        if (n - f0) % 300 == 0:
            Path(out_path + ".progress").write_text(str(n - f0))
    enc.stdin.close()
    enc.wait()
    dec.stdout.close()
    dec.wait()
    safe["frames_written"] = n - f0
    Path(out_path + ".safe.json").write_text(json.dumps(safe))
    return safe
