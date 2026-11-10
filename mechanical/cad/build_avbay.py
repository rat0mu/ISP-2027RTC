"""Generate the avionics bay concept model (avbay v0.4) in SOLIDWORKS.

Layout
- Bulkhead plate at the nose cone base carries everything.
- Horseshoe boards are clamped on four M3 threaded rods with spacers, the
  way a stack of round boards is normally held; nothing screws into the
  printed spine.
- A 3D printed spine stands on the bulkhead inside the board slot. Its
  lower part is an open channel holding four 18650 cells, reached from
  the open (+X) side.
- Above the boards the spine widens into two hollow equipment bays with
  filleted transitions; modules and antennas mount on their flat faces.

Drives a running SOLIDWORKS session through its COM API and writes native
SLDPRT / SLDASM files plus preview images next to this script. All
dimensions live in PARAMS (mm).

Requirements: Windows, SOLIDWORKS 2018 or later, Python 3.10+, pywin32.
Usage:        python mechanical/cad/build_avbay.py [--out DIR]

The nose cone is not modelled. Its inner profile, scaled from a low
resolution sketch, is used only for the printed clearance report. Nothing
here is a strength, thermal or manufacturing check.
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import sys

import pythoncom
import win32com.client
from win32com.client import VARIANT

VERSION = "v0_4"
PREFIX = f"avbay_{VERSION}_"

# ---------------------------------------------------------------- parameters
PARAMS = {
    # boards
    "pcb_dia": 110.0,
    "pcb_thk": 1.6,
    "pcb_count": 5,  # 1 backup, 2 power, 3 main, 4 reserved, 5 comms
    "rod_pcd": 98.0,  # pitch circle of the threaded rods
    "rod_angles": (45, 135, 225, 315),
    "rod_hole": 3.2,  # M3 clearance
    "rod_dia": 3.0,
    "nut_dia": 6.0,
    "nut_thk": 2.4,
    "spacer_od": 5.5,
    "spacer_base_len": 10.0,  # bulkhead -> first board
    "spacer_len": 15.0,  # between boards
    "slot_clear": 1.0,  # board slot to spine wall
    "slot_corner_r": 6.0,
    "tip_r": 3.0,  # rounding of the two horseshoe tips
    "conn_size": (22.0, 7.0),  # board-to-board connector placeholder, x by y
    "conn_pos": (15.0, 36.0),  # its centre on the +Y arm (mirrored on -Y)
    # bulkhead
    "bulkhead_dia": 138.0,
    "bulkhead_thk": 6.0,
    "retain_pcd": 128.0,  # 4 screws into the printed nose cone ring
    "retain_hole": 4.3,  # M4 clearance
    "ubolt_spacing": 60.0,  # along Y, straddling the spine
    "ubolt_hole": 6.5,  # M6 clearance
    "wire_hole": 10.0,  # deployment harness pass-through
    "wire_hole_x": -40.0,
    # spine: battery channel (U section, open toward +X)
    "cell_dia": 18.5,
    "cell_len": 65.0,
    "cavity_x": (-10.0, 10.0),  # cavity depth, cell axis at x = 0
    "cavity_half_y": 19.5,  # two cells side by side
    "spine_wall": 3.0,
    "spine_corner_r": 5.0,  # rounding of the two back corners
    "foot_x": (-25.0, 22.0),
    "foot_thk": 4.0,
    "foot_holes": [(-19.0, 15.0), (-19.0, -15.0), (16.0, 15.0), (16.0, -15.0)],
    "foot_hole": 4.3,  # M4 clearance
    "floor_thk": 3.0,
    "cell_gap": 2.0,  # contact space under each cell tier
    # spine: equipment bays (hollow, rounded boxes centred on the axis)
    "bay_wall": 4.0,
    "bay1_z": (110.0, 168.0),  # stations of bay 1 bottom and top
    "bay1_half": (34.0, 44.0),  # half size in x and y
    "bay1_corner_r": 12.0,
    "bay2_top_z": 238.0,
    "bay2_half": (23.5, 33.5),
    "bay2_corner_r": 10.0,
    "neck_fillet": 8.0,  # channel walls into the bay 1 floor
    "bay1_bottom_fillet": 6.0,
    "step_fillet": 5.0,  # bay 1 top edge, bay 2 foot and bay 2 top edge
    "bay2_window_z": (172.0, 230.0),  # access window in the +X wall of bay 2
    "bay2_window_half_y": 20.0,
    # nose cone inner surface (station from base, inner radius); not modelled,
    # used only for the clearance report
    "nose_profile": [
        (0.0, 70.0), (34.2, 70.0), (59.7, 68.4), (85.1, 66.8), (110.6, 64.4),
        (136.0, 61.3), (161.5, 57.3), (187.0, 54.1), (212.4, 48.5),
        (237.9, 43.0), (263.3, 36.6), (288.8, 30.2), (314.2, 22.3),
        (339.7, 14.3), (365.1, 6.4), (377.9, 0.0),
    ],
}

MM = 1e-3
TOL = 0.02  # mm, for matching edge end points
COLORS = {  # r, g, b, transparency
    "bulkhead": (0.75, 0.76, 0.78, 0.0),
    "pcb": (0.05, 0.45, 0.2, 0.0),
    "spacer": (0.85, 0.7, 0.3, 0.0),
    "steel": (0.6, 0.62, 0.65, 0.0),
    "conn": (0.08, 0.08, 0.08, 0.0),
    "spine": (0.36, 0.37, 0.4, 0.0),
    "cell": (0.15, 0.4, 0.85, 0.0),
}


# ------------------------------------------------------------------ helpers
def noarg(obj, name):
    """Late-bound COM exposes some zero-argument methods as properties."""
    value = getattr(obj, name)
    if value is None or isinstance(value, win32com.client.CDispatch):
        return value  # already the returned COM object
    return value() if callable(value) else value


def find_template(pattern: str) -> str:
    roots = [
        r"C:\ProgramData\SolidWorks\SOLIDWORKS *\templates",
        r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS *\templates",
    ]
    for root in roots:
        hits = sorted(glob.glob(os.path.join(root, "**", pattern), recursive=True))
        if hits:
            return hits[0]
    raise SystemExit(f"no SOLIDWORKS template matching {pattern!r}; pass it explicitly")


def ref_planes(model):
    """Return the default planes in creation order: front (XY), top, right."""
    planes = []
    feat = noarg(model, "FirstFeature")
    while feat is not None and len(planes) < 3:
        if noarg(feat, "GetTypeName2") == "RefPlane":
            planes.append(feat)
        feat = noarg(feat, "GetNextFeature")
    return planes


def start_sketch(model, plane_index=0):
    model.ClearSelection2(True)
    ref_planes(model)[plane_index].Select2(False, 0)
    sm = model.SketchManager
    sm.InsertSketch(True)
    sm.AddToDB = True  # no snapping / inference while adding entities
    return sm


def extrude(model, depth_mm, offset_mm=0.0):
    """Blind boss toward +Z, optionally starting offset_mm above the plane."""
    start = 3 if offset_mm else 0  # swStartOffset / swStartSketchPlane
    feat = model.FeatureManager.FeatureExtrusion2(
        True, False, False, 0, 0, depth_mm * MM, 0.0, False, False, False, False,
        0.0, 0.0, False, False, False, False, True, True, True,
        start, offset_mm * MM, False)
    model.SketchManager.AddToDB = False
    if feat is None:
        raise RuntimeError("extrusion failed")
    return feat


def cut(model, depth_mm, offset_mm):
    """Blind cut toward +Z starting offset_mm above the sketch plane.

    The third argument (Dir) must be True: a cut runs toward -Z by default,
    the opposite of a boss.
    """
    feat = model.FeatureManager.FeatureCut3(
        True, False, True, 0, 0, depth_mm * MM, 0.0, False, False, False, False,
        0.0, 0.0, False, False, False, False, False, True, True, True, True, False,
        3, offset_mm * MM, False)
    model.SketchManager.AddToDB = False
    if feat is None:
        raise RuntimeError("cut failed")
    return feat


def edge_ends(model):
    """Yield (edge, start, end) with end points in mm; skips closed edges."""
    for body in model.GetBodies2(0, False):
        for edge in body.GetEdges():
            v0, v1 = noarg(edge, "GetStartVertex"), noarg(edge, "GetEndVertex")
            if v0 is None or v1 is None:
                continue
            yield (edge, [v / MM for v in noarg(v0, "GetPoint")],
                   [v / MM for v in noarg(v1, "GetPoint")])


def fillet(model, radius_mm, pred, label):
    """Constant radius fillet on every edge whose two end points satisfy pred."""
    model.ClearSelection2(True)
    sel = noarg(model.SelectionManager, "CreateSelectData")
    sel.Mark = 1
    count = 0
    for edge, p0, p1 in edge_ends(model):
        if pred(p0, p1):
            edge.Select4(True, sel)
            count += 1
    if count == 0:
        raise RuntimeError(f"fillet '{label}': no edge matched")
    empty = lambda: VARIANT(pythoncom.VT_EMPTY, None)  # noqa: E731
    feat = model.FeatureManager.FeatureFillet3(
        195, radius_mm * MM, 0.0, 0.0, 0, 0, 0, empty(), empty(), empty(), empty(), empty())
    model.ClearSelection2(True)
    if feat is None:
        raise RuntimeError(f"fillet '{label}' failed on {count} edge(s)")
    print(f"    fillet {label}: R{radius_mm:g} on {count} edge(s)")
    return feat


def near(a, b):
    return abs(a - b) < TOL


def vertical_at(points):
    """Predicate: a vertical edge standing on one of the given (x, y) points."""
    def pred(p0, p1):
        return (near(p0[0], p1[0]) and near(p0[1], p1[1]) and not near(p0[2], p1[2])
                and any(near(p0[0], x) and near(p0[1], y) for x, y in points))
    return pred


def loop_at(z_part, on_outline):
    """Predicate: an edge lying at height z_part with both ends on an outline."""
    def pred(p0, p1):
        return (near(p0[2], z_part) and near(p1[2], z_part)
                and on_outline(p0[0], p0[1]) and on_outline(p1[0], p1[1]))
    return pred


def on_box(hx, hy):
    """Outline test for a rounded box of half size hx by hy centred on the axis."""
    def test(x, y):
        return ((near(abs(x), hx) and abs(y) <= hy + TOL)
                or (near(abs(y), hy) and abs(x) <= hx + TOL))
    return test


def circle(sm, x, y, dia):
    sm.CreateCircleByRadius(x * MM, y * MM, 0.0, dia / 2 * MM)


def polygon(sm, pts):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        sm.CreateLine(x0 * MM, y0 * MM, 0.0, x1 * MM, y1 * MM, 0.0)


def rect(sm, x0, y0, x1, y1):
    polygon(sm, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def rounded_rect(sm, hx, hy, r):
    """Rounded rectangle of half size hx by hy centred on the origin."""
    corners = [  # centre, arc start, arc end (counter-clockwise)
        ((hx - r, -hy + r), (hx - r, -hy), (hx, -hy + r)),
        ((hx - r, hy - r), (hx, hy - r), (hx - r, hy)),
        ((-hx + r, hy - r), (-hx + r, hy), (-hx, hy - r)),
        ((-hx + r, -hy + r), (-hx, -hy + r), (-hx + r, -hy)),
    ]
    for i, (c, a, b) in enumerate(corners):
        sm.CreateArc(c[0] * MM, c[1] * MM, 0.0, a[0] * MM, a[1] * MM, 0.0, b[0] * MM, b[1] * MM, 0.0, 1)
        nxt = corners[(i + 1) % 4][1]
        sm.CreateLine(b[0] * MM, b[1] * MM, 0.0, nxt[0] * MM, nxt[1] * MM, 0.0)


def polar(pcd, angles):
    return [(pcd / 2 * math.cos(math.radians(a)), pcd / 2 * math.sin(math.radians(a))) for a in angles]


def set_color(model, key):
    r, g, b, transparency = COLORS[key]
    try:
        model.MaterialPropertyValues = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8,
            [r, g, b, 1.0, 1.0, 0.3, 0.3, transparency, 0.0])
    except Exception as exc:  # appearance only
        print("  note: could not set colour:", exc)


def save(model, path):
    noarg(model, "EditRebuild3")
    err = model.SaveAs3(path, 0, 1)
    if err:
        raise RuntimeError(f"SaveAs3 failed ({err}) for {path}")


def box_mm(model):
    return [round(v / MM, 2) for v in model.GetPartBox(True)]


# ----------------------------------------------------------------- geometry
def spine_dims(p):
    cx0, cx1 = p["cavity_x"]
    wall = p["spine_wall"]
    return {
        "x_back": cx0 - wall,  # outer face of the back wall
        "x_front": cx1,  # open face
        "half_y": p["cavity_half_y"] + wall,  # outer face of the side walls
    }


# -------------------------------------------------------------------- parts
def build_disc(sw, tpl, path, dia, thk, holes, color):
    model = sw.NewDocument(tpl, 0, 0, 0)
    sm = start_sketch(model)
    circle(sm, 0, 0, dia)
    for add in holes:
        add(sm)
    extrude(model, thk)
    set_color(model, color)
    save(model, path)
    return model


def build_block(sw, tpl, path, size_x, size_y, height, color):
    model = sw.NewDocument(tpl, 0, 0, 0)
    sm = start_sketch(model)
    rect(sm, -size_x / 2, -size_y / 2, size_x / 2, size_y / 2)
    extrude(model, height)
    set_color(model, color)
    save(model, path)
    return model


def build_pcb(sw, tpl, path, p):
    """Horseshoe board: disc with a slot from behind the spine to the +X edge."""
    s = spine_dims(p)
    c = p["slot_clear"]
    r = p["pcb_dia"] / 2
    half = s["half_y"] + c
    x_in = s["x_back"] - c
    x_edge = math.sqrt(r * r - half * half)
    model = sw.NewDocument(tpl, 0, 0, 0)
    sm = start_sketch(model)
    sm.CreateArc(0.0, 0.0, 0.0, x_edge * MM, half * MM, 0.0, x_edge * MM, -half * MM, 0.0, 1)
    sm.CreateLine(x_edge * MM, -half * MM, 0.0, x_in * MM, -half * MM, 0.0)
    sm.CreateLine(x_in * MM, -half * MM, 0.0, x_in * MM, half * MM, 0.0)
    sm.CreateLine(x_in * MM, half * MM, 0.0, x_edge * MM, half * MM, 0.0)
    for x, y in polar(p["rod_pcd"], p["rod_angles"]):
        circle(sm, x, y, p["rod_hole"])
    extrude(model, p["pcb_thk"])
    print("  pcb_outline")
    fillet(model, p["slot_corner_r"], vertical_at([(x_in, half), (x_in, -half)]), "slot corners")
    fillet(model, p["tip_r"], vertical_at([(x_edge, half), (x_edge, -half)]), "horseshoe tips")
    set_color(model, "pcb")
    save(model, path)
    return model


def build_spine(sw, tpl, path, p, tiers):
    """Spine: foot, battery channel, two filleted equipment bays.

    Part origin sits on the bulkhead top face; stations in PARAMS and tiers
    are measured from the nose cone base, hence the `- base` everywhere.
    """
    s = spine_dims(p)
    base = p["bulkhead_thk"]
    cx0, cx1 = p["cavity_x"]
    hy_in, hy_out = p["cavity_half_y"], s["half_y"]
    xb, xf = s["x_back"], s["x_front"]
    cap = p["cell_gap"] + 1.0  # air above a cell tier before its floor
    channel_top = tiers[-1][1] + cap + p["floor_thk"]
    w = p["bay_wall"]
    (b1z0, b1z1), (b1x, b1y), b1r = p["bay1_z"], p["bay1_half"], p["bay1_corner_r"]
    b2z1, (b2x, b2y), b2r = p["bay2_top_z"], p["bay2_half"], p["bay2_corner_r"]
    model = sw.NewDocument(tpl, 0, 0, 0)
    print("  spine")

    sm = start_sketch(model)  # battery channel walls, up to the cap of the top tier
    polygon(sm, [(xb, -hy_out), (xf, -hy_out), (xf, -hy_in), (cx0, -hy_in),
                 (cx0, hy_in), (xf, hy_in), (xf, hy_out), (xb, hy_out)])
    extrude(model, channel_top - base)
    fillet(model, p["spine_corner_r"], vertical_at([(xb, hy_out), (xb, -hy_out)]), "channel back corners")

    sm = start_sketch(model)  # foot
    rect(sm, p["foot_x"][0], -hy_out, p["foot_x"][1], hy_out)
    for x, y in p["foot_holes"]:
        circle(sm, x, y, p["foot_hole"])
    extrude(model, p["foot_thk"])

    for _, z_top in tiers:  # floor above each cell tier
        sm = start_sketch(model)
        rect(sm, cx0 - 0.5, -hy_in - 0.5, cx1, hy_in + 0.5)
        extrude(model, p["floor_thk"], z_top + cap - base)

    sm = start_sketch(model)  # bay 1 floor
    rounded_rect(sm, b1x, b1y, b1r)
    extrude(model, w, b1z0 - base)
    sm = start_sketch(model)  # bay 1 walls
    rounded_rect(sm, b1x, b1y, b1r)
    rounded_rect(sm, b1x - w, b1y - w, b1r - w)
    extrude(model, b1z1 - b1z0 - 2 * w, b1z0 + w - base)
    sm = start_sketch(model)  # bay 1 roof
    rounded_rect(sm, b1x, b1y, b1r)
    extrude(model, w, b1z1 - w - base)
    sm = start_sketch(model)  # bay 2 walls
    rounded_rect(sm, b2x, b2y, b2r)
    rounded_rect(sm, b2x - w, b2y - w, b2r - w)
    extrude(model, b2z1 - b1z1 - w, b1z1 - base)
    sm = start_sketch(model)  # bay 2 top
    rounded_rect(sm, b2x, b2y, b2r)
    extrude(model, w, b2z1 - w - base)

    def on_channel(x, y):  # outer faces of the channel: back and both sides
        return ((near(abs(y), hy_out) and xb - TOL <= x <= xf + TOL)
                or (near(x, xb) and abs(y) <= hy_out + TOL))

    fillet(model, p["neck_fillet"], loop_at(b1z0 - base, on_channel), "channel into bay 1 floor")
    fillet(model, p["bay1_bottom_fillet"], loop_at(b1z0 - base, on_box(b1x, b1y)), "bay 1 bottom edge")
    fillet(model, p["step_fillet"], loop_at(b1z1 - base, on_box(b1x, b1y)), "bay 1 top edge")
    fillet(model, p["step_fillet"], loop_at(b1z1 - base, on_box(b2x, b2y)), "bay 2 foot")
    fillet(model, p["step_fillet"], loop_at(b2z1 - base, on_box(b2x, b2y)), "bay 2 top edge")

    # reopen the cell channel through the bay 1 floor and out through its +X wall
    z0, z1 = tiers[-1][0] - p["cell_gap"], tiers[-1][1] + cap
    sm = start_sketch(model)
    rect(sm, cx0, -hy_in, b1x + 5.0, hy_in)
    cut(model, z1 - z0, z0 - base)
    # join the two bays: open the bay 1 roof inside the bay 2 walls
    sm = start_sketch(model)
    rounded_rect(sm, b2x - w, b2y - w, b2r - w)
    cut(model, 2 * w, b1z1 - w - 1.0 - base)
    # access window in the +X wall of bay 2
    wz0, wz1 = p["bay2_window_z"]
    sm = start_sketch(model)
    rect(sm, b2x - w - 2.0, -p["bay2_window_half_y"], b2x + 5.0, p["bay2_window_half_y"])
    cut(model, wz1 - wz0, wz0 - base)

    set_color(model, "spine")
    save(model, path)
    return model


# ----------------------------------------------------------------- assembly
def place(sw, asm, path, z_mm, x_mm=0.0, y_mm=0.0):
    comp = asm.AddComponent5(path, 0, "", False, "", 0.0, 0.0, 0.0)
    if comp is None:
        raise RuntimeError(f"could not insert {path}")
    math_util = noarg(sw, "GetMathUtility")
    math_util._FlagAsMethod("CreateTransform")  # late binding would read it as a property
    xform = math_util.CreateTransform(VARIANT(
        pythoncom.VT_ARRAY | pythoncom.VT_R8,
        [1, 0, 0, 0, 1, 0, 0, 0, 1, x_mm * MM, y_mm * MM, z_mm * MM, 1, 0, 0, 0]))
    comp.Select2(False, 0)
    noarg(asm, "UnfixComponent")
    comp.Transform2 = xform
    comp.Select2(False, 0)
    noarg(asm, "FixComponent")
    asm.ClearSelection2(True)
    return comp


def snapshot(asm, path, view_name, view_id):
    """Save the graphics area as an image."""
    try:
        asm.ShowNamedView2(view_name, view_id)
        noarg(asm, "ViewZoomtofit2")
        asm.SaveAs3(path, 0, 1)
    except Exception as exc:
        print(f"  note: image {os.path.basename(path)} not written:", exc)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--out", default=here, help="output folder (default: this folder)")
    ap.add_argument("--part-template", default=None)
    ap.add_argument("--asm-template", default=None)
    args = ap.parse_args()

    p = PARAMS
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    part_tpl = args.part_template or find_template("part 0251mm to 1000mm.prtdot")
    asm_tpl = args.asm_template or find_template("assembly 0251mm to 1000mm.asmdot")

    def f(name):
        return os.path.join(out, PREFIX + name)

    names = ["bulkhead.SLDPRT", "pcb_outline.SLDPRT", "spacer_m3_10.SLDPRT", "spacer_m3_15.SLDPRT",
             "rod_m3.SLDPRT", "nut_m3.SLDPRT", "stack_connector.SLDPRT", "spine.SLDPRT",
             "cell_18650.SLDPRT", "assembly.SLDASM", "view_iso.png", "view_open_side.png",
             "view_side.png"]
    for n in names:
        if os.path.exists(f(n)):
            os.remove(f(n))

    sw = win32com.client.Dispatch("SldWorks.Application")
    sw.Visible = True
    if noarg(sw, "GetDocumentCount") != 0:
        raise SystemExit("close all SOLIDWORKS documents before running this script")

    # stations (mm from the nose cone base, +Z toward the tip)
    base = p["bulkhead_thk"]
    z_first = base + p["spacer_base_len"]
    pitch = p["pcb_thk"] + p["spacer_len"]
    pcb_z = [z_first + i * pitch for i in range(p["pcb_count"])]
    stack_top = pcb_z[-1] + p["pcb_thk"]
    rod_len = stack_top + p["nut_thk"] + 1.6
    tiers = []  # (z bottom, z top) of each cell tier: backup pair, then main pair
    z = base + p["foot_thk"] + p["cell_gap"]
    for _ in range(2):
        tiers.append((z, z + p["cell_len"]))
        z += p["cell_len"] + p["cell_gap"] + 1.0 + p["floor_thk"] + p["cell_gap"]
    s = spine_dims(p)
    rods = polar(p["rod_pcd"], p["rod_angles"])
    hole = lambda dia: (lambda sm: circle(sm, 0, 0, dia))  # noqa: E731

    print("building parts ...")
    half = p["ubolt_spacing"] / 2
    bulkhead = build_disc(sw, part_tpl, f("bulkhead.SLDPRT"), p["bulkhead_dia"], p["bulkhead_thk"], [
        lambda sm: [circle(sm, x, y, p["rod_hole"]) for x, y in rods],
        lambda sm: [circle(sm, x, y, p["retain_hole"]) for x, y in polar(p["retain_pcd"], (0, 90, 180, 270))],
        lambda sm: [circle(sm, x, y, p["foot_hole"]) for x, y in p["foot_holes"]],
        lambda sm: circle(sm, 0, half, p["ubolt_hole"]),
        lambda sm: circle(sm, 0, -half, p["ubolt_hole"]),
        lambda sm: circle(sm, p["wire_hole_x"], 0, p["wire_hole"]),
    ], "bulkhead")
    pcb = build_pcb(sw, part_tpl, f("pcb_outline.SLDPRT"), p)
    sp10 = build_disc(sw, part_tpl, f("spacer_m3_10.SLDPRT"), p["spacer_od"], p["spacer_base_len"],
                      [hole(p["rod_hole"])], "spacer")
    sp15 = build_disc(sw, part_tpl, f("spacer_m3_15.SLDPRT"), p["spacer_od"], p["spacer_len"],
                      [hole(p["rod_hole"])], "spacer")
    rod = build_disc(sw, part_tpl, f("rod_m3.SLDPRT"), p["rod_dia"], rod_len, [], "steel")
    nut = build_disc(sw, part_tpl, f("nut_m3.SLDPRT"), p["nut_dia"], p["nut_thk"], [hole(p["rod_hole"])], "steel")
    conn = build_block(sw, part_tpl, f("stack_connector.SLDPRT"), p["conn_size"][0], p["conn_size"][1],
                       p["spacer_len"], "conn")
    spine = build_spine(sw, part_tpl, f("spine.SLDPRT"), p, tiers)
    cell = build_disc(sw, part_tpl, f("cell_18650.SLDPRT"), p["cell_dia"], p["cell_len"], [], "cell")

    for label, model in (("bulkhead", bulkhead), ("pcb_outline", pcb), ("spacer_m3_10", sp10),
                         ("spacer_m3_15", sp15), ("rod_m3", rod), ("nut_m3", nut),
                         ("stack_connector", conn), ("spine", spine), ("cell_18650", cell)):
        print(f"  {label:16s} box [xmin ymin zmin xmax ymax zmax] mm = {box_mm(model)}")
    sb = box_mm(spine)
    if sb[2] < -0.01 or abs(sb[5] - (p["bay2_top_z"] - base)) > 0.01:
        raise RuntimeError("spine features were offset in the wrong direction")
    bodies = spine.GetBodies2(0, False)
    volume = noarg(spine.Extension, "CreateMassProperty").Volume * 1e6
    print(f"  spine: {len(bodies)} solid body, volume {volume:.0f} cm3")

    print("building assembly ...")
    asm = sw.NewDocument(asm_tpl, 0, 0, 0)
    comps = [("bulkhead", place(sw, asm, f("bulkhead.SLDPRT"), 0.0)),
             ("spine", place(sw, asm, f("spine.SLDPRT"), base))]
    for x, y in rods:
        comps.append(("rod", place(sw, asm, f("rod_m3.SLDPRT"), 0.0, x, y)))
        comps.append(("spacer_base", place(sw, asm, f("spacer_m3_10.SLDPRT"), base, x, y)))
        comps.append(("nut", place(sw, asm, f("nut_m3.SLDPRT"), stack_top, x, y)))
    cx, cy = p["conn_pos"]
    for i, z in enumerate(pcb_z, start=1):
        comps.append((f"pcb_layer_{i}", place(sw, asm, f("pcb_outline.SLDPRT"), z)))
        if i < len(pcb_z):
            for x, y in rods:
                comps.append((f"spacer_above_{i}", place(sw, asm, f("spacer_m3_15.SLDPRT"), z + p["pcb_thk"], x, y)))
            for y in (cy, -cy):
                comps.append((f"connector_above_{i}",
                              place(sw, asm, f("stack_connector.SLDPRT"), z + p["pcb_thk"], cx, y)))
    cell_y = p["cell_dia"] / 2 + 0.35
    for i, (z0, _) in enumerate(tiers, start=1):
        for y in (cell_y, -cell_y):
            comps.append((f"cell_tier_{i}", place(sw, asm, f("cell_18650.SLDPRT"), z0, 0.0, y)))
    noarg(asm, "EditRebuild3")

    print("component stations (z min .. z max, mm):")
    seen = set()
    for label, comp in comps:
        b = comp.GetBox(False, False)
        key = (label, round(b[2] / MM, 1))
        if key in seen:
            continue
        seen.add(key)
        print(f"  {label:20s} {b[2] / MM:7.1f} .. {b[5] / MM:7.1f}")

    mgr = asm.InterferenceDetectionManager
    mgr.TreatCoincidenceAsInterference = False
    for method in ("GetInterferences", "GetInterferenceCount", "Done"):
        mgr._FlagAsMethod(method)  # late binding would read these as properties
    found = mgr.GetInterferences()
    count = mgr.GetInterferenceCount()
    print(f"interference check: {count} interfering pair(s)")
    for item in (found or []):
        names_ = [noarg(c, "Name2") for c in item.Components]
        print(f"  {names_} volume {item.Volume * 1e9:.2f} mm^3")
    mgr.Done()

    def inner_radius(z):
        prof = p["nose_profile"]
        for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
            if z0 <= z <= z1:
                return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return 0.0

    def reach(hx, hy, r):  # farthest point of a rounded box from the axis
        return math.hypot(hx - r, hy - r) + r

    print("radial clearance to the nose cone inner surface (mm):")
    for label, radius, z in (
            ("bulkhead top edge", p["bulkhead_dia"] / 2, base),
            ("top board edge", p["pcb_dia"] / 2, stack_top),
            ("bay 1 corner, top", reach(*p["bay1_half"], p["bay1_corner_r"]), p["bay1_z"][1]),
            ("bay 2 corner, top", reach(*p["bay2_half"], p["bay2_corner_r"]), p["bay2_top_z"])):
        print(f"  {label:22s} z={z:6.1f}  part r={radius:5.1f}  cone r={inner_radius(z):5.1f}"
              f"  clearance={inner_radius(z) - radius:5.1f}")

    r_pcb = p["pcb_dia"] / 2
    slot_half = s["half_y"] + p["slot_clear"]
    slot_area = (slot_half * 2) * (math.sqrt(r_pcb ** 2 - slot_half ** 2) - (s["x_back"] - p["slot_clear"]))
    print(f"board area kept after the slot: about {100 * (1 - slot_area / (math.pi * r_pcb ** 2)):.0f} %")

    save(asm, f("assembly.SLDASM"))
    snapshot(asm, f("view_iso.png"), "*Isometric", 7)
    snapshot(asm, f("view_open_side.png"), "*Right", 4)
    snapshot(asm, f("view_side.png"), "*Top", 5)
    asm.ShowNamedView2("*Isometric", 7)
    noarg(asm, "ViewZoomtofit2")

    print("total components:", len(comps))
    print("cell tiers (z):", [(round(a, 1), round(b, 1)) for a, b in tiers])
    print("written to", out)


if __name__ == "__main__":
    sys.exit(main())
