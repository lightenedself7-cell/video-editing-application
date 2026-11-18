"""Widgets for the HiringCafe edit: brand icons, shapes, subscribe / like / comment / share, highlighter, zoom."""
import os, sys
import numpy as np, cv2
from functools import lru_cache
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *

BRAND = os.path.join(ROOT, "brand")
ROSE_HEX, RASP_HEX, WHITE_HEX = "#E25C8E", "#92205A", "#FAF9F8"

# ---------------------------------------------------------------- brand icons (fetched, never redrawn)
def _rgba(path, w):
    im = Image.open(path).convert("RGBA")
    im = im.resize((w, int(round(im.height * w / im.width))), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32); a[..., 3] /= 255
    return a

def _light_tile(inner, w, h, pad, r=None):
    """white rounded tile with `inner` (RGBA float) centred; used for dark marks / navy wordmarks."""
    r = r or int(min(w, h) * 0.24)
    m = rrect_mask(w, h, r)
    out = np.zeros((h, w, 4), np.float32); out[..., :3] = 250; out[..., 3] = m
    iw = w - 2 * pad; ih = h - 2 * pad
    s = min(iw / inner.shape[1], ih / inner.shape[0])
    inner = cv2.resize(inner, (max(int(inner.shape[1] * s), 1), max(int(inner.shape[0] * s), 1)), interpolation=cv2.INTER_AREA)
    y0 = (h - inner.shape[0]) // 2; x0 = (w - inner.shape[1]) // 2
    a = inner[..., 3:4]
    reg = out[y0:y0 + inner.shape[0], x0:x0 + inner.shape[1], :3]
    out[y0:y0 + inner.shape[0], x0:x0 + inner.shape[1], :3] = reg * (1 - a) + inner[..., :3] * a
    return out

@lru_cache(None)
def icon(name, size):
    """Square-ish brand icon, `size` px tall."""
    if name == "hiringcafe": return icon_sprite(f"{BRAND}/hiringcafe.png", size, tile=True)
    if name == "claude": return icon_sprite(f"{BRAND}/claude.png", size, tile=True)
    if name == "linkedin": return icon_sprite(f"{BRAND}/linkedin_512.png", size)
    if name == "sheets": return icon_sprite(f"{BRAND}/sheets.png", size)
    if name == "chatgpt": return _light_tile(_rgba(f"{BRAND}/chatgpt.png", 256), size, size, int(size * 0.17))
    if name == "indeed": return _light_tile(_rgba(f"{BRAND}/indeed_wordmark_800.png", 800), int(size * 2.3), size, int(size * 0.17), r=int(size * 0.24))
    raise KeyError(name)

