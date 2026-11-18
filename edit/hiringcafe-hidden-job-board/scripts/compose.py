"""Single-pass compositor for hiringcafe-hidden-job-board (clean-creator theme).

Usage: compose.py <first_frame> <last_frame_exclusive> <out.mp4>
       compose.py 0 0 <outdir> --png <frame> <frame> ...       (stills for inspection)
Reads the locked source, draws every approved beat from beats.py, writes an H.264 chunk without audio.
"""
import json, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui import *
from beats import *

# ---------------------------------------------------------------- static layers
GROUND_IMG = make_ground()
SX, SY, SW, SH = 64, 36, 1152, 648
SCREEN_MASK = rrect_mask(SW, SH, 22)[..., None]
SCREEN_RING = rrect_ring(SW, SH, 22, 1.5, 9.0, 0.8, RASP_HEX)
SCREEN_BASE = GROUND_IMG.copy(); over(SCREEN_BASE, SCREEN_RING, SX - 24, SY - 24)
ENTER, EXIT = 12 / FPS, 10 / FPS
FACE_CX = [(0, 2664, 560), (5284, 6128, 680), (15259, 15473, 660), (17467, 19920, 800)]   # presenter centre x per camera stretch
PBOX = {(0, 2664): (290, 0, 540, 560), (5284, 6128): (320, 0, 800, 560), (15259, 15473): (384, 0, 556, 560), (17467, 19920): (390, 0, 770, 560)}

def reveal(t, cue_, lead=0.2, dur=ENTER): return ease_out((t - (cue_ - lead)) / dur)
def env(t, a, b, ein=ENTER, eout=EXIT): return ease_out((t - a) / ein), ease_out((b - t) / eout)
def K(t, a, b, ein=ENTER, eout=EXIT): return min(*env(t, a, b, ein, eout))
def pop(p, s=1.5): return ease_back(clamp(p), s)

# ---------------------------------------------------------------- zoom path over the screen recordings
ZP = ZoomPath()
ZP.zoom(91.2, 94.0, 230, 70, 1.9)                              # b08 address bar
ZP.zoom(107.3, 112.4, 390, 352, 1.7)                           # b09 filter bar
ZP.zoom(129.2, 133.4, 330, 352, 1.8)                           # date posted chip / 24 h
ZP.zoom(139.6, 148.2, 200, 490, 1.7)                           # Atacama card (seen 5, 13 h)
ZP.zoom(163.6, 170.6, 400, 360, 1.7)                           # LinkedIn: only three results
ZP.zoom(209.6, 214.3, 520, 560, 1.5)                           # founders page: ex-SWE at Meta
ZP.path([(217.5, 480, 440, 1.9), (230.4, 480, 440, 1.9)])      # article
ZP.zoom(259.4, 266.0, 330, 265, 1.8)                           # date posted = 24 h (nurse search)
# b17 (revision 1, 2026-11-15): the first crop sat on the LEFT of the page and cut off "Apply now" / "Save Job"
# (top right of the job panel, x~714-1267, y~138). Now one steady, wider crop over both buttons (1.45x). The tracker
# views start at the left edge so the left nav + status tabs + first card stay in frame, with the tab strip (y~197)
# kept below the step bar (needs y0 <= ~140).
ZP.path([(278.4, 900, 250, 1.45), (283.6, 900, 250, 1.45), (290.4, 440, 395, 1.3), (297.0, 440, 395, 1.3),
         (302.0, 400, 430, 1.4), (310.0, 400, 430, 1.4), (318.6, 1000, 280, 1.7), (324.6, 1000, 280, 1.7)], tin=0.5, tout=0.5)
ZP.zoom(333.0, 346.0, 560, 330, 1.45)                           # network page
ZP.zoom(409.4, 421.0, 420, 560, 1.9)                            # WebWire article
ZP.zoom(447.0, 455.6, 450, 396, 2.0)                            # 33 jobs / 7 / 15
ZP.zoom(528.2, 534.8, 700, 330, 1.4)                           # connectors: pink funnel
ZP.zoom(541.6, 548.6, 760, 300, 1.5)                            # scheduled task
ZP.finish()

