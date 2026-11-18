"""Clean-creator drawing primitives (numpy float RGB canvas, 0-255)."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "brand/fonts/Montserrat.ttf")
FONT_I = os.path.join(ROOT, "brand/fonts/Montserrat-Italic.ttf")

def hexc(h): h = h.lstrip("#"); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], np.float32)
GROUND = hexc("#210A12"); RASP = hexc("#92205A"); DUSTY = hexc("#8C3D5D"); ROSE = hexc("#E25C8E")
WHITE = hexc("#FAF9F8"); BEZEL = hexc("#14070C")
W, H = 1280, 720

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smoother(x): x = clamp(x); return x * x * x * (x * (x * 6 - 15) + 10)
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x, s=1.2):
    x = clamp(x); x1 = x - 1; return 1 + (s + 1) * x1 ** 3 + s * x1 ** 2

# ---------- fonts / text ----------
@lru_cache(None)
def font(size, weight=400, italic=False):
    f = ImageFont.truetype(FONT_I if italic else FONT, size)
    f.set_variation_by_axes([weight])
    return f

def rich_segments(text, size, weight, bold_weight=800):
    """'a **b** c' -> [(str, font)]"""
    parts = text.split("**"); segs = []
    for i, p in enumerate(parts):
        if p: segs.append((p, font(size, bold_weight if i % 2 else weight)))
    return segs

def text_width(text, size, weight=400, bold_weight=800):
    return sum(f.getlength(s) for s, f in rich_segments(text, size, weight, bold_weight))

def wrap(text, size, weight, maxw, bold_weight=800):
    words = text.split(" "); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_width(t.replace("**", "") if t.count("**") % 2 else t, size, weight, bold_weight) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    # balance '**' across lines
    out = []; open_ = False
    for l in lines:
        if open_: l = "**" + l
        if l.count("**") % 2: l = l + "**"; open_ = True
        else: open_ = False
        out.append(l)
    return out

@lru_cache(None)
def text_sprite(text, size, weight=400, color="#FAF9F8", glow=0.0, italic=False, bold_weight=800, align="left", maxw=0, leading=1.25):
    """Returns RGBA uint8 array (premultiplied-free) with optional soft glow. Padding 24px."""
    lines = wrap(text, size, weight, maxw, bold_weight) if maxw else [text]
    pad = max(24, int(size * 0.22 * 3.2)) if glow > 0 else 24
    widths = [text_width(l, size, weight, bold_weight) for l in lines] if not italic else [font(size, weight, True).getlength(l) for l in lines]
    lh = int(size * leading)
    w = int(max(widths)) + pad * 2 + 4; h = lh * len(lines) + pad * 2
    img = Image.new("L", (w, h), 0); d = ImageDraw.Draw(img)
    y = pad
    for l, lw in zip(lines, widths):
        x = pad + (0 if align == "left" else (max(widths) - lw) / 2 if align == "center" else max(widths) - lw)
        if italic:
            d.text((x, y), l, font=font(size, weight, True), fill=255)
        else:
            for s, f in rich_segments(l, size, weight, bold_weight):
                d.text((x, y), s, font=f, fill=255); x += f.getlength(s)
        y += lh
    a = np.asarray(img).astype(np.float32) / 255
    col = hexc(color)
    rgba = np.zeros((h, w, 4), np.float32); rgba[..., :3] = col; rgba[..., 3] = a
    if glow > 0:
        g = cv2.GaussianBlur(a, (0, 0), size * 0.22) * glow
        alpha = np.clip(a + g * (1 - a), 0, 1)
        rgba[..., 3] = alpha
    return rgba, pad

def over(dst, rgba, x, y, alpha=1.0):
    """Alpha-composite float RGBA sprite (straight alpha) onto float RGB dst at integer-ish x,y."""
    if alpha <= 0.001: return
    h, w = rgba.shape[:2]
    x = int(round(x)); y = int(round(y))
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0: return
    s = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] * alpha
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a

def put_text(dst, text, size, x, y, weight=400, color="#FAF9F8", alpha=1.0, glow=0.0, anchor="lt", maxw=0, italic=False, align="left", bold_weight=800, scale=1.0):
    rgba, pad = text_sprite(text, size, weight, color, glow, italic, bold_weight, align, maxw)
    if scale != 1.0:
        rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR); pad = pad * scale
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
def rrect_ring(w, h, r, width=1.5, glow=8.0, glow_alpha=0.75, color="#92205A", glow_color=None, margin=24):
    """RGBA sprite of outline + outer glow for a w x h rounded rect, offset by -margin."""
    ss = 4; W2, H2 = w + 2 * margin, h + 2 * margin
    img = Image.new("L", (W2 * ss, H2 * ss), 0)
    ImageDraw.Draw(img).rounded_rectangle([margin * ss, margin * ss, (margin + w) * ss - 1, (margin + h) * ss - 1],
                                          radius=r * ss, outline=255, width=max(1, int(width * ss)))
    line = np.asarray(img.resize((W2, H2), Image.LANCZOS)).astype(np.float32) / 255
    g = cv2.GaussianBlur(line, (0, 0), glow) * glow_alpha * 3.0 if glow > 0 else 0 * line
    g = np.clip(g, 0, glow_alpha)
    col = hexc(color); gcol = hexc(glow_color or color)
    a = np.clip(line + g * (1 - line), 0, 1)
    rgb = (col * line[..., None] + gcol * (g * (1 - line))[..., None]) / np.maximum(a[..., None], 1e-4)
    out = np.zeros((H2, W2, 4), np.float32); out[..., :3] = rgb; out[..., 3] = a
    return out

@lru_cache(None)
def circle_mask(r, ss=4):
    d = int(np.ceil(2 * r)) + 2
    img = Image.new("L", (d * ss, d * ss), 0)
    c = d * ss / 2
    ImageDraw.Draw(img).ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], fill=255)
    return np.asarray(img.resize((d, d), Image.LANCZOS)).astype(np.float32) / 255

@lru_cache(None)
def circle_ring(r, width=2.0, glow=5.0, glow_alpha=0.7, color="#92205A", glow_color="#B5306F", margin=18):
    ss = 4; d = int(np.ceil(2 * r)) + 2 * margin
    img = Image.new("L", (d * ss, d * ss), 0); c = d * ss / 2
    ImageDraw.Draw(img).ellipse([c - r * ss, c - r * ss, c + r * ss, c + r * ss], outline=255, width=max(1, int(width * ss)))
    line = np.asarray(img.resize((d, d), Image.LANCZOS)).astype(np.float32) / 255
    g = np.clip(cv2.GaussianBlur(line, (0, 0), glow) * glow_alpha * 3.0, 0, glow_alpha)
    col = hexc(color); gcol = hexc(glow_color)
    a = np.clip(line + g * (1 - line), 0, 1)
    rgb = (col * line[..., None] + gcol * (g * (1 - line))[..., None]) / np.maximum(a[..., None], 1e-4)
    out = np.zeros((d, d, 4), np.float32); out[..., :3] = rgb; out[..., 3] = a
    return out, d / 2

def make_ground():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bg = np.empty((H, W, 3), np.float32); bg[:] = GROUND
    # soft orb, top-right corner, raspberry -> dusty rose
    d = np.sqrt((xx - 1180) ** 2 + (yy - 40) ** 2)
    a = np.clip(1 - d / 760, 0, 1) ** 2.2 * 0.55
    orb = RASP * (1 - np.clip(d / 760, 0, 1))[..., None] + DUSTY * np.clip(d / 760, 0, 1)[..., None]
    bg = bg * (1 - a[..., None]) + orb * a[..., None]
    # second faint orb bottom-left
    d2 = np.sqrt((xx - 60) ** 2 + (yy - 760) ** 2)
    a2 = np.clip(1 - d2 / 620, 0, 1) ** 2.4 * 0.22
    bg = bg * (1 - a2[..., None]) + RASP * a2[..., None]
    # very low-contrast grid
    grid = ((xx % 64 < 1) | (yy % 64 < 1)).astype(np.float32) * 0.035
    bg = bg * (1 - grid[..., None]) + WHITE * grid[..., None]
    return bg

def glass(dst, x, y, w, h, alpha=1.0, r=22, tint=0.62, blur=14, border_color="#92205A", glow=7.0, highlight=0.0):
    x, y, w, h = int(round(x)), int(round(y)), int(w), int(h)
    if alpha <= 0.001: return
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0: return
    region = dst[y0:y1, x0:x1]
    b = cv2.GaussianBlur(region, (0, 0), blur)
    b = b * (1 - tint) + GROUND * tint
    m = rrect_mask(w, h, r)[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * alpha
    dst[y0:y1, x0:x1] = region * (1 - m) + b * m
    ring = rrect_ring(w, h, r, 1.5, glow, 0.75, border_color)
    over(dst, ring, x - 24, y - 24, alpha)
    if highlight > 0:
        ring2 = rrect_ring(w, h, r, 2.0, 10.0, 0.9, "#E25C8E")
        over(dst, ring2, x - 24, y - 24, alpha * highlight)

def check_badge(dst, cx, cy, r, prog, alpha=1.0):
    """outlined glowing circle with a rose check that pops in with prog (0..1)."""
    ring, c = circle_ring(r, 1.5, 4.0, 0.6, "#92205A", "#92205A")
    over(dst, ring, cx - c, cy - c, alpha)
    if prog > 0:
        s = ease_back(prog, 1.4)
        spr = check_sprite(r)
        if s != 1:
            spr = cv2.resize(spr, None, fx=max(s, 0.05), fy=max(s, 0.05), interpolation=cv2.INTER_LINEAR)
        hh, ww = spr.shape[:2]
        over(dst, spr, cx - ww / 2, cy - hh / 2, alpha * clamp(prog * 3))

@lru_cache(None)
def check_sprite(r):
    ss = 4; d = int(2 * r + 16)
    img = Image.new("L", (d * ss, d * ss), 0); dr = ImageDraw.Draw(img); c = d * ss / 2
    pts = [(c - 0.5 * r * ss, c + 0.02 * r * ss), (c - 0.12 * r * ss, c + 0.42 * r * ss), (c + 0.58 * r * ss, c - 0.42 * r * ss)]
    dr.line(pts, fill=255, width=int(r * 0.26 * ss), joint="curve")
    for p in (pts[0], pts[2]):
        e = r * 0.13 * ss; dr.ellipse([p[0] - e, p[1] - e, p[0] + e, p[1] + e], fill=255)
    a = np.asarray(img.resize((d, d), Image.LANCZOS)).astype(np.float32) / 255
    g = np.clip(cv2.GaussianBlur(a, (0, 0), 3) * 0.8, 0, 1)
    al = np.clip(a + g * (1 - a), 0, 1)
    out = np.zeros((d, d, 4), np.float32); out[..., :3] = ROSE; out[..., 3] = al
    return out

def num_badge(dst, cx, cy, r, n, fill=0.0, alpha=1.0, active=0.0, scale=1.0):
    rr = r * scale
    if fill > 0 or active > 0:
        m = circle_mask(rr); c = m.shape[0] / 2
        col = RASP * (1 - active) + ROSE * active
        spr = np.zeros(m.shape + (4,), np.float32); spr[..., :3] = col; spr[..., 3] = m
        over(dst, spr, cx - c, cy - c, alpha * max(fill, active))
    ring, c = circle_ring(int(round(rr)), 2.0, 6.0 if active else 4.0, 0.8 if active else 0.55,
                          "#E25C8E" if active else "#92205A", "#E25C8E" if active else "#92205A")
    over(dst, ring, cx - c, cy - c, alpha)
    put_text(dst, str(n), int(round(18 * scale)), cx, cy + 1, 700, alpha=alpha, anchor="cm")

def icon_sprite(path, size, tile=False):
    im = Image.open(path).convert("RGBA")
    im.thumbnail((size * 4, size * 4), Image.LANCZOS)
    im = im.resize((int(im.width * size / max(im.size)), int(im.height * size / max(im.size))), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    out = np.zeros_like(a); out[..., :3] = a[..., :3]; out[..., 3] = a[..., 3] / 255
    if tile:  # round the corners of a square app icon (radius ~24%)
        m = rrect_mask(out.shape[1], out.shape[0], int(0.24 * size))
        out[..., 3] *= m
    return out
