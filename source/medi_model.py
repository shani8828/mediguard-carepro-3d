# MediGuard Care-Pro Concept C - geometry definition (single source of truth)
# Units: mm.  X = width (left -80 .. right +80), Y = depth (front face 0 .. rear 200),
# Z = height (0 .. 250).  Drawer #3 is shown extended 70 mm (front at Y = -70).
#
# Assumptions taken where the sketches disagree:
#   8 drawers on a 22 mm pitch (stack Z 20..196), 2 mm gap between 20 mm fronts
#   header slant follows 70 mm depth x 54 mm height (~37.6 deg), not 30 deg
#   timing-belt pulleys 165 mm centre-to-centre, closed depth 200 mm
import math

W, D, H = 160.0, 200.0, 250.0
BASE_H = 20.0
STACK_Z0, STACK_Z1 = 20.0, 196.0
PITCH, FRONT_H = 22.0, 20.0
N_DRAWERS = 8
EXT_DRAWER = 2          # index 0 = bottom; drawer #3 from bottom is extended
EXT = 70.0
WALL = 3.0
SLANT_D = 70.0
HDR_H = H - STACK_Z1    # 54
SLANT_ANG = math.degrees(math.atan2(HDR_H, SLANT_D))
SLANT_LEN = math.hypot(SLANT_D, HDR_H)
NY, NZ = -HDR_H / SLANT_LEN, SLANT_D / SLANT_LEN   # outward normal of slanted face

COL = {
    "shell": (0.93, 0.93, 0.90), "shell2": (0.85, 0.86, 0.84), "front": (0.97, 0.97, 0.95),
    "dark": (0.18, 0.19, 0.21), "screen": (0.20, 0.45, 0.75), "rubber": (0.12, 0.12, 0.12),
    "metal": (0.70, 0.72, 0.75), "brass": (0.80, 0.65, 0.30), "led": (0.20, 0.85, 0.35),
    "pcb": (0.10, 0.50, 0.25), "batt": (0.20, 0.35, 0.70), "belt": (0.15, 0.15, 0.15),
    "spring": (0.75, 0.75, 0.80), "blister": (0.80, 0.85, 0.90), "foil": (0.75, 0.77, 0.80),
    "accent": (0.95, 0.55, 0.15), "red": (0.85, 0.20, 0.20), "tray": (0.80, 0.83, 0.86),
}

parts = []


def add(name, group, color, prim, transforms=None, cut=False):
    """prim: ('box', x0,y0,z0,x1,y1,z1) | ('cyl', r, h, (bx,by,bz), (dx,dy,dz))
             ('tube', ri, ro, h, base, dir) | ('prismx', x0, x1, [(y,z),...])
             ('dome', r, centre, dir) | ('torus', R, r, centre, dir)
       transforms: list of ('rot', (ax,ay,az), deg) [about origin] or ('move', (x,y,z))
       cut=True -> hidden in the cut-away preview (right wall, roof ...)"""
    parts.append(dict(name=name, group=group, color=COL[color], prim=prim,
                      tf=transforms or [], cut=cut))


def on_slant(u, x, off, thick, sx, su, name, group, color, prim="box", r=None):
    """Place a feature on the slanted header face. u = distance along slope from front edge."""
    py, pz = u * SLANT_D / SLANT_LEN, STACK_Z1 + u * HDR_H / SLANT_LEN
    cy, cz = py + NY * off, pz + NZ * off
    tf = [("rot", (1, 0, 0), SLANT_ANG), ("move", (x, cy, cz))]
    if prim == "box":
        add(name, group, color, ("box", -sx / 2, -su / 2, -thick / 2, sx / 2, su / 2, thick / 2), tf)
    else:
        add(name, group, color, ("cyl", r, thick, (0, 0, -thick / 2), (0, 0, 1)), tf)


def rounded_profile():
    pts = [(0, 20), (D, 20)]
    R = 10.0
    for i in range(0, 7):                       # rear-top corner R10
        a = math.radians(90 * i / 6)
        pts.append((D - R + R * math.cos(a), H - R + R * math.sin(a)))
    pts += [(SLANT_D, H), (0, STACK_Z1)]
    return pts


def drawer_z(i):
    return STACK_Z0 + PITCH * i + 1.0


