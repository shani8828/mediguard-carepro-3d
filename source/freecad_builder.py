
# =====================================================================
#  FreeCAD builder  (Macro > Macros... > select this file > Execute)
#  Creates document "MediGuard_CarePro_C" with every part as its own
#  solid, grouped (Housing, Header, Drawer_1..8, Mechanism, Electronics,
#  Base, Ports), coloured, then saves .FCStd and exports .step next to
#  this macro (or in your home folder if that location is unknown).
# =====================================================================
CUTAWAY = False   # True = hide right wall / roof so the internals are visible

import os
import FreeCAD as App
import Part
from FreeCAD import Vector as V


def _make(p):
    k, *a = p["prim"]
    if k == "box":
        x0, y0, z0, x1, y1, z1 = a
        s = Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
    elif k == "cyl":
        r, h, b, d = a
        s = Part.makeCylinder(r, h, V(*b), V(*d))
    elif k == "tube":
        ri, ro, h, b, d = a
        dv = V(*d); dv.normalize()
        outer = Part.makeCylinder(ro, h, V(*b), dv)
        inner = Part.makeCylinder(ri, h + 2, V(*b) - dv * 1, dv)
        s = outer.cut(inner)
    elif k == "prismx":
        x0, x1, pts = a
        vs = [V(x0, y, z) for y, z in pts]
        vs.append(vs[0])
        s = Part.Face(Part.makePolygon(vs)).extrude(V(x1 - x0, 0, 0))
    elif k == "dome":
        r, c, d = a
        s = Part.makeSphere(r, V(*c), V(*d), 0, 90, 360)
    elif k == "rects":
        rs, z0, z1 = a
        s = Part.makeCompound([Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0)) for x0, y0, x1, y1 in rs])
    elif k == "torus":
        R, r, c, d = a
        s = Part.makeTorus(R, r, V(*c), V(*d))
    else:
        raise ValueError(k)
    for op in p["tf"]:
        if op[0] == "rot":
            s.rotate(V(0, 0, 0), V(*op[1]), op[2])
        else:
            s.translate(V(*op[1]))
    return s


def run():
    doc = App.newDocument("MediGuard_CarePro_C")
    groups, objs, fails = {}, [], []
    for p in build():
        try:
            shp = _make(p)
        except Exception as e:  # keep going if one part fails
            fails.append((p["name"], str(e)))
            continue
        g = groups.get(p["group"])
        if g is None:
            g = doc.addObject("App::DocumentObjectGroup", p["group"])
            groups[p["group"]] = g
        o = doc.addObject("Part::Feature", p["name"])
        o.Shape = shp
        g.addObject(o)
        objs.append(o)
        if App.GuiUp:
            o.ViewObject.ShapeColor = tuple(p["color"])
            if CUTAWAY and p["cut"]:
                o.ViewObject.Visibility = False
    doc.recompute()
    try:
        base = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        base = os.path.expanduser("~")
    fc = os.path.join(base, "MediGuard_CarePro_C.FCStd")
    st = os.path.join(base, "MediGuard_CarePro_C.step")
    try:
        doc.saveAs(fc)
    except Exception as e:
        fails.append(("save FCStd", str(e)))
    try:
        import Import
        Import.export(objs, st)
    except Exception as e:
        fails.append(("export STEP", str(e)))
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    App.Console.PrintMessage(f"MediGuard: {len(objs)} parts built. Saved {fc} and {st}\n")
    for n, e in fails:
        App.Console.PrintWarning(f"  failed: {n}: {e}\n")


run()
