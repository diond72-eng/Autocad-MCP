"""Native reusable joinery symbols. Hardware marked provisional is a coordination aid."""

from __future__ import annotations

from math import cos, radians, sin

from .cad import outline, poly

LEGEND = {
    "JY-SECTION-MARK": "Section reference. Origin at marker centre; nominal paper-scale symbol.",
    "JY-MATERIAL-TAG": "Replaceable material identifier, nominal paper-scale symbol.",
    "JY-GPO": "Power point, diagrammatic symbol.",
    "JY-DOWNLIGHT": "Ceiling fitting, diagrammatic symbol.",
    "JY-ISOLATION": "Water isolation device, diagrammatic symbol.",
    "JY-LED-PROFILE": "Recessed LED channel example; confirm supplier section.",
    "JY-LVL-FOOT": "Adjustable leg and kick clip section; confirm supplied hardware.",
    "JY-HINGE-CUP": "35 mm cup plan symbol. Confirm drill plate pattern for purchased item.",
    "JY-SHELF-PIN": "Illustrative 5 mm pin hardware envelope.",
    "JY-DOOR-PULL": "Representative pull; drilling dimension subject to hardware sample.",
    "JY-FRONTLOAD-APPLIANCE": "Representative appliance front; exact product on hold.",
}
SYMBOLS = tuple(LEGEND)


def add_reusable_blocks(doc):
    """Create symbols once so source views and downstream drawings share definitions."""
    if all(name in doc.blocks for name in SYMBOLS):
        return

    def new(name):
        return doc.blocks.new(name)

    def segment(b, a, c, layer="DETAIL"):
        b.add_line(a, c, dxfattribs={"layer": layer})

    def circle(b, xy, radius, layer="DETAIL"):
        b.add_circle(xy, radius, dxfattribs={"layer": layer})

    def attribute(b, tag, value, x, y, height):
        b.add_attdef(
            tag,
            (x, y),
            value,
            dxfattribs={"layer": "ANNO", "style": "ISO-JOINERY", "height": height},
        )

    b = new("JY-SECTION-MARK")
    circle(b, (0, 0), 3.65, "ANNO")
    segment(b, (-3.65, 0), (3.65, 0), "ANNO")
    attribute(b, "REF", "A", -0.84, 0.75, 2.05)
    attribute(b, "SHEET", "J104", -1.95, -2.43, 1.42)

    b = new("JY-MATERIAL-TAG")
    outline(b, 0, -0.8, 9.7, 4.05, "ANNO")
    attribute(b, "MATERIAL", "ML01", 1.15, 0, 2.5)

    b = new("JY-GPO")
    outline(b, -6, -4, 12, 8, "POWER")
    for x in (-2.6, 2.6):
        segment(b, (x, -1.8), (x, 1.8), "POWER")

    b = new("JY-DOWNLIGHT")
    circle(b, (0, 0), 6, "POWER")
    segment(b, (-4.2, -4.2), (4.2, 4.2), "POWER")
    segment(b, (-4.2, 4.2), (4.2, -4.2), "POWER")

    b = new("JY-ISOLATION")
    circle(b, (0, 0), 5, "WATER")
    segment(b, (-5, 0), (5, 0), "WATER")
    segment(b, (0, -5), (0, 5), "WATER")

    b = new("JY-LED-PROFILE")
    poly(b, [(-9, 0), (-9, 8), (-7, 8), (-7, 2), (7, 2), (7, 8), (9, 8), (9, 0)], "DETAIL", True)
    outline(b, -7, 0.1, 14, 1.6, "DETAIL")

    b = new("JY-LVL-FOOT")
    outline(b, -22, 0, 44, 9, "DETAIL")
    outline(b, -9, 9, 18, 85, "DETAIL")
    outline(b, -20, 94, 40, 8, "DETAIL")
    for y in range(14, 44, 6):
        segment(b, (-9, y), (9, y + 3))
    poly(b, [(-36, 42), (-28, 42), (-28, 50), (-9, 50), (-9, 56), (-36, 56)], "DETAIL", True)

    b = new("JY-HINGE-CUP")
    circle(b, (0, 0), 17.5)
    circle(b, (0, 0), 14.5)
    # The centre and diameter are the only drill dimensions in this block.
    segment(b, (-20, 0), (20, 0), "AXIS")
    segment(b, (0, -20), (0, 20), "AXIS")

    b = new("JY-SHELF-PIN")
    circle(b, (0, 0), 2.5)
    outline(b, 0, -2.5, 10, 5, "DETAIL")

    b = new("JY-DOOR-PULL")
    outline(b, -4, -64, 8, 128, "DETAIL")
    circle(b, (0, -53), 3)
    circle(b, (0, 53), 3)

    b = new("JY-FRONTLOAD-APPLIANCE")
    outline(b, 0, 0, 584, 835, "JOINERY")
    outline(b, 14, 24, 556, 790, "DETAIL")
    segment(b, (14, 730), (570, 730))
    for r in (211, 181, 160):
        circle(b, (292, 363), r)
    outline(b, 436, 780, 91, 22, "DETAIL")
    circle(b, (351, 775), 17)
    outline(b, 56, 756, 133, 34, "DETAIL")

    def p(a):
        return (292 + 190 * cos(radians(a)), 363 + 190 * sin(radians(a)))

    segment(b, p(25), p(75))
    attribute(b, "ID", "WM", 274, 363, 20)
