"""Clean Creator components. Each draws one beat from its `props`; nothing here is specific to one video.

Signature: fn(ctx, beat, props, t, out, S) -> frame
  ctx   Context (kit, W, H, fps, project_dir, icon())
  t     source time in seconds
  out   a writable copy of the source frame (float RGB); overlay components draw on it and return it
  S     the untouched source frame (inset components rebuild the frame from it)
Sizes are written for a 1280x720 design space; multiply by `u` (= width / 1280).
"""
from __future__ import annotations

import cv2
import numpy as np

from renderer.gfx import (clamp, ease_back, ease_out, over, put_text, rrect_mask, rrect_ring, smoother, text_width, wrap)


# ---------- shared timing ----------
def _enter(ctx):
    return ctx.tokens["motion"]["enter_frames"] / ctx.fps


def _exit(ctx):
    return ctx.tokens["motion"]["exit_frames"] / ctx.fps


def _reveal(ctx, t, cue, lead=0.25, dur_frames=12):
    return ease_out((t - (cue - lead)) / (dur_frames / ctx.fps))


# ---------- OVERLAY_CARD ----------
def glass_card(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    a, e = beat["start"], beat["end"]
    pin = ease_out((t - a) / (14 / fps))
    pout = ease_out((e - t) / (12 / fps))
    k = min(pin, pout)
    if k <= 0:
        return out
    L = beat["layout"]
    x, w = L["x"], L["width"]
    pad, tx = 22 * u, 40 * u
    maxw = w - pad - tx - 12 * u
    rows = props["rows"]
    header = props.get("header")
    hs = [len(wrap(r["text"], int(round(20 * u)), 400, maxw)) * 25 * u for r in rows]
    top_extra = 74 * u if header else 0
    h = pad * 2 + top_extra + sum(hs) + 16 * u * (len(rows) - 1)
    y = (L["y"] + L["height"] / 2) - h / 2
    dx = (1 - k) * 60 * u
    kit.glass(out, x + dx, y, w, h, alpha=k)
    yy = y + 22 * u
    if header:
        p = _reveal(ctx, t, header["cue"])
        if header.get("icon"):
            over(out, ctx.icon(header["icon"], 74), x + dx + 22 * u + (1 - p) * 14 * u, yy + 4 * u, p * k)
        put_text(out, header["text"], 15 * u, x + dx + (22 + 82) * u + (1 - p) * 14 * u, yy + 20 * u, 500, color=kit.text, alpha=p * k * 0.85)
        yy += top_extra
    for row, hh in zip(rows, hs):
        p = _reveal(ctx, t, row["cue"])
        if p > 0:
            ox = x + dx + 22 * u + (1 - p) * 18 * u
            if row.get("icon"):
                over(out, ctx.icon(row["icon"], 24), ox, yy + 1 * u, p * k)
            else:
                kit.dot(out, ox + 8 * u, yy + 8 * u, 4.5, p * k)
            put_text(out, row["text"], 20 * u, ox + 40 * u, yy, 400, color=kit.text, alpha=p * k, maxw=maxw, bold_weight=750)
        yy += hh + 16 * u
    return out


# ---------- SELECTIVE_TEXT ----------
def kinetic_keyword(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    cue = props["cue"]
    p = clamp((t - (cue - 0.15)) / (10 / fps))
    pout = ease_out((beat["end"] - t) / (8 / fps))
    if p <= 0 or pout <= 0:
        return out
    L = beat["layout"]
    anchor = props.get("anchor")
    ax = anchor["x"] if anchor else L["x"] + L["width"] / 2
    ay = anchor["y"] if anchor else L["y"] + 18 * u
    s = 0.9 + 0.1 * ease_back(p, 1.6)
    a = clamp(p * 2) * pout
    put_text(out, props["lead"], 24 * u, ax, ay, 300, color=kit.text, alpha=a, anchor="cm", scale=s)
    put_text(out, props["word"], 46 * u, ax, ay + 44 * u, 800, color=kit.text, alpha=a, anchor="cm", glow=0.5, scale=s)
    return out


def question_beat(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    a, e = beat["start"], beat["end"]
    k = min(smoother((t - a) / (10 / fps)), smoother((e - t) / (10 / fps)))
    if k <= 0:
        return out
    blurred = cv2.GaussianBlur(out, (0, 0), 6 * u * k + 0.01)
    out = blurred * (1 - 0.45 * k)
    L = beat["layout"]
    p = _reveal(ctx, t, props["cue"]) * min(1, smoother((e - t) / (10 / fps)))
    put_text(out, props["text"], 28 * u, L["x"] + L["width"] / 2, L["y"] + L["height"] / 2 + (1 - p) * 8 * u, 300,
             color=kit.text, alpha=p, anchor="cm", bold_weight=800)
    return out


# ---------- PRESENTER_INSET ----------
def _place_presenter(ctx, ground, S, p, dest, src_cx=None):
    """p in 0..1. dest = final rect (x, y, w, h). With src_cx the source is cropped to the rect's aspect around that x."""
    kit, W, H = ctx.kit, ctx.W, ctx.H
    if p <= 0:
        return S.copy(), False
    dx, dy, dw, dh = [v0 + (v1 - v0) * p for v0, v1 in zip((0, 0, W, H), dest)]
    if src_cx is not None:
        sw = H * dw / dh
        scx = W / 2 + (src_cx - W / 2) * p
        sx0, sy0, sh = scx - sw / 2, 0, H
    else:
        sx0, sy0, sw, sh = 0, 0, W, H
    s = dw / sw
    out = ground.copy()
    X0, Y0 = int(np.floor(dx)), int(np.floor(dy))
    X1, Y1 = int(np.ceil(dx + dw)), int(np.ceil(dy + dh))
    M = np.float32([[s, 0, dx - sx0 * s - X0], [0, s, dy - sy0 * s - Y0]])
    patch = cv2.warpAffine(S, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    r = 24 * kit.u * p
    m = rrect_mask(X1 - X0, Y1 - Y0, max(int(round(r)), 0))[..., None] if r >= 0.5 else np.ones((Y1 - Y0, X1 - X0, 1), np.float32)
    reg = out[Y0:Y1, X0:X1]
    out[Y0:Y1, X0:X1] = reg * (1 - m) + patch * m
    if p > 0.02:
        mg = kit.px(24)
        ring = rrect_ring(X1 - X0, Y1 - Y0, max(int(round(r)), 1), 1.5 * kit.u, 8.0 * kit.u, 0.75, kit.accent, None, mg)
        over(out, ring, X0 - mg, Y0 - mg, p)
    return out, True


def _inset_frame(ctx, beat, S, t, draw, dest, src_cx):
    mv = ctx.tokens["motion"]
    move_in, move_out = mv["inset_move_in_frames"] / ctx.fps, mv["inset_move_out_frames"] / ctx.fps
    a, e = beat["start"], beat["end"]
    p = min(smoother((t - a) / move_in), smoother((e - t) / move_out))
    out, moved = _place_presenter(ctx, ctx.ground(), S, p, dest, src_cx)
    if not moved:
        return out
    gk = 1.0
    if t > e - move_out - 8 / ctx.fps:
        gk = max(0.0, min(1.0, ease_out((e - move_out - t) / (8 / ctx.fps))))
    landed = a + move_in
    if t >= landed and gk > 0:
        draw(out, landed, gk)
    return out


def side_column_list(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    pl = beat["presenter_layout"]
    dest = (pl["x"], pl["y"], pl["width"], pl["height"])
    src_cx = props.get("source_cx", ctx.W / 2)  # where the presenter sits in the source frame; the column crops around it

    def draw(o, landed, gk):
        cx0 = pl["x"] + pl["width"] + 56 * u
        row_w = ctx.W - cx0 - 48 * u
        tp = ease_out((t - landed) / _enter(ctx))
        put_text(o, props["title"], 52 * u, cx0 + 4 * u, 70 * u + (1 - tp) * 10 * u, 800, color=kit.text, alpha=tp * gk, glow=0.55)
        rows = props["rows"]
        emphasised = [bool(r.get("emphasis")) for r in rows]
        if not any(emphasised):
            emphasised[-1] = True
        y = 158 * u
        for row, emph in zip(rows, emphasised):
            cue = row["cue"]
            p = _reveal(ctx, t, max(cue, landed + 0.3))
            if p > 0:
                x = cx0 + (1 - p) * 28 * u
                kit.glass(o, x, y, row_w, 72 * u, alpha=p * gk, r=20, highlight=1.0 if emph else 0.0)
                kit.check_badge(o, x + 40 * u, y + 36 * u, 15, clamp((t - cue) / (8 / fps)), alpha=p * gk)
                put_text(o, row["text"], 24 * u, x + 76 * u, y + 36 * u, 600 if emph else 400, color=kit.text, alpha=p * gk, anchor="lm", bold_weight=800)
            y += 86 * u

    return _inset_frame(ctx, beat, S, t, draw, dest, src_cx)


def recap_window(ctx, beat, props, t, out, S):
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    pl = beat["presenter_layout"]
    dest = (pl["x"], pl["y"], pl["width"], pl["height"])

    def draw(o, landed, gk):
        pc = ease_out((t - landed) / (14 / fps))
        if props.get("caption"):
            put_text(o, props["caption"], 20 * u, pl["x"] + pl["width"] / 2, pl["y"] + pl["height"] + 28 * u + (1 - pc) * 6 * u, 300,
                     color=kit.text, alpha=pc * gk * 0.92, anchor="ct", italic=True)
        cx0 = pl["x"] + pl["width"] + 44 * u
        row_w = ctx.W - cx0 - 40 * u
        put_text(o, props["title"], 34 * u, cx0, pl["y"] + 10 * u + (1 - pc) * 8 * u, 800, color=kit.text, alpha=pc * gk, glow=0.5)
        y = pl["y"] + 76 * u
        for row in props["rows"]:
            cue = row["cue"]
            p = _reveal(ctx, t, max(cue, landed + 0.2))
            if p > 0:
                x = cx0 + (1 - p) * 24 * u
                kit.glass(o, x, y, row_w, 92 * u, alpha=p * gk, r=20)
                kit.check_badge(o, x + 40 * u, y + 46 * u, 17, clamp((t - cue) / (8 / fps)), alpha=p * gk)
                put_text(o, row["text"], 21 * u, x + 76 * u, y + 46 * u, 400, color=kit.text, alpha=p * gk, anchor="lm", maxw=row_w - 100 * u, bold_weight=750)
            y += 110 * u

    return _inset_frame(ctx, beat, S, t, draw, dest, None)


COMPONENTS = {
    "glass-card": glass_card,
    "kinetic-keyword": kinetic_keyword,
    "question-beat": question_beat,
    "side-column-list": side_column_list,
    "recap-window": recap_window,
}
