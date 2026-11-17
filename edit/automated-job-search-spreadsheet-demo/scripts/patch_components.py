"""One-off patch: adds explainer-card strike, pipeline and focus-points components (run once)."""
import json

D = r"\\wsl$\Ubuntu-24.04\home\dev\video-editing-application\skills\theme-renderer\themes\teal-spotlight"
p = D + r"\components.py"
s = open(p, encoding="utf-8", newline="").read().replace("\r\n", "\n")
if "def pipeline(" in s:
    raise SystemExit("already patched")

# 1. strike-through on explainer rows
anchor = """            if skeleton:
                sy = ry + max(tile"""
strike = """            if row.get("strike") is not None:  # the presenter says "I didn't do this": a line is drawn through the row
                sp = ease_out((t - row["strike"]) / (10 / fps))
                if sp > 0:
                    mw = Wc - (tx - X) - pad
                    for li, ln in enumerate(wrap(row["text"], int(round(21 * u)), 500, mw)):
                        lw = text_width(ln, int(round(21 * u)), 500, 800)
                        yy = ry + (2 * u if skeleton else 8 * u) + 27 * u * li + 15 * u
                        cv2.line(out, (int(tx), int(yy)), (int(tx + (lw + 6 * u) * sp), int(yy)), tuple(float(c) for c in hexc("#E5484D")),
                                 max(int(round(4 * u)), 2), cv2.LINE_AA)
"""
assert anchor in s
s = s.replace(anchor, strike + anchor, 1)

