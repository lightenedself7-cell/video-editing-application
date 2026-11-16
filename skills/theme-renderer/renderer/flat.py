"""Shared components for the flat, light themes (personal, navy-amber, lime-tech). Tokens decide the look.

A theme's components.py is just `from renderer.flat import COMPONENTS`. What differs per theme lives in tokens.json:
  colors: ground (canvas), accent, text (ink), muted, card, line, badge_text, ornament_a, ornament_b
  flat:   ornament ("wheels" | "balls" | "nodes"), highlight ("pill" | "bar"), grid line colour comes from ground.grid
Sizes are written for 1280x720 and multiplied by u (= width / 1280). Signature: fn(ctx, beat, props, t, out, S) -> frame.
"""
from __future__ import annotations

import cv2
import numpy as np

from .gfx import clamp, ease_back, ease_out, hexc, over, put_text, rrect_mask, rrect_ring, smoother, text_width, wrap


def _c(ctx, name):
    return ctx.tokens["colors"][name]


def _flat(ctx, name, default=None):
    return ctx.tokens.get("flat", {}).get(name, default)


def _reveal(ctx, t, cue, lead=0.25, frames=12):
    return ease_out((t - (cue - lead)) / (frames / ctx.fps))


def _circle(img, cx, cy, r, color, alpha=1.0):
    if alpha <= 0.001 or r <= 0:
        return
    layer = img.copy()
    cv2.circle(layer, (int(round(cx * 16)), int(round(cy * 16))), int(round(r * 16)), tuple(float(v) for v in hexc(color)), -1, cv2.LINE_AA, 4)
    img[:] = img * (1 - alpha) + layer * alpha


def _card(ctx, out, x, y, w, h, alpha=1.0, r=20, fill=None, line=None, shadow=0.16):
    """White card with a soft paper shadow and a hairline border."""
    u = ctx.kit.u
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    if alpha <= 0.001 or w < 2 or h < 2:
        return
    rr = int(round(r * u))
    pad = int(30 * u)
    sh = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    sh[pad + int(8 * u):pad + int(8 * u) + h, pad:pad + w] = rrect_mask(w, h, rr)
    sh = cv2.GaussianBlur(sh, (0, 0), 10 * u)
    spr = np.zeros(sh.shape + (4,), np.float32)
    spr[..., :3] = hexc(_c(ctx, "ink_shadow") if "ink_shadow" in ctx.tokens["colors"] else _c(ctx, "text"))
    spr[..., 3] = sh * shadow
    over(out, spr, x - pad, y - pad, alpha)
    body = np.zeros((h, w, 4), np.float32)
    body[..., :3] = hexc(fill or _c(ctx, "card"))
    body[..., 3] = rrect_mask(w, h, rr)
    over(out, body, x, y, alpha)
    mg = int(10 * u)
    over(out, rrect_ring(w, h, rr, 1.3 * u, 0.0, 0.0, line or _c(ctx, "line"), None, mg), x - mg, y - mg, alpha)


def _ornaments(ctx, out, t, k=1.0):
    """Corner decoration on the canvas, animated from the clock so it keeps moving across beats."""
    kind = _flat(ctx, "ornament", "none")
    W, H, u = ctx.W, ctx.H, ctx.kit.u
    if kind == "wheels":  # continuously rotating 8-spoke wheels, top-left (counter-clockwise) and bottom-right (clockwise)
        for cx, cy, direction in ((0.02 * W, 0.06 * H, -1.0), (0.985 * W, 0.95 * H, 1.0)):
            ang = np.deg2rad(direction * t * ctx.fps * 0.4)
            layer = out.copy()
            col = tuple(float(v) for v in hexc(_c(ctx, "ornament_a")))
            L, sw = 0.156 * W, max(1, int(round(0.028 * W)))
            for i in range(8):
                a = ang + i * np.pi / 4
                cv2.line(layer, (int(cx), int(cy)), (int(cx + L * np.cos(a)), int(cy + L * np.sin(a))), col, sw, cv2.LINE_AA)
            cv2.circle(layer, (int(cx), int(cy)), int(0.022 * W), col, -1, cv2.LINE_AA)
            out[:] = out * (1 - k) + layer * k
    elif kind == "balls":  # overlapping circles top-right and bottom-left with a slight drift
        d = 5 * u * np.sin(t * 1.3)
        for (bx, by, sx) in ((W, 0.0, -1.0), (0.0, H, 1.0)):
            _circle(out, bx + sx * 0.02 * W + d, by - sx * -0.0 + (0.01 * H if by == 0 else -0.01 * H) + d, 0.074 * W, _c(ctx, "ornament_a"), k)
            _circle(out, bx + sx * 0.085 * W - d, by + (0.09 * H if by == 0 else -0.09 * H) - d, 0.06 * W, _c(ctx, "ornament_b"), k)
    elif kind == "nodes":  # thin connector rule with round nodes
        y = 0.075 * H
        x0, x1 = 0.06 * W, 0.94 * W
        layer = out.copy()
        cv2.line(layer, (int(x0), int(y)), (int(x1), int(y)), tuple(float(v) for v in hexc(_c(ctx, "line"))), max(1, int(round(1.5 * u))), cv2.LINE_AA)
        out[:] = out * (1 - k) + layer * k
        for x in (x0, 0.5 * W, x1):
            _circle(out, x, y, 5 * u, _c(ctx, "accent"), k)


