"""Tessellate medi_model parts -> STL + preview renders + viewer JSON (numpy only)."""
import json, math, struct, sys
import numpy as np
import medi_model as M

SEG = 32


def frame(d):
    d = np.array(d, float); d /= np.linalg.norm(d)
    a = np.array([1, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1, 0])
    u = np.cross(d, a); u /= np.linalg.norm(u); v = np.cross(d, u)
    return u, v, d


def box(x0, y0, z0, x1, y1, z1):
    v = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
    f = [(0, 2, 3), (0, 3, 1), (4, 5, 7), (4, 7, 6), (0, 1, 5), (0, 5, 4),
         (2, 6, 7), (2, 7, 3), (0, 4, 6), (0, 6, 2), (1, 3, 7), (1, 7, 5)]
    return v[np.array(f)]


def ring(c, u, v, r, n=SEG):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return c + r * (np.cos(a)[:, None] * u + np.sin(a)[:, None] * v)


def cap(center, pts, flip):
    n = len(pts); tris = []
    for i in range(n):
        t = [center, pts[i], pts[(i + 1) % n]]
        tris.append(t[::-1] if flip else t)
    return tris


def side(a, b):
    n = len(a); tris = []
    for i in range(n):
        j = (i + 1) % n
        tris += [[a[i], b[i], b[j]], [a[i], b[j], a[j]]]
    return tris


def cyl(r, h, base, d):
    u, v, w = frame(d); b = np.array(base, float); t = b + w * h
    r0, r1 = ring(b, u, v, r), ring(t, u, v, r)
    return np.array(cap(b, r0, True) + cap(t, r1, False) + side(r0, r1))


def tube(ri, ro, h, base, d):
    u, v, w = frame(d); b = np.array(base, float); t = b + w * h
    o0, o1, i0, i1 = ring(b, u, v, ro), ring(t, u, v, ro), ring(b, u, v, ri), ring(t, u, v, ri)
    return np.array(side(o0, o1) + side(i1, i0) + side(i0, o0) + side(o1, i1))


def prismx(x0, x1, pts):
    pts = [np.array(p, float) for p in pts]
    a = [np.array([x0, p[0], p[1]]) for p in pts]
    b = [np.array([x1, p[0], p[1]]) for p in pts]
    ca, cb = np.mean(a, 0), np.mean(b, 0)
    return np.array(cap(ca, a, True) + cap(cb, b, False) + side(a, b))


def dome(r, c, d):
    u, v, w = frame(d); c = np.array(c, float); tris = []
    rings = [ring(c + w * r * math.sin(math.radians(t)), u, v, r * math.cos(math.radians(t)), 20)
             for t in np.linspace(0, 85, 6)]
    for a, b in zip(rings[:-1], rings[1:]):
        tris += side(a, b)
    tris += cap(c + w * r, rings[-1], False) + cap(c, rings[0], True)
    return np.array(tris)


def torus(R, r, c, d, n=24, m=8):
    u, v, w = frame(d); c = np.array(c, float); P = np.zeros((n, m, 3))
    for i in range(n):
        a = 2 * math.pi * i / n; e = math.cos(a) * u + math.sin(a) * v
        for j in range(m):
            b = 2 * math.pi * j / m
            P[i, j] = c + (R + r * math.cos(b)) * e + r * math.sin(b) * w
    tris = []
    for i in range(n):
        for j in range(m):
            a, b, cc, dd = P[i, j], P[(i + 1) % n, j], P[(i + 1) % n, (j + 1) % m], P[i, (j + 1) % m]
            tris += [[a, b, cc], [a, cc, dd]]
    return np.array(tris)


def rotm(ax, deg):
    ax = np.array(ax, float); ax /= np.linalg.norm(ax); x, y, z = ax
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg)); C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def mesh(p):
    k, *a = p["prim"]
    t = {"box": box, "cyl": cyl, "tube": tube, "prismx": prismx, "dome": dome, "torus": torus}[k](*a)
    for op in p["tf"]:
        if op[0] == "rot":
            t = t @ rotm(op[1], op[2]).T
        else:
            t = t + np.array(op[1])
    return t


def write_stl(path, tris):
    with open(path, "wb") as f:
        f.write(b"MediGuard CarePro Concept C (mm)".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            n = np.cross(t[1] - t[0], t[2] - t[0]); L = np.linalg.norm(n); n = n / L if L else n
            f.write(struct.pack("<12fH", *n, *t[0], *t[1], *t[2], 0))


if __name__ == "__main__":
    out = sys.argv[1]
    parts = M.build()
    meshes = [(p, mesh(p)) for p in parts]
    alltris = np.concatenate([m for _, m in meshes])
    write_stl(f"{out}/MediGuard_CarePro_C.stl", alltris)
    lo, hi = alltris.reshape(-1, 3).min(0), alltris.reshape(-1, 3).max(0)
    print("triangles", len(alltris), "bbox min", lo.round(1), "max", hi.round(1))
    # viewer json: per part rounded vertices
    data = []
    for p, m in meshes:
        data.append(dict(n=p["name"], g=p["group"], c=[round(x, 3) for x in p["color"]], cut=p["cut"],
                         v=[round(float(x), 2) for x in m.reshape(-1)]))
    json.dump(data, open(f"{out}/model.json", "w"), separators=(",", ":"))
    np.save(f"{out}/_meshes.npy", np.array([m for _, m in meshes], dtype=object), allow_pickle=True)
