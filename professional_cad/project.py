"""Build a coordinated drawing package without MCP or proprietary CAD."""

import csv
import json
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from tempfile import TemporaryDirectory

from ezdxf.render import MeshBuilder

from .cad import API
from .geometry import draw_box, front, merged_chain, project_iso, section
from .model import Project, components

SCALES = (5, 10, 12, 15, 20, 25, 30, 35, 40, 50, 60, 75, 100, 125)


def scale(width, height, paper_w, paper_h):
    required = max(width / paper_w, height / paper_h)
    return next((s for s in SCALES if s >= required), SCALES[-1])


def room_plan(v, project):
    v.rect(0, 0, project.width, project.depth, "CUT")
    v.faced(0, -100, project.width, 100, "CUT", "ANSI31", v.s * 1.65)
    v.faced(-100, 0, 100, project.depth, "CUT", "ANSI31", v.s * 1.65)
    v.faced(project.width, 0, 100, project.depth, "CUT", "ANSI31", v.s * 1.65)


def service_plan(v, items):
    for item in items:
        x, y, s = item.x, item.y, v.s
        layer = {"power": "POWER", "light": "POWER", "water": "WATER", "waste": "WASTE"}[item.kind]
        if item.kind == "power":
            v.rect(x - 1.2 * s, y - 0.75 * s, 2.4 * s, 1.5 * s, layer)
        else:
            v.circ(x, y, 1.4 * s, layer)
        v.line((x - s, y), (x + s, y), layer)
        v.label(item.id, x + 2 * s, y + s, 1.95)


