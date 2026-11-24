"""Axis-aligned orthographic sections from native-scale component boxes."""

from math import isclose

CUT_PATTERNS = {"BK01": "ANSI37", "DF01": "ANSI32", "KP01": "ANSI32", "ST01": "ANSI36"}


def draw_box(view, part, axes, layer=None):
    (a, b), (c, d) = part.bounds(axes)
    view.rect(a, c, b - a, d - c, layer or part.layer)


def section(view, parts, axes, cut_axis, station, depth_direction=1):
    for part in parts:
        if part.role == "opening":
            (a, b), (c, d) = part.bounds(axes)
            view.dashbox(a, c, b - a, d - c)
            continue
        ((a, b), (c, d), (start, end)) = part.bounds((*axes, cut_axis))
        if start <= station < end:
            pattern = CUT_PATTERNS.get(part.material, "ANSI31")
            view.faced(a, c, b - a, d - c, part.layer, pattern, view.s * 1.35)
        elif (start - station) * depth_direction > 0:
            draw_box(view, part, axes, "DETAIL")


def front(view, parts, internal=False, rear=False):
    for part in parts:
        role = part.role
        if role == "opening":
            (a, b), (c, d) = part.bounds((0, 2))
            view.dashbox(a, c, b - a, d - c)
            continue
        if rear:
            show = role.startswith(("back", "fixing", "side", "plinth"))
        elif internal:
            show = not role.startswith(("door", "handle", "drawer-front", "drawer-handle"))
        else:
            show = (
                role.startswith(
                    ("side", "door", "handle", "drawer-front", "drawer-handle", "plinth")
                )
                or role == "top"
            )
        if show:
            draw_box(view, part, (0, 2), "JOINERY" if part.layer == "JCUT" else part.layer)


def project_iso(view, parts, explode=False):
    def iso(x, y, z):
        return (0.86 * x + 0.5 * y, 0.34 * x - 0.59 * y + 0.91 * z)

    for part in sorted(parts, key=lambda p: (p.z, p.y, p.x, p.id)):
        if part.role == "opening" or part.layer == "DETAIL":
            continue
        x, y, z, w, d, h = part.x, part.y, part.z, part.w, part.d, part.h
        if explode and part.role.startswith(("door", "drawer-front")):
            y += 160
        if explode and part.role == "back":
            y -= 120
        for face in (
            ((x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)),
            ((x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)),
            ((x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)),
        ):
            view.poly([iso(*point) for point in face], part.layer, True)


def merged_chain(values, tolerance=1e-7):
    result = []
    for value in sorted(values):
        if not result or not isclose(value, result[-1], abs_tol=tolerance):
            result.append(value)
    return list(zip(result, result[1:], strict=False))
