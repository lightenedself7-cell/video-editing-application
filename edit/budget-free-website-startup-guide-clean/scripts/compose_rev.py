"""Revision compositor (pass 1, opening): adds behind-the-head titles, a ringed list over the presenter,
UI/address zooms inside framed screens and a named-rule highlight. Original compose.py is untouched.

Usage: compose_rev.py <f0> <f1_exclusive> <out.mp4>            render a chunk
       compose_rev.py --png <outdir> <frame> [<frame> ...]    render stills
"""
import os, sys, json, subprocess
import numpy as np, cv2
HERE = "/home/dev/video-editing-application/edit/budget-free-website-startup-guide-clean/scripts"
sys.path.insert(0, HERE)
import compose as C
from gfx import *

FPS = 30
MATTE = "/home/dev/videos/rev/matte"

# ---------- matte ----------
def matte_at(n):
    p = f"{MATTE}/m{n:05d}.png"
    if not os.path.exists(p): return None
    m = cv2.imread(p, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    m = np.clip((m - 0.15) / 0.7, 0, 1)            # tighten the soft edge
    m = cv2.GaussianBlur(m, (0, 0), 1.1)
    return m[..., None]

# ---------- behind-the-head title ----------
def behind_title(base, n, spec, t):
    a, e, cue = spec["t0"], spec["t1"], spec["cue"]
    pin = clamp((t - cue) / 0.35); pout = ease_out((e - t) / 0.28)
    k = min(pin, pout)
    if k <= 0: return base
    m = matte_at(n)
    if m is None: return base
    s = 0.92 + 0.08 * ease_back(pin, 1.5)
    size = spec["size"]; yc = spec["y"]; gap = spec["gap"]; cx = spec.get("cx", 640)
    wl = text_width(spec["left"], size, 800, 800); wr = text_width(spec["right"], size, 800, 800)
    xl = cx - gap / 2 - wl / 2; xr = cx + gap / 2 + wr / 2     # the head sits in the gap between the two words
    L = np.zeros((720, 1280, 3), np.float32)                    # text layer (white on black) for glow + mask
    put_text(L, spec["left"], size, xl, yc, 800, anchor="cm", alpha=k, scale=s)
    put_text(L, spec["right"], size, xr, yc, 800, anchor="cm", alpha=k, scale=s)
    if spec.get("lead"):
        put_text(L, spec["lead"], 30, xl - wl / 2 + 4, yc - size * 0.80, 300, anchor="lm", alpha=k * clamp((t - cue - 0.1) / 0.3))
    if spec.get("qual"):
        put_text(L, spec["qual"], 26, xr + wr / 2 - 4, yc + size * 0.80, 300, anchor="rm", alpha=k * clamp((t - cue - 0.25) / 0.3))
    mask = L[..., 0:1] / 255.0
    glow = np.clip(cv2.GaussianBlur(mask[..., 0], (0, 0), 16) * 0.9, 0, 0.8)[..., None]
    T = base * (1 - glow) + WHITE * glow                        # soft white glow, no sprite edges
    T = T * (1 - mask) + WHITE * mask
    return T * (1 - m) + base * m

HOOK = dict(t0=1.0, t1=4.9, cue=1.12, left="HOTEL", right="WEBSITE", gap=300, size=84, y=130, cx=640, lead="My dad's", qual="built for under $10")
TWOHRS = dict(t0=44.2, t1=47.8, cue=44.32, left="UNDER", right="2 HOURS", gap=350, size=80, y=130, cx=628, lead=None, qual="start to finish")

# ---------- ringed list over the presenter ----------
LIST = [("Step by step", 37.40), ("Free AI tools", 39.50), ("The simple fix", 41.52)]
LIST_T0, LIST_T1 = 37.2, 43.9
def draw_ring_list(out, t):
    kout = ease_out((LIST_T1 - t) / 0.5)
    if kout <= 0: return
    # soft dark side wash so the text reads on any wall colour
    wash = np.zeros((720, 330, 4), np.float32); wash[..., :3] = GROUND
    g = np.linspace(0.55, 0.0, 330)[None, :]
    wash[..., 3] = np.repeat(g, 720, 0) * clamp((t - LIST_T0) / 0.4) * kout
    over(out, wash, 0, 0)
    y = 210
    for i, (txt, cue) in enumerate(LIST):
        p = reveal(t, cue)
        if p > 0:
            ox = 30 + (1 - p) * -30
            on = clamp((t - cue) / 0.3)
            num_badge(out, ox + 26, y, 24, i + 1, fill=0.0, alpha=p * kout, active=on * (1 if i == 2 and t > 44.2 else 0.0))
            put_text(out, txt, 23, ox + 66, y, 600, alpha=p * kout, anchor="lm", maxw=190, glow=0.15, bold_weight=800)
        y += 92

# ---------- named-rule highlight ----------
RULE = (154.0, 157.4, 154.08)
def draw_rule(out, t):
    a, e, cue = RULE
    k = min(ease_out((t - a) / 0.4), ease_out((e - t) / 0.3))
    if k <= 0: return
    out *= (1 - 0.38 * k)                                   # calm the screen so the rule reads at the centre
    w, h = 980, 124; x = 640 - w / 2; y = 360 - h / 2 + (1 - k) * 16
    glass(out, x, y, w, h, alpha=k, r=62, highlight=1.0, tint=0.7)
    put_text(out, "The **golden rule** of building with **AI Studio**", 40, 640, 360 + (1 - k) * 16, 400, alpha=k, anchor="cm", bold_weight=800, glow=0.2)

# ---------- zoom inside the framed screen ----------
# keyframes: (t, focus_x, focus_y, scale) in source pixels; eased between neighbours
ZOOMS = [  # (keyframes (t, fx, fy, scale) in source px, bubble_right)
    ([(126.80, 640, 360, 1.0), (127.25, 190, 74, 1.9), (129.35, 190, 74, 1.9), (129.80, 640, 360, 1.0)], False, None),     # aistudio.google.com
    ([(87.30, 640, 360, 1.0), (87.80, 470, 586, 1.75), (90.40, 470, 586, 1.75), (91.10, 480, 628, 1.75), (93.20, 480, 628, 1.75), (93.70, 640, 360, 1.0)], False, None),  # prep doc
    ([(216.95, 640, 360, 1.0), (217.40, 120, 560, 1.8), (219.60, 120, 560, 1.8), (220.10, 640, 360, 1.0)], True, "flat"),    # click Upload (flat fill: no smeared bubble)
    ([(147.00, 640, 360, 1.0), (147.45, 1027, 495, 2.0), (152.80, 1027, 495, 2.0), (153.30, 640, 360, 1.0)], False, None),    # mic: click and talk
    ([(464.60, 640, 360, 1.0), (465.05, 1040, 650, 1.8), (467.20, 1040, 650, 1.8), (467.70, 640, 360, 1.0)], False, None),   # Restore version
    ([(487.90, 640, 360, 1.0), (488.40, 335, 160, 2.0), (492.60, 335, 160, 2.0), (493.30, 1180, 160, 2.0), (496.00, 1180, 160, 2.0),
      (499.20, 1150, 270, 2.0), (509.20, 1150, 270, 2.0), (509.80, 640, 360, 1.0)], False, None),                           # angle bracket -> Export -> Download zip
    ([(572.30, 640, 360, 1.0), (572.75, 230, 56, 1.9), (575.00, 230, 56, 1.9), (575.45, 640, 360, 1.0)], False, None),     # free cloudflare address
    ([(650.30, 640, 360, 1.0), (650.75, 300, 56, 1.9), (654.00, 300, 56, 1.9), (654.45, 640, 360, 1.0)], False, None),     # pagespeed.web.dev
]
def zoom_state(t):
    for kf, br, mode in ZOOMS:
        if kf[0][0] <= t <= kf[-1][0]:
            for (t0, x0, y0, s0), (t1, x1, y1, s1) in zip(kf, kf[1:]):
                if t0 <= t <= t1:
                    u = smoother((t - t0) / (t1 - t0))
                    return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, s0 + (s1 - s0) * u, br, mode
    return None

_orig_fs = C.framed_screen; _orig_bub = C.bubble_at
def framed_screen_zoom(S, n):
    z = zoom_state(n / FPS)
    if z is None or z[2] < 1.001: return _orig_fs(S, n)
    fx, fy, s, br, mode = z
    cw, ch = 1280 / s, 720 / s
    x0 = min(max(fx - cw / 2, 0), 1280 - cw); y0 = min(max(fy - ch / 2, 0), 720 - ch)
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    Sbase = S
    c0 = _orig_bub(n)
    if c0:  # remove the baked bubble so it is not enlarged by the zoom; the real one is redrawn below
        cx, cy, r = c0; pad = int(r) + 14
        xa, ya, xb, yb = max(int(cx) - pad, 0), max(int(cy) - pad, 0), min(int(cx) + pad, 1280), min(int(cy) + pad, 720)
        crop = np.clip(S[ya:yb, xa:xb], 0, 255).astype(np.uint8)
        mk = np.zeros(crop.shape[:2], np.uint8); cv2.circle(mk, (int(cx) - xa, int(cy) - ya), int(r) + 6, 255, -1)
        Sbase = S.copy()
        if mode == "flat":   # flat colour from the ring just outside the bubble, feathered: clean, no smear
            ring = cv2.dilate(mk, np.ones((25, 25), np.uint8)) & ~cv2.dilate(mk, np.ones((9, 9), np.uint8))
            col = np.median(crop[ring > 0], axis=0)
            fm = cv2.GaussianBlur(mk.astype(np.float32) / 255, (0, 0), 3)[..., None]
            Sbase[ya:yb, xa:xb] = S[ya:yb, xa:xb] * (1 - fm) + col * fm
        else:
            Sbase[ya:yb, xa:xb] = cv2.inpaint(crop, mk, 6, cv2.INPAINT_TELEA).astype(np.float32)
    Sz = cv2.warpAffine(Sbase, M, (1280, 720), flags=cv2.INTER_CUBIC)
    C.bubble_at = lambda n_: None
    try: out = _orig_fs(Sz, n)
    finally: C.bubble_at = _orig_bub
    c = _orig_bub(n)
    if c:
        cxo = C.SX + c[0] * C.SF
        if br: cxo = C.SX + C.SW - c[2] * C.SF - 26      # keep the round bubble, tucked bottom-right so it never covers the target
        C.draw_bubble(out, S, c, cxo, C.SY + c[1] * C.SF, C.SF)
    return out
C.framed_screen = framed_screen_zoom


# ---------- static vs dynamic, presenter full-frame (b24) ----------
def side_card(out, x, y, w, h, k, hl=0.0):
    glass(out, x + (1 - k) * (-40 if x < 640 else 40), y, w, h, alpha=k, r=22, highlight=hl)

def draw_compare_full(out, t, a, e):
    k_out = ease_out((e - 0.4 - t) / 0.4)
    if k_out <= 0: return
    hl = smoother((t - 344.66) / (14 / FPS))
    CARD_Y, CARD_H = 100, 460
    # left: STATIC (short points, timed to the words)
    pL = reveal(t, 306.06) * k_out
    if pL > 0:
        side_card(out, 22, CARD_Y, 236, CARD_H, pL)
        ox = 22 + (1 - pL) * -40
        put_text(out, "STATIC", 26, ox + 24, 134, 800, alpha=pL, glow=0.4)
        for txt, cue, yy in [("A **brochure**", 328.9, 196), ("Same for **everyone**", 329.4, 268), ("Just **files**", 331.1, 340),
                             ("Info, call or **WhatsApp**", 335.7, 412)]:
            p = reveal(t, cue) * k_out
            if p > 0: put_text(out, txt, 20, ox + 24 + (1 - p) * -14, yy, 400, alpha=p, maxw=190, bold_weight=800)
    # right: DYNAMIC
    pR = reveal(t, 305.14) * k_out
    if pR > 0:
        side_card(out, 1000, CARD_Y, 258, CARD_H, pR, hl)
        ox = 1000 + (1 - pR) * 40
        put_text(out, "DYNAMIC", 26, ox + 24, 134, 800, alpha=pR, glow=0.4)
        for txt, cue, yy in [("Different for **each person**", 307.9, 196), ("Train booking, **banking app**", 313.5, 326),
                             ("Server, database, **logins**", 323.4, 398), ("**Live** availability, payments, accounts", 346.1, 470)]:
            p = reveal(t, cue) * k_out
            if p > 0: put_text(out, txt, 20, ox + 24 + (1 - p) * 14, yy, 400, alpha=p, maxw=212, bold_weight=800)
        pa = reveal(t, 311.10) * k_out
        if pa > 0:
            over(out, C.ICON["Amazon"], ox + 24, 258 + (1 - pa) * 8, pa)
            put_text(out, "Amazon", 18, ox + 92, 285, 500, alpha=pa * 0.9, anchor="lm")
    p = reveal(t, 344.66) * k_out
    if p > 0:
        glass(out, 330, 624 + (1 - p) * 12, 620, 60, alpha=p, r=30, highlight=1.0)
        put_text(out, "No limits \u2192 a full **React app**", 24, 640, 654 + (1 - p) * 12, 500, alpha=p, anchor="cm", bold_weight=800)

# ---------- Upload menu row: crisp redraw + pulse (the recording's bubble hides the end of the word) ----------
UP_BOX = (22, 575, 132, 607)      # source px of the "Upload" menu row
UP_T0, UP_T1 = 217.40, 220.10
def draw_upload_row(out, S, t):
    z = zoom_state(t)
    if z is None or z[2] < 1.15 or not (UP_T0 <= t <= UP_T1): return
    fx, fy, sc = z[0], z[1], z[2]
    cw, ch = 1280 / sc, 720 / sc
    x0 = min(max(fx - cw / 2, 0), 1280 - cw); y0 = min(max(fy - ch / 2, 0), 720 - ch)
    k = sc * C.SF
    def P(x, y): return C.SX + (x - x0) * k, C.SY + (y - y0) * k
    a = ease_out((t - 217.62) / 0.25) * ease_out((UP_T1 - 0.45 - t) / 0.3) * clamp((sc - 1.15) / 0.5)
    if a <= 0: return
    xa, ya = P(UP_BOX[0], UP_BOX[1]); xb, yb = P(UP_BOX[2], UP_BOX[3])
    w, h = int(round(xb - xa)), int(round(yb - ya))
    bg = np.median(S[578:603, 24:34].reshape(-1, 3), axis=0)
    # tile
    m = rrect_mask(w, h, int(h * 0.22))
    spr = np.zeros((h, w, 4), np.float32); spr[..., :3] = bg; spr[..., 3] = m
    over(out, spr, xa, ya, a)
    # upload glyph
    g = np.zeros((h, w), np.uint8); cx, cy = int(h * 0.55), int(h * 0.5); u = h * 0.22; th = max(2, int(h * 0.07))
    cv2.line(g, (cx, int(cy + u)), (cx, int(cy - u)), 255, th, cv2.LINE_AA)
    cv2.line(g, (cx, int(cy - u)), (int(cx - u * 0.7), int(cy - u * 0.2)), 255, th, cv2.LINE_AA)
    cv2.line(g, (cx, int(cy - u)), (int(cx + u * 0.7), int(cy - u * 0.2)), 255, th, cv2.LINE_AA)
    cv2.line(g, (int(cx - u * 0.9), int(cy + u * 1.25)), (int(cx + u * 0.9), int(cy + u * 1.25)), 255, th, cv2.LINE_AA)
    gs = np.zeros((h, w, 4), np.float32); gs[..., :3] = hexc("#3C4043"); gs[..., 3] = g / 255.0
    over(out, gs, xa, ya, a)
    put_text(out, "Upload", int(round(h * 0.44)), xa + h * 0.98, ya + h * 0.5, 450, color="#3C4043", alpha=a, anchor="lm")
    # pulse ring (two soft pulses) + expanding ripple
    ph = (t - 217.7)
    pulse = 0.55 + 0.45 * np.sin(2 * np.pi * ph * 1.4) if ph > 0 else 0.55
    ring = rrect_ring(w + 14, h + 14, int(h * 0.22) + 7, 2.2, 9.0, 0.9, "#E25C8E")
    over(out, ring, xa - 7 - 24, ya - 7 - 24, a * pulse)
    r = ((t - 217.9) % 1.0) if t > 217.9 else 1.0
    e = ease_out(r); grow = int(e * h * 0.9)
    rr = rrect_ring(w + 14 + 2 * grow, h + 14 + 2 * grow, int(h * 0.22) + 7 + grow, 1.6, 6.0, 0.7, "#E25C8E")
    over(out, rr, xa - 7 - grow - 24, ya - 7 - grow - 24, a * (1 - e) * 0.8)
    # cursor on top (tip at the original pointer position)
    tx, ty = P(44, 598); cs = k * 0.55
    pts = np.array([[0, 0], [0, 17], [4.2, 13.2], [7.2, 20], [9.6, 19], [6.8, 12.4], [12, 12.4]], np.float32) * cs + np.array([tx, ty], np.float32)
    cm = np.zeros((720, 1280), np.uint8); cv2.fillPoly(cm, [pts.astype(np.int32)], 255, cv2.LINE_AA)
    edge = cv2.dilate(cm, np.ones((3, 3), np.uint8))
    for mask, col in ((edge, np.array([30, 30, 30], np.float32)), (cm, np.array([255, 255, 255], np.float32))):
        al = (mask.astype(np.float32) / 255.0)[..., None] * a
        out[:] = out * (1 - al) + col * al

# ---------- frame ----------
def reveal(t, cue, lead=0.25, dur=12 / FPS): return ease_out((t - (cue - lead)) / dur)

def render_rev(n, S):
    t = n / FPS
    if 44.1 <= t < 47.9:                      # replaces the right-column keyword
        C.draw_keyword = lambda *a, **k: None
    b24 = C.BEATS["b24"]
    if b24["start"] <= t < b24["end"]:
        out = C.base_frame(S, n).copy(); draw_compare_full(out, t, b24["start"], b24["end"])
        return out, None
    out, ref = C.render(n, S)
    if UP_T0 <= t <= UP_T1: draw_upload_row(out, S, t)
    if 1.0 <= t < 4.95: out = behind_title(out, n, HOOK, t)
    elif 44.1 <= t < 47.9: out = behind_title(out, n, TWOHRS, t)
    elif LIST_T0 <= t < LIST_T1: draw_ring_list(out, t)
    elif RULE[0] <= t < RULE[1]: draw_rule(out, t)
    return out, ref

def png_mode(outdir, frames):
    os.makedirs(outdir, exist_ok=True)
    for n in frames:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{n / FPS:.4f}", "-i", C.SRC, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        S = np.frombuffer(raw, np.uint8).reshape(720, 1280, 3).astype(np.float32)
        out, _ = render_rev(n, S)
        cv2.imwrite(f"{outdir}/r{n:05d}.png", cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))

def chunk_mode(f0, f1, outp):
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f0 / FPS:.6f}", "-i", C.SRC, "-frames:v", str(f1 - f0), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-threads", "2",
                            "-x264-params", "keyint=60:min-keyint=60:scenecut=0", outp], stdin=subprocess.PIPE)
    FS = 1280 * 720 * 3; n = f0
    while n < f1:
        buf = dec.stdout.read(FS)
        if len(buf) < FS: break
        S = np.frombuffer(buf, np.uint8).reshape(720, 1280, 3).astype(np.float32)
        out, _ = render_rev(n, S)
        enc.stdin.write(np.clip(out + 0.5, 0, 255).astype(np.uint8).tobytes()); n += 1
        if (n - f0) % 150 == 0: open(outp + ".progress", "w").write(str(n - f0))
    enc.stdin.close(); enc.wait(); dec.wait()

if __name__ == "__main__":
    if sys.argv[1] == "--png": png_mode(sys.argv[2], [int(x) for x in sys.argv[3:]])
    else: chunk_mode(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
