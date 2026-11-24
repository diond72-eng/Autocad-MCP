# Baseline and acceptance record

The accepted 15-sheet Rev 06 output and the unmodified producing environment
were preserved before refactoring. The private execution was AutoCAD MCP Pro
1.8.0 using ezdxf, with Python 3.12, Osifont and binary CTB, native DXF generation,
the ezdxf PyMuPDF vector backend, 300 dpi MuPDF proofs, and ODA AC1027 conversion
with Xvfb and DXF read-back. Exact versions, converter hashes, package lists,
MCP logs and source inputs are recorded in the private snapshot.

Re-running the unchanged private sources reproduced sheet counts and vector
drawing counts on every page. A strict PDF/raster digest differed on 12 of 15
sheets. Vector inspection located small coordinate variations in ezdxf's
randomized hatch clipping. The maximum measured mean absolute RGB difference
was 0.01236 on a 0–255 scale at 150 dpi. The original golden file was kept
unchanged. The new generic plotter seeds ezdxf's hatch pass under a lock and
restores the caller's random state; its repeated-output regression checks both
vector and raster digests.

The five sample jobs are explicitly anonymised. They demonstrate different
geometry and coordinate schedules. They still need project-specific trade
detailing for an approved manufacturing or build issue. The generic engine
has not reproduced the complete private job through its new schema, and the
current capabilities therefore support a preview release.