def _canvas(ctx, t, k=1.0):
    canvas = ctx.ground()
    _ornaments(ctx, canvas, t, 1.0)
    return canvas


def _highlight(ctx, out, text, cx, cy, size, alpha, face_weight=600):
    """The key phrase: a filled pill (lime-tech) or an underline bar (others)."""
    u = ctx.kit.u
    tw = text_width(text, int(round(size)), face_weight, 800)
    if _flat(ctx, "highlight", "bar") == "pill":
        pw, ph = tw + 54 * u, size * 1.5
        body = np.zeros((int(ph), int(pw), 4), np.float32)
        body[..., :3] = hexc(_c(ctx, "accent"))
        body[..., 3] = rrect_mask(int(pw), int(ph), int(ph / 2))
        over(out, body, cx - pw / 2, cy - ph / 2, alpha)
        put_text(out, text, size, cx, cy, face_weight, color=_c(ctx, "text"), alpha=alpha, anchor="cm")
    else:
        put_text(out, text, size, cx, cy, face_weight, color=_c(ctx, "text"), alpha=alpha, anchor="cm")
        bar = np.zeros((int(max(6 * u, 3)), int(tw)), np.float32)
        spr = np.zeros(bar.shape + (4,), np.float32)
        spr[..., :3] = hexc(_c(ctx, "accent"))
        spr[..., 3] = 1.0
        over(out, spr, cx - tw / 2, cy + size * 0.62, alpha)


def _badge(ctx, out, cx, cy, r, label, alpha):
    _circle(out, cx, cy, r, _c(ctx, "accent"), alpha)
    put_text(out, label, r * 1.05, cx, cy, 700, color=_c(ctx, "badge_text"), alpha=alpha, anchor="cm")


# ---------- FULLSCREEN_MOTION ----------
def title_scene(ctx, beat, props, t, out, S):
    u, fps, W, H = ctx.kit.u, ctx.fps, ctx.W, ctx.H
    a, e = beat["start"], beat["end"]
    k = min(smoother((t - a) / (14 / fps)), smoother((e - t) / (12 / fps)))
    if k <= 0:
        return out
    card = _canvas(ctx, t)
    cue = props.get("cue", a + 0.3)
    p = _reveal(ctx, t, cue, 0.1, 14)
    size = 84 * u
    lines = []
    for chunk in props["title"].split("\n"):
        lines += wrap(chunk, int(round(size)), 600, W * 0.78, 800)
    lh = size * 1.12
    cy = H * (0.38 if props.get("key") else 0.5)
    for i, line in enumerate(lines):
        pi = ease_out((t - (cue - 0.1 + 0.08 * i)) / (14 / fps))
        put_text(card, line, size, W / 2, cy + (i - (len(lines) - 1) / 2) * lh + (1 - pi) * 22 * u, 600, color=_c(ctx, "text"), alpha=pi, anchor="cm", bold_weight=800)
    if props.get("subtitle"):
        put_text(card, props["subtitle"], 26 * u, W / 2, cy + (len(lines) / 2) * lh + 22 * u, 400, color=_c(ctx, "muted"), alpha=p, anchor="cm")
    if props.get("key"):
        pk = ease_back(clamp((t - (cue + 0.35)) / (12 / fps)), 1.4)
        if pk > 0.02:
            _highlight(ctx, card, props["key"], W / 2, cy + (len(lines) / 2) * lh + (112 if props.get("subtitle") else 70) * u, 58 * u, clamp(pk * 2))
    if k >= 0.999:
        return card
    edge = int(round(W * (1 - k)))
    res = out.copy()
    res[:, edge:] = card[:, edge:]
    return res


