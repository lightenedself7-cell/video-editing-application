import cv2, numpy as np
ang = np.linspace(0, 2 * np.pi, 240, endpoint=False)
def rim_score(f, cx, cy, r):
    xi = cx + (r - 3.5) * np.cos(ang); yi = cy + (r - 3.5) * np.sin(ang)
    xo = cx + (r + 3.5) * np.cos(ang); yo = cy + (r + 3.5) * np.sin(ang)
    ok = (xi >= 0) & (xi < 1280) & (xo >= 0) & (xo < 1280) & (yi >= 0) & (yi < 720) & (yo >= 0) & (yo < 720)
    if ok.sum() < 60: return 0.0
    cl = lambda v, hi: np.clip(np.round(v).astype(int), 0, hi - 1)
    a = f[cl(yi[ok], 720), cl(xi[ok], 1280)].astype(int)
    b = f[cl(yo[ok], 720), cl(xo[ok], 1280)].astype(int)
    return float((np.abs(a - b).sum(1) > 45).mean())
def candidate(f):
    """f: RGB uint8 HxWx3. Returns (cx, cy, r, score) or None."""
    r_, g_, b_ = [f[..., k].astype(int) for k in range(3)]
    m = (((r_ - g_ > 45) & (b_ - g_ > 15)) | ((r_ > 110) & (r_ - g_ > 60) & (r_ - b_ > 40))).astype(np.uint8)
    m[:300, :] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    best = None
    for k in np.argsort(-st[1:, cv2.CC_STAT_AREA])[:3] + 1:
        if st[k, cv2.CC_STAT_AREA] < 2500: continue
        cnts, _ = cv2.findContours((lab == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        (cx, cy), rad = cv2.minEnclosingCircle(np.vstack(cnts))
        if not 70 < rad < 175: continue
        # local refine: search small neighbourhood for best rim score
        bs = (0, cx, cy, rad)
        for dr in range(-6, 7, 2):
            for dx in range(-6, 7, 2):
                for dy in range(-6, 7, 2):
                    s = rim_score(f, cx + dx, cy + dy, rad + dr)
                    if s > bs[0]: bs = (s, cx + dx, cy + dy, rad + dr)
        if best is None or bs[0] > best[3]: best = (round(bs[1], 1), round(bs[2], 1), round(bs[3], 1), round(bs[0], 2))
    return best
