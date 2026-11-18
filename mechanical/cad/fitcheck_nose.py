"""Place the avionics bay assembly inside the real nose cone and check the fit.

Builds a separate assembly (fitcheck_<avbay>_in_<nose>.SLDASM) holding the
avionics bay assembly and the nose cone part, runs the SOLIDWORKS
interference check, and prints the radial clearance of the main envelope
points against the nose cone's actual inner surface (from its tessellation).

Usage:  python mechanical/cad/fitcheck_nose.py [--nose NOSE_v1.SLDPRT] [--avbay avbay_v0_5_assembly.SLDASM]

Assumes the nose cone part is modelled along +X with its tip at x = 0 and
its open end at x = length (as NOSE_v1 is); it is rotated so that the open
end lands on the assembly's z = 0 plane and the tip points toward +Z.
Requires a running SOLIDWORKS with no documents open.
"""

from __future__ import annotations

import argparse
import math
import os
import sys

import pythoncom
import win32com.client
from win32com.client import VARIANT

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_avbay as b  # noqa: E402

MM = b.MM
noarg = b.noarg


def inner_profile(nose, length_mm, step=5.0):
    """Smallest inner radius seen in each `step` mm band of station z."""
    bins = {}
    for body in nose.GetBodies2(0, False):
        for face in body.GetFaces():
            fb = [v / MM for v in noarg(face, "GetBox")]
            if max(abs(fb[1]), abs(fb[4])) > 70.5 or noarg(noarg(face, "GetSurface"), "IsPlane"):
                continue  # outer skin and the flat end faces
            tri = face.GetTessTriangles(True)
            for i in range(0, len(tri), 3):
                z = length_mm - tri[i] / MM
                r = math.hypot(tri[i + 1], tri[i + 2]) / MM
                k = int(z // step)
                bins[k] = min(bins.get(k, 1e9), r)

    def radius(z):
        """Conservative inner radius at station z: the smallest value among the
        nearest sampled bands on either side (the tessellation is coarse, so some
        bands hold no vertices)."""
        k = int(z // step)
        below = next((bins[j] for j in range(k, k - 8, -1) if j in bins), None)
        above = next((bins[j] for j in range(k + 1, k + 9) if j in bins), None)
        vals = [v for v in (below, above) if v is not None]
        return min(vals) if vals else float("nan")

    return radius, max(bins) * step


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nose", default=os.path.join(here, "NOSE_v1.SLDPRT"))
    ap.add_argument("--avbay", default=os.path.join(here, b.PREFIX + "assembly.SLDASM"))
    args = ap.parse_args()
    nose_path, avbay_path = os.path.abspath(args.nose), os.path.abspath(args.avbay)
    stem = f"fitcheck_{os.path.splitext(os.path.basename(avbay_path))[0]}_in_{os.path.splitext(os.path.basename(nose_path))[0]}"
    out = os.path.join(here, stem + ".SLDASM")

    sw = win32com.client.Dispatch("SldWorks.Application")
    sw.Visible = True
    if noarg(sw, "GetDocumentCount") != 0:
        raise SystemExit("close all SOLIDWORKS documents before running this script")

    nose = sw.OpenDoc(nose_path, 1)
    if nose is None:
        raise SystemExit(f"could not open {nose_path}")
    length = nose.GetPartBox(True)[3] / MM
    radius, z_tip = inner_profile(nose, length)
    print(f"nose: length {length:.1f} mm, inner tip at z = {z_tip:.0f} mm")

    avbay_doc = sw.OpenDoc(avbay_path, 2)  # an assembly must be loaded before it can be inserted
    if avbay_doc is None:
        raise SystemExit(f"could not open {avbay_path}")
    avbay_front = b.ref_planes(avbay_doc)[0].Name  # names differ with the SOLIDWORKS language
    avbay_axis, feat = None, noarg(avbay_doc, "FirstFeature")
    while feat is not None:
        if noarg(feat, "GetTypeName2") == "RefAxis":
            avbay_axis = feat.Name
        feat = noarg(feat, "GetNextFeature")
    if avbay_axis is None:
        raise SystemExit("the avbay assembly has no reference axis; rebuild it with build_avbay.py")
    lock_parts = [os.path.join(here, b.PREFIX + name + ".SLDPRT")
                  for name in ("nose_lock", "nose_lock_key", "nose_gasket", "nose_centering_ring")]
    for path in lock_parts:  # a document must be loaded before it can be inserted
        if sw.OpenDoc(path, 1) is None:
            raise SystemExit(f"could not open {path}")
    if os.path.exists(out):
        os.remove(out)
    asm = sw.NewDocument(b.find_template("assembly 0251mm to 1000mm.asmdot"), 0, 0, 0)
    mu = noarg(sw, "GetMathUtility")
    mu._FlagAsMethod("CreateTransform")

    def add(path, matrix, fixed=True):
        comp = asm.AddComponent5(path, 0, "", False, "", 0.0, 0.0, 0.0)
        if comp is None:
            raise RuntimeError(f"could not insert {path}")
        comp.Select2(False, 0)
        noarg(asm, "UnfixComponent")
        comp.Transform2 = mu.CreateTransform(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, matrix))
        if fixed:
            comp.Select2(False, 0)
            noarg(asm, "FixComponent")
        asm.ClearSelection2(True)
        return comp

    off = b.nose_lock_offset(b.PARAMS)  # the bulkhead sits above the twist-lock lugs
    # the avbay is left floating and held by two mates, so it can be dragged in and out and turned
    avbay_comp = add(avbay_path, [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, off * MM, 1, 0, 0, 0], fixed=False)
    for path in lock_parts:  # built in nose cone coordinates
        add(path, [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0])
    # part +X (tip -> open end) maps to assembly -Z: open end on z = 0, tip at z = length
    nose_comp = add(nose_path, [0, 0, -1, 0, 1, 0, 1, 0, 0, 0, 0, length * MM, 1, 0, 0, 0])
    try:
        nose_comp.MaterialPropertyValues = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.55, 0.7, 0.95, 1, 1, 0.3, 0.3, 0.75, 0])
    except Exception as exc:  # appearance only
        print("  note: could not make the nose cone transparent:", exc)
    noarg(asm, "EditRebuild3")

    # one mate: avbay axis coincident with the nose cone axis, so the avbay can only slide along
    # the axis and turn about it. A limit distance mate (to stop it at the locked station) could
    # not be created through AddMate5 on SOLIDWORKS 2018 - it comes out as a fixed distance - so
    # add it by hand if wanted; see mechanical/cad/README.md.
    travel = 460.0
    p_ = b.PARAMS
    asm_axis = b.add_axis(asm)
    asm._FlagAsMethod("AddMate5")

    def feature(model, name):
        feat = noarg(model, "FirstFeature")
        while feat is not None:
            if feat.Name == name:
                return feat
            feat = noarg(feat, "GetNextFeature")
        raise RuntimeError(f"no feature named {name}")

    def mate(kind, first, second, dist=0.0, upper=0.0, lower=0.0):
        asm.ClearSelection2(True)
        first.Select2(False, 1)
        second.Select2(True, 1)
        err = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        made = asm.AddMate5(kind, 2, False, dist, upper, lower, 1.0, 1.0, 0.0, 0.0, 0.0, False, False, 0, err)
        asm.ClearSelection2(True)
        if made is None:
            raise RuntimeError(f"mate type {kind} failed (status {err.value})")
        return made

    mate(0, feature(asm, asm_axis), avbay_comp.FeatureByName(avbay_axis))  # swMateCOINCIDENT

    def pose(z_mm, deg):  # avbay transform: turned `deg` about Z, bulkhead bottom at station z_mm
        c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        return [c, s_, 0, -s_, c, 0, 0, 0, 1, 0, 0, z_mm * MM, 1, 0, 0, 0]

    def holds(z_mm, deg):
        """Put the avbay in a pose and rebuild; True if the mates leave it there."""
        want = pose(z_mm, deg)
        avbay_comp.Transform2 = mu.CreateTransform(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, want))
        noarg(asm, "EditRebuild3")
        got = avbay_comp.Transform2.ArrayData
        return max(abs(got[i] - want[i]) for i in range(12)) < 1e-6

    tab, lug = p_["bulkhead_tab"]["span"], p_["nose_lock"]["lug_span"]
    turn = (lug[1] + (360.0 / p_["bulkhead_tab"]["count"] + lug[0] - lug[1]) / 2) - (tab[0] + tab[1]) / 2
    checks = {
        "locked": holds(off, 0.0),
        "turned to the insertion angle": holds(off, turn),
        "pulled out 200 mm": holds(off - 200.0, turn),
        "pulled out all the way": holds(off - travel, turn),
    }
    sideways = pose(off, 0.0)
    sideways[9] = 10.0 * MM  # 10 mm off the axis: the mate must pull it back
    avbay_comp.Transform2 = mu.CreateTransform(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, sideways))
    noarg(asm, "EditRebuild3")
    on_axis = abs(avbay_comp.Transform2.ArrayData[9]) < 1e-6
    if not holds(off, 0.0):
        raise RuntimeError("could not return the avbay to the locked position")
    print(f"mate: avbay axis coincident with the nose cone axis; insertion angle {turn:.1f} deg")
    for label, ok in checks.items():
        print(f"  pose allowed - {label}: {ok}")
    print(f"  moved 10 mm off the axis, the mate pulls it back: {on_axis}")
    if not all(checks.values()):
        raise RuntimeError("a pose that should be reachable is not allowed by the mates")

    mgr = asm.InterferenceDetectionManager
    mgr.TreatCoincidenceAsInterference = False
    mgr.TreatSubAssembliesAsComponents = False
    for method in ("GetInterferences", "GetInterferenceCount", "Done"):
        mgr._FlagAsMethod(method)
    found = mgr.GetInterferences()
    print("interference check:", mgr.GetInterferenceCount(), "interfering pair(s)")
    for item in (found or []):
        print("  ", [noarg(c, "Name2") for c in item.Components], f"volume {item.Volume * 1e9:.1f} mm^3")
    mgr.Done()

    p = b.PARAMS
    base = p["bulkhead_thk"]
    top_board = base + p["spacer_base_len"] + (p["pcb_count"] - 1) * (p["pcb_thk"] + p["spacer_len"]) + p["pcb_thk"]
    top2, sma = p["bay_z"][1], p["sma_base"]["len"]
    reach = lambda hx, hy, r: math.hypot(hx - r, hy - r) + r  # noqa: E731
    whip = lambda key: (math.hypot(*p[key]["pos"]) + p[key]["dia"] / 2, top2 + sma + p[key]["len"])  # noqa: E731
    points = [
        ("bulkhead tab edge", p["bulkhead_tab"]["r"], base),
        ("top board edge", p["pcb_dia"] / 2, top_board),
        ("bay corner, bottom", reach(*p["bay_half"], p["bay_corner_r"]), p["bay_z"][0]),
        ("bay corner, top", reach(*p["bay_half"], p["bay_corner_r"]), top2),
        ("433 whip tip", *whip("ant_433")),
        ("920 bracket, top", math.hypot(abs(p["ant_920"]["pos"][0]) + p["ant_920"]["mount"]["half_x"],
                                        p["bay_half"][1] + p["ant_920"]["mount"]["out"]), p["ant_920"]["mount"]["z"][1]),
        ("920 SMA jack", math.hypot(*p["ant_920"]["pos"]) + p["sma_base"]["dia"] / 2, p["ant_920"]["mount"]["z"][0]),
        ("tracker whip tip", *whip("ant_tracker")),
        ("zip-tie post, top row", math.hypot(p["clip"]["x"] + p["clip"]["gap"] / 2 + p["clip"]["post"],
                                             p["bay_half"][1] + p["clip"]["out"]), p["clip"]["rows_z"][-1] + p["clip"]["tall"]),
        ("GPS board outer edge", math.hypot(p["bay_half"][0] + p["boss"]["height"] + p["gps_board"]["size"][0],
                                            p["gps_board"]["size"][1] / 2), p["gps_board"]["z"] + p["gps_board"]["size"][2]),
    ]
    al, ab, asw = p["altimeter"], p["alt_batt"], p["alt_switch"]
    x_back = b.spine_dims(p)["x_back"]
    cover_out = -x_back + ab["depth"] + ab["cover_thk"]  # outer face of the battery retainer plate
    cover_top = ab["z"] + ab["size"][2] + ab["top_clear"] + ab["roof"]
    points += [
        ("altimeter outer edge", math.hypot(p["bay_half"][0] + p["boss"]["height"] + al["size"][0], al["size"][1] / 2),
         al["z"] + al["size"][2]),
        ("alt battery cover", math.hypot(cover_out, ab["size"][1] / 2 + ab["side_clear"] + ab["wall"]), cover_top),
        ("alt switch", math.hypot(cover_out + asw["size"][0], asw["size"][1] / 2), cover_top),
        ("recovery antenna tip", math.hypot(abs(p["ant_recovery"]["pos"][0]) + p["ant_recovery"]["whip"][0] / 2,
                                            p["bay_half"][1] + p["ant_recovery"]["pad"][1] + p["ant_recovery"]["sma"][1]
                                            + p["ant_recovery"]["whip"][1]),
         p["ant_recovery"]["pos"][1] + p["ant_recovery"]["whip"][0] / 2),
    ]
    nl = p["nose_lock"]
    points = [(label, r, z + off) for label, r, z in points]  # avbay stations -> nose cone stations
    points.append(("centering ring", nl["ring_r"][1], off + nl["ring_z"] + nl["ring_thk"]))
    print(f"avbay is raised {off:.1f} mm above the nose cone open end by the twist-lock lugs")
    def interp(z):  # linear interpolation of the measured profile copied into build_avbay.py
        prof = p["nose_profile"]
        for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
            if z0 <= z <= z1:
                return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return 0.0

    # "worst" uses the smallest radius of the neighbouring sampled bands (the bands are up to
    # 20 mm apart, so it can be far too pessimistic); "interp" interpolates between them
    print("radial clearance against the nose cone inner surface (mm):")
    for label, r, z in points:
        print(f"  {label:22s} z={z:6.1f}  part r={r:5.1f}  clearance: worst={radius(z) - r:6.1f}  interp={interp(z) - r:6.1f}")
    print(f"free length above the highest part to the inner tip: about {z_tip - max(z for _, _, z in points):.0f} mm")

    err = asm.SaveAs3(out, 0, 1)
    if err:
        raise RuntimeError(f"SaveAs3 failed ({err})")
    for name, view, vid in (("iso", "*Isometric", 7), ("side", "*Top", 5)):
        asm.ShowNamedView2(view, vid)
        noarg(asm, "ViewZoomtofit2")
        asm.SaveAs3(os.path.join(here, f"{stem}_{name}.png"), 0, 1)
    asm.ShowNamedView2("*Isometric", 7)
    noarg(asm, "ViewZoomtofit2")
    print("written:", out)


if __name__ == "__main__":
    sys.exit(main())