def layout_package(project, parts):
    api = API()
    a = api.sheet("J101", "DIMENSIONED PLAN AND FRONT ELEVATION")
    s = max(
        scale(project.width + 650, project.ceiling + 485, 310, 151),
        scale(project.width + 650, project.depth + 310, 310, 53),
    )
    x0 = -8 * s
    p = api.view(a, 15, 209, 319, 62, s, "GENERAL PLAN", (x0, -9 * s))
    p.flip_plan()
    room_plan(p, project)
    cut = max(
        150,
        min(
            project.ceiling - 1,
            min((c.z + c.height * 0.42 for c in project.cabinets if c.z < 500), default=500),
        ),
    )
    section(p, parts, (0, 1), 2, cut)
    service_plan(p, project.services)
    p.dim((0, 0), (project.width, 0), (0, -6.5 * s))
    if project.depth / s > 7:
        p.dim((0, 0), (0, project.depth), (-5.5 * s, 0), 90)
    f = api.view(a, 15, 29, 319, 163, s, "FRONT ELEVATION", (x0, -8 * s))
    f.rect(0, 0, project.width, project.ceiling, "CUT")
    front(f, parts)
    low = [c for c in project.cabinets if c.z < 500]
    stations = [n for c in low for n in (c.x, c.x + c.width)]
    for begin, end in merged_chain(stations):
        if end - begin >= 5 * s:
            f.dim((begin, 0), (end, 0), (0, -3.5 * s))
    f.dim((0, 0), (project.width, 0), (0, -6.7 * s))
    f.dim((project.width, 0), (project.width, project.ceiling), (project.width + 4 * s, 0), 90)
    for c in low:
        f.label(c.id, c.x + min(c.width / 5, 3 * s), c.z + c.height + 1.8 * s, 1.95)
    if project.cabinets:
        focus = next((c for c in low if c.kind != "appliance"), project.cabinets[0])
        f.ref(focus.x + focus.width * 0.48, focus.z + focus.height * 0.42, "A", "J102")
        p.ref(
            focus.x + focus.width * 0.48,
            min(project.depth - 3.7 * s, focus.y + focus.depth + 5 * s),
            "A",
            "J102",
        )
        a = api.sheet("J102", "INTERNAL ELEVATION AND COMPONENT SECTIONS")
        i = api.view(
            a,
            15,
            151,
            319,
            119,
            scale(project.width + 560, project.ceiling + 360, 310, 119),
            "DOORS REMOVED",
            (-180, -85),
        )
        i.rect(0, 0, project.width, project.ceiling, "CUT")
        front(i, parts, internal=True)
        for c in project.cabinets:
            i.label(c.id, c.x + c.width * 0.26, c.z + c.height * 0.32, 1.95)
        i.dim((0, 0), (project.width, 0), (0, -55))
        focus_parts = [p for p in parts if p.assembly == focus.id]
        s2 = scale(focus.depth + 280, focus.height + focus.z + 300, 95, 107)
        sv = api.view(a, 15, 24, 96, 108, s2, "A. BODY SECTION", (focus.y - 115, -11 * s2))
        station = focus.x + focus.width * 0.48
        section(sv, focus_parts, (1, 2), 0, station)
        sv.line((focus.y - 90, 0), (focus.y + focus.depth + 70, 0), "CUT")
        sv.dim((focus.y, focus.z), (focus.y + focus.depth, focus.z), (0, -7 * s2))
        sv.dim(
            (focus.y + focus.depth, focus.z),
            (focus.y + focus.depth, focus.z + focus.height),
            (focus.y + focus.depth + 5 * s2, 0),
            90,
        )
        sv.ref(focus.y + focus.depth * 0.53, focus.z + focus.height * 0.45, "D1", "J102")
        dt = api.view(
            a, 121, 24, 99, 108, 5, "D1. SIDE / BACK JUNCTION", (focus.x - 55, focus.y - 55)
        )
        section(dt, focus_parts, (0, 1), 2, focus.z + focus.height * 0.41)
        dt.dim((focus.x, focus.y), (focus.x + focus.board, focus.y), (0, focus.y - 25))
        dt.tag(focus.body_material, focus.x + focus.board + 28, focus.y + focus.depth * 0.40)
        sx = scale(
            focus.width + focus.depth * 0.75 + 310,
            focus.height + focus.z + focus.width * 0.4 + focus.depth * 0.6 + 300,
            100,
            105,
        )
        iso = api.view(a, 230, 24, 104, 108, sx, "ASSEMBLY AXON", (-110, -0.61 * focus.depth - 40))
        project_iso(
            iso, [replace(part, x=part.x - focus.x, y=part.y - focus.y) for part in focus_parts]
        )
    a = api.sheet("G001", "DRAWING REGISTER AND SCHEDULES")
    rows = [(c.id, c.kind, c.x, c.y, c.z, c.width, c.depth, c.height) for c in project.cabinets]
    if rows:
        for start in range(0, len(rows), 22):
            if start:
                a = api.sheet(f"G{start // 22 + 1:03d}", "CABINET SCHEDULE CONTINUED")
            api.table(
                a,
                "CABINET SET-OUT / MM",
                ["ID", "TYPE", "X", "Y", "Z", "W", "D", "H"],
                rows[start : start + 22],
                15,
                257,
                [0, 29, 86, 115, 144, 173, 202, 231, 304],
                6.4,
            )
    api.notes(
        a,
        15,
        100,
        "RELEASE CONTROLS",
        [
            "PROVISIONAL BODY AND HARDWARE SYSTEMS.",
            "APPROVE SHOP SAMPLES, FIXINGS AND SITE SET-OUT BEFORE MANUFACTURE.",
            "NATIVE COMPONENT GEOMETRY AND SCHEDULES SHARE THE SAME DIMENSIONS.",
        ],
        5,
    )
    if project.services:
        a = api.sheet("M101", "SERVICES SET-OUT")
        s = scale(project.width + 700, project.depth + 550, 312, 159)
        p = api.view(a, 14, 96, 320, 171, s, "SERVICES PLAN", (-8 * s, -9 * s))
        p.flip_plan()
        room_plan(p, project)
        for part in parts:
            if part.role.startswith(("side", "plinth")):
                draw_box(p, part, (0, 1), "BACKGROUND")
        service_plan(p, project.services)
        p.dim((0, 0), (project.width, 0), (0, -6 * s))
        service_rows = [(q.id, q.kind, q.x, q.y, q.z) for q in project.services]
        api.table(
            a,
            "SERVICE STATIONS / MM",
            ["ID", "SYSTEM", "X", "Y", "Z"],
            service_rows[:10],
            15,
            80,
            [0, 37, 100, 155, 210, 310],
            5.6,
        )
        for start in range(10, len(service_rows), 24):
            a = api.sheet(f"M{102 + (start - 10) // 24:03d}", "SERVICE STATIONS CONTINUED")
            api.table(
                a,
                "SERVICE STATIONS / MM",
                ["ID", "SYSTEM", "X", "Y", "Z"],
                service_rows[start : start + 24],
                15,
                254,
                [0, 37, 100, 155, 210, 310],
                6,
            )
    api.d.appids.new("PROCAD")
    assembly = api.d.blocks.new("PROCAD-COMPONENT-ASSEMBLY")
    for part in parts:
        if part.role == "opening":
            continue
        x, y, z = part.x, part.y, part.z
        X, Y, Z = x + part.w, y + part.d, z + part.h
        builder = MeshBuilder()
        builder.add_mesh(
            vertices=[
                (x, y, z),
                (X, y, z),
                (X, Y, z),
                (x, Y, z),
                (x, y, Z),
                (X, y, Z),
                (X, Y, Z),
                (x, Y, Z),
            ],
            faces=[
                (3, 2, 1, 0),
                (4, 5, 6, 7),
                (0, 1, 5, 4),
                (1, 2, 6, 5),
                (2, 3, 7, 6),
                (3, 0, 4, 7),
            ],
        )
        entity = builder.render_mesh(assembly, dxfattribs={"layer": "COMPONENTS-3D"})
        entity.set_xdata("PROCAD", [(1000, part.id), (1000, part.material), (1000, part.status)])
    if len(assembly):
        api.d.modelspace().add_blockref(
            assembly.name, (-40000, -40000, 0), dxfattribs={"layer": "COMPONENTS-3D"}
        )
    return api


