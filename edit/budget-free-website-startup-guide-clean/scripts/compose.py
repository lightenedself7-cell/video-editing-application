"""Single-pass compositor for budget-free-website-startup-guide-clean (clean-creator theme).

Usage: compose.py <first_frame> <last_frame_exclusive> <out.mp4> [--png frameN ...]
Reads the locked source, applies the approved editorial-directive.json, writes an H.264 chunk (no audio).
"""
import json, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, "editorial-directive.json")))
SRC = D["source"]["path"]; FPS = 30; NFR = 21881
BEATS = {b["id"]: b for b in D["beats"]}
BRAND = os.path.join(ROOT, "brand")

# ---------- source structure ----------
SCREEN_FR = [(2347, 2836), (3715, 8699), (11100, 20924)]
def is_screen(n): return any(a <= n < b for a, b in SCREEN_FR)
CIRC = {"A": (92.6, 625.4, 90.9), "B": (131.5, 584.3, 127.6), "C": (106.6, 611.6, 98.0), "D": (211.1, 508.0, 149.6),
        "E": (1135.0, 459.0, 107.8), "F": (1129.0, 555.0, 130.7), "G": (158.1, 557.0, 133.6), "H": (125.0, 593.0, 116.6),
        "I": (115.9, 602.0, 107.6), "J": (108.5, 609.5, 100.0)}
_bf = json.load(open(os.path.join(ROOT, "reports/bubble_frames.json")))
BUB = {}
for t, k, s in _bf: BUB[int(round(t * FPS))] = k
def bubble_at(n):
    if not is_screen(n): return None
    for d in (0, -1, 1, -2, 2, -3, 3):
        k = BUB.get(n + d, "missing")
        if k != "missing" and k is not None: return CIRC[k]
        if k is None and d == 0:
            # real absence (e.g. 513-527 s) when neighbours agree
            if BUB.get(n - 3) is None and BUB.get(n + 3) is None: return None
    return None

# ---------- static layers ----------
GROUND_IMG = make_ground()
SF = 0.9; SX, SY, SW, SH = 64, 36, 1152, 648
SCREEN_MASK = rrect_mask(SW, SH, 22)[..., None]
SCREEN_RING = rrect_ring(SW, SH, 22, 1.5, 9.0, 0.8, "#92205A")
SCREEN_BASE = GROUND_IMG.copy(); over(SCREEN_BASE, SCREEN_RING, SX - 24, SY - 24)

ICON = {"WhatsApp": icon_sprite(f"{BRAND}/whatsapp.png", 24), "Google AI Studio": icon_sprite(f"{BRAND}/ai_studio.png", 24),
        "Cloudflare": icon_sprite(f"{BRAND}/cloudflare.png", 30), "Amazon": icon_sprite(f"{BRAND}/amazon_touch.png", 54, tile=True),
        "CloudflareBig": icon_sprite(f"{BRAND}/cloudflare.png", 74)}

def T(t): return t  # seconds