def checklist_scene(ctx, beat, props, t, out, S):
    u, fps, W, H = ctx.kit.u, ctx.fps, ctx.W, ctx.H
    a, e = beat["start"], beat["end"]
    k = min(smoother((t - a) / (14 / fps)), smoother((e - t) / (12 / fps)))
    if k <= 0:
        return out
    card = _canvas(ctx, t)
    put_text(card, props["title"], 52 * u, 96 * u, 118 * u + (1 - k) * 16 * u, 600, color=_c(ctx, "text"), alpha=k, bold_weight=800)
    rows = props["rows"]
    rh, gap = 72 * u, 16 * u
    y = 206 * u
    for i, row in enumerate(rows):
        p = _reveal(ctx, t, row["cue"])
        if p > 0:
            x = 96 * u + (1 - p) * 30 * u
            _card(ctx, card, x, y, W - 192 * u, rh, alpha=p * k, r=18)
            _badge(ctx, card, x + 42 * u, y + rh / 2, 20 * u, str(i + 1), p * k)
            put_text(card, row["text"], 28 * u, x + 86 * u, y + rh / 2, 500, color=_c(ctx, "text"), alpha=p * k, anchor="lm", bold_weight=800, maxw=W - 192 * u - 120 * u)
        y += rh + gap
    if k >= 0.999:
        return card
    edge = int(round(W * (1 - k)))
    res = out.copy()
    res[:, edge:] = card[:, edge:]
    return res


# ---------- OVERLAY_CARD / SELECTIVE_TEXT ----------
def card_overlay(ctx, beat, props, t, out, S):
    u, fps = ctx.kit.u, ctx.fps
    a, e = beat["start"], beat["end"]
    k = min(ease_out((t - a) / (14 / fps)), ease_out((e - t) / (12 / fps)))
    if k <= 0:
        return out
    L = beat["layout"]
    rows = props["rows"]
    pad, tx = 22 * u, 44 * u
    maxw = L["width"] - pad - tx - 14 * u
    hs = [len(wrap(r["text"], int(round(20 * u)), 500, maxw)) * 26 * u for r in rows]
    title_h = 50 * u if props.get("title") else 0
    h = pad * 2 + title_h + sum(hs) + 14 * u * (len(rows) - 1)
    y = L["y"] + L["height"] / 2 - h / 2
    x = L["x"] + (1 - k) * 50 * u
    _card(ctx, out, x, y, L["width"], h, alpha=k, r=18, shadow=0.0)  # no shadow: it must not reach the presenter side
    yy = y + pad
    if props.get("title"):
        put_text(out, props["title"], 17 * u, x + pad, yy + 4 * u, 700, color=_c(ctx, "muted"), alpha=k)
        yy += title_h
    for row, hh in zip(rows, hs):
        p = _reveal(ctx, t, row["cue"])
        if p > 0:
            ox = x + pad + (1 - p) * 16 * u
            _circle(out, ox + 8 * u, yy + 11 * u, 6 * u, ctx.tokens["colors"].get("bullet", _c(ctx, "accent")), p * k)
            put_text(out, row["text"], 20 * u, ox + 26 * u, yy, 500, color=_c(ctx, "text"), alpha=p * k, maxw=maxw, bold_weight=800)
        yy += hh + 14 * u
    return out


def keyword_pill(ctx, beat, props, t, out, S):
    u, fps = ctx.kit.u, ctx.fps
    cue = props["cue"]
    p = clamp((t - (cue - 0.15)) / (10 / fps))
    pout = ease_out((beat["end"] - t) / (8 / fps))
    if p <= 0 or pout <= 0:
        return out
    L = beat["layout"]
    s = 0.92 + 0.08 * ease_back(p, 1.5)
    cx, cy = L["x"] + L["width"] / 2, L["y"] + L["height"] / 2
    if props.get("lead"):
        put_text(out, props["lead"], 20 * u, cx, cy - 34 * u, 500, color=_c(ctx, "muted"), alpha=clamp(p * 2) * pout, anchor="cm")
    size = 40 * u * s
    tw = text_width(props["word"], int(round(size)), 700, 800)
    pw, ph = tw + 48 * u, size * 1.6
    body = np.zeros((int(ph), int(pw), 4), np.float32)
    body[..., :3] = hexc(_c(ctx, "accent"))
    body[..., 3] = rrect_mask(int(pw), int(ph), int(ph / 2))
    over(out, body, cx - pw / 2, cy + 6 * u - ph / 2 + (28 * u if props.get("lead") else 0), clamp(p * 2) * pout)
    put_text(out, props["word"], size, cx, cy + 6 * u + (28 * u if props.get("lead") else 0), 700, color=_c(ctx, "text") if _flat(ctx, "highlight") == "pill" else _c(ctx, "badge_text"), alpha=clamp(p * 2) * pout, anchor="cm")
    return out


