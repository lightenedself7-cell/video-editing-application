"""Teal Spotlight components. Livelier than Clean Creator: tilted labels, bold offset shadows, one marigold pop.

Signature: fn(ctx, beat, props, t, out, S) -> frame   (see clean-creator/components.py for the argument meanings)
Sizes are written for a 1280x720 design space; multiply by `u` (= width / 1280).
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from renderer.gfx import (clamp, ease_back, ease_out, hexc, over, put_text, rrect_mask, rrect_ring, smoother, text_width, wrap)


# ---------- helpers ----------
def _col(ctx, name):
    return ctx.tokens["colors"][name]


def _poly_sprite(pts, color, ss=4):
    """RGBA sprite of a filled polygon given absolute points; returns (sprite, x, y)."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = int(np.floor(min(xs))) - 2, int(np.floor(min(ys))) - 2
    w, h = int(np.ceil(max(xs))) - x0 + 2, int(np.ceil(max(ys))) - y0 + 2
    img = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(img).polygon([((px - x0) * ss, (py - y0) * ss) for px, py in pts], fill=255)
    a = np.asarray(img.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255
    spr = np.zeros((h, w, 4), np.float32)
    spr[..., :3] = hexc(color)
    spr[..., 3] = a
    return spr, x0, y0


def _poly(out, pts, color, alpha=1.0):
    spr, x, y = _poly_sprite(pts, color)
    over(out, spr, x, y, alpha)


def _rot_pts(pts, cx, cy, deg):
    r = np.deg2rad(deg)
    c, s = np.cos(r), np.sin(r)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def _rect_pts(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _rotated_text(out, text, size, cx, cy, deg, weight, color, alpha, face="display", glow=0.0, scale=1.0):
    """Draw text centred on (cx, cy), rotated by deg (positive = clockwise on screen)."""
    from renderer.gfx import text_sprite
    rgba, pad = text_sprite(text, int(round(size)), weight, color, glow, False, 800, "left", 0, 1.25, face)
    if scale != 1.0:
        rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = rgba.shape[:2]
    r = np.deg2rad(deg)
    nw, nh = int(abs(w * np.cos(r)) + abs(h * np.sin(r))) + 2, int(abs(w * np.sin(r)) + abs(h * np.cos(r))) + 2
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -deg, 1.0)
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    rot = cv2.warpAffine(rgba, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    rot[..., :3] = rgba[0, 0, :3]
    over(out, rot, cx - nw / 2, cy - nh / 2, alpha)


def _enter(ctx):
    return ctx.tokens["motion"]["enter_frames"] / ctx.fps


def _exit(ctx):
    return ctx.tokens["motion"]["exit_frames"] / ctx.fps


def _caps(text):
    """Upper-case but leave the ** emphasis markers alone."""
    return text.upper()


def _shadowed_poly(out, pts, color, shadow_color, offset, alpha):
    _poly(out, [(x + offset, y + offset) for x, y in pts], shadow_color, alpha * 0.9)
    _poly(out, pts, color, alpha)


# ---------- FULLSCREEN_MOTION ----------
def section_title(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    W, H = ctx.W, ctx.H
    a, e = beat["start"], beat["end"]
    k_in = smoother((t - a) / (14 / fps))
    k_out = smoother((e - t) / (12 / fps))
    k = min(k_in, k_out)
    if k <= 0:
        return out
    card = ctx.ground()
    pop, teal, deep, shadow, mint = _col(ctx, "pop"), _col(ctx, "accent"), _col(ctx, "deep"), _col(ctx, "shadow"), _col(ctx, "mint")
    local = t - a
    # plus-sign grid
    step = 96 * u
    for gy in np.arange(step / 2, H, step):
        for gx in np.arange(step / 2, W, step):
            arm = 5 * u
            _poly(card, _rect_pts(gx - arm, gy - 0.9 * u, 2 * arm, 1.8 * u), mint, 0.16)
            _poly(card, _rect_pts(gx - 0.9 * u, gy - arm, 1.8 * u, 2 * arm), mint, 0.16)
    # thin diagonal accent lines
    for i, off in enumerate((-0.15, 0.05, 0.25)):
        x0 = W * (0.55 + off)
        drift = 8 * u * np.sin(local * 0.6 + i)
        _poly(card, [(x0 + drift, -10), (x0 + 2.4 * u + drift, -10), (x0 - 0.45 * W + 2.4 * u + drift, H + 10), (x0 - 0.45 * W + drift, H + 10)], teal, 0.3)
    # thick translucent bands, one marigold edge
    bx = (1 - ease_out(local / (16 / fps))) * W * 0.3
    band_top = [(-40 + bx, 0.58 * H), (W + 40 + bx, 0.40 * H), (W + 40 + bx, 0.40 * H + 120 * u), (-40 + bx, 0.58 * H + 120 * u)]
    band_bot = [(-40 - bx, 0.86 * H), (W + 40 - bx, 0.70 * H), (W + 40 - bx, 0.70 * H + 70 * u), (-40 - bx, 0.86 * H + 70 * u)]
    _poly(card, band_top, teal, 0.22)
    _poly(card, band_bot, deep, 0.55)
    _poly(card, [band_top[3], band_top[2], (band_top[2][0], band_top[2][1] + 5 * u), (band_top[3][0], band_top[3][1] + 5 * u)], pop, 0.95)
    cue = props.get("cue", a + 0.3)
    p = clamp((t - (cue - 0.1)) / (14 / fps))
    cx = W / 2
    ty = H * 0.40
    if props.get("kicker"):
        put_text(card, _caps(props["kicker"]), 26 * u, cx, ty - 112 * u + (1 - ease_out(p)) * 10 * u, 700, color=mint, alpha=ease_out(p) * 0.9, anchor="cm", face="display")
    # title lines (one line per \n, wrapped to 86% of the width)
    size = 104 * u
    lines = []
    for chunk in _caps(props["title"]).split("\n"):
        lines += wrap(chunk, int(round(size)), 800, W * 0.86, 800, "display")
    lh = size * 0.98
    for i, line in enumerate(lines):
        pi = ease_out((t - (cue - 0.1 + i * 0.08)) / (14 / fps))
        yy = ty + (i - (len(lines) - 1) / 2) * lh + (1 - pi) * 26 * u
        put_text(card, line, size, cx + 6 * u, yy + 6 * u, 800, color=shadow, alpha=pi * 0.8, anchor="cm", face="display")
        put_text(card, line, size, cx, yy, 800, color=_col(ctx, "text"), alpha=pi, anchor="cm", glow=0.5, face="display")
    # key phrase on a tilted marigold block
    if props.get("key"):
        ksize = 96 * u
        kw = text_width(_caps(props["key"]), int(round(ksize)), 800, 800, "display")
        kcx, kcy = cx, ty + (len(lines) / 2) * lh + 68 * u
        pk = ease_back(clamp((t - (cue + 0.35)) / (12 / fps)), 1.5)
        s = max(pk, 0.001)
        bw, bh = (kw + 70 * u) * s, 124 * u * s
        pts = _rot_pts(_rect_pts(kcx - bw / 2, kcy - bh / 2, bw, bh), kcx, kcy, -3.0)
        _shadowed_poly(card, pts, pop, shadow, 9 * u, clamp(pk * 2))
        _rotated_text(card, _caps(props["key"]), ksize, kcx, kcy, -3.0, 800, _col(ctx, "ground"), clamp(pk * 2), scale=s)
    # brand tiles joined by plus signs
    tiles = props.get("tiles") or []
    if tiles:
        n = len(tiles)
        base = 108 * u
        gap = 74 * u
        total = n * base + (n - 1) * gap
        x = cx - total / 2
        ty2 = H * 0.80
        for i, tile in enumerate(tiles):
            pt = ease_back(clamp((t - tile["cue"]) / (12 / fps)), 1.5)
            if pt > 0:
                big = base * (1.3 if (n % 2 == 1 and i == n // 2 and n > 1) else 1.0)
                spr = ctx.icon(tile["icon"], int(round(big / u)), tile=True)
                sc = max(pt, 0.05)
                spr = cv2.resize(spr, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
                hh, ww = spr.shape[:2]
                tcx, tcy = x + base / 2, ty2
                pad = 8 * u * sc
                border = _rot_pts(_rect_pts(tcx - ww / 2 - pad, tcy - hh / 2 - pad, ww + 2 * pad, hh + 2 * pad), tcx, tcy, (-4, 3, 5, -3)[i % 4])
                _shadowed_poly(card, border, pop if big > base else mint, shadow, 6 * u, clamp(pt * 2))
                over(card, spr, tcx - ww / 2, tcy - hh / 2, clamp(pt * 2))
            if i < n - 1:
                pp = clamp((t - tiles[i + 1]["cue"]) / (8 / fps))
                px, py = x + base + gap / 2, ty2
                arm = 15 * u
                _poly(card, _rect_pts(px - arm, py - 3 * u, 2 * arm, 6 * u), pop, pp)
                _poly(card, _rect_pts(px - 3 * u, py - arm, 6 * u, 2 * arm), pop, pp)
            x += base + gap
    # wipe in from the right, out to the right
    if k >= 0.999:
        return card
    edge = int(round(W * (1 - k)))
    out = out.copy()
    out[:, edge:] = card[:, edge:]
    return out


# ---------- spotlight ----------
def _view_for(ctx, box):
    """Source-pixel view rectangle (x, y, w, h), frame aspect, that frames `box` with padding."""
    W, H = ctx.W, ctx.H
    bw, bh = box["width"], box["height"]
    pad = 1.16
    vw = max(bw * pad, bh * pad * W / H)
    vh = vw * H / W
    if vw >= W:
        return (0.0, 0.0, float(W), float(H))
    cx = box["x"] + bw / 2
    cy = box["y"] + bh / 2
    x = min(max(cx - vw / 2, 0), W - vw)
    y = min(max(cy - vh / 2, 0), H - vh)
    return (x, y, vw, vh)


def _lerp_rect(a, b, p):
    return tuple(x0 + (x1 - x0) * p for x0, x1 in zip(a, b))


def spotlight_box(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    W, H = ctx.W, ctx.H
    a, e = beat["start"], beat["end"]
    zf = ctx.tokens["motion"]["zoom_frames"] / fps
    boxes = props["boxes"]
    full = (0.0, 0.0, float(W), float(H))
    # state machine over boxes: view and box rect interpolated by the zoom progress into the active box
    view, brect, dk = full, None, 0.0
    prev_view, prev_box = full, None
    for b in boxes:
        start = max(b["cue"] - 0.35, a)
        p = smoother((t - start) / zf)
        bx = (float(b["x"]), float(b["y"]), float(b["width"]), float(b["height"]))
        tv = _view_for(ctx, b)
        if p <= 0:
            break
        view = _lerp_rect(prev_view, tv, p)
        brect = bx if prev_box is None else _lerp_rect(prev_box, bx, p)
        dk = p if prev_box is None else 1.0
        prev_view, prev_box = tv, bx
        active = b
    # zoom back out at the end
    pe = smoother((e - t) / zf)
    if pe < 1:
        view = _lerp_rect(full, view, pe)
        dk *= pe
        if brect is not None and pe <= 0:
            brect = None
    if brect is None:
        return out
    vx, vy, vw, vh = view
    s = W / vw
    M = np.float32([[s, 0, -vx * s], [0, s, -vy * s]])
    zoomed = cv2.warpAffine(S, M, (W, H), flags=cv2.INTER_LINEAR if s >= 1 else cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
    # box in output coordinates
    bx0, by0 = (brect[0] - vx) * s, (brect[1] - vy) * s
    bw, bh = brect[2] * s, brect[3] * s
    ix0, iy0, iw, ih = int(round(bx0)), int(round(by0)), max(int(round(bw)), 2), max(int(round(bh)), 2)
    blurred = cv2.GaussianBlur(zoomed, (0, 0), 7 * u * dk + 0.01)
    dimmed = blurred * (1 - 0.58 * dk)
    mask = np.zeros((H, W, 1), np.float32)
    r = max(int(round(16 * u * min(s, 2))), 2)
    m = rrect_mask(iw, ih, min(r, iw // 2, ih // 2))
    x0, y0, x1, y1 = max(ix0, 0), max(iy0, 0), min(ix0 + iw, W), min(iy0 + ih, H)
    if x1 > x0 and y1 > y0:
        mask[y0:y1, x0:x1, 0] = m[y0 - iy0:y1 - iy0, x0 - ix0:x1 - ix0]
    res = dimmed * (1 - mask) + zoomed * mask
    # marker highlight on the key line (starts shortly after the box lands)
    mk = active.get("marker") if boxes else None
    if mk:
        pm = ease_out((t - (active["cue"] + 0.45)) / (14 / fps)) * min(1.0, pe * 3)
        if pm > 0:
            mx0, my0 = (mk["x"] - vx) * s, (mk["y"] - vy) * s
            mw, mh = mk["width"] * s * pm, mk["height"] * s
            xa, ya, xb, yb = max(int(mx0), 0), max(int(my0), 0), min(int(mx0 + mw), W), min(int(my0 + mh), H)
            if xb > xa and yb > ya:
                pop = hexc(_col(ctx, "pop")) / 255.0
                res[ya:yb, xa:xb] = res[ya:yb, xa:xb] * (0.5 + 0.5 * pop) + 34 * pop

    # outline + glow
    mg = kit.px(30)
    ring = rrect_ring(iw, ih, min(r, iw // 2, ih // 2), 3.0 * u, 12.0 * u, 0.85, _col(ctx, "accent"), _col(ctx, "mint"), mg)
    over(res, ring, ix0 - mg, iy0 - mg, clamp(dk * 1.5))
    return res


# ---------- OVERLAY_CARD / SELECTIVE_TEXT ----------
def lower_third_tag(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    a, e = beat["start"], beat["end"]
    cue = props["cue"]
    pin = ease_back(clamp((t - (cue - 0.15)) / (11 / fps)), 1.4)
    pout = ease_out((e - t) / (9 / fps))
    k = min(pin, pout)
    if k <= 0.001:
        return out
    L = beat["layout"]
    size = 40 * u
    txt = _caps(props["text"])
    tw = text_width(txt, int(round(size)), 800, 800, "display")
    sub = props.get("sub")
    h = 64 * u + (26 * u if sub else 0)
    w = tw + 96 * u
    slant = 22 * u
    x, y = L["x"], L["y"]
    dx = (1 - clamp(k)) * -90 * u
    pts = [(x + slant + dx, y), (x + w + dx, y), (x + w - slant + dx, y + h), (x + dx, y + h)]
    cx, cy = x + w / 2 + dx, y + h / 2
    deg = -2.5
    pts = _rot_pts(pts, cx, cy, deg)
    a_ = clamp(pin * 1.6) * clamp(pout * 2)
    _poly(out, [(px + 9 * u, py + 9 * u) for px, py in pts], _col(ctx, "shadow"), a_ * 0.85)
    _poly(out, pts, _col(ctx, "deep"), a_)
    edge = _rot_pts([(x + slant + dx, y), (x + slant + 9 * u + dx, y), (x + 9 * u + dx, y + h), (x + dx, y + h)], cx, cy, deg)
    _poly(out, edge, _col(ctx, "pop"), a_)
    _rotated_text(out, txt, size, cx + 6 * u, cy - (11 * u if sub else 0), deg, 800, _col(ctx, "text"), a_)
    if sub:
        _rotated_text(out, sub, 17 * u, cx + 6 * u, cy + 21 * u, deg, 600, _col(ctx, "mint"), a_, face="regular")
    return out


def explainer_card(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    a, e = beat["start"], beat["end"]
    k = min(ease_out((t - a) / (14 / fps)), ease_out((e - t) / (12 / fps)))
    if k <= 0:
        return out
    L = beat["layout"]
    x, w = L["x"], L["width"]
    rows = props["rows"]
    skeleton = props.get("skeleton", True)
    title = props.get("title")
    pad = 22 * u
    tile = 40 * u
    text_w = w - pad - tile - 22 * u - pad
    row_hs = []
    for r_ in rows:
        n_lines = len(wrap(r_["text"], int(round(21 * u)), 500, text_w))
        row_hs.append(max(tile, n_lines * 27 * u) + (24 * u if skeleton else 0) + 12 * u)
    top = (62 if title else 14) * u
    h = pad + top + sum(row_hs) + 6 * u
    y = (L["y"] + L["height"] / 2) - h / 2
    dx = (1 - k) * 70 * u
    X, Y, Wc, Hc = int(round(x + dx)), int(round(y)), int(w), int(h)
    # soft drop shadow
    sh = np.zeros((Hc + 80, Wc + 80), np.float32)
    sh[40 + 10:40 + 10 + Hc, 40 + 10:40 + 10 + Wc] = rrect_mask(Wc, Hc, int(round(22 * u)))  # shifted right and down: keeps the glow off the presenter side
    sh = cv2.GaussianBlur(sh, (0, 0), 8 * u)
    spr = np.zeros(sh.shape + (4,), np.float32)
    spr[..., :3] = hexc(_col(ctx, "shadow"))
    spr[..., 3] = sh * 0.6
    over(out, spr, X - 40, Y - 40, k)
    # card body with a pastel wash along the top edge
    body = np.zeros((Hc, Wc, 3), np.float32)
    body[:] = hexc(_col(ctx, "card"))
    wash = np.linspace(0, 1, Wc, dtype=np.float32)[None, :, None]
    c1, c2, c3 = hexc(_col(ctx, "wash_a")), hexc(_col(ctx, "wash_b")), hexc(_col(ctx, "wash_c"))
    stops = np.where(wash < 0.5, c1 * (1 - wash * 2) + c2 * (wash * 2), c2 * (1 - (wash - 0.5) * 2) + c3 * ((wash - 0.5) * 2))
    fade = np.clip(1 - np.arange(Hc, dtype=np.float32)[:, None, None] / (70 * u), 0, 1)
    body = body * (1 - fade) + stops * fade
    m = rrect_mask(Wc, Hc, int(round(22 * u)))
    x0, y0 = max(X, 0), max(Y, 0)
    x1, y1 = min(X + Wc, ctx.W), min(Y + Hc, ctx.H)
    if x1 > x0 and y1 > y0:
        mm = m[y0 - Y:y1 - Y, x0 - X:x1 - X][..., None] * k
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - mm) + body[y0 - Y:y1 - Y, x0 - X:x1 - X] * mm
    mg = kit.px(10)
    over(out, rrect_ring(Wc, Hc, int(round(22 * u)), 1.4 * u, 0.0, 0.0, _col(ctx, "card_line"), None, mg), X - mg, Y - mg, k)
    yy = Y + pad
    if title:
        put_text(out, _caps(title), 30 * u, X + pad + 4 * u, yy + 4 * u, 800, color=_col(ctx, "ink"), alpha=k, face="display")
        yy += top - pad + 14 * u
    else:
        yy += top - pad
    centers = []
    ry = yy
    for i, row in enumerate(rows):
        i_row = i
        p = clamp((t - (row["cue"] - 0.25)) / (12 / fps))
        p = ease_out(p)
        cxr = X + pad + tile / 2 + 4 * u
        cyr = ry + tile / 2
        centers.append((cxr, cyr, p))
        if p > 0:
            if row.get("icon"):
                spr_i = ctx.icon(row["icon"], int(round(tile / u)), tile=True)
                over(out, spr_i, cxr - spr_i.shape[1] / 2, cyr - spr_i.shape[0] / 2, p * k)
            else:
                tp = _rot_pts(_rect_pts(cxr - tile / 2, cyr - tile / 2, tile, tile), cxr, cyr, (-4, 3, -2, 4)[i % 4])
                _poly(out, tp, _col(ctx, "accent"), p * k)
                put_text(out, str(i + 1), 22 * u, cxr, cyr, 800, color=_col(ctx, "card"), alpha=p * k, anchor="cm", face="display")
            tx = X + pad + tile + 22 * u + (1 - p) * 14 * u
            put_text(out, row["text"], 21 * u, tx, ry + (2 * u if skeleton else 8 * u), 500, color=_col(ctx, "ink"), alpha=p * k, maxw=Wc - (tx - X) - pad, bold_weight=800)
            if skeleton:
                sy = ry + max(tile, len(wrap(row["text"], int(round(21 * u)), 500, text_w)) * 27 * u) + 6 * u
                for j, frac in enumerate((0.78, 0.52)):
                    bw = (Wc - (tx - X) - pad) * frac * p
                    _poly(out, _rect_pts(tx, sy + 11 * j * u, bw, 6 * u), _col(ctx, "skeleton"), k)
        ry += row_hs[i_row]

    for (x_a, y_a, p_a), (x_b, y_b, p_b) in zip(centers, centers[1:]):
        pl = min(p_a, p_b)
        if pl > 0:
            _poly(out, _rect_pts(x_a - 1 * u, y_a + tile / 2 + 3 * u, 2 * u, (y_b - y_a - tile - 6 * u) * pl), _col(ctx, "card_line"), k)
    return out


COMPONENTS = {
    "section-title": section_title,
    "spotlight-box": spotlight_box,
    "lower-third-tag": lower_third_tag,
    "explainer-card": explainer_card,
}