def put_icon(dst, name, size, x, y, alpha=1.0, scale=1.0):
    spr = icon(name, size)
    if scale != 1.0:
        spr = cv2.resize(spr, None, fx=max(scale, 0.05), fy=max(scale, 0.05), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    over(dst, spr, x - (spr.shape[1] - icon(name, size).shape[1]) / 2, y - (spr.shape[0] - icon(name, size).shape[0]) / 2, alpha)
    return spr.shape[1], spr.shape[0]

# ---------------------------------------------------------------- small drawing helpers
def _sprite_from_L(L, color, glow=0.0, glow_r=4.0):
    a = np.clip(L, 0, 1)
    if glow > 0:
        g = cv2.GaussianBlur(a, (0, 0), glow_r) * glow
        a = np.clip(a + g * (1 - a), 0, 1)
    out = np.zeros(a.shape + (4,), np.float32); out[..., :3] = hexc(color) if isinstance(color, str) else color; out[..., 3] = a
    return out

def line_sprite(p0, p1, width, color, prog=1.0, glow=0.7, head=0, cap=True):
    """AA line from p0 to p1 drawn to `prog`; returns (rgba, x, y). Optional arrow head (px)."""
    x0, y0 = p0; x1, y1 = p1
    xe, ye = x0 + (x1 - x0) * prog, y0 + (y1 - y0) * prog
    pad = int(width * 3 + head + 8)
    bx0, by0 = int(min(x0, xe) - pad), int(min(y0, ye) - pad); bx1, by1 = int(max(x0, xe) + pad), int(max(y0, ye) + pad)
    w, h = bx1 - bx0, by1 - by0; ss = 3
    img = Image.new("L", (w * ss, h * ss), 0); d = ImageDraw.Draw(img)
    pts = [((x0 - bx0) * ss, (y0 - by0) * ss), ((xe - bx0) * ss, (ye - by0) * ss)]
    d.line(pts, fill=255, width=int(width * ss))
    if cap:
        for p in pts:
            r = width * ss / 2; d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)
    if head and prog > 0.98:
        ang = np.arctan2(y1 - y0, x1 - x0); hl = head * ss; hw = head * 0.62 * ss
        tip = pts[1]; b = (tip[0] - np.cos(ang) * hl, tip[1] - np.sin(ang) * hl)
        d.polygon([tip, (b[0] + np.sin(ang) * hw, b[1] - np.cos(ang) * hw), (b[0] - np.sin(ang) * hw, b[1] + np.cos(ang) * hw)], fill=255)
    L = np.asarray(img.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
    return _sprite_from_L(L, color, glow, max(width, 3)), bx0, by0

def put_line(dst, p0, p1, width, color, prog=1.0, alpha=1.0, glow=0.7, head=0, dashed=False):
    if prog <= 0: return
    if dashed:
        n = int(np.hypot(p1[0] - p0[0], p1[1] - p0[1]) // 18)
        for i in range(n):
            a0 = i / n; a1 = (i + 0.55) / n
            if a0 > prog: break
            q0 = (p0[0] + (p1[0] - p0[0]) * a0, p0[1] + (p1[1] - p0[1]) * a0)
            q1 = (p0[0] + (p1[0] - p0[0]) * min(a1, prog), p0[1] + (p1[1] - p0[1]) * min(a1, prog))
            s, x, y = line_sprite(q0, q1, width, color, 1.0, 0.0); over(dst, s, x, y, alpha)
        return
    s, x, y = line_sprite(p0, p1, width, color, prog, glow, head); over(dst, s, x, y, alpha)

def fill_sprite(w, h, r, color, alpha=1.0):
    m = rrect_mask(int(w), int(h), int(r))
    s = np.zeros((int(h), int(w), 4), np.float32); s[..., :3] = hexc(color) if isinstance(color, str) else color; s[..., 3] = m * alpha
    return s

def disc(dst, cx, cy, r, color, alpha=1.0):
    m = circle_mask(r); s = np.zeros(m.shape + (4,), np.float32); s[..., :3] = hexc(color); s[..., 3] = m
    over(dst, s, cx - m.shape[1] / 2, cy - m.shape[0] / 2, alpha)

def rule_text(dst, parts, size, cx, cy, alpha=1.0, weight=600, glow=0.4, hl_weight=800):
    """parts: [(text, is_key)] centred on cx; key parts are rose."""
    ws = [text_width(t, size, hl_weight if k else weight) for t, k in parts]
    x = cx - sum(ws) / 2
    for (t, k), w in zip(parts, ws):
        put_text(dst, t, size, x, cy, hl_weight if k else weight, color=(ROSE_HEX if k else WHITE_HEX), alpha=alpha, anchor="lm", glow=glow)
        x += w

# ---------------------------------------------------------------- UI glyphs (generic controls, not brand marks)
@lru_cache(None)
def glyph(kind, size):
    ss = 4; S = size * ss; img = Image.new("L", (S, S), 0); d = ImageDraw.Draw(img); u = S / 24
    P = lambda pts: [(x * u, y * u) for x, y in pts]
    if kind == "thumb":
        d.rounded_rectangle([2 * u, 10 * u, 6.5 * u, 22 * u], radius=1.2 * u, fill=255)
        d.polygon(P([(8.5, 10.5), (12, 2.5), (14.2, 2.5), (15, 4.5), (14, 9), (20.6, 9), (22, 10.8), (20.6, 21), (19.2, 22), (9, 22), (8.5, 21)]), fill=255)
    elif kind == "bubble":
        d.rounded_rectangle([2 * u, 3 * u, 22 * u, 17 * u], radius=3.5 * u, fill=255)
        d.polygon(P([(6, 16), (6, 22), (12, 16.5)]), fill=255)
    elif kind == "bell":
        d.pieslice([5 * u, 3 * u, 19 * u, 17 * u], 180, 360, fill=255)
        d.polygon(P([(5, 10), (19, 10), (20.5, 17), (3.5, 17)]), fill=255)
        d.ellipse([10 * u, 18 * u, 14 * u, 22 * u], fill=255)
    elif kind == "share":   # forward arrow
        d.polygon(P([(14, 3), (22.5, 11), (14, 19), (14, 14), (7, 15.5), (2, 20), (3.5, 12.5), (8, 9), (14, 8)]), fill=255)
    elif kind == "check":
        d.line(P([(4, 12.5), (9.5, 18), (20, 6)]), fill=255, width=int(3.2 * u), joint="curve")
    elif kind == "cross":
        d.line(P([(5, 5), (19, 19)]), fill=255, width=int(3.2 * u)); d.line(P([(19, 5), (5, 19)]), fill=255, width=int(3.2 * u))
    elif kind == "clock":
        d.ellipse([2 * u, 2 * u, 22 * u, 22 * u], outline=255, width=int(2.4 * u)); d.line(P([(12, 6.5), (12, 12.5), (16.5, 14.5)]), fill=255, width=int(2.4 * u))
    L = np.asarray(img.resize((size, size), Image.LANCZOS)).astype(np.float32) / 255
    return L

def put_glyph(dst, kind, size, cx, cy, color=WHITE_HEX, alpha=1.0, scale=1.0, glow=0.0):
    L = glyph(kind, size)
    spr = _sprite_from_L(L, color, glow, size * 0.12)
    if scale != 1.0: spr = cv2.resize(spr, None, fx=max(scale, 0.05), fy=max(scale, 0.05), interpolation=cv2.INTER_LINEAR)
    over(dst, spr, cx - spr.shape[1] / 2, cy - spr.shape[0] / 2, alpha)

def cursor(dst, x, y, alpha=1.0, press=0.0):
    ss = 4; S = 40; img = Image.new("L", (S * ss, S * ss), 0); d = ImageDraw.Draw(img)
    pts = [(2, 2), (2, 26), (8, 20.5), (12.5, 30), (16.5, 28), (12, 19), (20, 19)]
    d.polygon([(a * ss, b * ss) for a, b in pts], fill=255)
    L = np.asarray(img.resize((S, S), Image.LANCZOS)).astype(np.float32) / 255
    sh = cv2.GaussianBlur(L, (0, 0), 2.5) * 0.5
    spr = np.zeros((S, S, 4), np.float32); spr[..., :3] = 250; spr[..., 3] = L
    sp = np.zeros((S, S, 4), np.float32); sp[..., 3] = sh
    sc = 1.0 - 0.12 * press
    if sc != 1.0:
        spr = cv2.resize(spr, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR); sp = cv2.resize(sp, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
    over(dst, sp, x + 2, y + 3, alpha); over(dst, spr, x, y, alpha)

# ---------------------------------------------------------------- YouTube-style controls in theme colours
def like_button(dst, x, y, state, alpha=1.0, w=108, h=48):
    """state 0..1: 0 outline, 1 filled rose with white thumb. x,y = top-left."""
    glass(dst, x, y, w, h, alpha=alpha, r=h // 2, tint=0.78, blur=6, glow=4.0)
    if state > 0:
        over(dst, fill_sprite(w, h, h // 2, ROSE_HEX, 1.0), x, y, alpha * state)
    put_glyph(dst, "thumb", 24, x + 30, y + h / 2 - 1, WHITE_HEX, alpha, scale=1 + 0.25 * np.sin(np.pi * clamp(state * 1.0)) * (state < 1))
    put_text(dst, "Like", 17, x + 54, y + h / 2 + 1, 600, alpha=alpha, anchor="lm")

def comment_button(dst, x, y, alpha=1.0, w=146, h=48, state=0.0):
    glass(dst, x, y, w, h, alpha=alpha, r=h // 2, tint=0.78, blur=6, glow=4.0, highlight=state)
    put_glyph(dst, "bubble", 24, x + 30, y + h / 2, WHITE_HEX, alpha)
    put_text(dst, "Comment", 17, x + 54, y + h / 2 + 1, 600, alpha=alpha, anchor="lm")

def subscribe_pill(dst, x, y, state, alpha=1.0, w=232, h=56, press=0.0, bell=0.0):
    """state 0: SUBSCRIBE (raspberry fill) -> 1: Subscribed (outlined glass) with bell. x,y top-left."""
    sc = 1 - 0.06 * press
    ww, hh = int(w * sc), int(h * sc); xx, yy = x + (w - ww) / 2, y + (h - hh) / 2
    if state < 0.5:
        over(dst, fill_sprite(ww, hh, hh // 2, RASP_HEX, 1.0), xx, yy, alpha)
        ring = rrect_ring(ww, hh, hh // 2, 1.5, 8.0, 0.8, ROSE_HEX); over(dst, ring, xx - 24, yy - 24, alpha)
        put_text(dst, "SUBSCRIBE", 19, xx + ww / 2, yy + hh / 2 + 1, 800, alpha=alpha, anchor="cm")
    else:
        glass(dst, xx, yy, ww, hh, alpha=alpha, r=hh // 2, tint=0.78, blur=6, glow=6.0, highlight=1.0)
        put_glyph(dst, "check", 22, xx + 34, yy + hh / 2, ROSE_HEX, alpha)
        put_text(dst, "Subscribed", 18, xx + 54, yy + hh / 2 + 1, 700, alpha=alpha, anchor="lm")
        put_glyph(dst, "bell", 24, xx + ww - 30, yy + hh / 2 - 1, WHITE_HEX, alpha * clamp(bell * 4), scale=1.0)

def share_button(dst, x, y, state, alpha=1.0, w=150, h=52, press=0.0):
    sc = 1 - 0.06 * press
    ww, hh = int(w * sc), int(h * sc); xx, yy = x + (w - ww) / 2, y + (h - hh) / 2
    glass(dst, xx, yy, ww, hh, alpha=alpha, r=hh // 2, tint=0.78, blur=6, glow=5.0, highlight=state)
    if state > 0: over(dst, fill_sprite(ww, hh, hh // 2, RASP_HEX, 1.0), xx, yy, alpha * state * 0.85)
    put_glyph(dst, "share", 24, xx + 34, yy + hh / 2, WHITE_HEX, alpha)
    put_text(dst, "Share", 18, xx + 58, yy + hh / 2 + 1, 600, alpha=alpha, anchor="lm")

# ---------------------------------------------------------------- highlighter (rose underline sweep, in window space)
def underline(dst, x0, x1, y, prog, alpha=1.0, th=6.0, glow=0.55):
    if prog <= 0 or x1 - x0 < 2: return
    xe = x0 + (x1 - x0) * prog
    s, bx, by = line_sprite((x0 + th / 2, y), (max(xe - th / 2, x0 + th / 2 + 0.1), y), th, ROSE_HEX, 1.0, glow)
    over(dst, s, bx, by, alpha)

# ---------------------------------------------------------------- zoom path (rect interpolation)
IDENT = (0.0, 0.0, 1280.0, 720.0)
def rect_of(cx, cy, z):
    w, h = 1280.0 / z, 720.0 / z
    return (min(max(cx - w / 2, 0), 1280 - w), min(max(cy - h / 2, 0), 720 - h), w, h)

class ZoomPath:
    """Keyframed crop rectangles over the screen recording. `zoom(a, b, cx, cy, z)`: reaches full zoom at `a`
    (lands on the spoken word), holds to `b`, eases back by b+tout."""
    def __init__(self): self.k = []
    def zoom(self, a, b, cx, cy, z, tin=0.45, tout=0.45):
        r = rect_of(cx, cy, z); self.k += [(a - tin, IDENT), (a, r), (b, r), (b + tout, IDENT)]
    def path(self, pts, tin=0.45, tout=0.45):
        """pts: [(t, cx, cy, z)] - pans between held rectangles."""
        t0 = pts[0][0]; self.k.append((t0 - tin, IDENT))
        self.k += [(t, rect_of(cx, cy, z)) for t, cx, cy, z in pts]
        self.k.append((pts[-1][0] + tout, IDENT))
    def finish(self):
        self.k.sort(key=lambda kv: kv[0]); return self
    def rect(self, t):
        k = self.k
        if not k or t <= k[0][0] or t >= k[-1][0]: return IDENT
        lo, hi = 0, len(k) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if k[mid][0] <= t: lo = mid
            else: hi = mid
        (t0, r0), (t1, r1) = k[lo], k[hi]
        s = smoother((t - t0) / max(t1 - t0, 1e-6))
        return tuple(a + (b - a) * s for a, b in zip(r0, r1))