# ---------- PRESENTER_INSET ----------
def inset_checklist(ctx, beat, props, t, out, S):
    u, fps, W, H = ctx.kit.u, ctx.fps, ctx.W, ctx.H
    mv = ctx.tokens["motion"]
    a, e = beat["start"], beat["end"]
    move_in, move_out = mv["inset_move_in_frames"] / fps, mv["inset_move_out_frames"] / fps
    p = min(smoother((t - a) / move_in), smoother((e - t) / move_out))
    if p <= 0:
        return S.copy()
    pl = beat["presenter_layout"]
    dest = (pl["x"], pl["y"], pl["width"], pl["height"])
    res = out * (1 - p) + _canvas(ctx, t) * p
    dx, dy, dw, dh = [v0 + (v1 - v0) * p for v0, v1 in zip((0, 0, W, H), dest)]
    src_cx = props.get("source_cx", W / 2)
    sw = H * dw / dh if p > 0.001 and dw / dh < W / H else W
    scx = W / 2 + (src_cx - W / 2) * p
    sx0 = scx - sw / 2 if sw < W else 0
    sh = H if sw < W else H
    s = dw / sw
    iw, ih = max(int(round(dw)), 2), max(int(round(dh)), 2)
    M = np.float32([[s, 0, -sx0 * s], [0, s, 0]])
    patch = cv2.warpAffine(S, M, (iw, ih), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    r = int(round(22 * u * p))
    m = (rrect_mask(iw, ih, max(r, 1)) if r >= 1 else np.ones((ih, iw), np.float32))[..., None]
    X, Y = int(round(dx)), int(round(dy))
    x0, y0, x1, y1 = max(X, 0), max(Y, 0), min(X + iw, W), min(Y + ih, H)
    if x1 > x0 and y1 > y0:
        mm = m[y0 - Y:y1 - Y, x0 - X:x1 - X]
        res[y0:y1, x0:x1] = res[y0:y1, x0:x1] * (1 - mm) + patch[y0 - Y:y1 - Y, x0 - X:x1 - X] * mm
    if p > 0.02:
        mg = int(14 * u)
        over(res, rrect_ring(iw, ih, max(r, 1), 3 * u, 0.0, 0.0, _c(ctx, "accent"), None, mg), X - mg, Y - mg, p)
    landed = a + move_in
    gk = clamp(ease_out((e - move_out - t) / (8 / fps))) if t > e - move_out - 8 / fps else 1.0
    if t >= landed and gk > 0:
        cx0 = pl["x"] + pl["width"] + 52 * u
        row_w = W - cx0 - 48 * u
        tp = ease_out((t - landed) / (12 / fps))
        put_text(res, props["title"], 46 * u, cx0, 78 * u + (1 - tp) * 10 * u, 600, color=_c(ctx, "text"), alpha=tp * gk, bold_weight=800)
        y = 160 * u
        for i, row in enumerate(props["rows"]):
            q = _reveal(ctx, t, max(row["cue"], landed + 0.3))
            if q > 0:
                x = cx0 + (1 - q) * 24 * u
                _card(ctx, res, x, y, row_w, 68 * u, alpha=q * gk, r=16)
                _badge(ctx, res, x + 38 * u, y + 34 * u, 17 * u, str(i + 1), q * gk)
                put_text(res, row["text"], 24 * u, x + 76 * u, y + 34 * u, 500, color=_c(ctx, "text"), alpha=q * gk, anchor="lm", maxw=row_w - 96 * u, bold_weight=800)
            y += 82 * u
    return res


COMPONENTS = {
    "title-scene": title_scene,
    "checklist-scene": checklist_scene,
    "card-overlay": card_overlay,
    "keyword-pill": keyword_pill,
    "inset-checklist": inset_checklist,
}
