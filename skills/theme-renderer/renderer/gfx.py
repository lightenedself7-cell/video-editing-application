"""Drawing primitives for theme templates (numpy float RGB canvas, values 0-255).

Pure helpers (easing, compositing, text, shapes) live at module level. Anything that depends on a theme's
colours is a method of `Kit`, which is built from the theme's tokens.json and the delivery size.
Sizes in components are written for a 1280x720 design space and multiplied by `kit.u` (= width / 1280).
"""
from __future__ import annotations

import os
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

DESIGN_W = 1280


def hexc(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smoother(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x, s=1.2):
    x = clamp(x)
    x1 = x - 1
    return 1 + (s + 1) * x1 ** 3 + s * x1 ** 2


# ---------- fonts / text ----------
_FONTS = {"regular": None, "italic": None}


def set_fonts(regular: str, italic: str) -> None:
    """Point the text helpers at a theme's variable fonts (weight axis). Clears the caches."""
    _FONTS["regular"], _FONTS["italic"] = regular, italic
    font.cache_clear()
    text_sprite.cache_clear()


@lru_cache(None)
def font(size, weight=400, italic=False):
    f = ImageFont.truetype(_FONTS["italic"] if italic else _FONTS["regular"], size)
    f.set_variation_by_axes([weight])
    return f


def rich_segments(text, size, weight, bold_weight=800):
    """'a **b** c' -> [(str, font)]"""
    parts = text.split("**")
    segs = []
    for i, p in enumerate(parts):
        if p:
            segs.append((p, font(size, bold_weight if i % 2 else weight)))
    return segs


def text_width(text, size, weight=400, bold_weight=800):
    return sum(f.getlength(s) for s, f in rich_segments(text, size, weight, bold_weight))


def wrap(text, size, weight, maxw, bold_weight=800):
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_width(t.replace("**", "") if t.count("**") % 2 else t, size, weight, bold_weight) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    out = []
    open_ = False
    for l in lines:
        if open_:
            l = "**" + l
        if l.count("**") % 2:
            l = l + "**"
            open_ = True
        else:
            open_ = False
        out.append(l)
    return out


@lru_cache(None)
def text_sprite(text, size, weight=400, color="#FFFFFF", glow=0.0, italic=False, bold_weight=800, align="left", maxw=0, leading=1.25):
    """RGBA float sprite (straight alpha) with optional soft glow. Padding 24px."""
    lines = wrap(text, size, weight, maxw, bold_weight) if maxw else [text]
    pad = 24
    widths = [text_width(l, size, weight, bold_weight) for l in lines] if not italic else [font(size, weight, True).getlength(l) for l in lines]
    lh = int(size * leading)
    w = int(max(widths)) + pad * 2 + 4
    h = lh * len(lines) + pad * 2
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    y = pad
    for l, lw in zip(lines, widths):
        x = pad + (0 if align == "left" else (max(widths) - lw) / 2 if align == "center" else max(widths) - lw)
        if italic:
            d.text((x, y), l, font=font(size, weight, True), fill=255)
        else:
            for s, f in rich_segments(l, size, weight, bold_weight):
                d.text((x, y), s, font=f, fill=255)
                x += f.getlength(s)
        y += lh
    a = np.asarray(img).astype(np.float32) / 255
    col = hexc(color)
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., :3] = col
    rgba[..., 3] = a
    if glow > 0:
        g = cv2.GaussianBlur(a, (0, 0), size * 0.22) * glow
        rgba[..., 3] = np.clip(a + g * (1 - a), 0, 1)
    return rgba, pad


def over(dst, rgba, x, y, alpha=1.0):
    """Alpha-composite a float RGBA sprite (straight alpha) onto float RGB dst."""
    if alpha <= 0.001:
        return
    h, w = rgba.shape[:2]
    x = int(round(x))
    y = int(round(y))
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] * alpha
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a


def put_text(dst, text, size, x, y, weight=400, color="#FFFFFF", alpha=1.0, glow=0.0, anchor="lt", maxw=0, italic=False, align="left", bold_weight=800, scale=1.0):
    size = int(round(size))
    maxw = int(round(maxw)) if maxw else 0
    rgba, pad = text_sprite(text, size, weight, color, glow, italic, bold_weight, align, maxw)
    if scale != 1.0:
        rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        pad = pad * scale
    h, w = rgba.shape[:2]
    ox = {"l": -pad, "c": -w / 2, "r": -(w - pad)}[anchor[0]]
    oy = {"t": -pad, "m": -h / 2, "b": -(h - pad)}[anchor[1]]
    over(dst, rgba, x + ox, y + oy, alpha)
    return w - 2 * pad, h - 2 * pad