# ---------- bubble ----------
def draw_bubble(dst, S, circ, cx_out, cy_out, scale):
    cx, cy, r = circ
    R = r * scale
    pad = 3
    x0, y0 = int(np.floor(cx - r - pad)), int(np.floor(cy - r - pad)); x1, y1 = int(np.ceil(cx + r + pad)), int(np.ceil(cy + r + pad))
    sx0, sy0, sx1, sy1 = max(x0, 0), max(y0, 0), min(x1, 1280), min(y1, 720)
    crop = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
    crop[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = S[sy0:sy1, sx0:sx1]
    # warp so circle centre lands on (cx_out, cy_out) at given scale (sub-pixel)
    M = np.float32([[scale, 0, cx_out - scale * (cx - x0)], [0, scale, cy_out - scale * (cy - y0)]])
    bx0, by0 = int(np.floor(cx_out - R - 2)), int(np.floor(cy_out - R - 2)); bw, bh = int(2 * R + 5), int(2 * R + 5)
    M[0, 2] -= bx0; M[1, 2] -= by0
    patch = cv2.warpAffine(crop, M, (bw, bh), flags=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    d = np.sqrt((xx + bx0 + 0.5 - cx_out) ** 2 + (yy + by0 + 0.5 - cy_out) ** 2)
    m = np.clip(R - 0.6 - d + 0.5, 0, 1)  # 1px AA edge, a hair inside the source edge
    spr = np.zeros((bh, bw, 4), np.float32); spr[..., :3] = patch; spr[..., 3] = m
    over(dst, spr, bx0, by0)
    ring, c = circle_ring(int(round(R)), 2.0, 5.0, 0.7, "#92205A", "#B5306F")
    over(dst, ring, cx_out - c, cy_out - c)

def framed_screen(S, n):
    out = SCREEN_BASE.copy()
    sm = cv2.resize(S, (SW, SH), interpolation=cv2.INTER_AREA)
    reg = out[SY:SY + SH, SX:SX + SW]
    out[SY:SY + SH, SX:SX + SW] = reg * (1 - SCREEN_MASK) + sm * SCREEN_MASK
    # border glow over the picture edge too (outline sits on the edge)
    over(out, SCREEN_RING, SX - 24, SY - 24)
    c = bubble_at(n)
    if c: draw_bubble(out, S, c, SX + c[0] * SF, SY + c[1] * SF, SF)
    return out

# ---------- camera punch-ins ----------
PUNCH = []
for b in D["beats"]:
    for p in b.get("punch_ins", []): PUNCH.append((p["in"], p["out"], p["scale"]))
def punch(S, t):
    for a, b, s in PUNCH:
        if a <= t < b:
            cw, ch = 1280 / s, 720 / s
            x0 = 640 - cw / 2 - 8; y0 = 18
            M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
            return cv2.warpAffine(S, M, (1280, 720), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return S

def base_frame(S, n):
    t = n / FPS
    return framed_screen(S, n) if is_screen(n) else punch(S, t).copy()

# ---------- helpers ----------
ENTER = 12 / FPS; EXIT = 10 / FPS
def env(t, a, b, ein=ENTER, eout=EXIT):
    """entrance progress, exit progress"""
    return ease_out((t - a) / ein), ease_out((b - t) / eout)

def reveal(t, cue, lead=0.25, dur=12 / FPS):
    return ease_out((t - (cue - lead)) / dur)

# ---------- OVERLAY_CARD on camera: glass card ----------
CARD_SPEC = {
    "b02": [("Instant on **mobile**", 7.72, None), ("Book on **WhatsApp**", 10.12, "WhatsApp"), ("**$0** hosting", 12.22, None), ("Domain under **$10** / year", 18.28, None)],
    "b06": [("**Rooms**", 62.74, None), ("**Rates**", 63.84, None), ("**WhatsApp** or call", 65.74, None)],
    "b26": [("**25 MiB** file limit", 361.26, None), ("Upload **failed**", 363.30, None)],
}
def card_layout(bid):
    rows = CARD_SPEC[bid]; x, w = 976, 280; pad = 22; tx = 40; maxw = w - pad - tx - 12
    hs = []
    for txt, cue, ic in rows:
        lines = wrap(txt, 20, 400, maxw); hs.append(len(lines) * 25)
    top_extra = 74 if bid == "b26" else 0
    h = pad * 2 + top_extra + sum(hs) + 16 * (len(rows) - 1)
    y = 340 - h / 2
    return x, y, w, h, hs, top_extra, maxw

def draw_card(out, bid, t):
    b = BEATS[bid]; a, e = b["start"], b["end"]
    pin, pout = env(t, a, e, 14 / FPS, 12 / FPS)
    k = min(pin, pout)
    if k <= 0: return
    x, y, w, h, hs, top_extra, maxw = card_layout(bid)
    dx = (1 - k) * 60
    glass(out, x + dx, y, w, h, alpha=k)
    yy = y + 22
    if bid == "b26":
        p = reveal(t, 357.88)
        ic = ICON["CloudflareBig"]
        over(out, ic, x + dx + 22 + (1 - p) * 14, yy + 4, p * k)
        put_text(out, "Cloudflare", 15, x + dx + 22 + 82 + (1 - p) * 14, yy + 20, 500, alpha=p * k * 0.85)
        yy += top_extra
    for (txt, cue, ic), hh in zip(CARD_SPEC[bid], hs):
        p = reveal(t, cue)
        if p > 0:
            ox = x + dx + 22 + (1 - p) * 18
            if ic:
                over(out, ICON[ic], ox, yy + 1, p * k)
            else:
                m = circle_mask(4.5); s = np.zeros(m.shape + (4,), np.float32); s[..., :3] = ROSE; s[..., 3] = m
                over(out, s, ox + 8, yy + 8, p * k)
            put_text(out, txt, 20, ox + 40, yy, 400, alpha=p * k, maxw=maxw, bold_weight=750)
        yy += hh + 16

# ---------- chips over screens ----------
CHIP_SPEC = {"b12": ("Google AI Studio", 124.60, "Google AI Studio", None), "b14": ("Reality check", 192.52, None, None),
             "b16": ("Real photos", 215.88, None, 1), "b18": ("Distances", 227.62, None, 2), "b20": ("Booking button", 249.68, None, 3),
             "b36": ("Cloudflare Drop", 528.10, "Cloudflare", None), "b39": ("Open on your phone, tap every button", 573.88, None, None),
             "b39c": ("Check every room, rate, number", 591.12, None, None), "b41": ("Under **$10** / year", 613.52, None, None),
             "b43": ("Wholesale, **zero markup**", 631.32, None, None)}
def draw_chip(out, bid, t):
    b = BEATS[bid]; txt, cue, ic, num = CHIP_SPEC[bid]
    start = cue - 0.25
    pin = ease_out((t - start) / ENTER); pout = ease_out((b["end"] - t) / EXIT)
    k = min(pin, pout)
    if k <= 0: return
    L = b["layout"]; right = L["x"] + L["width"]
    lead = 40 if (ic or num) else 16
    maxw = L["width"] - lead - 16
    lines = wrap(txt, 16, 500, maxw)
    tw = max(text_width(l, 16, 500, 750) for l in lines)
    w = int(lead + tw + 18); h = 22 + 20 * len(lines)
    x = right - w + (1 - k) * 24; y = L["y"] + 2
    glass(out, x, y, w, h, alpha=k, r=h // 2 if len(lines) == 1 else 16, tint=0.80, blur=8, glow=5.0)
    cy = y + h / 2
    if ic: over(out, ICON[ic], x + 12, cy - ICON[ic].shape[0] / 2, k)
    if num: num_badge(out, x + 22, cy, 12, num, fill=1.0, alpha=k, scale=0.82)
    put_text(out, txt, 16, x + lead, cy, 500, alpha=k, anchor="lm", maxw=maxw, bold_weight=750)

# ---------- selective text ----------
def draw_keyword(out, t):
    b = BEATS["b04"]; cue = 44.32
    p = clamp((t - (cue - 0.15)) / (10 / FPS)); pout = ease_out((b["end"] - t) / (8 / FPS))
    if p <= 0 or pout <= 0: return
    s = 0.9 + 0.1 * ease_back(p, 1.6)
    a = clamp(p * 2) * pout
    put_text(out, "under", 24, 1112, 268, 300, alpha=a, anchor="cm", scale=s)
    put_text(out, "2 HOURS", 46, 1112, 312, 800, alpha=a, anchor="cm", glow=0.5, scale=s)

def question_beat(out, t):
    b = BEATS["b23"]
    k = min(smoother((t - b["start"]) / (10 / FPS)), smoother((b["end"] - t) / (10 / FPS)))
    if k <= 0: return out
    bl = cv2.GaussianBlur(out, (0, 0), 6 * k + 0.01)
    out = bl * (1 - 0.45 * k)
    p = reveal(t, 294.42) * min(1, smoother((b["end"] - t) / (10 / FPS)))
    put_text(out, "No limits: what kind of site does AI **build**?", 28, 640, 644 + (1 - p) * 8, 300, alpha=p, anchor="cm", bold_weight=800)
    return out

# ---------- presenter inset (column / window) ----------
MOVE_IN = 33 / FPS; MOVE_OUT = 23 / FPS
COL = (32, 32, 368, 656); COL_SRC_CX = 610.0
WIN = (48, 120, 768, 432)
def inset_progress(t, a, e):
    return min(smoother((t - a) / MOVE_IN), smoother((e - t) / MOVE_OUT))

def place_presenter(out_bg, S, p, dest, src_cx=None):
    """p in 0..1; dest = final rect. column: src height 720 constant; window: full frame."""
    if p <= 0: return S.copy(), False
    dx, dy, dw, dh = [0 + (v1 - v0) * p + v0 for v0, v1 in zip((0, 0, 1280, 720), dest)]
    if src_cx is not None:
        sw = 720 * dw / dh; scx = 640 + (src_cx - 640) * p
        sx0 = scx - sw / 2; sy0 = 0; sh = 720
    else:
        sx0, sy0, sw, sh = 0, 0, 1280, 720
    s = dw / sw
    out = out_bg.copy()
    X0, Y0 = int(np.floor(dx)), int(np.floor(dy)); X1, Y1 = int(np.ceil(dx + dw)), int(np.ceil(dy + dh))
    M = np.float32([[s, 0, dx - sx0 * s - X0], [0, s, dy - sy0 * s - Y0]])
    patch = cv2.warpAffine(S, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    r = 24 * p
    m = rrect_mask(X1 - X0, Y1 - Y0, max(int(round(r)), 0))[..., None] if r >= 0.5 else np.ones((Y1 - Y0, X1 - X0, 1), np.float32)
    reg = out[Y0:Y1, X0:X1]
    out[Y0:Y1, X0:X1] = reg * (1 - m) + patch * m
    if p > 0.02:
        ring = rrect_ring(X1 - X0, Y1 - Y0, max(int(round(r)), 1), 1.5, 8.0, 0.75, "#92205A")
        over(out, ring, X0 - 24, Y0 - 24, p)
    return out, True

COLUMN_ROWS = {
    "b09": dict(title=("PREP", 117.40 - 17.0), rows=[("Real photos", 95.74), ("About **2 hours**", 101.30), ("Domain price", 102.20),
                                                     ("Missing info? **Leave it out**", 110.98), ("The prep is the **work**", 117.40)]),
}
def draw_column_list(out, bid, t, gk):
    spec = COLUMN_ROWS[bid]; b = BEATS[bid]
    landed = b["start"] + MOVE_IN
    tp = ease_out((t - landed) / ENTER)
    put_text(out, "PREP", 52, 460, 70 + (1 - tp) * 10, 800, alpha=tp * gk, glow=0.55)
    y = 158
    for i, (txt, cue) in enumerate(spec["rows"]):
        p = reveal(t, max(cue, landed + 0.3))
        last = i == len(spec["rows"]) - 1
        if p > 0:
            x = 456 + (1 - p) * 28
            glass(out, x, y, 776, 72, alpha=p * gk, r=20, highlight=(1.0 if last else 0.0))
            check_badge(out, x + 40, y + 36, 15, clamp((t - cue) / (8 / FPS)), alpha=p * gk)
            put_text(out, txt, 24, x + 76, y + 36, 600 if last else 400, alpha=p * gk, anchor="lm", bold_weight=800)
        y += 72 + 14

def draw_compare(out, t, gk):
    b = BEATS["b24"]; landed = b["start"] + MOVE_IN
    p0 = reveal(t, max(303.6, landed + 0.1))
    put_text(out, "TWO KINDS OF SITES", 40, 456, 64 + (1 - p0) * 10, 800, alpha=p0 * gk, glow=0.5)
    hl = smoother((t - 344.66) / (14 / FPS))
    for i, (name, cue) in enumerate((("DYNAMIC", 305.14), ("STATIC", 306.06))):
        p = reveal(t, cue)
        if p <= 0: continue
        x = 456 + i * 396 + (1 - p) * 24; y = 132
        glass(out, x, y, 380, 384, alpha=p * gk, r=24, highlight=(hl if i == 0 else 0.0))
        put_text(out, name, 30, x + 28, y + 26, 800, alpha=p * gk, glow=0.45, color=("#FAF9F8"))
    # dynamic lines
    x = 456 + 28; y = 132
    rows = [((x, y + 92), "Knows **who you are**", 307.20), ((x, y + 278), "Server + **database**", 323.0)]
    rows_s = [((852 + 28, y + 92), "A **brochure**: same page for everyone", 328.98), ((852 + 28, y + 190), "Enough for a **small hotel**", 335.42)]
    for (px, py), txt, cue in rows + rows_s:
        p = reveal(t, cue)
        if p > 0: put_text(out, txt, 21, px + (1 - p) * 16, py, 400, alpha=p * gk, maxw=324, bold_weight=750)
    p = reveal(t, 311.10)
    if p > 0:
        over(out, ICON["Amazon"], x + (1 - p) * 16, y + 178, p * gk)
        put_text(out, "Amazon", 18, x + 70 + (1 - p) * 16, y + 205, 500, alpha=p * gk * 0.9, anchor="lm")
    p = reveal(t, 344.66)
    if p > 0:
        glass(out, 456, 536 + (1 - p) * 12, 776, 64, alpha=p * gk, r=32, highlight=1.0)
        put_text(out, "No limits → a full **React app**", 24, 456 + 388, 568 + (1 - p) * 12, 500, alpha=p * gk, anchor="cm", bold_weight=800)

RECAP_ROWS = [("**$0** hosting fees", 702.58), ("Built for under **$10**", 705.34), ("Prompts in the **pinned comment**", 711.02)]
def draw_recap(out, t, gk):
    b = BEATS["b48"]; landed = b["start"] + MOVE_IN
    pc = ease_out((t - landed) / (14 / FPS))
    put_text(out, "A budget-free website, start to finish", 20, 48 + 384, 580 + (1 - pc) * 6, 300, alpha=pc * gk * 0.92, anchor="ct", italic=True)
    put_text(out, "RECAP", 34, 860, 130 + (1 - pc) * 8, 800, alpha=pc * gk, glow=0.5)
    y = 196
    for txt, cue in RECAP_ROWS:
        p = reveal(t, max(cue, landed + 0.2))
        if p > 0:
            x = 860 + (1 - p) * 24
            glass(out, x, y, 380, 92, alpha=p * gk, r=20)
            check_badge(out, x + 40, y + 46, 17, clamp((t - cue) / (8 / FPS)), alpha=p * gk)
            put_text(out, txt, 21, x + 76, y + 46, 400, alpha=p * gk, anchor="lm", maxw=280, bold_weight=750)
        y += 92 + 18

def inset_frame(S, t, bid):
    b = BEATS[bid]; a, e = b["start"], b["end"]
    p = inset_progress(t, a, e)
    dest, scx = (COL, COL_SRC_CX) if bid in ("b09", "b24") else (WIN, None)
    out, moved = place_presenter(GROUND_IMG, S, p, dest, scx)
    if not moved: return out
    # graphics: wait for landing, leave before the return move
    gk = min(1.0, ease_out((e - MOVE_OUT - t) / (8 / FPS))) if t > e - MOVE_OUT - 8 / FPS else 1.0
    gk = max(gk, 0.0)
    if t >= a + MOVE_IN and gk > 0:
        if bid == "b09": draw_column_list(out, bid, t, gk)
        elif bid == "b24": draw_compare(out, t, gk)
        else: draw_recap(out, t, gk)
    return out

# ---------- full-screen panels ----------
ROAD = ["Prep", "Build", "Go static", "Mobile check", "Go live", "Speed check"]
NX = [160 + i * 192 for i in range(6)]; NY = 430
def roadmap_panel(bid, t):
    b = BEATS[bid]; rm = b["roadmap"]; cue = b["reveal_sync"][0]["time"]
    active = rm["active"]; first = bid == "b07"; final = active == "all"
    P = GROUND_IMG.copy()
    landed = b["start"] + 15 / FPS
    # title
    title = "THE ENTIRE PROCESS" if final else ROAD[active - 1].upper()
    pt = reveal(t, cue)
    put_text(P, title, 60, 640, 236 + (1 - pt) * 12, 800, alpha=pt, anchor="cm", glow=0.6)
    # path
    for i in range(6):
        appear = 1.0 if not first else ease_out((t - (landed + 0.08 * i)) / (8 / FPS))
        if i < 5 and appear > 0:
            x0, x1 = NX[i] + 34, NX[i + 1] - 34
            seg = np.zeros((6, x1 - x0, 4), np.float32); seg[..., :3] = RASP; seg[2:4, :, 3] = 0.7
            seg[..., 3] = cv2.GaussianBlur(seg[..., 3], (0, 0), 1.0)
            over(P, seg, x0, NY - 3, appear)
            # lit segment: segments leading to the active node
            tgt = 6 if final else active
            if i + 1 < tgt:
                lit = 1.0 if (not final and i + 1 < tgt - 1) else smoother((t - (cue - 0.2 + (0.07 * i if final else 0))) / (12 / FPS))
                if lit > 0:
                    L = int((x1 - x0) * lit)
                    if L > 1:
                        s2 = np.zeros((14, L, 4), np.float32); s2[..., :3] = ROSE
                        core = np.zeros((14, L), np.float32); core[6:8] = 1.0
                        s2[..., 3] = np.clip(core + cv2.GaussianBlur(core, (0, 0), 3) * 1.5, 0, 1)
                        over(P, s2, x0, NY - 7)
    for i in range(6):
        appear = 1.0 if not first else ease_out((t - (landed + 0.08 * i)) / (8 / FPS))
        if appear <= 0: continue
        n = i + 1
        if final:
            on = clamp((t - (cue - 0.1 + 0.07 * i)) / (8 / FPS))
            num_badge(P, NX[i], NY, 28, n, fill=1.0, alpha=appear, active=on, scale=0.85 + 0.15 * ease_back(on) if on > 0 else 1.0)
            la = 0.6 + 0.4 * on; lw = 600
        elif n < active:
            num_badge(P, NX[i], NY, 28, n, fill=1.0, alpha=appear); la, lw = 0.75, 400
        elif n == active:
            on = clamp((t - (cue - 0.1)) / (10 / FPS))
            num_badge(P, NX[i], NY, 28, n, fill=0.0, alpha=appear, active=on, scale=(0.8 + 0.2 * ease_back(on)) if on > 0 else 1.0)
            la, lw = 0.6 + 0.4 * on, (700 if on > 0.5 else 400)
        else:
            num_badge(P, NX[i], NY, 28, n, fill=0.0, alpha=appear * 0.8); la, lw = 0.5, 400
        put_text(P, ROAD[i], 19, NX[i], NY + 52, lw, alpha=appear * la, anchor="ct")
    return P

PHONE = {"b30": ("LOOK AT IT\nON A PHONE", 395.7), "b32": ("AFTER\nTHE FIX", 430.04)}
PH_CROP = (596, 176, 314, 510); PH_S = 1.2
def phone_panel(bid, S, t):
    P = GROUND_IMG.copy()
    title, cue = PHONE[bid]
    sx, sy, sw, sh = PH_CROP
    scr = cv2.resize(S[sy:sy + sh, sx:sx + sw], (int(sw * PH_S), int(sh * PH_S)), interpolation=cv2.INTER_CUBIC)
    h, w = scr.shape[:2]; cx, cy = 470, 360
    bez = 11
    ox, oy = cx - w / 2 - bez, cy - h / 2 - bez
    ow, oh = w + 2 * bez, h + 2 * bez
    # body
    m = rrect_mask(int(ow), int(oh), 46)
    body = np.zeros((int(oh), int(ow), 4), np.float32); body[..., :3] = BEZEL; body[..., 3] = m
    over(P, body, ox, oy)
    ring = rrect_ring(int(ow), int(oh), 46, 1.5, 10.0, 0.85, "#92205A")
    over(P, ring, ox - 24, oy - 24)
    ms = rrect_mask(w, h, 34)
    spr = np.zeros((h, w, 4), np.float32); spr[..., :3] = scr; spr[..., 3] = ms
    over(P, spr, cx - w / 2, cy - h / 2)
    # speaker slot
    sl = rrect_mask(54, 5, 2); s2 = np.zeros((5, 54, 4), np.float32); s2[..., :3] = hexc("#3A1A26"); s2[..., 3] = sl
    over(P, s2, cx - 27, oy + 3)
    # title
    p = reveal(t, cue)
    for j, line in enumerate(title.split("\n")):
        put_text(P, line, 46, 760, 150 + j * 56 + (1 - p) * 10, 800, alpha=p, glow=0.55)
    # presenter bubble (live, from the recording), bottom-right
    draw_bubble(P, S, CIRC["F"], 1088, 548, 0.9)
    return P

def fullscreen_frame(base, S, t, bid):
    b = BEATS[bid]; a, e = b["start"], b["end"]
    P = roadmap_panel(bid, t) if "roadmap" in b else phone_panel(bid, S, t)
    IN, OUT = 15 / FPS, 12 / FPS
    if t < a + IN: k = smoother((t - a) / IN); ent = True
    elif t > e - OUT: k = smoother((e - t) / OUT); ent = False
    else: return P
    # 180-degree shutter: horizontal blur matching half a frame of travel (no stepped ghosts)
    tp = t - 0.5 / FPS if ent else t + 0.5 / FPS
    kp = smoother((tp - a) / IN) if ent else smoother((e - tp) / OUT)
    blur_px = int(round(abs(k - kp) * 1280))
    off = (1 - k) * 1280
    fb = base.copy()
    push = int(round(k * 90))  # parallax push + dim on the footage
    if push: fb = np.concatenate([fb[:, push:], np.repeat(fb[:, -1:], push, 1)], 1)
    fb *= (1 - 0.45 * k)
    pblur = max(1, int(round(abs(k - kp) * 90)))
    if pblur > 1: fb = cv2.blur(fb, (pblur, 1))
    xo = int(round(off))
    if xo < 1280:
        Pv = P[:, :1280 - xo]
        if blur_px > 1:
            # blur the panel plus its leading edge so the edge smears too
            ext = np.concatenate([fb[:, max(xo - blur_px, 0):xo], Pv], 1)
            ext = cv2.blur(ext, (blur_px, 1))
            fb[:, max(xo - blur_px, 0):] = ext
        else:
            fb[:, xo:] = Pv
        sw = min(40, max(xo - blur_px, 0))
        if sw > 0:  # soft leading-edge shadow on the footage
            g = np.linspace(0, 0.35, sw)[None, :, None]
            x1 = max(xo - blur_px, 0)
            fb[:, x1 - sw:x1] *= (1 - g)
    return fb

# ---------- main frame ----------
TIMELINE = sorted(D["beats"], key=lambda b: b["start"])
def beat_at(t):
    for b in TIMELINE:
        if b["start"] <= t < b["end"]: return b
    return None

PROT = D["protected_regions"][0]
def render(n, S):
    t = n / FPS
    b = beat_at(t)
    base = base_frame(S, n)
    if b is None: return base, None
    tr = b["treatment"]; bid = b["id"]
    if tr == "FULLSCREEN_MOTION": return fullscreen_frame(base, S, t, bid), None
    if tr == "PRESENTER_INSET": return inset_frame(S, t, bid), None
    if tr == "OVERLAY_CARD":
        out = base.copy()
        if b.get("screen"): draw_chip(out, bid, t)
        else: draw_card(out, bid, t)
        return out, base
    if tr == "SELECTIVE_TEXT":
        if bid == "b23": return question_beat(base.copy(), t), None
        out = base.copy(); draw_keyword(out, t); return out, base
    return base, None

def main():
    f0, f1, outp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    pngs = [int(x) for x in sys.argv[5:]] if len(sys.argv) > 4 and sys.argv[4] == "--png" else None
    frames = pngs if pngs else range(f0, f1)
    safe = {"max_overlay_delta_in_protected": 0.0, "frames_checked": 0}
    if pngs:
        for n in pngs:
            S = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{n / FPS:.4f}", "-i", SRC, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            S = np.frombuffer(S, np.uint8).reshape(720, 1280, 3).astype(np.float32)
            out, _ = render(n, S)
            cv2.imwrite(f"{outp}/f{n:05d}.png", cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        return
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f0 / FPS:.6f}", "-i", SRC, "-frames:v", str(f1 - f0), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-threads", "2",
                            "-x264-params", "keyint=60:min-keyint=60:scenecut=0", outp], stdin=subprocess.PIPE)
    n = f0; FS = 1280 * 720 * 3
    px, py, pw, ph = PROT["x"], PROT["y"], PROT["width"], PROT["height"]
    while n < f1:
        buf = dec.stdout.read(FS)
        if len(buf) < FS: break
        S = np.frombuffer(buf, np.uint8).reshape(720, 1280, 3).astype(np.float32)
        out, ref = render(n, S)
        if ref is not None and not is_screen(n):
            dlt = float(np.abs(out[py:py + ph, px:px + pw] - ref[py:py + ph, px:px + pw]).max())
            safe["max_overlay_delta_in_protected"] = max(safe["max_overlay_delta_in_protected"], dlt); safe["frames_checked"] += 1
        enc.stdin.write(np.clip(out + 0.5, 0, 255).astype(np.uint8).tobytes())
        n += 1
        if (n - f0) % 300 == 0:
            with open(outp + ".progress", "w") as fh: fh.write(str(n - f0))
    enc.stdin.close(); enc.wait(); dec.wait()
    safe["frames_written"] = n - f0
    json.dump(safe, open(outp + ".safe.json", "w"))

if __name__ == "__main__":
    main()
