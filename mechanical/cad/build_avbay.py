"""Generate the avionics bay concept model (avbay v0.10) in SOLIDWORKS.

Layout
- Bulkhead plate at the nose cone base carries everything.
- Horseshoe boards are clamped on four M3 threaded rods with spacers, the
  way a stack of round boards is normally held; nothing screws into the
  printed spine.
- A 3D printed spine stands on the bulkhead inside the board slot. Its
  lower part is an open channel holding four 18650 cells standing upright:
  two welded pairs, each pair one behind the other along X so the channel
  (and the board slot) stays narrow, with about 1 mm of sleeve room around
  them. A pair slides out through the open (+X) side, which is closed by a
  printed cover held with eight M3 screws.
- Above the boards the spine widens (filleted neck) into one hollow
  equipment bay of constant section. The competition's stock GPS tracker
  stands inside it and slides in and out through the open +X side. The
  other three faces carry screw bosses for small modules and zip-tie posts
  for cables; a separate printed cap closes the top and carries the 433 MHz
  and tracker antennas and the GPS patch. The 920 MHz antenna hangs down
  along the -Y face from a small printed bracket.

Drives a running SOLIDWORKS session through its COM API and writes native
SLDPRT / SLDASM files plus preview images next to this script. All
dimensions live in PARAMS (mm).

Requirements: Windows, SOLIDWORKS 2018 or later, Python 3.10+, pywin32.
Usage:        python mechanical/cad/build_avbay.py [--out DIR]

The nose cone itself is not part of the output; its inner profile (measured
from NOSE_v1.SLDPRT) is used only for the printed clearance report, and
fitcheck_nose.py places the result inside the real nose cone. Nothing here
is a strength, thermal or manufacturing check.
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

VERSION = "v0_10"
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
    "spacer_len": 11.81,  # between boards = mated height of Samtec SFM/TFM, lead style -32
    "slot_clear": 1.0,  # board slot to spine wall
    "slot_corner_r": 6.0,
    "tip_r": 3.0,  # rounding of the two horseshoe tips
    # board-to-board stacking connector placeholders (Samtec SFM/TFM, 1.27 mm, two rows);
    # body sizes are estimates until samples are measured. x by y, centre at (x, +-y).
    "conn_main": (31.0, 6.0),  # 2x20 on the +Y arm, main system bus
    "conn_backup": (18.3, 6.0),  # 2x10 on the -Y arm, backup system bus
    "conn_pos": (13.0, 36.0),
    # bulkhead
    "bulkhead_dia": 130.0,  # NOSE_v1 shoulder bore is 132
    "bulkhead_thk": 6.0,
    "retain_pcd": 118.0,  # 4 screws into the printed nose cone ring
    "retain_hole": 4.3,  # M4 clearance
    "ubolt_spacing": 60.0,  # along Y, straddling the spine
    "ubolt_hole": 6.5,  # M6 clearance
    "wire_hole": 10.0,  # deployment harness pass-through
    "wire_hole_x": -40.0,
    # spine: battery channel (U section, open toward +X)
    "cell_dia": 18.5,
    "cell_len": 65.0,
    "cavity_x": (-20.5, 20.5),  # two cells one behind the other along X, about 1 mm sleeve room
    "cavity_half_y": 11.0,  # one cell wide, 1.75 mm per side for a sleeve
    "spine_wall": 3.0,
    "spine_corner_r": 5.0,  # rounding of the two back corners
    "foot_x": (-27.0, 24.0),
    "foot_half_y": 22.0,  # wider than the channel so the screws clear its walls
    "foot_thk": 4.0,
    "foot_holes": [(-21.0, 17.5), (-21.0, -17.5), (18.0, 17.5), (18.0, -17.5)],
    "foot_hole": 4.3,  # M4 clearance
    "floor_thk": 3.0,
    "cell_gap": 2.0,  # contact space under each cell tier
    # screwed side cover over the open (+X) face of the battery channel; lugs on
    # the outside of the channel walls sit between the boards (rows are stations)
    "cover": {"thk": 3.0, "end_gap": 0.5, "lug_len": 8.0, "lug_out": 6.0, "lug_tall": 8.0,
              "rows_z": (23.5, 63.7, 96.0, 135.0), "pilot": 2.5, "screw_hole": 3.4,
              "wire_half": 4.0, "wire_tall": 6.0, "floor_clear": 0.5},
    # spine: equipment bays (hollow, rounded boxes centred on the axis)
    "bay_wall": 4.0,
    "bay_z": (110.0, 276.0),  # stations of the bay floor and top
    "bay_half": (30.0, 40.0),  # half size in x and y, constant over the height
    "bay_corner_r": 10.0,
    "neck_fillet": 8.0,  # channel walls into the bay 1 floor
    "bay_bottom_fillet": 6.0,
    "bay_top_fillet": 5.0,
    "window_z": (114.0, 268.0),  # opening in the +X wall: cells below, tracker above
    "window_half_y": 34.0,
    # stock GPS tracker (Rocket Beacon, potted box with 18650, LoRa + GNSS); size
    # estimated from the technical note's pictures, not measured
    "tracker": {"size": (32.0, 65.0, 110.0), "z": 158.0},  # x, y, z extents; stands on the axis
    # antenna placeholders on the bay 2 top face: (x, y) centre, footprint, height
    # flexible (rubber duck) antennas on the cap: (x, y) centre, diameter, length
    "ant_433": {"pos": (0.0, 0.0), "dia": 6.0, "len": 150.0},  # backup system telemetry (DEC-001); on axis; a true quarter wave (~165) does not fit the tip
    "ant_920": {"pos": (-2.0, -45.0), "dia": 6.0, "len": 80.0,  # main system telemetry (DEC-001)
                "mount": {"z": (242.0, 250.0), "half_x": 5.0, "out": 10.0, "hole": 6.5}},  # bracket on the -Y face; SMA and whip hang below it
    "ant_tracker": {"pos": (14.0, 14.0), "dia": 6.0, "len": 80.0},  # the tracker's own LoRa antenna (TW band)
    "sma_base": {"dia": 8.0, "len": 10.0},  # SMA jack under each antenna
    "gnss_patch": {"pos": (-17.5, 0.0), "size": (25.0, 25.0), "thk": 4.0},  # custom GPS
    # removable top cap: plate on the wall tops, lip inside the walls, two screws into the Y walls
    "cap": {"thk": 4.0, "lip": 3.0, "lip_clear": 0.3, "screw_hole": 2.7, "screw_y": 38.0, "ant_hole": 6.5},
    # mounting bosses on the -X, +Y and -Y faces (M3 self-tapping), rows are stations
    "boss": {"dia": 6.0, "hole": 2.5, "height": 3.0, "rows_z": (130.0, 170.0, 210.0, 250.0),
             "y_face_x": (-12.5, 12.5), "x_face_y": (-15.0, 15.0)},
    # zip-tie posts on the +Y and -Y faces: two 2.5 mm posts with a 4 mm gap, 8 mm tall
    "clip": {"post": 2.5, "gap": 4.0, "tall": 8.0, "out": 6.0, "x": 10.0, "rows_z": (135.0, 175.0, 215.0, 250.0)},
    # custom GPS board placeholder standing on the -X face bosses: thickness (x), width (y), height (z)
    "gps_board": {"size": (8.0, 30.0, 45.0), "z": 190.0},
    # nose cone inner surface (station from the open end, inner radius), measured
    # from NOSE_v1.SLDPRT; used only for the clearance report (fitcheck_nose.py
    # does the real geometric check)
    "nose_profile": [  # NOSE_v1.SLDPRT inner surface, 80 mm shoulder then the ogive
        (0.0, 66.0), (80.0, 66.0), (80.01, 70.0), (100.0, 69.8), (115.0, 69.3),
        (135.0, 68.5), (155.0, 67.4), (170.0, 66.0), (190.0, 64.3), (205.0, 62.3),
        (225.0, 60.0), (240.0, 57.4), (260.0, 54.5), (280.0, 51.3), (295.0, 47.8),
        (315.0, 44.0), (330.0, 39.9), (350.0, 35.5), (370.0, 30.7), (385.0, 25.7),
        (405.0, 20.3), (425.0, 14.6), (440.0, 8.6), (460.0, 2.3), (465.0, 0.0),
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
    "cover": (0.85, 0.45, 0.1, 0.35),
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


def side_boss(model, plane_index, sketch, depth_mm, offset_mm, negative):
    """Boss standing on a face parallel to the Top plane (index 1, faces at
    y = +-offset) or the Right plane (index 2, faces at x = +-offset).

    Sketch mapping measured on this SOLIDWORKS: Top plane (x, y) -> model
    (X, -Z), extrudes along +Y; Right plane (x, y) -> model (-Z, Y), extrudes
    along +X. `negative` flips both the start offset and the direction, which
    puts the boss on the -Y / -X face.
    """
    sm = start_sketch(model, plane_index)
    sketch(sm)
    feat = model.FeatureManager.FeatureExtrusion2(
        True, False, negative, 0, 0, depth_mm * MM, 0.0, False, False, False, False,
        0.0, 0.0, False, False, False, False, True, True, True, 3, offset_mm * MM, negative)
    model.SketchManager.AddToDB = False
    if feat is None:
        raise RuntimeError("side boss failed")
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
    (bz0, bz1), (bx, by), br = p["bay_z"], p["bay_half"], p["bay_corner_r"]
    model = sw.NewDocument(tpl, 0, 0, 0)
    print("  spine")

    sm = start_sketch(model)  # battery channel walls, up to the cap of the top tier
    polygon(sm, [(xb, -hy_out), (xf, -hy_out), (xf, -hy_in), (cx0, -hy_in),
                 (cx0, hy_in), (xf, hy_in), (xf, hy_out), (xb, hy_out)])
    extrude(model, channel_top - base)
    fillet(model, p["spine_corner_r"], vertical_at([(xb, hy_out), (xb, -hy_out)]), "channel back corners")

    sm = start_sketch(model)  # foot
    rect(sm, p["foot_x"][0], -p["foot_half_y"], p["foot_x"][1], p["foot_half_y"])
    for x, y in p["foot_holes"]:
        circle(sm, x, y, p["foot_hole"])
    extrude(model, p["foot_thk"])

    for _, z_top in tiers:  # floor above each cell tier
        sm = start_sketch(model)
        rect(sm, cx0 - 0.5, -hy_in - 0.5, cx1, hy_in + 0.5)
        extrude(model, p["floor_thk"], z_top + cap - base)

    sm = start_sketch(model)  # bay floor
    rounded_rect(sm, bx, by, br)
    extrude(model, w, bz0 - base)
    sm = start_sketch(model)  # bay walls
    rounded_rect(sm, bx, by, br)
    rounded_rect(sm, bx - w, by - w, br - w)
    extrude(model, bz1 - bz0 - 2 * w, bz0 + w - base)

    def on_channel(x, y):  # outer faces of the channel: back and both sides
        return ((near(abs(y), hy_out) and xb - TOL <= x <= xf + TOL)
                or (near(x, xb) and abs(y) <= hy_out + TOL))

    fillet(model, p["neck_fillet"], loop_at(bz0 - base, on_channel), "channel into bay floor")
    fillet(model, p["bay_bottom_fillet"], loop_at(bz0 - base, on_box(bx, by)), "bay bottom edge")

    # reopen the cell channel through the bay floor
    z0, z1 = tiers[-1][0] - p["cell_gap"], tiers[-1][1] + cap
    sm = start_sketch(model)
    rect(sm, cx0, -hy_in, bx + 5.0, hy_in)
    cut(model, z1 - z0, z0 - base)
    # let the side cover (as wide as the channel) pass through the bay floor
    cv = p["cover"]
    sm = start_sketch(model)
    rect(sm, xf, -hy_out - cv["floor_clear"], bx + 5.0, hy_out + cv["floor_clear"])
    cut(model, w + 1.5, bz0 - 1.0 - base)
    # one opening in the +X wall: cell access below, tracker access above
    wz0, wz1 = p["window_z"]
    sm = start_sketch(model)
    rect(sm, bx - w - 2.0, -p["window_half_y"], bx + 5.0, p["window_half_y"])
    cut(model, wz1 - wz0, wz0 - base)
    # cap screw holes down into the +Y / -Y wall tops
    cap = p["cap"]
    wall_top = bz1 - cap["thk"]
    sm = start_sketch(model)
    for y in (cap["screw_y"], -cap["screw_y"]):
        circle(sm, 0.0, y, cap["screw_hole"] - 0.4)  # pilot for a self-tapping screw
    cut(model, 8.0, wall_top - 8.0 - base)

    # mounting bosses: +Y and -Y faces (Top plane: sketch y = -(z - base)), -X face (Right plane: sketch x = -(z - base))
    bo = p["boss"]
    for negative in (False, True):
        def bosses_y(sm, negative=negative):
            for x in bo["y_face_x"]:
                for z in bo["rows_z"]:
                    circle(sm, x, -(z - base), bo["dia"])
                    circle(sm, x, -(z - base), bo["hole"])
        side_boss(model, 1, bosses_y, bo["height"], by, negative)
    def bosses_x(sm):
        for y in bo["x_face_y"]:
            for z in bo["rows_z"]:
                circle(sm, -(z - base), y, bo["dia"])
                circle(sm, -(z - base), y, bo["hole"])
    side_boss(model, 2, bosses_x, bo["height"], bx, True)

    # cover screw lugs on the outside of the channel walls (Right plane, extruded along +X)
    def lugs(sm):
        for z in cv["rows_z"]:
            for sign in (1, -1):
                y0, y1 = sorted((sign * (hy_out - 0.5), sign * (hy_out + cv["lug_out"])))
                rect(sm, -(z + cv["lug_tall"] / 2 - base), y0, -(z - cv["lug_tall"] / 2 - base), y1)
                circle(sm, -(z - base), sign * (hy_out + cv["lug_out"] / 2), cv["pilot"])
    side_boss(model, 2, lugs, cv["lug_len"], xf - cv["lug_len"], False)

    # bracket for the side-mounted 920 MHz antenna on the -Y face, with a vertical hole for the SMA jack
    a9 = p["ant_920"]
    mz0, mz1 = a9["mount"]["z"]
    mx, mh = a9["pos"][0], a9["mount"]["half_x"]
    side_boss(model, 1, lambda sm: rect(sm, mx - mh, -(mz0 - base), mx + mh, -(mz1 - base)),
              a9["mount"]["out"], by, True)
    sm = start_sketch(model)
    circle(sm, *a9["pos"], a9["mount"]["hole"])
    cut(model, mz1 - mz0 + 2.0, mz0 - 1.0 - base)

    # zip-tie posts on the +Y and -Y faces
    cl = p["clip"]
    for negative in (False, True):
        def posts(sm):
            for z in cl["rows_z"]:
                for x0 in (cl["x"] - cl["gap"] / 2 - cl["post"], cl["x"] + cl["gap"] / 2):
                    rect(sm, x0, -(z - base), x0 + cl["post"], -(z + cl["tall"] - base))
        side_boss(model, 1, posts, cl["out"], by, negative)

    set_color(model, "spine")
    save(model, path)
    return model


def build_cap(sw, tpl, path, p):
    """Removable top cap: lip (z 0..lip) that sits inside the bay walls, then
    the plate with antenna and screw holes; top edge filleted."""
    (bx, by), br, w, cap = p["bay_half"], p["bay_corner_r"], p["bay_wall"], p["cap"]
    c = w + cap["lip_clear"]
    model = sw.NewDocument(tpl, 0, 0, 0)
    sm = start_sketch(model)  # lip
    rounded_rect(sm, bx - c, by - c, br - c)
    extrude(model, cap["lip"])
    sm = start_sketch(model)  # plate
    rounded_rect(sm, bx, by, br)
    for y in (cap["screw_y"], -cap["screw_y"]):
        circle(sm, 0.0, y, cap["screw_hole"])
    for key in ("ant_433", "ant_tracker"):  # the 920 MHz antenna is on the -Y face
        circle(sm, *p[key]["pos"], cap["ant_hole"])
    extrude(model, cap["thk"], cap["lip"])
    print("  cap")
    fillet(model, p["bay_top_fillet"], loop_at(cap["lip"] + cap["thk"], on_box(bx, by)), "cap top edge")
    set_color(model, "spine")
    save(model, path)
    return model


def cover_span(p, tiers):
    """Stations of the side cover: just above the foot to the top of the channel."""
    z0 = p["bulkhead_thk"] + p["foot_thk"] + p["cover"]["end_gap"]
    z1 = tiers[-1][1] + p["cell_gap"] + 1.0 + p["floor_thk"] - p["cover"]["end_gap"]
    return z0, z1


def build_cover(sw, tpl, path, p, tiers):
    """Side cover of the battery channel, modelled in assembly coordinates
    (stations from the nose cone base): a plate on the open face with an ear
    and a screw hole at each lug, a notch at the bottom for the backup pack
    leads and a window above the middle floor for the main pack leads."""
    s, cv = spine_dims(p), p["cover"]
    hw, he = s["half_y"], s["half_y"] + cv["lug_out"]
    z0, z1 = cover_span(p, tiers)
    t2 = cv["lug_tall"] / 2
    right = [(hw, z0)]
    for z in cv["rows_z"]:
        right += [(hw, z - t2), (he, z - t2), (he, z + t2), (hw, z + t2)]
    right.append((hw, z1))
    left = [(-y, z) for y, z in reversed(right)]
    wh, wt = cv["wire_half"], cv["wire_tall"]
    outline = right + left + [(-wh, z0), (-wh, z0 + wt), (wh, z0 + wt), (wh, z0)]
    main_z = tiers[-1][0] - p["cell_gap"]  # bottom of the main pack's contact space
    model = sw.NewDocument(tpl, 0, 0, 0)

    def sketch(sm):  # Right plane: sketch (x, y) -> model (-Z, Y)
        polygon(sm, [(-z, y) for y, z in outline])
        rect(sm, -(main_z + wt), -wh, -main_z, wh)
        for z in cv["rows_z"]:
            for sign in (1, -1):
                circle(sm, -z, sign * (hw + cv["lug_out"] / 2), cv["screw_hole"])
    side_boss(model, 2, sketch, cv["thk"], s["x_front"], False)
    print("  cell_cover")
    set_color(model, "cover")
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

    names = ["bulkhead.SLDPRT", "pcb_outline.SLDPRT", "spacer_m3_10.SLDPRT", "spacer_m3_stack.SLDPRT",
             "rod_m3.SLDPRT", "nut_m3.SLDPRT", "stack_connector_2x20.SLDPRT", "stack_connector_2x10.SLDPRT",
             "spine.SLDPRT",
             "cell_18650.SLDPRT", "ant_433.SLDPRT", "ant_920.SLDPRT", "ant_tracker.SLDPRT",
             "sma_base.SLDPRT", "gnss_patch.SLDPRT", "tracker.SLDPRT", "cap.SLDPRT", "gps_board.SLDPRT",
             "cell_cover.SLDPRT", "assembly.SLDASM", "view_iso.png", "view_antenna_side.png",
             "view_open_side.png", "view_side.png"]
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
    sp15 = build_disc(sw, part_tpl, f("spacer_m3_stack.SLDPRT"), p["spacer_od"], p["spacer_len"],
                      [hole(p["rod_hole"])], "spacer")
    rod = build_disc(sw, part_tpl, f("rod_m3.SLDPRT"), p["rod_dia"], rod_len, [], "steel")
    nut = build_disc(sw, part_tpl, f("nut_m3.SLDPRT"), p["nut_dia"], p["nut_thk"], [hole(p["rod_hole"])], "steel")
    conn = build_block(sw, part_tpl, f("stack_connector_2x20.SLDPRT"), p["conn_main"][0], p["conn_main"][1],
                       p["spacer_len"], "conn")
    conn_b = build_block(sw, part_tpl, f("stack_connector_2x10.SLDPRT"), p["conn_backup"][0], p["conn_backup"][1],
                         p["spacer_len"], "conn")
    spine = build_spine(sw, part_tpl, f("spine.SLDPRT"), p, tiers)
    cell = build_disc(sw, part_tpl, f("cell_18650.SLDPRT"), p["cell_dia"], p["cell_len"], [], "cell")
    cover = build_cover(sw, part_tpl, f("cell_cover.SLDPRT"), p, tiers)
    a433, a920, atrk = p["ant_433"], p["ant_920"], p["ant_tracker"]
    sma, patch, trk = p["sma_base"], p["gnss_patch"], p["tracker"]
    whip433 = build_disc(sw, part_tpl, f("ant_433.SLDPRT"), a433["dia"], a433["len"], [], "conn")
    whip920 = build_disc(sw, part_tpl, f("ant_920.SLDPRT"), a920["dia"], a920["len"], [], "conn")
    sma_base = build_disc(sw, part_tpl, f("sma_base.SLDPRT"), sma["dia"], sma["len"], [], "spacer")
    gnss_patch = build_block(sw, part_tpl, f("gnss_patch.SLDPRT"), patch["size"][0], patch["size"][1], patch["thk"], "conn")
    whip_trk = build_disc(sw, part_tpl, f("ant_tracker.SLDPRT"), atrk["dia"], atrk["len"], [], "conn")
    tracker = build_block(sw, part_tpl, f("tracker.SLDPRT"), trk["size"][0], trk["size"][1], trk["size"][2], "conn")
    cap_part = build_cap(sw, part_tpl, f("cap.SLDPRT"), p)
    gb = p["gps_board"]
    gps_board = build_block(sw, part_tpl, f("gps_board.SLDPRT"), gb["size"][0], gb["size"][1], gb["size"][2], "pcb")

    for label, model in (("bulkhead", bulkhead), ("pcb_outline", pcb), ("spacer_m3_10", sp10),
                         ("spacer_m3_stack", sp15), ("rod_m3", rod), ("nut_m3", nut),
                         ("stack_connector_2x20", conn), ("stack_connector_2x10", conn_b), ("spine", spine), ("cell_18650", cell),
                         ("ant_433", whip433), ("ant_920", whip920), ("sma_base", sma_base),
                         ("ant_tracker", whip_trk), ("gnss_patch", gnss_patch), ("tracker", tracker),
                         ("cap", cap_part), ("gps_board", gps_board), ("cell_cover", cover)):
        print(f"  {label:16s} box [xmin ymin zmin xmax ymax zmax] mm = {box_mm(model)}")
    sb = box_mm(spine)
    if sb[2] < -0.01 or abs(sb[5] - (p["bay_z"][1] - p["cap"]["thk"] - base)) > 0.01:
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
                comps.append((f"spacer_above_{i}", place(sw, asm, f("spacer_m3_stack.SLDPRT"), z + p["pcb_thk"], x, y)))
            for part, y in (("stack_connector_2x20.SLDPRT", cy), ("stack_connector_2x10.SLDPRT", -cy)):
                comps.append((f"connector_above_{i}", place(sw, asm, f(part), z + p["pcb_thk"], cx, y)))
    cell_x = p["cell_dia"] / 2 + 0.75
    for i, (z0, _) in enumerate(tiers, start=1):
        for x in (cell_x, -cell_x):
            comps.append((f"cell_tier_{i}", place(sw, asm, f("cell_18650.SLDPRT"), z0, x, 0.0)))
    comps.append(("cell_cover", place(sw, asm, f("cell_cover.SLDPRT"), 0.0)))
    top2 = p["bay_z"][1]
    comps.append(("cap", place(sw, asm, f("cap.SLDPRT"), top2 - p["cap"]["thk"] - p["cap"]["lip"])))
    comps.append(("gps_board", place(sw, asm, f("gps_board.SLDPRT"), gb["z"],
                                     -p["bay_half"][0] - p["boss"]["height"] - gb["size"][0] / 2, 0.0)))
    for key, part in (("ant_433", "ant_433.SLDPRT"), ("ant_tracker", "ant_tracker.SLDPRT")):
        x, y = p[key]["pos"]
        comps.append((key + "_sma", place(sw, asm, f("sma_base.SLDPRT"), top2, x, y)))
        comps.append((key, place(sw, asm, f(part), top2 + sma["len"], x, y)))
    z_sma = a920["mount"]["z"][0] - sma["len"]  # side antenna hangs below its bracket
    comps.append(("ant_920_sma", place(sw, asm, f("sma_base.SLDPRT"), z_sma, *a920["pos"])))
    comps.append(("ant_920", place(sw, asm, f("ant_920.SLDPRT"), z_sma - a920["len"], *a920["pos"])))
    comps.append(("gnss_patch", place(sw, asm, f("gnss_patch.SLDPRT"), top2, *patch["pos"])))
    comps.append(("tracker", place(sw, asm, f("tracker.SLDPRT"), trk["z"])))
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
            ("bay corner, bottom", reach(*p["bay_half"], p["bay_corner_r"]), p["bay_z"][0]),
            ("bay corner, top", reach(*p["bay_half"], p["bay_corner_r"]), top2),
            ("433 whip tip", math.hypot(*a433["pos"]) + a433["dia"] / 2, top2 + sma["len"] + a433["len"]),
            ("920 bracket, top", math.hypot(abs(a920["pos"][0]) + a920["mount"]["half_x"],
                                            p["bay_half"][1] + a920["mount"]["out"]), a920["mount"]["z"][1]),
            ("920 SMA jack", math.hypot(*a920["pos"]) + sma["dia"] / 2, a920["mount"]["z"][0]),
            ("tracker whip tip", math.hypot(*atrk["pos"]) + atrk["dia"] / 2, top2 + sma["len"] + atrk["len"]),
            ("zip-tie post, top row", math.hypot(p["clip"]["x"] + p["clip"]["gap"] / 2 + p["clip"]["post"],
                                                 p["bay_half"][1] + p["clip"]["out"]), p["clip"]["rows_z"][-1] + p["clip"]["tall"]),
            ("GPS board outer edge", math.hypot(p["bay_half"][0] + p["boss"]["height"] + gb["size"][0], gb["size"][1] / 2),
             gb["z"] + gb["size"][2])):
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
    snapshot(asm, f("view_antenna_side.png"), "*Bottom", 6)  # the -Y face with the 920 MHz antenna
    asm.ShowNamedView2("*Isometric", 7)
    noarg(asm, "ViewZoomtofit2")

    cz0, cz1 = cover_span(p, tiers)
    print(f"side cover: x {s['x_front']:.1f}..{s['x_front'] + p['cover']['thk']:.1f}, z {cz0:.1f}..{cz1:.1f}, "
          f"lug rows {p['cover']['rows_z']}")
    print(f"board slot: width {2 * slot_half:.1f}, from x = {s['x_back'] - p['slot_clear']:.1f}")
    print("total components:", len(comps))
    print("cell tiers (z):", [(round(a, 1), round(b, 1)) for a, b in tiers])
    print("written to", out)


if __name__ == "__main__":
    sys.exit(main())