# ---------- shapes ----------
@lru_cache(None)
def rrect_mask(w, h, r, ss=4):
    img = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=r * ss, fill=255)
    return np.asarray(img.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255


@lru_cache(None)
def rrect_ring(w, h, r, width=1.5, glow=8.0, glow_alpha=0.75, color="#FFFFFF", glow_color=None, margin=24):
    """RGBA sprite of an outline plus outer glow for a w x h rounded rect, offset by -margin."""
    ss = 4
    W2, H2 = w + 2 * margin, h + 2 * margin
    img = Image.new("L", (W2 * ss, H2 * ss), 0)
    ImageDraw.Draw(img).rounded_rectangle([margin * ss, margin * ss, (margin + w) * ss - 1, (margin + h) * ss - 1],
                                          radius=r * ss, outline=255, width=max(1, int(width * ss)))
    line = np.asarray(img.resize((W2, H2), Image.LANCZOS)).astype(np.float32) / 255
    g = cv2.GaussianBlur(line, (0, 0), glow) * glow_alpha * 3.0 if glow > 0 else 0 * line
    g = np.clip(g, 0, glow_alpha)
    col = hexc(color)
    gcol = hexc(glow_color or color)
    a = np.clip(line + g * (1 - line), 0, 1)
    rgb = (col * line[..., None] + gcol * (g * (1 - line))[..., None]) / np.maximum(a[..., None], 1e-4)
    out = np.zeros((H2, W2, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a
    return out


@lru_cache(None)
def circle_mask(r, ss=4):
    d = int(np.ceil(2 * r)) + 2
    img = Image.new("L", (d * ss, d * ss), 0)
    c = d * ss / 2
    ImageDraw.Draw(img).ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], fill=255)
    return np.asarray(img.resize((d, d), Image.LANCZOS)).astype(np.float32) / 255


@lru_cache(None)
def circle_ring(r, width=2.0, glow=5.0, glow_alpha=0.7, color="#FFFFFF", glow_color="#FFFFFF", margin=18):
    ss = 4
    d = int(np.ceil(2 * r)) + 2 * margin
    img = Image.new("L", (d * ss, d * ss), 0)
    c = d * ss / 2
    ImageDraw.Draw(img).ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], outline=255, width=max(1, int(width * ss)))
    line = np.asarray(img.resize((d, d), Image.LANCZOS)).astype(np.float32) / 255
    g = np.clip(cv2.GaussianBlur(line, (0, 0), glow) * glow_alpha * 3.0, 0, glow_alpha)
    col = hexc(color)
    gcol = hexc(glow_color)
    a = np.clip(line + g * (1 - line), 0, 1)
    rgb = (col * line[..., None] + gcol * (g * (1 - line))[..., None]) / np.maximum(a[..., None], 1e-4)
    out = np.zeros((d, d, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a
    return out, d / 2


@lru_cache(None)
def check_sprite(r, color):
    ss = 4
    d = int(2 * r + 16)
    img = Image.new("L", (d * ss, d * ss), 0)
    dr = ImageDraw.Draw(img)
    c = d * ss / 2
    pts = [(c - 0.5 * r * ss, c + 0.02 * r * ss), (c - 0.12 * r * ss, c + 0.42 * r * ss), (c + 0.58 * r * ss, c - 0.42 * r * ss)]
    dr.line(pts, fill=255, width=int(r * 0.26 * ss), joint="curve")
    for p in (pts[0], pts[2]):
        e = r * 0.13 * ss
        dr.ellipse([p[0] - e, p[1] - e, p[0] + e, p[1] + e], fill=255)
    a = np.asarray(img.resize((d, d), Image.LANCZOS)).astype(np.float32) / 255
    g = np.clip(cv2.GaussianBlur(a, (0, 0), 3) * 0.8, 0, 1)
    al = np.clip(a + g * (1 - a), 0, 1)
    out = np.zeros((d, d, 4), np.float32)
    out[..., :3] = hexc(color)
    out[..., 3] = al
    return out


def icon_sprite(path, size, tile=False):
    im = Image.open(path).convert("RGBA")
    im.thumbnail((size * 4, size * 4), Image.LANCZOS)
    im = im.resize((int(im.width * size / max(im.size)), int(im.height * size / max(im.size))), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    out = np.zeros_like(a)
    out[..., :3] = a[..., :3]
    out[..., 3] = a[..., 3] / 255
    if tile:
        m = rrect_mask(out.shape[1], out.shape[0], int(0.24 * size))
        out[..., 3] *= m
    return out


# ---------- theme kit ----------
class Kit:
    """Theme-aware drawing built from tokens.json at a given delivery size."""

    def __init__(self, tokens: dict, theme_dir: str, width: int, height: int):
        self.tokens = tokens
        self.W, self.H = int(width), int(height)
        self.u = width / DESIGN_W
        c = tokens["colors"]
        self.c = c
        self.ground = hexc(c["ground"])
        self.accent = c["accent"]
        self.glow_color = c.get("glow", c["accent"])
        self.highlight = c["highlight"]
        self.text = c["text"]
        self.text_rgb = hexc(c["text"])
        fonts = tokens["fonts"]
        set_fonts(os.path.join(theme_dir, fonts["regular"]), os.path.join(theme_dir, fonts["italic"]))
        self._ground_img = None

    def px(self, v: float) -> int:
        return int(round(v * self.u))

    def make_ground(self) -> np.ndarray:
        if self._ground_img is not None:
            return self._ground_img.copy()
        W, H, u = self.W, self.H, self.u
        spec = self.tokens["ground"]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        bg = np.empty((H, W, 3), np.float32)
        bg[:] = self.ground
        for o in spec.get("orbs", []):
            cx, cy, rad = o["cx"] * u, o["cy"] * u, o["radius"] * u
            d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
            tt = np.clip(d / rad, 0, 1)
            a = np.clip(1 - d / rad, 0, 1) ** o["power"] * o["strength"]
            orb = hexc(o["from"]) * (1 - tt)[..., None] + hexc(o["to"]) * tt[..., None]
            bg = bg * (1 - a[..., None]) + orb * a[..., None]
        g = spec.get("grid")
        if g:
            step = g["step"] * u
            grid = (((xx % step) < 1) | ((yy % step) < 1)).astype(np.float32) * g["alpha"]
            bg = bg * (1 - grid[..., None]) + self.text_rgb * grid[..., None]
        self._ground_img = bg
        return bg.copy()

    def glass(self, dst, x, y, w, h, alpha=1.0, r=22, tint=0.62, blur=14, glow=7.0, highlight=0.0):
        u = self.u
        x, y, w, h = int(round(x)), int(round(y)), int(w), int(h)
        r, blur, glow = int(round(r * u)), blur * u, glow * u
        if alpha <= 0.001:
            return
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, self.W), min(y + h, self.H)
        if x1 <= x0 or y1 <= y0:
            return
        region = dst[y0:y1, x0:x1]
        b = cv2.GaussianBlur(region, (0, 0), blur)
        b = b * (1 - tint) + self.ground * tint
        m = rrect_mask(w, h, r)[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * alpha
        dst[y0:y1, x0:x1] = region * (1 - m) + b * m
        mg = self.px(24)
        over(dst, rrect_ring(w, h, r, 1.5 * u, glow, 0.75, self.accent, None, mg), x - mg, y - mg, alpha)
        if highlight > 0:
            over(dst, rrect_ring(w, h, r, 2.0 * u, 10.0 * u, 0.9, self.highlight, None, mg), x - mg, y - mg, alpha * highlight)

    def check_badge(self, dst, cx, cy, r, prog, alpha=1.0):
        """Outlined glowing circle with a highlight-colour check that pops in with prog (0..1)."""
        u = self.u
        r = int(round(r * u))
        ring, c = circle_ring(r, 1.5 * u, 4.0 * u, 0.6, self.accent, self.accent, self.px(18))
        over(dst, ring, cx - c, cy - c, alpha)
        if prog > 0:
            s = ease_back(prog, 1.4)
            spr = check_sprite(r, self.highlight)
            if s != 1:
                spr = cv2.resize(spr, None, fx=max(s, 0.05), fy=max(s, 0.05), interpolation=cv2.INTER_LINEAR)
            hh, ww = spr.shape[:2]
            over(dst, spr, cx - ww / 2, cy - hh / 2, alpha * clamp(prog * 3))

    def dot(self, dst, cx, cy, r, alpha=1.0):
        """Small solid bullet in the highlight colour."""
        m = circle_mask(r * self.u)
        s = np.zeros(m.shape + (4,), np.float32)
        s[..., :3] = hexc(self.highlight)
        s[..., 3] = m
        over(dst, s, cx, cy, alpha)
