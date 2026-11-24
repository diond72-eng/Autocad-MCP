# Professional CAD engine

The professional extension runs on Linux independently of AutoCAD MCP. The
existing upstream Windows and Linux backend interfaces and tool names are
untouched. Use upstream commands for editing and auditing drawings and this
extension for generating a dimensioned multi-sheet draft from a typed job.
The bundled profile carries the accepted Rev 06 line hierarchy, native
dimensions, A3 rail, section hatching, Osifont and the binary CTB.

## Quick start

Install Python 3.12 and [uv](https://docs.astral.sh/uv/). Start at the cloned fork root.

```sh
scripts/professional-cad/setup.sh
uv run --no-sync python -m professional_cad generate examples/professional-cad/kitchen.json /tmp/kitchen-issue
uv run --no-sync professional-cad validate /tmp/kitchen-issue
uv run --no-sync pytest -q tests/test_professional_cad.py
```

Open the consolidated `package.pdf` and crop the 300 dpi sheets for review.
Native editable `drawing.dxf`, individual plots, a parameter copy, component and
quantity schedules, and audit results are in the issue directory. Output
directories must be new. Generate revisions into new directories.

## Codex and plugin

The authoritative skill is `skills/professional-cad/SKILL.md`.
The setup script links it into the repository's `.agents/skills` discovery
location. Restart or open a new Codex session in the repo, then ask to use
`$professional-cad` for the drawing task. Run
`scripts/professional-cad/install_skill.sh /absolute/skills/directory` for a
different standalone skill root. The skill remains in the checkout.

The Codex plugin manifest points to the same skills directory and exposes an
optional stdio sidecar. Local Codex must be able to run
`professional-cad-mcp` from the installed environment. Configure
`PROFESSIONAL_CAD_WORKSPACE` to an existing private job folder. Typical local
registration, if supported by the installed Codex client, is:

```sh
codex mcp add professional-cad --env PROFESSIONAL_CAD_WORKSPACE=/absolute/job -- /absolute/repo/.venv/bin/professional-cad-mcp
```

Cloud clients with no local MCP registration can use the CLI. Keep inputs and
artifacts in a private job workspace. An MCP client returns a structured report
from `professional_cad_generate_project` and can recheck the relative output
directory with `professional_cad_validate_project`. No arbitrary path, overwrite
or URL inputs are supported.

## Inputs and revisions

`professional-cad schema` returns the typed input. All coordinates are
millimetres from finished wall and floor datums. Choose room width, depth and
ceiling, then give each cabinet and service station a unique ID. Explicitly
enter carcass materials and vendor dimensions. Generic back, panel, feet and
hardware values are provisional by default. Drawer-only and door-only units
have different component construction. Split mixed modules where needed.

Example prompt: “Use the professional CAD skill to draw a 3000 mm wardrobe,
verify opening and scribe dimensions, generate internal and finished views,
and retain the package for trade coordination.” Supply actual hardware,
materials and release notes. Do not publish confidential inputs.

For a revision to an existing DXF, first use upstream `drawing_open`,
`drawing_info` and `drawing_audit`. Reconcile the observed dimensions with a
new job parameter file before regenerating. Arbitrary third-party DXFs are
not automatically parsed into joinery parameters.

## Templates, export and QA

The native A3 DXF template and symbol library are in
`assets/professional-cad`. Install the supplied Osifont or configure the CAD
application to resolve it. Font substitution is deliberately disabled in the
plotter. The same profile defines dimensions, material hatches and CTB.
The plotter uses PyMuPDF to emit vector paths, including letter outlines,
and retains editable text in CAD.

The CLI supports DXF on every supported Linux install. Optional DWG export
requires a separately installed ODA File Converter. Set
`ODA_FILE_CONVERTER` and if needed `ODA_XVFB` and run
`bash scripts/professional-cad/convert_oda.sh NEW_DXF_DIRECTORY CONVERSION_DIRECTORY`.
The script requires AC1027 output and converts it back to DXF for read-back.
It makes no DWT claim. Compare reopened geometry, not just the header.

Use `professional-cad compare OLD.pdf NEW.pdf` for per-page vector and
150 dpi raster signatures. Rerender each page at 300 dpi and visually check
component boundaries, notes, sections, edge clashes and manufactured
clearances. A passing audit does not release drawings to manufacture.
The public fixture is anonymised. See the private golden master record for
available benchmark evidence.

## Extend

Add manufacturer profiles as separate validated JSON inputs with actual
published material and system sizes. Extend `model.py` to add a component
family and `geometry.py` to add projections. Keep input truth out of
`project.py` sheet composition. Set material cut patterns in the geometry
mapping, and validate them with the profile. Change a published style via a new
versioned profile and regression review. See the capability register before
promising a new discipline or conversion.
