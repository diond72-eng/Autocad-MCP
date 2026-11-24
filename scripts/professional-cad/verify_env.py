"""Report runtime components and the resolved bundled technical font."""

import json
import platform
import shutil
from importlib.metadata import version
from pathlib import Path

from professional_cad.cad import PROFILE, setup

doc = setup()
result = {
    "os": platform.platform(),
    "python": platform.python_version(),
    "packages": {n: version(n) for n in ("ezdxf", "PyMuPDF", "Pillow", "pydantic", "mcp")},
    "font": doc.styles.get(PROFILE["font"]["cad_style"]).dxf.font,
    "profile": PROFILE["id"],
    "poppler": bool(shutil.which("pdftoppm")),
    "oda": bool(shutil.which("ODAFileConverter")),
    "mm": doc.units == 4,
    "cwd": Path.cwd().name,
}
print(json.dumps(result, indent=2))