def build():
    parts.clear()
    xi = W / 2 - WALL   # 77 inner face of side walls

    # ---------------- HOUSING ----------------
    prof = rounded_profile()
    add("Wall_Left", "Housing", "shell", ("prismx", -W / 2, -xi, prof))
    add("Wall_Right", "Housing", "shell", ("prismx", xi, W / 2, prof), cut=True)
    add("Back_Wall", "Housing", "shell", ("box", -xi, D - 5, 20, xi, D, H - 10))
    add("Back_Corner_Round", "Housing", "shell", ("cyl", 10, 2 * xi, (-xi, D - 10, H - 10), (1, 0, 0)), cut=True)
    add("Roof_Flat", "Housing", "shell", ("box", -xi, SLANT_D, H - WALL, xi, D - 10, H), cut=True)
    p1, p2 = (0, STACK_Z1), (SLANT_D, H)
    poly = [p1, p2, (p2[0] - NY * WALL, p2[1] - NZ * WALL), (p1[0] - NY * WALL, p1[1] - NZ * WALL)]
    add("Header_Slanted_Panel", "Housing", "shell2", ("prismx", -xi, xi, poly))
    add("Header_Front_Rail", "Housing", "shell2", ("box", -xi, 0, STACK_Z1 - 3, xi, 5, STACK_Z1))
    add("Header_Inner_Deck", "Housing", "shell2", ("box", -xi, 5, STACK_Z1 - 4, xi, 160, STACK_Z1 - 2), cut=True)
    add("Floor_Plate", "Housing", "shell2", ("box", -xi, 0, 18, xi, D - 5, 20))
    add("Stile_Left", "Housing", "front", ("box", -xi, 0, STACK_Z0, -68, 5, STACK_Z1 - 3))
    add("Stile_Right_LockPanel", "Housing", "front", ("box", 68, 0, STACK_Z0, xi, 5, STACK_Z1 - 3))
    add("Partition_Rear_L", "Housing", "shell2", ("box", -xi, 160, 20, 38, 163, STACK_Z1 - 2))
    add("Partition_Rear_R", "Housing", "shell2", ("box", 62, 160, 20, xi, 163, STACK_Z1 - 2), cut=True)
    # plinth base (hollow) + rubber feet
    add("Plinth_Bottom", "Base", "shell2", ("box", -78, 3, 3, 78, 197, 5))
    add("Plinth_Front", "Base", "shell", ("box", -78, 3, 5, 78, 5, 18))
    add("Plinth_Back", "Base", "shell", ("box", -78, 195, 5, 78, 197, 18))
    add("Plinth_Left", "Base", "shell", ("box", -78, 5, 5, -76, 195, 18))
    add("Plinth_Right", "Base", "shell", ("box", 76, 5, 5, 78, 195, 18), cut=True)
    for i, (fx, fy) in enumerate([(-66, 15), (66, 15), (-66, 185), (66, 185)]):
        add(f"Rubber_Foot_{i+1}", "Base", "rubber", ("cyl", 7, 3, (fx, fy, 0), (0, 0, 1)))

    # ---------------- HEADER: display + speaker ----------------
    on_slant(SLANT_LEN / 2, -36, 1.0, 2.0, 72, 52, "Display_Module_Bezel", "Header", "dark")
    on_slant(SLANT_LEN / 2, -36, 2.2, 0.4, 58, 43, "Display_Active_Screen", "Header", "screen")
    on_slant(SLANT_LEN / 2, 40, 0.75, 1.5, 0, 0, "Speaker_Grille", "Header", "dark", "cyl", 21)
    for k in range(-3, 4):
        on_slant(SLANT_LEN / 2 + k * 5, 40, 1.7, 0.4, 30 - abs(k) * 3.5, 2.2,
                 f"Speaker_Slot_{k+4}", "Header", "shell2")
    # right side ports & reset, antenna
    add("USB_C_DC_Port", "Ports", "dark", ("box", W / 2, 180, 12, W / 2 + 0.6, 190, 18), cut=True)
    add("Reset_Button", "Ports", "accent", ("cyl", 4, 0.8, (W / 2, 185, 40), (1, 0, 0)), cut=True)
    add("GSM_Antenna_Base", "Ports", "dark", ("cyl", 5, 4, (64, 192, H), (0, 0, 1)))
    add("GSM_Antenna_Mast", "Ports", "dark", ("cyl", 3, 45, (64, 192, H + 4), (0, 0, 1)))

    # ---------------- DRAWERS ----------------
    for i in range(N_DRAWERS):
        z0 = drawer_z(i)
        dy = -EXT if i == EXT_DRAWER else 0.0
        g = f"Drawer_{i+1}"
        mv = [("move", (0, dy, 0))] if dy else []
        add(f"D{i+1}_Front", g, "front", ("box", -68, 0, z0, 68, 5, z0 + FRONT_H), mv)
        add(f"D{i+1}_Finger_Pull", g, "dark", ("box", -25, -0.5, z0 + 6, 25, 0.2, z0 + 14), mv)
        for k, lx in enumerate((-60, -54, -48)):
            add(f"D{i+1}_LED_{k+1}", g, "led" if k <= i % 3 else "dark",
                ("cyl", 1.5, 0.8, (lx, 0.2, z0 + 15), (0, -1, 0)), mv)
        add(f"D{i+1}_Meal_Icon", g, "accent", ("box", -57, -0.4, z0 + 4, -51, 0.2, z0 + 9), mv)
        add(f"D{i+1}_Popper_Dock", g, "shell2", ("box", 38, -0.6, z0 + 2, 64, 0.2, z0 + 18), mv)
        add(f"D{i+1}_Override_Pin", g, "dark", ("cyl", 1.25, 0.8, (32, 0.2, z0 + 5), (0, -1, 0)), mv)
        # tray body
        add(f"D{i+1}_Tray_Floor", g, "tray", ("box", -66, 5, z0, 66, 150, z0 + 1.5), mv)
        add(f"D{i+1}_Tray_Side_L", g, "tray", ("box", -66, 5, z0, -64.5, 150, z0 + 16), mv)
        add(f"D{i+1}_Tray_Side_R", g, "tray", ("box", 64.5, 5, z0, 66, 150, z0 + 16), mv)
        add(f"D{i+1}_Tray_Rear", g, "tray", ("box", -66, 148.5, z0, 66, 150, z0 + 16), mv)
        add(f"D{i+1}_Runner_L", g, "metal", ("box", -68, 10, z0 + 5, -66, 148, z0 + 9), mv)
        add(f"D{i+1}_Runner_R", g, "metal", ("box", 66, 10, z0 + 5, 68, 148, z0 + 9), mv)
        # rear latch (engaged by striker) + hall magnet
        add(f"D{i+1}_Latch_Hook", g, "accent", ("box", 44, 150, z0 + 6, 56, 158, z0 + 14), mv)
        add(f"D{i+1}_Hall_Magnet", g, "dark", ("cyl", 2.5, 3, (-58, 150, z0 + 10), (0, 1, 0)), mv)
        # fixed parts per level (do not move with drawer)
        add(f"Guide_Track_L_{i+1}", "Mechanism", "metal", ("box", -xi, 8, z0 + 4, -68.2, 158, z0 + 10))
        add(f"Guide_Track_R_{i+1}", "Mechanism", "metal", ("box", 68.2, 8, z0 + 4, xi, 158, z0 + 10), cut=True)
        add(f"Hall_Sensor_{i+1}", "Electronics", "dark", ("box", -62, 158, z0 + 7, -54, 160, z0 + 13))
        # ejection compression spring between tray rear and partition
        sy0 = 150 - (EXT if i == EXT_DRAWER else 0) + 0
        L = 160 - sy0
        n = max(4, int(L / 3.5))
        for k in range(n):
            add(f"D{i+1}_Eject_Spring_{k}", "Mechanism", "spring",
                ("torus", 3.5, 0.6, (-25, sy0 + (k + 0.5) * L / n, z0 + 9), (0, 1, 0)))
        if i < N_DRAWERS and i != 0:
            add(f"Tamper_Lock_{i+1}", "Housing", "brass", ("cyl", 4, 1.5, (72.5, 0, z0 + 10), (0, -1, 0)))
            add(f"Tamper_Lock_Key_{i+1}", "Housing", "dark", ("box", 72, -1.8, z0 + 7.5, 73, -1.4, z0 + 12.5))
    add("CD_Override_Pinhole", "Housing", "dark", ("cyl", 1.25, 1, (72.5, 0, 28), (0, -1, 0)))

    # ---------------- EXTENDED DRAWER #3 DETAILS ----------------
    z0 = drawer_z(EXT_DRAWER)
    g = f"Drawer_{EXT_DRAWER+1}"
    fy = -EXT          # front face Y
    add("Clamshell_Foil_Carrier", g, "foil", ("box", -55, fy + 12, z0 + 1.5, 55, fy + 127, z0 + 3.5))
    add("Carrier_Hinge_Spine", g, "metal", ("cyl", 1.5, 110, (-55, fy + 127, z0 + 4), (1, 0, 0)))
    nb = 0
    for gx in (-31, 31):
        for cx in (-9, 9):
            for ry in (30, 52, 74):
                nb += 1
                add(f"Blister_Pocket_{nb:02d}", g, "blister", ("dome", 6, (gx + cx, fy + ry, z0 + 3.5), (0, 0, 1)))
    # pill-popper lever (22 x 38), hinged at its rear, angled up
    hx, hy, hz = 47, fy + 40, z0 + FRONT_H - 2
    add("Popper_Lever_Hinge", g, "metal", ("cyl", 2, 26, (hx - 13, hy, hz), (1, 0, 0)))
    add("Popper_Lever_Arm", g, "accent", ("box", -11, -38, 0, 11, 0, 4),
        [("rot", (1, 0, 0), -12), ("move", (hx, hy, hz))])
    add("Popper_Punch_Pin", g, "metal", ("cyl", 1.5, 18, (hx, fy + 16, z0 + 4), (0, 0, 1)))
    # front lip, drop chute, catch cup, IR pair (catch cup sits under the lip)
    add("Drop_Chute", g, "shell2", ("tube", 5.5, 7, 14, (hx, fy + 16, z0 - 14), (0, 0, 1)))
    add("Catch_Cup", g, "accent", ("tube", 6.5, 8, 6, (hx, fy + 16, z0 - 20), (0, 0, 1)))
    add("Catch_Cup_Bottom", g, "accent", ("cyl", 8, 1, (hx, fy + 16, z0 - 21), (0, 0, 1)))
    for s in (-11, 11):
        add(f"IR_{'Emitter' if s < 0 else 'Receiver'}", g, "red", ("cyl", 1.5, 4, (hx + s, fy + 16, z0 - 9), (1 if s < 0 else -1, 0, 0)))

    # ---------------- STRIKER MECHANISM (rear) ----------------
    bx, by = 50.0, 180.0
    zl, zu = 55.0, 220.0
    for nm, zz in (("Lower", zl), ("Upper", zu)):
        add(f"Pulley_{nm}", "Mechanism", "metal", ("cyl", 8, 10, (bx - 5, by, zz), (1, 0, 0)))
        add(f"Pulley_{nm}_Axle", "Mechanism", "metal", ("cyl", 1.5, 24, (bx - 12, by, zz), (1, 0, 0)))
        add(f"Belt_Wrap_{nm}", "Mechanism", "belt", ("tube", 8, 9.5, 6, (bx - 3, by, zz), (1, 0, 0)))
    add("GT2_Belt_Front_Run", "Mechanism", "belt", ("box", bx - 3, by - 9.5, zl, bx + 3, by - 8, zu))
    add("GT2_Belt_Rear_Run", "Mechanism", "belt", ("box", bx - 3, by + 8, zl, bx + 3, by + 9.5, zu))
    for s in (-10, 10):
        add(f"Carriage_Guide_Rod_{'L' if s < 0 else 'R'}", "Mechanism", "metal",
            ("cyl", 2, 190, (bx + s, by - 12, 46), (0, 0, 1)))
    cz = drawer_z(EXT_DRAWER) + 10
    add("Striker_Carriage", "Mechanism", "accent", ("box", bx - 13, by - 16, cz - 9, bx + 13, by - 7, cz + 9))
    add("Striker_Wedge_45deg", "Mechanism", "red",
        ("prismx", bx - 6, bx + 6, [(by - 16, cz - 7), (by - 16, cz + 7), (by - 23, cz)]))
    add("Base_Stepper_Motor", "Mechanism", "dark", ("box", bx - 14, by - 14, 21, bx + 14, by + 14, 45))
    add("Motor_Shaft_Pulley", "Mechanism", "metal", ("cyl", 3, 8, (bx, by, 45), (0, 0, 1)))

    # ---------------- ELECTRONICS IN BASE ----------------
    add("Battery_Pack_5000mAh", "Electronics", "batt", ("box", -65, 12, 5, 65, 100, 17))
    add("Main_PCB", "Electronics", "pcb", ("box", -65, 105, 5, 65, 190, 6.6))
    for k, (cx, cy, sx, sy, hh) in enumerate([(-30, 130, 20, 20, 3), (10, 125, 14, 10, 2),
                                              (35, 160, 18, 12, 4), (-40, 170, 10, 10, 6),
                                              (55, 182, 12, 9, 4)]):
        add(f"PCB_Component_{k+1}", "Electronics", "dark",
            ("box", cx - sx / 2, cy - sy / 2, 6.6, cx + sx / 2, cy + sy / 2, 6.6 + hh))
    add("GSM_Module", "Electronics", "metal", ("box", 46, 140, 6.6, 70, 158, 9))
    return parts


if __name__ == "__main__":
    build()
    print(len(parts), "parts; slant angle %.1f deg" % SLANT_ANG)