new = '''

def _bg_grid(ctx, card, local):
    """Dark teal ground with the plus grid and drifting diagonal lines (used by pipeline)."""
    u, W, H = ctx.kit.u, ctx.W, ctx.H
    mint, teal = _col(ctx, "mint"), _col(ctx, "accent")
    step = 96 * u
    for gy in np.arange(step / 2, H, step):
        for gx in np.arange(step / 2, W, step):
            arm = 5 * u
            _poly(card, _rect_pts(gx - arm, gy - 0.9 * u, 2 * arm, 1.8 * u), mint, 0.16)
            _poly(card, _rect_pts(gx - 0.9 * u, gy - arm, 1.8 * u, 2 * arm), mint, 0.16)
    for i, off in enumerate((-0.15, 0.05, 0.25)):
        x0 = W * (0.55 + off)
        drift = 8 * u * np.sin(local * 0.6 + i)
        _poly(card, [(x0 + drift, -10), (x0 + 2.4 * u + drift, -10), (x0 - 0.45 * W + 2.4 * u + drift, H + 10), (x0 - 0.45 * W + drift, H + 10)], teal, 0.3)


def _wipe(out, card, k, W):
    if k >= 0.999:
        return card
    edge = int(round(W * (1 - k)))
    out = out.copy()
    out[:, edge:] = card[:, edge:]
    return out


def _bgr(c):
    return tuple(float(v) for v in hexc(c))


def pipeline(ctx, beat, props, t, out, S):
    """Full-screen pipeline: every step in a row joined by arrows. Steps before `active` are done (check), `active` pops in marigold at `cue`,
    later steps stay dim. One beat per step, so each lights up when the presenter reaches it."""
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    W, H = ctx.W, ctx.H
    a, e = beat["start"], beat["end"]
    k = min(smoother((t - a) / (14 / fps)), smoother((e - t) / (12 / fps)))
    if k <= 0:
        return out
    card = ctx.ground()
    pop, teal, deep, shadow, mint = _col(ctx, "pop"), _col(ctx, "accent"), _col(ctx, "deep"), _col(ctx, "shadow"), _col(ctx, "mint")
    _bg_grid(ctx, card, t - a)
    steps, active = props["steps"], int(props["active"])
    cue = props.get("cue", a + 0.3)
    n = len(steps)
    nw, gap = 176 * u, 34 * u
    nh = 214 * u
    total = n * nw + (n - 1) * gap
    x0 = (W - total) / 2
    cy = H * 0.55
    put_text(card, _caps(props.get("title", "The pipeline")), 46 * u, W / 2, H * 0.20, 800, color=_col(ctx, "text"), anchor="cm", face="display", glow=0.4)
    put_text(card, "STEP %d OF %d" % (active + 1, n), 22 * u, W / 2, H * 0.20 + 46 * u, 700, color=mint, anchor="cm", face="display", alpha=0.9)
    pa = ease_back(clamp((t - (cue - 0.1)) / (12 / fps)), 1.6)
    for i, st in enumerate(steps):
        cx = x0 + i * (nw + gap) + nw / 2
        state = "done" if i < active else ("active" if i == active else "todo")
        sc = 1.0
        if state == "active":
            sc = 0.92 + 0.2 * clamp(pa) if pa > 0 else 0.92
        tilt = (-1.6, 1.2)[i % 2] if state != "active" else 0.0
        w_, h_ = nw * sc, nh * sc
        pts = _rot_pts(_rect_pts(cx - w_ / 2, cy - h_ / 2, w_, h_), cx, cy, tilt)
        if state == "active":
            glow = _rot_pts(_rect_pts(cx - w_ / 2 - 10 * u, cy - h_ / 2 - 10 * u, w_ + 20 * u, h_ + 20 * u), cx, cy, tilt)
            _poly(card, glow, pop, 0.28 * clamp(pa))
            _shadowed_poly(card, pts, pop, shadow, 9 * u, 1.0)
            ink, sub_c = _col(ctx, "ground"), _col(ctx, "ground")
        elif state == "done":
            _shadowed_poly(card, pts, teal, shadow, 6 * u, 1.0)
            ink, sub_c = _col(ctx, "text"), mint
        else:
            _poly(card, pts, deep, 0.55)
            ink, sub_c = mint, mint
        al = 1.0 if state != "todo" else 0.55
        by = cy - h_ / 2 + 44 * u * sc
        if state == "done":
            cv2.circle(card, (int(cx), int(by)), int(22 * u), _bgr(pop), -1, cv2.LINE_AA)
            cv2.polylines(card, [np.array([[cx - 10 * u, by + 1 * u], [cx - 2 * u, by + 9 * u], [cx + 11 * u, by - 8 * u]], np.int32)], False,
                          _bgr(_col(ctx, "ground")), max(int(4 * u), 2), cv2.LINE_AA)
        else:
            put_text(card, str(i + 1), 52 * u * sc, cx, by, 800, color=ink, alpha=al, anchor="cm", face="display")
        lines = wrap(st["label"], int(round(24 * u * sc)), 700, nw - 26 * u, 800)
        ly = cy - h_ / 2 + 104 * u * sc
        for j, ln in enumerate(lines):
            put_text(card, ln, 24 * u * sc, cx, ly + j * 29 * u * sc, 700, color=ink, alpha=al, anchor="cm", bold_weight=800)
        if st.get("sub"):
            sl = wrap(st["sub"], int(round(17 * u * sc)), 500, nw - 26 * u, 700)
            sy = cy + h_ / 2 - (24 + 21 * (len(sl) - 1)) * u * sc
            for j, ln in enumerate(sl):
                put_text(card, ln, 17 * u * sc, cx, sy + j * 21 * u * sc, 500, color=sub_c, alpha=al * 0.9, anchor="cm")
        if i < n - 1:
            ax0, ax1 = cx + nw / 2 + 5 * u, cx + nw / 2 + gap - 5 * u
            col = _bgr(pop if i < active else mint)
            cv2.line(card, (int(ax0), int(cy)), (int(ax1 - 5 * u), int(cy)), col, max(int(4 * u), 2), cv2.LINE_AA)
            cv2.fillConvexPoly(card, np.array([[ax1, cy], [ax1 - 11 * u, cy - 9 * u], [ax1 - 11 * u, cy + 9 * u]], np.int32), col, cv2.LINE_AA)
    return _wipe(out, card, k, W)


def focus_points(ctx, beat, props, t, out, S):
    """Presenter blurred and dimmed; the points come forward in large slabs, centred, one per cue."""
    kit, u, fps = ctx.kit, ctx.kit.u, ctx.fps
    W, H = ctx.W, ctx.H
    a, e = beat["start"], beat["end"]
    k = min(smoother((t - a) / (14 / fps)), smoother((e - t) / (12 / fps)))
    if k <= 0:
        return out
    pop, teal, deep, shadow, mint = _col(ctx, "pop"), _col(ctx, "accent"), _col(ctx, "deep"), _col(ctx, "shadow"), _col(ctx, "mint")
    blur = cv2.GaussianBlur(S, (0, 0), 12 * u * k + 0.01)
    res = blur * (1 - 0.62 * k) + hexc(deep) * 0.62 * k * 0.55
    pts_ = props["points"]
    n = len(pts_)
    title = props.get("title")
    slab_h, gap = 96 * u, 26 * u
    block = n * slab_h + (n - 1) * gap
    top = H / 2 - block / 2 + (36 * u if title else 0)
    if title:
        tp = ease_out((t - (a + 0.15)) / (14 / fps)) * k
        put_text(res, _caps(title), 64 * u, W / 2 + 5 * u, top - 70 * u + 5 * u, 800, color=shadow, alpha=tp * 0.8, anchor="cm", face="display")
        put_text(res, _caps(title), 64 * u, W / 2, top - 70 * u, 800, color=_col(ctx, "text"), alpha=tp, anchor="cm", face="display", glow=0.5)
    sw = 820 * u
    shown = [j for j, q in enumerate(pts_) if t >= q["cue"] - 0.2]
    latest_i = max(shown) if shown else -1
    for i, pt in enumerate(pts_):
        p = ease_back(clamp((t - (pt["cue"] - 0.2)) / (13 / fps)), 1.35)
        if p <= 0.01:
            continue
        al = clamp(p * 1.6) * k
        cx = W / 2
        cy = top + i * (slab_h + gap) + slab_h / 2 + (1 - clamp(p)) * 46 * u
        tilt = (-1.4, 1.0, -0.8, 1.2)[i % 4]
        latest = i == latest_i
        pts = _rot_pts(_rect_pts(cx - sw / 2, cy - slab_h / 2, sw, slab_h), cx, cy, tilt)
        _shadowed_poly(res, pts, deep, shadow, 9 * u, al)
        edge = _rot_pts(_rect_pts(cx - sw / 2, cy - slab_h / 2, 14 * u, slab_h), cx, cy, tilt)
        _poly(res, edge, pop if latest else teal, al)
        tx = cx - sw / 2 + 44 * u
        if pt.get("icon"):
            spr = ctx.icon(pt["icon"], 64, tile=True)
            over(res, spr, tx + 4 * u, cy - spr.shape[0] / 2, al)
            tx += 92 * u
        else:
            put_text(res, str(i + 1), 46 * u, tx + 18 * u, cy, 800, color=pop if latest else mint, alpha=al, anchor="cm", face="display")
            tx += 70 * u
        put_text(res, pt["text"], 38 * u, tx, cy - 22 * u, 600, color=_col(ctx, "text"), alpha=al, maxw=sw - (tx - (cx - sw / 2)) - 30 * u, bold_weight=800)
    return _wipe(out, res, k, W)
'''
s = s.replace("\n\nCOMPONENTS = {", new + "\n\nCOMPONENTS = {", 1)
s = s.replace('    "screen-share": screen_share,\n}', '    "screen-share": screen_share,\n    "pipeline": pipeline,\n    "focus-points": focus_points,\n}')
open(p, "w", encoding="utf-8", newline="").write(s)