def generate(spec: Project, destination: Path, proof=True):
    """Build into a sibling staging directory and publish only after successful validation."""
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    parts = [part for cabinet in spec.cabinets for part in components(cabinet)]
    api = layout_package(spec, parts)
    rail = {
        "FINISHES": [
            "ML01  CARCASS / SHELVES",
            "DF01  FRONT / APPROVE SAMPLE",
            "BK01  REAR PANEL",
            "KP01  REMOVABLE PLINTH",
        ],
        "FITTINGS": ["HG01  HINGE / VERIFY", "HD01  HANDLES / VERIFY", "FX01  FIXINGS / VERIFY"],
        "APPLIANCES": ["VERIFY PRODUCT ENVELOPES"],
        "NOTES": ["X/Y FROM FINISHED WALLS", "Z FROM FINISHED FLOOR", *spec.notes],
    }
    with TemporaryDirectory(prefix=".cad-stage-", dir=destination.parent) as temp:
        output = Path(temp) / "issue"
        api.save(output, spec.title, spec.revision, "TRADE REVIEW / HOLD", rail, proof)
        rows = [asdict(p) for p in parts]
        (output / "components.json").write_text(json.dumps(rows, indent=2) + "\n")
        if rows:
            with (output / "components.csv").open("w", newline="") as file:
                writer = csv.DictWriter(file, rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        counts = Counter(p.material for p in parts)
        (output / "materials.json").write_text(
            json.dumps(dict(sorted(counts.items())), indent=2) + "\n"
        )
        (output / "project.json").write_text(spec.model_dump_json(indent=2) + "\n")
        (output / "viewports.json").write_text(json.dumps(api.meta, indent=2) + "\n")
        from .qa import verify

        result = verify(output)
        (output / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
        output.rename(destination)
    return result
