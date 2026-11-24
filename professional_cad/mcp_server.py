"""Optional stdio bridge. Existing AutoCAD MCP tools remain unchanged."""

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .model import Project
from .project import generate
from .qa import verify

server = FastMCP("professional-cad")


def allowed_output(name: str, must_exist=False) -> Path:
    root_var = os.environ.get("PROFESSIONAL_CAD_WORKSPACE")
    if not root_var:
        raise ValueError("Set PROFESSIONAL_CAD_WORKSPACE to an existing private job directory")
    root = Path(root_var).resolve(strict=True)
    if not root.is_dir() or Path(name).name != name or name in ("", ".", ".."):
        raise ValueError("Provide a single directory name inside the configured workspace")
    out = root / name
    if out.is_symlink() or out.resolve().parent != root:
        raise ValueError("Symlinks and paths outside the MCP workspace are refused")
    if must_exist:
        if not out.is_dir():
            raise ValueError("Package directory does not exist")
        if any(
            (out / file).is_symlink() for file in ("drawing.dxf", "package.pdf", "viewports.json")
        ):
            raise ValueError("Package inputs cannot be symlinks")
    return out


@server.tool()
def professional_cad_generate_project(project: Project, output_name: str) -> dict:
    """Generate an editable, dimensioned A3 package in a new directory under the configured job workspace."""
    return generate(project, allowed_output(output_name))


@server.tool()
def professional_cad_validate_project(output_name: str) -> dict:
    """Reopen the editable CAD and vector drawings to check audit, font and scale integrity."""
    return verify(allowed_output(output_name, True))


def main():
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