r = json.loads(open(D + r"\registry.json", encoding="utf-8").read())
num = {"type": "number", "required": True}
c = r["components"]
c["explainer-card"]["props"]["rows"]["items"]["strike"] = {"type": "number"}
c["pipeline"] = {"summary": "Full-screen pipeline of steps joined by arrows: finished steps get a check, the current step pops in marigold on its cue, later steps stay dim. One beat per step.",
                 "treatments": ["FULLSCREEN_MOTION"], "touches_presenter": True, "needs": [],
                 "props": {"title": {"type": "string"}, "cue": {"type": "number"}, "active": dict(num),
                           "steps": {"type": "array", "required": True, "min": 2, "max": 8,
                                     "items": {"label": {"type": "string", "required": True}, "sub": {"type": "string"}}}}}
c["focus-points"] = {"summary": "Presenter blurred and dimmed; the points come forward as large centred slabs one by one on their cues.",
                     "treatments": ["FULLSCREEN_MOTION"], "touches_presenter": True, "needs": [],
                     "props": {"title": {"type": "string"},
                               "points": {"type": "array", "required": True, "min": 1, "max": 4,
                                          "items": {"text": {"type": "string", "required": True}, "cue": dict(num), "icon": {"type": "string"}}}}}
open(D + r"\registry.json", "w", encoding="utf-8", newline="").write(json.dumps(r, indent=2) + "\n")
print("patched")
