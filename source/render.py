"""Simple z-buffer renderer for preview PNGs."""
import math, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import medi_model as M
from build_mesh import mesh


def render(parts, az, el, size=1100, hide_cut=False, title="", path="out.png", zoom=1.0):
    a, e = math.radians(az), math.radians(el)
    fwd = np.array([math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)])  # toward viewer
    right = np.array([math.cos(a), math.sin(a), 0.0])
    up = np.cross(fwd, right)
    light = fwd * 0.6 + up * 0.5 + right * 0.3; light /= np.linalg.norm(light)
    tris, cols = [], []
    for p in parts:
        if hide_cut and p["cut"]:
            continue
        m = mesh(p); tris.append(m); cols.append(np.tile(p["color"], (len(m), 1)))
    T = np.concatenate(tris); C = np.concatenate(cols)
    P = np.stack([T @ right, T @ up, T @ fwd], -1)
    lo, hi = P[..., :2].reshape(-1, 2).min(0), P[..., :2].reshape(-1, 2).max(0)
    sc = (size * 0.9 / (hi - lo).max()) * zoom
    ctr = (lo + hi) / 2
    S = np.empty_like(P)
    S[..., 0] = (P[..., 0] - ctr[0]) * sc + size / 2
    S[..., 1] = size / 2 - (P[..., 1] - ctr[1]) * sc
    S[..., 2] = P[..., 2]
    N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); L = np.linalg.norm(N, axis=1); L[L == 0] = 1; N /= L[:, None]
    shade = 0.35 + 0.65 * np.abs(N @ light)
    img = np.ones((size, size, 3)); zb = np.full((size, size), -1e9)
    for t, c, s in zip(S, C, shade):
        x0, y0 = max(int(t[:, 0].min()), 0), max(int(t[:, 1].min()), 0)
        x1, y1 = min(int(t[:, 0].max()) + 1, size - 1), min(int(t[:, 1].max()) + 1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax_, ay, az_), (bx, by, bz), (cx, cy, cz) = t
        den = (by - cy) * (ax_ - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
        w1 = ((cy - ay) * (xs - cx) + (ax_ - cx) * (ys - cy)) / den
        w2 = 1 - w0 - w1
        msk = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        if not msk.any():
            continue
        z = w0 * az_ + w1 * bz + w2 * cz
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = msk & (z > sub)
        sub[upd] = z[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = np.array(c) * s
    fig = plt.figure(figsize=(size / 100, size / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(img); ax.axis("off")
    if title:
        ax.text(20, 40, title, fontsize=16, color="#333")
    fig.savefig(path); plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1]
    parts = M.build()
    render(parts, -35, 25, title="MediGuard Care-Pro C — front iso (drawer #3 open)", path=f"{out}/preview_iso_front.png")
    render(parts, 50, 22, hide_cut=True, title="Cut-away: right wall & roof hidden", path=f"{out}/preview_cutaway.png")
    render(parts, 0, 0, title="Front view", path=f"{out}/preview_front.png")
    scr = [p for p in parts if p["group"] == "Display_Screen" or p["name"].startswith("Display_")]
    render(scr, 0, 90 - M.SLANT_ANG, size=1300, path=f"{out}/preview_screen.png")
    render(parts, 90, 0, hide_cut=True, title="Right side, wall hidden (internals)", path=f"{out}/preview_side_internal.png")
