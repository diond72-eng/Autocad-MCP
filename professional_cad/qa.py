"""Native/vector validation and quantum-stable PDF/image comparisons."""
import hashlib
import json

import ezdxf
import pymupdf as fitz

from .cad import ASSETS, PROFILE


def verify(path):
    doc=ezdxf.readfile(path/"drawing.dxf")
    audit=doc.audit()
    if audit.errors or audit.fixes or doc.units!=4:
        raise ValueError("DXF audit or millimetre-unit check failed")
    if any(block.block.is_xref for block in doc.blocks):
        raise ValueError("Unexpected unresolved DXF reference")
    if not (ASSETS/"fonts"/doc.styles.get(PROFILE["font"]["cad_style"]).dxf.font).is_file():
        raise ValueError("Font mapping is unavailable")
    expected=json.loads((path/"viewports.json").read_text())
    layouts=[l for l in doc.layouts if l.name!="Model"]
    actual=sorted((l.name,round(v.dxf.view_height/v.dxf.height,6)) for l in layouts for v in l.viewports() if v.dxf.id>1 and v.dxf.flags&16384)
    if actual!=sorted((row[0],row[1]) for row in expected):
        raise ValueError("Locked viewport scales failed read-back")
    dims=list(doc.modelspace().query("DIMENSION"))
    if any(d.dxf.text not in ("<>","") for d in dims):
        raise ValueError("Measurement override on a native dimension")
    with fitz.open(path/"package.pdf") as pdf:
        if len(pdf)!=len(layouts):
            raise ValueError("PDF layout count differs from DXF")
        for page in pdf:
            if (page.get_images() or not page.get_drawings() or
                abs(page.rect.width*25.4/72-420)>.02 or abs(page.rect.height*25.4/72-297)>.02):
                raise ValueError("Expected nonempty A3 landscape vector plot")
    return {"sheets":len(layouts),"native_dimensions":len(dims),"locked_viewports":len(actual),
            "vector_pdf":True,"cad_audit_errors":0,"cad_audit_fixes":0,
            "visual_review":"300 dpi human review required before issue"}


def signature(path):
    with fitz.open(path) as pdf:
        return [
            {"drawings":len(p.get_drawings()),"text":p.get_text(),"images":len(p.get_images()),
             "render_sha256":hashlib.sha256(p.get_pixmap(dpi=150,alpha=False).samples).hexdigest(),
             "vector_sha256":hashlib.sha256(repr(p.get_drawings()).encode()).hexdigest()}
            for p in pdf
        ]
