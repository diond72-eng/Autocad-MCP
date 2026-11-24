---
name: professional-cad
description: Produce or revise editable CAD, DXF, DWG, architectural drawings, joinery shop drawings, cabinet fabrication drawings, construction details, technical elevations, building sections and coordinated services drawing packages. Use the Linux headless professional drafting profile, physical component models and validated vector plots.
---

# Professional CAD

1. Inspect all incoming CAD, plans, schedules, construction notes and references.
   Record the design hierarchy, survey datums, revision status, approved
   geometry, third-party restrictions and what must be field-verified.
2. Load the repository profile at
   `professional_cad/profiles/professional-cad-v1.0.json`. Follow
   [the shop drawing workflow](references/workflow.md) for unsupported project
   details and visual review. Use mm at 1:1 and plot landscape A3.
3. Select a discipline and use a common editable geometry model. Give
   each physical component a material, position and thickness. Use the same
   cuts and backing model for every orthographic view. Mark proposed hardware
   and manufacturer-dependent interfaces as provisional.
4. Inspect the JSON schema with `python -m professional_cad schema`.
   Generate with `python -m professional_cad generate input.json new-output`.
   Browse `examples/professional-cad` for model inputs. Prefer the existing
   AutoCAD MCP tools for opening, inspecting and auditing CAD when connected.
5. Review dimension chains, actual wall set-out, lineweights, material
   hatches, boxed callouts and procurement quantities against the geometry.
   Extend the component model and drawing composition when a generic package
   lacks necessary sections or service details. Use physical parts rather than
   schematic boxes for construction work.
6. Render every sheet at 300 dpi. Inspect full sheets and enlarged crops,
   compare a prototype against the applicable benchmark, fix overlaps and
   recalculate before propagating the sheet treatment. Successful execution
   alone is insufficient.
7. Run `python -m professional_cad validate new-output` and reopen CAD.
   Keep editable DXF. Produce DWG only after actual conversion and read-back.
   Retain superseded revisions and document release holds and verification gaps.