def framed_screen(S, t):
    r = ZP.rect(t); x0, y0, w, h = r; s = SW / w
    if w >= 1279.0:
        sm = cv2.resize(S, (SW, SH), interpolation=cv2.INTER_AREA)
    else:
        M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
        sm = cv2.warpAffine(S, M, (SW, SH), flags=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
    out = SCREEN_BASE.copy(); reg = out[SY:SY + SH, SX:SX + SW]
    out[SY:SY + SH, SX:SX + SW] = reg * (1 - SCREEN_MASK) + sm * SCREEN_MASK
    over(out, SCREEN_RING, SX - 24, SY - 24)
    return out

def S2W(x, y, t):
    x0, y0, w, h = ZP.rect(t); s = SW / w
    return SX + (x - x0) * s, SY + (y - y0) * s

# ---------------------------------------------------------------- camera punch-ins on quiet stretches
def _quiet_zones():
    zones = []
    for a, b in CAMERA_FR:
        t0, t1 = a / FPS, b / FPS; cur = t0
        for bt in BEATS:
            if bt["end"] <= t0 or bt["start"] >= t1: continue
            if bt["id"] == "b06":                       # keyword at the end; punch only the first part
                zones.append((max(cur, 64.4), 75.4)); cur = max(cur, bt["end"]); continue
            if bt["start"] - 0.4 > cur: zones.append((cur, bt["start"] - 0.4))
            cur = max(cur, bt["end"] + 0.4)
        if cur < t1: zones.append((cur, t1))
    return [(a, b) for a, b in zones if b - a >= 6.0]

def _make_punches():
    """Jump-cut push-ins (110/112 %) on pauses inside quiet camera zones: >=3 s normal, then >=3.5 s pushed."""
    P = []; flip = 0
    for a, b in _quiet_zones():
        t = a; on = False; start = a
        for m in sentence_breaks(a, b):
            if not on and m - t >= 2.5 and b - m >= 1.9: start = m; on = True; t = m
            elif on and m - t >= 3.5: P.append((start, m, 1.10 if flip % 2 == 0 else 1.12)); flip += 1; on = False; t = m
        if on: P.append((start, b, 1.10 if flip % 2 == 0 else 1.12)); flip += 1
    return P
PUNCH = _make_punches()

def face_cx(n):
    for a, b, c in FACE_CX:
        if a <= n < b: return c
    return 640

def punch(S, n):
    t = n / FPS
    for a, b, s in PUNCH:
        if a <= t < b:
            w = 1280 / s; x0 = min(max(face_cx(n) - w / 2, 0), 1280 - w)
            M = np.float32([[s, 0, -x0 * s], [0, s, 0]])
            return cv2.warpAffine(S, M, (1280, 720), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return S

def base_frame(S, n):
    t = n / FPS
    return punch(S, n).copy() if is_camera(n) else framed_screen(S, t)

# ---------------------------------------------------------------- generic pieces
def chip(out, t, a, b, text, cue_, slot=0, icon_name=None, num=None, w_min=0, xr=1198, y0=52, count=None):
    """Glass pill, top-right inside the screen window. `count`=(final, fmt, cue_start): number ticks up."""
    start = cue_ - 0.2
    k = min(ease_out((t - start) / ENTER), ease_out((b - t) / EXIT))
    if k <= 0: return
    if count:
        fin, fmt, c0 = count; v = int(round(fin * ease_out((t - c0) / 0.7))); text = fmt.format(v)
    lead = 40 if icon_name else 18
    tw = text_width(text.replace("**", ""), 17, 600, 800)
    w = int(max(lead + tw + 22, w_min)); h = 38
    x = xr - w + (1 - k) * 26; y = y0 + slot * 46
    glass(out, x, y, w, h, alpha=k, r=h // 2, tint=0.80, blur=8, glow=5.0)
    if icon_name: put_icon(out, icon_name, 24, x + 10, y + 7, k)
    put_text(out, text, 17, x + lead, y + h / 2 + 1, 600, alpha=k, anchor="lm", bold_weight=800)

def side_card(out, t, a, b, x, y, w, rows, side=1, ein=14 / FPS):
    """Frosted card in a side margin. rows: [(text, cue, icon|None)] revealed one at a time."""
    k = min(ease_out((t - a) / ein), ease_out((b - t) / (12 / FPS)))
    if k <= 0: return
    tx = 44; maxw = w - 22 - tx - 12
    hs = [max(len(wrap(r[0], 20, 400, maxw)) * 25, 34 if r[2] else 25) for r in rows]
    h = 44 + sum(hs) + 16 * (len(rows) - 1)
    dx = (1 - k) * 60 * side
    glass(out, x + dx, y, w, h, alpha=k)
    yy = y + 22
    for (txt, cue_, ic), hh in zip(rows, hs):
        p = reveal(t, cue_)
        if p > 0:
            ox = x + dx + 22 + (1 - p) * 18 * side
            if ic: put_icon(out, ic, 28, ox, yy + (hh - 28) / 2, p * k)
            else: disc(out, ox + 8, yy + 12, 4.5, ROSE_HEX, p * k)
            put_text(out, txt, 20, ox + 40, yy + (0 if not ic else (hh - 25) / 2), 400, alpha=p * k, maxw=maxw, bold_weight=750)
        yy += hh + 16

def kw(out, t, lines, cue_, b, cx, cy, gap=6, a_fade=0.35):
    """Kinetic keyword: lines [(text, size, weight)] stacked, springing 90->100 % on the cue, fading out at b."""
    p = clamp((t - (cue_ - 0.15)) / (10 / FPS)); po = ease_out((b - t) / (9 / FPS))
    if p <= 0 or po <= 0: return
    s = 0.9 + 0.1 * pop(p, 1.6); a = clamp(p * 2) * po
    hs = [int(l[1] * 1.15) for l in lines]; y = cy - (sum(hs) + gap * (len(lines) - 1)) / 2
    for (txt, size, wt), hh in zip(lines, hs):
        put_text(out, txt, size, cx, y + hh / 2, wt, alpha=a, anchor="cm", glow=0.5 if size >= 40 else 0, scale=s)
        y += hh + gap

def ringed(out, t, a, b, x, y, items, w, step=92, size=22):
    """Ringed list over the presenter: items [(text, sub, cue, kind, icon)], kind 'check'|'cross'|int."""
    k = ease_out((b - t) / (10 / FPS))
    pb = reveal(t, items[0][2], 0.35) * k
    if pb > 0:
        n = len(items); glass(out, x - 18 + (1 - pb) * -26, y - 46, w + 36, (n - 1) * step + 92, alpha=pb, r=26, tint=0.78, blur=10, glow=6.0)
    for i, (txt, sub, cue_, kind, ic) in enumerate(items):
        p = reveal(t, cue_) * k
        if p <= 0: continue
        cy = y + i * step; ox = x + (1 - p) * -26
        ring, c = circle_ring(22, 2.0, 6.0, 0.8, ROSE_HEX if kind != "cross" else "#8C3D5D", ROSE_HEX if kind != "cross" else "#8C3D5D")
        over(out, ring, ox + 22 - c, cy - c, p)
        if kind == "check": put_glyph(out, "check", 24, ox + 22, cy, ROSE_HEX, p * pop(clamp((t - cue_) / 0.28)), glow=0.6)
        elif kind == "cross": put_glyph(out, "cross", 22, ox + 22, cy, "#B98099", p)
        else: put_text(out, str(kind), 20, ox + 22, cy + 1, 700, alpha=p, anchor="cm")
        tw = put_text(out, txt, size, ox + 56, cy - (9 if sub else 0), 600, alpha=p, anchor="lm", maxw=w - 56)[0]
        if sub: put_text(out, sub, 15, ox + 56, cy + 15, 300, alpha=p * 0.85, anchor="lm", italic=True)
        if ic: put_icon(out, ic, 24, ox + 56 + tw + 10, cy - (9 if sub else 0) - 12, p)

def scrim_bottom(out, k, h=230, strength=0.82):
    g = (np.linspace(0, 1, h) ** 1.2)[:, None, None] * strength * k
    out[720 - h:] = out[720 - h:] * (1 - g) + GROUND * g

def subscribe_seq(out, t, t0, x, y, like=True, comment=True, hold_to=None):
    """Like / comment buttons pop in, SUBSCRIBE pill appears, cursor clicks -> Subscribed + bell. x,y = top-left."""
    u = t - t0
    if u < 0: return
    k = 1.0 if hold_to is None else ease_out((hold_to - t) / (10 / FPS))
    if k <= 0: return
    yy = y
    if like or comment:
        if like:
            p = pop(u / 0.35, 1.4); st = smoother((u - 0.5) / 0.25)
            if p > 0: like_button(out, x, yy, st, alpha=clamp(p * 2) * k)
        if comment:
            p = pop((u - 0.25) / 0.35, 1.4)
            if p > 0: comment_button(out, x + (118 if like else 0), yy, alpha=clamp(p * 2) * k)
        yy += 66
    p = ease_out((u - 0.5) / 0.35)
    if p <= 0: return
    clickt = 1.7; st = smoother((u - clickt) / 0.18); press = np.sin(np.pi * clamp((u - clickt + 0.05) / 0.2))
    sx = x + (1 - p) * -30
    subscribe_pill(out, sx, yy, st, alpha=p * k, press=max(press, 0), bell=clamp((u - clickt - 0.25) / 0.4))
    # cursor travels in, clicks, rests
    cp = smoother((u - 0.95) / 0.75); cx0, cy0 = x + 330, yy + 110; cx1, cy1 = x + 120, yy + 36
    if cp > 0:
        cursor(out, cx0 + (cx1 - cx0) * cp, cy0 + (cy1 - cy0) * cp, alpha=k * clamp(cp * 4), press=max(press, 0))

# ---------------------------------------------------------------- beats on camera
def b01(out, t):
    e = 4.6; fo = ease_out((e - t) / (10 / FPS))
    for name, cx, cy, size, c_in, c_x in (("linkedin", 138, 340, 124, 2.40, 2.95), ("indeed", 1066, 340, 84, 3.00, 3.55)):
        p = pop((t - c_in) / (10 / FPS), 1.5)
        if p <= 0: continue
        w = icon(name, size).shape[1]; dim = 1 - 0.5 * smoother((t - c_x) / 0.3)
        put_icon(out, name, size, cx - w / 2, cy - size / 2, clamp(p * 2) * fo * dim, scale=max(p, 0.05))
        put_line(out, (cx - w / 2 - 16, cy + size / 2 + 12), (cx + w / 2 + 16, cy - size / 2 - 12), 9, ROSE_HEX, prog=smoother((t - c_x) / 0.24), alpha=fo)

def b02(out, t):
    kw(out, t, [("10x", 118, 800)], 5.74, 10.0, 1068, 300)
    kw(out, t, [("BETTER", 46, 800)], 6.62, 10.0, 1068, 392)

def b03(out, t):
    b = BY_ID["b03"]; a, e = 14.7, b["end"]
    k = K(t, a, e, 14 / FPS, 12 / FPS)
    if k <= 0: return
    x, y, w, h = 884, 176, 372, 296; dx = (1 - k) * 60
    glass(out, x + dx, y, w, h, alpha=k)
    p = reveal(t, 15.34)
    if p > 0:
        put_icon(out, "hiringcafe", 60, x + dx + 24, y + 20, p * k, scale=0.9 + 0.1 * pop(p))
        put_text(out, "HiringCafe", 30, x + dx + 98, y + 50, 800, alpha=p * k, anchor="lm", glow=0.4)
    p = reveal(t, 17.9)
    if p > 0:
        s = 1 + 0.07 * np.sin(np.pi * clamp((t - 17.9) / 0.9))
        pw, ph = int(324 * s), int(50 * s)
        glass(out, x + dx + 24 + (324 - pw) / 2, y + 102 - (ph - 50) / 2, pw, ph, alpha=p * k, r=ph // 2, tint=0.85, blur=6, highlight=1.0)
        put_text(out, "hiringcafe.com", int(23 * s), x + dx + 186, y + 127, 600, alpha=p * k, anchor="cm")
    for i, (txt, c) in enumerate((("Free", 19.54), ("No account needed", 20.88))):
        p = reveal(t, c)
        if p > 0:
            yy = y + 176 + i * 54; ox = x + dx + 24 + (1 - p) * 20
            glass(out, ox, yy, 324, 44, alpha=p * k, r=22, tint=0.8, blur=6, glow=4.0)
            put_glyph(out, "check", 20, ox + 24, yy + 22, ROSE_HEX, p * k)
            put_text(out, txt, 20, ox + 46, yy + 23, 500, alpha=p * k, anchor="lm", bold_weight=750)

def b04(out, t):
    cx = 1064
    k = ease_out((t - 23.76) / ENTER) * ease_out((35.2 - t) / EXIT)
    if k <= 0: return
    dim = 1 - 0.55 * smoother((t - 30.6) / 0.5)
    v = int(round(400 * ease_out((t - 24.3) / 5.0))); v = max(1, v)
    put_text(out, "APPLICANT #", 26, cx, 262 + (1 - k) * 10, 600, alpha=k * dim, anchor="cm")
    put_text(out, f"{v}", 128, cx, 352, 800, alpha=k * dim, anchor="cm", glow=0.6)
    r = reveal(t, 30.6)
    if r > 0: put_text(out, "nobody is reading", 24, cx, 438 + (1 - r) * 8, 300, alpha=r * k, anchor="cm", italic=True)

def b06(out, t):
    kw(out, t, [("YOU ARE", 50, 700)], 75.72, 78.7, 1070, 300)
    kw(out, t, [("EARLY", 88, 800)], 76.1, 78.7, 1070, 392)

def b10(out, t):
    a, e = 176.6, 186.0
    ringed(out, t, a, e, 36, 230, [("Company site", None, 178.68, "check", None), ("HiringCafe", None, 180.14, "check", "hiringcafe"),
                                   ("LinkedIn", "not yet", 181.72, "cross", None)], 232, step=96)

def b11(out, t):
    a, e = 186.0, 191.4
    k = K(t, a, e)
    if k <= 0: return
    scrim_bottom(out, k, h=160)
    p1 = reveal(t, 186.16); p2 = reveal(t, 186.52)
    rule_text(out, [("Time is your ", 0), ("leverage", 1)], 34, 640, 636 + (1 - p1) * 8, alpha=p1 * k)
    rule_text(out, [("Early applicants ", 0), ("get the call", 1)], 30, 640, 682 + (1 - p2) * 8, alpha=p2 * k, weight=500)

def b12(out, t):
    a, e = 191.4, 197.5
    k = K(t, a, e, 14 / FPS, 12 / FPS)
    if k <= 0: return
    x, y, w, h = 28, 300, 264, 124; dx = (1 - k) * -50
    glass(out, x + dx, y, w, h, alpha=k)
    put_text(out, "COMING UP", 15, x + dx + 24, y + 26, 700, alpha=k * 0.8, anchor="lm")
    p = reveal(t, 192.30)
    if p > 0: put_icon(out, "claude", 52, x + dx + 28, y + 50, p * k, scale=0.85 + 0.15 * pop(p))
    p2 = reveal(t, 195.4)
    if p2 > 0:
        put_glyph(out, "share", 20, x + dx + 132, y + 76, ROSE_HEX, p2 * k)
        put_icon(out, "sheets", 46, x + dx + 170, y + 53, p2 * k, scale=0.85 + 0.15 * pop(p2))

def b13(out, t): subscribe_seq(out, t, 199.0, 28, 240, hold_to=203.8)

def b24(out, t): subscribe_seq(out, t, 510.6, 28, 270, like=False, comment=False, hold_to=515.7)

def b28(out, t):
    a, e = 597.1, 610.8
    k = ease_out((t - 603.4) / ENTER) * ease_out((e - t) / EXIT)
    if k <= 0: return
    v = int(5_000_000 * ease_out((t - 603.6) / 3.0)) if t < 606.7 else 5_000_000
    txt = f"{v:,}+"
    put_text(out, txt, 44, 188, 300, 800, alpha=k, anchor="cm", glow=0.55)
    put_text(out, "JOBS", 28, 188, 352, 700, alpha=k, anchor="cm")
    p = reveal(t, 607.6)
    if p > 0: put_text(out, "all day · free", 20, 188, 394 + (1 - p) * 8, 300, alpha=p * k, anchor="cm", italic=True)

def b29(out, t):
    a, e = 610.8, 617.6
    k = K(t, a, e, 14 / FPS, 12 / FPS)
    if k <= 0: return
    x, y, w, h = 28, 210, 320, 290; dx = (1 - k) * -60
    hl = smoother((t - 615.26) / 0.45)
    glass(out, x + dx, y, w, 130, alpha=k)
    glass(out, x + dx, y + 148, w, 130, alpha=k * reveal(t, 615.0), highlight=hl)
    for (name, ic, rows, ytop, c0) in (("LINKEDIN", "linkedin", ["Networking", "Posting"], y, 611.06), ("HIRINGCAFE", "hiringcafe", ["Finding"], y + 148, 615.0)):
        p = reveal(t, c0)
        if p <= 0: continue
        put_icon(out, ic, 34, x + dx + 22, ytop + 16, p * k)
        put_text(out, name, 19, x + dx + 66, ytop + 34, 800, alpha=p * k, anchor="lm")
        for j, r in enumerate(rows):
            cj = (612.74 if r == "Networking" else 613.9 if r == "Posting" else 615.44)
            q = reveal(t, cj)
            if q > 0:
                disc(out, x + dx + 32, ytop + 72 + j * 30, 4.5, ROSE_HEX, q * k)
                put_text(out, r, 22, x + dx + 48 + (1 - q) * 14, ytop + 73 + j * 30, 500, alpha=q * k, anchor="lm")

def b30(out, t):
    """Quote: footage dims and blurs, big centred quote with HiringCafe icon. Returns new frame."""
    a, e = 617.6, 623.4
    k = min(smoother((t - a) / (10 / FPS)), smoother((e - t) / (10 / FPS)))
    if k <= 0: return out
    out = cv2.GaussianBlur(out, (0, 0), 7 * k + 0.01) * (1 - 0.55 * k)
    p1 = reveal(t, 619.4, 0.1, 14 / FPS) * min(1, smoother((e - t) / (10 / FPS)))
    p2 = reveal(t, 621.55, 0.1, 14 / FPS) * min(1, smoother((e - t) / (10 / FPS)))
    put_text(out, "“", 140, 640, 170, 800, color=ROSE_HEX, alpha=p1 * 0.9, anchor="cm")
    rule_text(out, [("LinkedIn", 1), (" is for ", 0), ("being found.", 1)], 52, 640, 318 + (1 - p1) * 10, alpha=p1, weight=500, hl_weight=800, glow=0.5)
    rule_text(out, [("HiringCafe", 1), (" is for ", 0), ("finding.", 1)], 52, 640, 408 + (1 - p2) * 10, alpha=p2, weight=500, hl_weight=800, glow=0.5)
    pi = reveal(t, 621.55) * min(1, smoother((e - t) / (10 / FPS)))
    if pi > 0: put_icon(out, "hiringcafe", 64, 640 - 32, 478, pi, scale=0.9 + 0.1 * pop(pi))
    return out

def b31(out, t):
    a, e = 623.4, 634.9
    k = K(t, a, e, 14 / FPS, 12 / FPS)
    if k <= 0: return
    p = reveal(t, 624.0)
    if p > 0:
        s = 1 + 0.06 * np.sin(np.pi * clamp((t - 624.1) / 0.9))
        glass(out, 28, 104, 320, 54, alpha=p * k, r=27, tint=0.85, blur=6, highlight=1.0)
        put_icon(out, "hiringcafe", 30, 42, 116, p * k)
        put_text(out, "hiringcafe.com", int(21 * s), 88, 132, 600, alpha=p * k, anchor="lm")
    ringed(out, t, a, e, 36, 212, [("Bookmark", None, 624.4, 1, None), ("Search your title", None, cue("search your title"), 2, None),
                                   ("Last 24 hours", None, cue("last 24 hours"), 3, None), ("Apply to one", None, cue("apply for one job"), 4, None)], 300, step=88)

def b32(out, t):
    a, e = 634.9, 640.2
    k = K(t, a, e)
    if k <= 0: return
    p = pop((t - 634.48) / 0.4, 1.4)
    if p <= 0: return
    comment_button(out, 28 - (1 - k) * 40, 300, alpha=clamp(p * 2) * k, w=190, state=smoother((t - 635.0) / 0.3))

def b33(out, t):
    subscribe_seq(out, t, 640.5, 28, 270, like=True, comment=False, hold_to=645.8)

def b34(out, t):
    a, e = 645.9, 652.3
    k = K(t, a, e)
    if k <= 0: return
    u = t - 648.0
    p = pop((t - 646.2) / 0.4, 1.3); sx = 28 - (1 - k) * 40
    if p <= 0: return
    click = 648.9; st = smoother((t - click) / 0.2); press = max(np.sin(np.pi * clamp((t - click + 0.05) / 0.2)), 0)
    share_button(out, sx, 300, st, alpha=clamp(p * 2) * k, press=press)
    cp = smoother((t - 648.0) / 0.8)
    if cp > 0: cursor(out, 28 + 250 + (28 + 60 - 278) * cp, 300 + 120 + (300 + 30 - 420) * cp, alpha=k * clamp(cp * 4), press=press)
    if t > click:       # forward arrow flies off the button
        f = smoother((t - click - 0.1) / 0.7)
        put_glyph(out, "share", 22, 28 + 34 + 120 * f, 326 - 26 * f, ROSE_HEX, alpha=(1 - f) * k * 0.9)

# ---------------------------------------------------------------- beats on screens (chips + highlighter)
def b08(out, t): chip(out, t, 88.8, 95.0, "hiringcafe.com", 91.3, 0, "hiringcafe")

def _timed(out, t, a, b, text, cue_, slot=0, icon_name=None, count=None):
    if a <= t < b: chip(out, t, a, b, text, cue_, slot, icon_name, count=count)

def screen_chips(out, t):
    _timed(out, t, 88.8, 95.0, "hiringcafe.com", 91.3, 0, "hiringcafe")
    _timed(out, t, 143.8, 149.5, "Posted 13 h ago · 0 applied", 144.0)
    _timed(out, t, 163.8, 173.0, "Not on LinkedIn yet", 164.0, 0, "linkedin")
    _timed(out, t, 207.9, 212.0, "Started as a spreadsheet", 208.38)
    _timed(out, t, 211.9, 216.9, "10,000 hard-to-find jobs", 212.04, 0)
    _timed(out, t, 259.8, 266.2, "Date posted: 24 h", 260.06, 0)
    _timed(out, t, 233.4, 238.2, "Classic search", 233.64, 0)
    _timed(out, t, 234.9, 238.2, "AI search", 235.14, 1)
    _timed(out, t, 339.1, 346.4, "Network: recruiters come to you", 339.34, 0)
    _timed(out, t, 349.8, 354.5, "Add jobs: recruiters only", 350.04, 0)
    _timed(out, t, 447.0, 457.0, "{} jobs", 447.26, 0, count=(33, "{} jobs", 447.0))
    _timed(out, t, 449.1, 457.0, "{} matching", 449.30, 1, count=(7, "{} matching", 449.1))
    _timed(out, t, 450.4, 457.0, "{} related", 450.64, 2, count=(15, "{} related", 450.4))
    _timed(out, t, 468.4, 473.0, "Email alerts", 468.64, 0)
    _timed(out, t, 476.7, 490.5, "Free plan: 1 agent chat", 476.94, 0)
    _timed(out, t, 502.7, 508.6, "Everything shown = free", 502.86, 0)
    _timed(out, t, 521.5, 528.0, "Claude", 521.72, 0, "claude")
    _timed(out, t, 525.4, 528.0, "ChatGPT", 525.64, 1, "chatgpt")
    _timed(out, t, 547.3, 555.0, "Google Sheets", 547.54, 0, "sheets")
    # step breadcrumb for b17
    if 278.0 <= t < 326.8: steps_bar(out, t)

STEPS = [("Save", cue("save the job")), ("Applied", cue("move to apply")), ("Interviewing", 295.2), ("Notes", cue("add the notes"))]
def steps_bar(out, t):
    a, e = 278.0, 326.8
    k = min(ease_out((t - (STEPS[0][1] - 0.4)) / ENTER), ease_out((e - t) / EXIT))
    if k <= 0: return
    ws = [int(text_width(s, 17, 600, 800)) + 40 for s, _ in STEPS]; gap = 34; total = sum(ws) + gap * (len(ws) - 1)
    x = 640 - total / 2; y = 50
    glass(out, x - 18, y - 6, total + 36, 50, alpha=k, r=25, tint=0.82, blur=8, glow=5.0)
    cur = max([i for i, (s, c) in enumerate(STEPS) if t >= c - 0.2] or [0])
    for i, ((s, c), w) in enumerate(zip(STEPS, ws)):
        on = 1.0 if i == cur else 0.0; done = i < cur
        al = k * (0.45 + 0.55 * (reveal(t, c)))
        if done: put_glyph(out, "check", 18, x + 14, y + 19, ROSE_HEX, al)
        put_text(out, s, 17, x + (30 if done else 20), y + 20, 800 if on else 500, color=(ROSE_HEX if on else WHITE_HEX), alpha=al, anchor="lm")
        x += w
        if i < len(STEPS) - 1:
            put_glyph(out, "share", 14, x + gap / 2 - 2, y + 20, WHITE_HEX, k * 0.5)
            x += gap

def rule_pill(out, t, a, b, parts, cue_, y=626):
    k = min(ease_out((t - (cue_ - 0.2)) / ENTER), ease_out((b - t) / EXIT))
    if k <= 0: return
    wtot = sum(text_width(p_, 26, 800 if kk else 500) for p_, kk in parts) + 70
    glass(out, 640 - wtot / 2, y - 30, wtot, 60, alpha=k, r=30, tint=0.82, blur=8, glow=6.0, highlight=0.6)
    rule_text(out, parts, 26, 640, y + 1, alpha=k, glow=0.3)

HL = []   # (t0, t1, x0, x1, y, window) source-space underlines drawn in window space (they follow the zoom)
def _hl(t0, t1, x0, x1, y, dur=0.38): HL.append((t0, t1, x0, x1, y, dur))
# founders page (ex-SWE at Meta, bottom edge of the card) -> box highlight handled in draw_hl
_hl(209.9, 216.3, 468, 568, 720, 0.4)
# article (hrtechfeed), source coordinates of the 1280x720 recording
_hl(217.05, 230.6, 518, 558, 442, 0.3)       # Reddit
_hl(219.72, 230.6, 690, 742, 501, 0.3); _hl(220.06, 230.6, 199, 372, 521, 0.5)   # 2 million monthly active users
_hl(222.42, 230.6, 363, 526, 621, 0.5)       # without any marketing spend
_hl(225.30, 230.6, 330, 580, 601, 0.7)       # built for people looking for a job
_hl(227.12, 230.6, 586, 740, 601, 0.5)       # not for people advertising
# WebWire article (launch line)
_hl(409.38, 421.4, 451, 624, 489, 0.4)       # Monday, September 28, 2026
_hl(412.5, 421.4, 372, 571, 599, 0.9)        # ... launching its
_hl(413.76, 421.4, 223, 528, 618, 2.4)       # AI talent agent, allowing anyone to create AI agents to
_hl(417.7, 421.4, 223, 487, 636, 2.1)        # search across millions of jobs on their behalf.

def draw_hl(out, t):
    for t0, t1, x0, x1, y, dur in HL:
        if not (t0 - 0.05 <= t < t1 + 0.4): continue
        k = ease_out((t1 + 0.35 - t) / 0.35) if t >= t1 else 1.0
        wx0, wy = S2W(x0, y, t); wx1, _ = S2W(x1, y, t)
        underline(out, max(wx0, SX + 6), min(wx1, SX + SW - 6), min(wy, SY + SH - 4), clamp((t - t0) / dur) if dur > 0 else 1, alpha=k)


# ---------------------------------------------------------------- inset layouts
MOVE_IN, MOVE_OUT = 33 / FPS, 23 / FPS
WIN = (48, 120, 768, 432)

def inset_progress(t, a, e): return min(smoother((t - a) / MOVE_IN), smoother((e - t) / MOVE_OUT))

def place_presenter(bg, S, p, dest):
    if p <= 0: return S.copy(), False
    dx, dy, dw, dh = [v0 + (v1 - v0) * p for v0, v1 in zip((0, 0, 1280, 720), dest)]
    s = dw / 1280.0
    out = bg.copy()
    X0, Y0 = int(np.floor(dx)), int(np.floor(dy)); X1, Y1 = int(np.ceil(dx + dw)), int(np.ceil(dy + dh))
    M = np.float32([[s, 0, dx - X0], [0, s, dy - Y0]])
    patch = cv2.warpAffine(S, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    r = 24 * p
    m = rrect_mask(X1 - X0, Y1 - Y0, max(int(round(r)), 0))[..., None] if r >= 0.5 else np.ones((Y1 - Y0, X1 - X0, 1), np.float32)
    reg = out[Y0:Y1, X0:X1]; out[Y0:Y1, X0:X1] = reg * (1 - m) + patch * m
    if p > 0.02:
        over(out, rrect_ring(X1 - X0, Y1 - Y0, max(int(round(r)), 1), 1.5, 8.0, 0.75, RASP_HEX), X0 - 24, Y0 - 24, p)
    return out, True

@lru_cache(None)
def donut_sprite(p20, p80, r_out=112, th=30):
    ss = 3; d = 2 * (r_out + 16); img20 = Image.new("L", (d * ss, d * ss), 0); img80 = Image.new("L", (d * ss, d * ss), 0)
    c = d * ss / 2; box = [c - r_out * ss + th * ss / 2, c - r_out * ss + th * ss / 2, c + r_out * ss - th * ss / 2, c + r_out * ss - th * ss / 2]
    ImageDraw.Draw(img20).arc(box, -90, -90 + 72 * p20, fill=255, width=th * ss)
    ImageDraw.Draw(img80).arc(box, -90 + 72, -90 + 72 + 288 * p80, fill=255, width=th * ss)
    a20 = np.asarray(img20.resize((d, d), Image.LANCZOS)).astype(np.float32) / 255
    a80 = np.asarray(img80.resize((d, d), Image.LANCZOS)).astype(np.float32) / 255
    out = np.zeros((d, d, 4), np.float32)
    a = np.clip(a20 + a80, 0, 1)
    out[..., :3] = (hexc(ROSE_HEX) * a20[..., None] + hexc("#6E2A47") * a80[..., None]) / np.maximum(a[..., None], 1e-4)
    g = np.clip(cv2.GaussianBlur(a20, (0, 0), 7) * 0.9, 0, 1)
    out[..., 3] = np.clip(a + g * (1 - a), 0, 1)
    return out

def inset_b07(out, t, gk):
    a, e = 79.0, 88.8; landed = a + MOVE_IN
    cx, cy = 1040, 312
    p20 = smoother((t - 81.1) / 0.9); p80 = smoother((t - 85.2) / 1.4)
    if p20 > 0 or p80 > 0:
        spr = donut_sprite(round(p20, 3), round(p80, 3)); over(out, spr, cx - spr.shape[1] / 2, cy - spr.shape[0] / 2, gk)
    pt = ease_out((t - landed) / ENTER)
    put_text(out, "THE REAL PICTURE", 34, 1040, 122 + (1 - pt) * 8, 800, alpha=pt * gk, anchor="cm", glow=0.5)
    big = "80%" if t >= 85.2 else "20%"
    if p20 > 0: put_text(out, big, 54, cx, cy, 800, alpha=gk, anchor="cm", glow=0.5)
    r1 = reveal(t, 81.54)
    if r1 > 0:
        put_text(out, "20%", 22, 880, 496 + (1 - r1) * 10, 800, color=ROSE_HEX, alpha=r1 * gk, anchor="lm")
        put_text(out, "paid to promote", 22, 936, 496 + (1 - r1) * 10, 400, alpha=r1 * gk, anchor="lm")
    r2 = reveal(t, 85.36)
    if r2 > 0:
        put_text(out, "80%", 22, 880, 540 + (1 - r2) * 10, 800, color="#C0839C", alpha=r2 * gk, anchor="lm")
        put_text(out, "everything else", 22, 936, 540 + (1 - r2) * 10, 400, alpha=r2 * gk, anchor="lm")
        put_icon(out, "hiringcafe", 34, 1196, 520, r2 * gk, scale=0.9 + 0.1 * pop(r2))

RAIL_X = 906
def inset_b27(out, t, gk):
    a, e = 582.3, 595.8; landed = a + MOVE_IN
    steps = [("Careers page", cue("job starts", after=582.5), None), ("HiringCafe", cue("picks them up", after=585.0), "hiringcafe"),
             ("Ghost jobs filtered", cue("ghost jobs", after=588.0), None), ("You apply early", cue("you see them early", after=590.0), None)]
    ys = [168 + i * 112 for i in range(4)]
    pt = ease_out((t - landed) / ENTER)
    put_text(out, "THE WHOLE THING", 30, 1010, 108 + (1 - pt) * 8, 800, alpha=pt * gk, anchor="cm", glow=0.5)
    # rail: glow grows down to the active node
    cur_y = None
    for (txt, c, ic), y in zip(steps, ys):
        if t >= c - 0.1: cur_y = y
    base = np.zeros((520, 14, 4), np.float32); base[..., :3] = hexc("#4A1830"); base[:, 5:9, 3] = 0.8
    over(out, base, RAIL_X - 7, 150, pt * gk)
    if cur_y is not None:
        prev = [y for (txt, c, ic), y in zip(steps, ys) if t >= c - 0.1]
        top = ys[0]; end = top + (cur_y - top) * smoother((t - ([c for (_, c, _), y in zip(steps, ys) if y == cur_y][0] - 0.1)) / 0.5) if cur_y > top else top
        L = int(max(end - top, 1)); lit = np.zeros((L, 14, 4), np.float32); lit[..., :3] = hexc(ROSE_HEX)
        core = np.zeros((L, 14), np.float32); core[:, 5:9] = 1.0
        lit[..., 3] = np.clip(core + cv2.GaussianBlur(core, (0, 0), 3) * 1.4, 0, 1); over(out, lit, RAIL_X - 7, top, gk)
    for i, ((txt, c, ic), y) in enumerate(zip(steps, ys)):
        p = reveal(t, c, 0.1)
        on = clamp((t - (c - 0.1)) / 0.3); last_on = (i == max([j for j, (_, cc, _) in enumerate(steps) if t >= cc - 0.1] or [-1]))
        num_badge(out, RAIL_X, y, 24, i + 1, fill=1.0 if on > 0 else 0.0, alpha=gk * (0.55 + 0.45 * on), active=on if last_on else 0.0, scale=1.0 + 0.12 * last_on)
        if p > 0:
            put_text(out, txt, 26, RAIL_X + 48 + (1 - p) * 20, y, 700 if last_on else 400, alpha=p * gk * (1.0 if last_on else 0.7), anchor="lm")
            if ic: put_icon(out, ic, 32, RAIL_X + 48 + text_width(txt, 26, 700) + 14, y - 16, p * gk)

def inset_frame(S, t, bid):
    b = BY_ID[bid]; a, e = b["start"], b["end"]
    p = inset_progress(t, a, e)
    out, moved = place_presenter(GROUND_IMG, S, p, WIN)
    if not moved: return out
    gk = 1.0
    if t > e - MOVE_OUT - 8 / FPS: gk = max(ease_out((e - MOVE_OUT - t) / (8 / FPS)), 0.0)
    if t >= a + MOVE_IN and gk > 0:
        (inset_b07 if bid == "b07" else inset_b27)(out, t, gk)
    return out

# ---------------------------------------------------------------- full-screen panels
def title_in(P, t, text, cue_, y=96, size=48):
    p = reveal(t, cue_, 0.1, 14 / FPS)
    if p > 0: put_text(P, text, size, 640, y + (1 - p) * 12, 800, alpha=p, anchor="cm", glow=0.6)

def poly_line(P, pts, prog, width, color, alpha=1.0, head=0, glow=0.7):
    seg = [np.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]; tot = sum(seg); d = tot * prog; acc = 0
    for i, ((a, b), L) in enumerate(zip(zip(pts, pts[1:]), seg)):
        if d <= acc: break
        f = clamp((d - acc) / L); last = (i == len(seg) - 1)
        put_line(P, a, b, width, color, prog=f, alpha=alpha, glow=glow, head=(head if last else 0))
        acc += L

def panel_b05(t):
    P = GROUND_IMG.copy()
    title_in(P, t, "WHERE A JOB STARTS", 37.0, 78, 44)
    N1 = (230, 270); hub = (660, 270); LI = (1060, 180); IN = (1060, 360)
    # delayed path (careers -> recruiter -> boards)
    dim = 1 - 0.5 * smoother((t - 56.0) / 0.6)
    pl = reveal(t, 42.12)
    if pl > 0:
        poly_line(P, [(N1[0] + 150, N1[1]), hub, (LI[0] - 80, LI[1])], smoother((t - 42.0) / 0.9), 4, RASP_HEX, alpha=dim, glow=0.0)
    pi = reveal(t, 42.9)
    if pi > 0: poly_line(P, [hub, (IN[0] - 110, IN[1])], smoother((t - 42.8) / 0.9), 4, RASP_HEX, alpha=dim, glow=0.0)
    p = reveal(t, 39.4, 0.1, 14 / FPS)
    if p > 0:
        glass(P, N1[0] - 150 + (1 - p) * -30, N1[1] - 56, 300, 112, alpha=p, r=24, highlight=0.7)
        put_text(P, "Company careers page", 24, N1[0] + (1 - p) * -30, N1[1], 700, alpha=p, anchor="cm", maxw=250, align="center")
    for nm, pos, size, c in (("linkedin", LI, 96, 42.12), ("indeed", IN, 74, 42.9)):
        q = pop((t - (c - 0.1)) / 0.4, 1.4)
        if q > 0:
            w = icon(nm, size).shape[1]; put_icon(P, nm, size, pos[0] - w / 2, pos[1] - size / 2, clamp(q * 2) * dim, scale=max(q, 0.05))
    r = pop((t - 49.3) / 0.4, 1.3)
    if r > 0:
        glass(P, hub[0] - 96, hub[1] - 34, 192, 68, alpha=clamp(r * 2), r=34, tint=0.85, highlight=0.0)
        put_text(P, "Recruiter", 22, hub[0], hub[1] + 1, 600, alpha=clamp(r * 2), anchor="cm")
    d = reveal(t, 53.86, 0.1)
    if d > 0:
        glass(P, hub[0] + 40, hub[1] - 130 + (1 - d) * -10, 168, 46, alpha=d, r=23, tint=0.85)
        put_glyph(P, "clock", 22, hub[0] + 64, hub[1] - 107 + (1 - d) * -10, ROSE_HEX, d)
        put_text(P, "DELAY", 19, hub[0] + 86, hub[1] - 106 + (1 - d) * -10, 800, alpha=d, anchor="lm")
    # the shortcut
    sp = smoother((t - 55.6) / 1.3)
    HC = (1020, 574)
    if sp > 0:
        poly_line(P, [(N1[0], N1[1] + 56), (N1[0], HC[1]), (HC[0] - 150, HC[1])], sp, 9, ROSE_HEX, glow=1.1, head=22)
    hp = pop((t - 56.3) / 0.45, 1.3)
    if hp > 0:
        glass(P, HC[0] - 150 + 20, HC[1] - 62, 330, 124, alpha=clamp(hp * 2), r=28, highlight=1.0)
        put_icon(P, "hiringcafe", 70, HC[0] - 126 + 20, HC[1] - 35, clamp(hp * 2), scale=max(hp, 0.05))
        put_text(P, "HiringCafe", 30, HC[0] - 40 + 20, HC[1], 800, alpha=clamp(hp * 2), anchor="lm", glow=0.4)
    q = reveal(t, 62.78, 0.1)
    if q > 0:
        glass(P, 380 + (1 - q) * -20, HC[1] - 74, 190, 46, alpha=q, r=23, tint=0.85, highlight=1.0)
        put_text(P, "3× a day", 22, 475 + (1 - q) * -20, HC[1] - 51, 800, alpha=q, anchor="cm")
    return P

TITLES = ["Account Executive", "Sales Executive", "Account Manager", "Business Development Rep", "Territory Manager",
          "Client Partner", "Sales Consultant", "Revenue Manager", "Sales Associate", "Relationship Manager"]
def panel_b19(t):
    P = GROUND_IMG.copy()
    title_in(P, t, "THE MISTAKE", 356.78, 92, 46)
    cw, ch = 224, 88; gx, gy = 16, 18; x0 = 640 - (5 * cw + 4 * gy) / 2
    split = smoother((t - 363.0) / 0.8)
    dim9 = 1 - 0.68 * smoother((t - cue("other nine")) / 0.5)
    p = reveal(t, 357.2, 0.1, 14 / FPS)
    for i, name in enumerate(TITLES):
        col, row = i % 5, i // 5
        tx = x0 + col * (cw + gy); ty = 268 + row * (ch + gx)
        st = clamp(split * 1.4 - 0.04 * i) if i else clamp(split * 1.4)
        cx = 640 - cw / 2 + (tx - (640 - cw / 2)) * smoother(st); cy = 318 + (ty - 318) * smoother(st)
        if i > 0 and split <= 0: continue
        al = (p if i == 0 else 1.0) * (1.0 if i == 0 else dim9) if split > 0 else p
        if i == 0 and split <= 0:
            glass(P, 640 - 190, 318 - 49 + (1 - p) * 14, 380, 98, alpha=p, r=26, highlight=0.8)
            put_text(P, name, 30, 640, 318 + (1 - p) * 14, 700, alpha=p, anchor="cm")
            continue
        glass(P, cx, cy, cw, ch, alpha=al, r=22, highlight=1.0 if i == 0 else 0.0)
        put_text(P, name, 20, cx + cw / 2, cy + ch / 2, 600 if i == 0 else 400, alpha=al, anchor="cm", maxw=cw - 28, align="center")
    lab = reveal(t, 363.1, 0.1)
    if lab > 0 and split > 0.5: put_text(P, "10 companies, 10 names", 26, 640, 500, 500, alpha=lab * clamp((split - 0.5) * 2), anchor="cm")
    o = reveal(t, cue("other nine"), 0.1)
    if o > 0: put_text(P, "you only ever see 1 of 10", 26, 640, 572 + (1 - o) * 8, 400, alpha=o, anchor="cm", italic=True)
    return P

PROMPT = [("Here", 380.38), ("is", 380.48), ("my", 380.60), ("resume,", 380.74), ("list", 381.02), ("every", 381.78), ("job", 382.20),
          ("title", 382.46), ("companies", 382.72), ("use", 383.12), ("for", 383.50), ("roles", 383.78), ("I’m", 384.14), ("qualified", 384.40),
          ("for,", 384.80), ("including", 385.22), ("ones", 385.66), ("I", 386.28), ("might", 386.56), ("not", 386.82), ("think", 387.04), ("of.", 387.34)]
def panel_b20(t):
    P = GROUND_IMG.copy()
    title_in(P, t, "THE PROMPT", 375.0, 92, 46)
    for nm, x, c in (("claude", 470, 374.6), ("chatgpt", 666, 375.18)):
        q = pop((t - c) / 0.4, 1.3)
        if q > 0: put_icon(P, nm, 52, x - 26, 150, clamp(q * 2), scale=max(q, 0.05))
    put_text(P, "or", 18, 568, 176, 300, alpha=reveal(t, 375.0), anchor="cm", italic=True)
    gp = reveal(t, 378.9, 0.1, 16 / FPS)
    if gp > 0:
        X, Y, Wd, Hh = 150 + (1 - gp) * 40, 238, 980, 250
        glass(P, X, Y, Wd, Hh, alpha=gp, r=28, highlight=0.7)
        put_text(P, "PROMPT", 15, X + 34, Y + 34, 800, color=ROSE_HEX, alpha=gp, anchor="lm")
        full = " ".join(w for w, _ in PROMPT)
        lines = wrap(full, 30, 400, Wd - 80)
        idx = 0; yy = Y + 84
        for ln in lines:
            ws = ln.replace("**", "").split(" "); vis = []
            for w in ws:
                st = PROMPT[idx][1]; dur = 0.26
                n = int(round(len(w) * clamp((t - st) / dur)))
                vis.append(w[:n]); idx += 1
                if n < len(w): vis += [""] * (len(ws) - len(vis)); break
            txt = " ".join(v for v in vis if v != "" or False)
            if txt.strip(): put_text(P, txt, 30, X + 40, yy, 400, alpha=gp, anchor="lm")
            yy += 44
            if idx < len(PROMPT) and t < PROMPT[idx - 1][1] + 0.3 and len(vis) < len(ws): break
    for txt, c, x in (("Different titles", 388.62, 330), ("Search each one", 394.4, 640)):
        q = reveal(t, c)
        if q > 0:
            glass(P, x - 130, 540 + (1 - q) * 12, 260, 50, alpha=q, r=25, tint=0.85)
            put_text(P, txt, 20, x, 565 + (1 - q) * 12, 600, alpha=q, anchor="cm")
    return P

def panel_b26(t):
    P = GROUND_IMG.copy()
    title_in(P, t, "WHY MIDNIGHT?", 555.2, 92, 46)
    X0, X1, Y = 100, 1180, 330; unit = (X1 - X0) / 24
    wins = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 24)]
    c5 = cue("five hours sessions")
    for i, (h0, h1) in enumerate(wins):
        p = reveal(t, c5 + 0.28 * i, 0.1)
        if p <= 0: continue
        lit = smoother((t - cue("while I'm asleep")) / 0.6) if i == 0 else 0.0
        x = X0 + h0 * unit + 4; w = (h1 - h0) * unit - 8
        glass(P, x, Y - 56 + (1 - p) * 14, w, 112, alpha=p, r=22, tint=0.7, highlight=lit)
        if lit > 0:
            over(P, fill_sprite(w, 112, 22, RASP_HEX, 0.55 * lit), x, Y - 56, 1.0)
        put_text(P, f"{h1 - h0} h", 28, x + w / 2, Y + (1 - p) * 14, 700 if i == 0 else 400, alpha=p * (0.5 + 0.5 * (1 if i == 0 else 0.0) + 0.3 * (1 - lit) * (i > 0)), anchor="cm")
    for h in (0, 6, 12, 18, 24):
        a = reveal(t, c5 - 0.2)
        put_text(P, f"{h:02d}:00", 17, X0 + h * unit, Y + 92, 400, alpha=a * 0.7, anchor="cm")
    m = reveal(t, 555.74)
    if m > 0:
        glass(P, X0 - 40, Y - 130 + (1 - m) * 10, 150, 44, alpha=m, r=22, tint=0.85, highlight=1.0)
        put_text(P, "MIDNIGHT", 18, X0 + 35, Y - 108 + (1 - m) * 10, 800, alpha=m, anchor="cm")
    s = reveal(t, cue("while I'm asleep"), 0.1)
    if s > 0:
        put_text(P, "used while you sleep", 30, X0 + 2.5 * unit, Y + 156 + (1 - s) * 10, 700, color=ROSE_HEX, alpha=s, anchor="cm", glow=0.5)
    for txt, c, x, ic in (("$20 Claude plan", cue("claude plan", after=560), 330, "claude"), ("Never ran out", cue("never run out", after=560), 700, None)):
        if t < c - 0.3: continue
        q = reveal(t, c)
        glass(P, x - 150, 646 + (1 - q) * 10, 300, 52, alpha=q, r=26, tint=0.85)
        if ic: put_icon(P, ic, 30, x - 128, 657 + (1 - q) * 10, q)
        put_text(P, txt, 21, x + (14 if ic else 0), 672 + (1 - q) * 10, 600, alpha=q, anchor="cm")
    for txt, c, x in (("Fresh by morning", cue("fresh by morning"), 330), ("Still counts weekly", 566.0, 700)):
        q = reveal(t, c)
        if q > 0:
            glass(P, x - 150, 556 + (1 - q) * 10, 300, 52, alpha=q, r=26, tint=0.85)
            put_text(P, txt, 21, x, 582 + (1 - q) * 10, 600, alpha=q, anchor="cm")
    return P

FULL = {"b05": (panel_b05, "right"), "b19": (panel_b19, "bottom"), "b20": (panel_b20, "right"), "b26": (panel_b26, "top")}

def slide_composite(fb, P, k, kp, direction):
    """Panel slides over the footage with a 180-degree shutter blur; footage pushes and dims."""
    if direction == "bottom": fb = fb.transpose(1, 0, 2); P = P.transpose(1, 0, 2)
    elif direction == "top": fb = fb[::-1].transpose(1, 0, 2); P = P[::-1].transpose(1, 0, 2)
    fb = np.ascontiguousarray(fb); P = np.ascontiguousarray(P); L = fb.shape[1]
    blur_px = int(round(abs(k - kp) * L)); xo = int(round((1 - k) * L))
    push = int(round(k * 90 * L / 1280))
    if push: fb = np.concatenate([fb[:, push:], np.repeat(fb[:, -1:], push, 1)], 1)
    fb = fb * (1 - 0.45 * k)
    pblur = max(1, int(round(abs(k - kp) * 90)))
    if pblur > 1: fb = cv2.blur(fb, (pblur, 1))
    if xo < L:
        Pv = P[:, :L - xo]
        if blur_px > 1:
            ext = np.concatenate([fb[:, max(xo - blur_px, 0):xo], Pv], 1); ext = cv2.blur(ext, (blur_px, 1)); fb[:, max(xo - blur_px, 0):] = ext
        else: fb[:, xo:] = Pv
        sw = min(40, max(xo - blur_px, 0))
        if sw > 0:
            g = np.linspace(0, 0.35, sw)[None, :, None]; x1 = max(xo - blur_px, 0); fb[:, x1 - sw:x1] *= (1 - g)
    if direction == "bottom": fb = fb.transpose(1, 0, 2)
    elif direction == "top": fb = fb.transpose(1, 0, 2)[::-1]
    return np.ascontiguousarray(fb)

def fullscreen_frame(base, t, bid):
    b = BY_ID[bid]; a, e = b["start"], b["end"]; fn, direction = FULL[bid]
    P = fn(t); IN, OUT = 15 / FPS, 12 / FPS
    if t < a + IN: k = smoother((t - a) / IN); kp = smoother((t - 0.5 / FPS - a) / IN)
    elif t > e - OUT: k = smoother((e - t) / OUT); kp = smoother((e - t - 0.5 / FPS) / OUT)
    else: return P
    return slide_composite(base, P, k, kp, direction)

# ---------------------------------------------------------------- frame dispatch
CAM_DRAW = {"b01": b01, "b02": b02, "b03": b03, "b04": b04, "b06": b06, "b10": b10, "b11": b11, "b12": b12, "b13": b13, "b24": b24,
            "b28": b28, "b29": b29, "b31": b31, "b32": b32, "b33": b33, "b34": b34}

def render(n, S):
    """Returns (frame, reference-without-overlay or None for the protected-region check)."""
    t = n / FPS; b = beat_at(t)
    base = base_frame(S, n)
    if is_screen(n) and not (b and b["treatment"] in ("FULLSCREEN_MOTION", "PRESENTER_INSET")):
        out = base.copy(); draw_hl(out, t); screen_chips(out, t); rule_pill(out, t, 238.3, 270.4, [("One filter = the ", 0), ("whole strategy", 1)], 267.9, y=630)
        return out, None
    if b is None: return base, None
    bid = b["id"]
    if bid == "b30": return b30(base.copy(), t), None          # quote: footage blurs in place (no slide)
    if b["treatment"] == "FULLSCREEN_MOTION": return fullscreen_frame(base, t, bid), None
    if b["treatment"] == "PRESENTER_INSET": return inset_frame(S, t, bid), None
    fn = CAM_DRAW.get(bid)
    if fn is None: return base, None
    out = base.copy(); fn(out, t)
    return out, base

def pbox(n):
    for (a, bb), box in PBOX.items():
        if a <= n < bb: return box
    return None

def decode_frame(n):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{n / FPS:.4f}", "-i", SRC, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(720, 1280, 3).astype(np.float32)

def main():
    f0, f1, outp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    if len(sys.argv) > 4 and sys.argv[4] == "--png":
        os.makedirs(outp, exist_ok=True)
        for n in [int(x) for x in sys.argv[5:]]:
            out, _ = render(n, decode_frame(n))
            cv2.imwrite(f"{outp}/f{n:05d}.png", cv2.cvtColor(np.clip(out + 0.5, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        return
    safe = {"max_overlay_delta_in_protected": 0.0, "frames_checked": 0, "frames_written": 0}
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f0 / FPS:.6f}", "-i", SRC, "-frames:v", str(f1 - f0), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-threads", "2",
                            "-x264-params", "keyint=60:min-keyint=60:scenecut=0", outp], stdin=subprocess.PIPE)
    FS = 1280 * 720 * 3; n = f0
    while n < f1:
        buf = dec.stdout.read(FS)
        if len(buf) < FS: break
        S = np.frombuffer(buf, np.uint8).reshape(720, 1280, 3).astype(np.float32)
        out, ref = render(n, S)
        box = pbox(n)
        if ref is not None and box is not None:
            x, y, w, h = box
            safe["max_overlay_delta_in_protected"] = max(safe["max_overlay_delta_in_protected"], float(np.abs(out[y:y + h, x:x + w] - ref[y:y + h, x:x + w]).max())); safe["frames_checked"] += 1
        enc.stdin.write(np.clip(out + 0.5, 0, 255).astype(np.uint8).tobytes()); n += 1
        if (n - f0) % 300 == 0: open(outp + ".progress", "w").write(str(n - f0))
    enc.stdin.close(); enc.wait(); dec.wait()
    safe["frames_written"] = n - f0
    json.dump(safe, open(outp + ".safe.json", "w"))

if __name__ == "__main__":
    main()
