from pathlib import Path

import pytest

pytest.importorskip("pymupdf")

from professional_cad.cad import PROFILE, setup
from professional_cad.geometry import merged_chain
from professional_cad.mcp_server import allowed_output
from professional_cad.model import Cabinet, Project, components
from professional_cad.project import generate
from professional_cad.qa import signature, verify

FIXTURES = Path(__file__).resolve().parents[1] / "examples/professional-cad"


def test_cabinet_assembly_clearance_and_join():
    c = Cabinet(
        id="B01",
        kind="base",
        x=40,
        y=10,
        z=150,
        width=600,
        depth=540,
        height=700,
        board=16,
        back=12,
        service_void=25,
        shelves=[300],
    )
    parts = {p.role: p for p in components(c)}
    assert parts["side-left"].w == parts["side-right"].w == 16
    assert parts["back"].y == 35 and parts["back"].d == 12
    assert parts["plinth"].y + parts["plinth"].d == 10 + 540 + 22 - 60
    assert parts["side-right"].x + parts["side-right"].w == 640
    assert parts["door-0-left"].x == 41 and parts["door-1-left"].x == 341
    assert parts["shelf-1"].w + 2 * c.board == c.width
    assert merged_chain([40, 640, 640, 1000]) == [(40, 640), (640, 1000)]


def test_drawing_profile():
    doc = setup()
    assert doc.units == 4
    assert doc.styles.get("ISO-JOINERY").dxf.font == PROFILE["font"]["file"]
    assert doc.layers.get("JCUT").dxf.lineweight == 35
    assert doc.layers.get("HIDE" if "HIDE" in doc.layers else "HIDDEN").dxf.lineweight == 13
    assert doc.dimstyles.get("SHOP").dxf.dimtxt == 2.5


@pytest.mark.parametrize("name", ["vanity", "wardrobe", "utility", "room-services", "kitchen"])
def test_clean_vector_issue(name, tmp_path):
    p = Project.model_validate_json((FIXTURES / f"{name}.json").read_bytes())
    target = tmp_path / "issue"
    report = generate(p, target, proof=False)
    assert report["vector_pdf"] and report["native_dimensions"] >= 4
    assert verify(target) == report
    with pytest.raises(FileExistsError):
        generate(p, target, proof=False)
    if name == "kitchen":
        other = tmp_path / "repeat"
        generate(p, other, proof=False)
        assert signature(target / "package.pdf") == signature(other / "package.pdf")


def test_mcp_workspace_boundary(tmp_path, monkeypatch):
    monkeypatch.setenv("PROFESSIONAL_CAD_WORKSPACE", str(tmp_path))
    assert allowed_output("new") == tmp_path / "new"
    for name in ("../private", "/tmp/private", "abc/../outside", ""):
        with pytest.raises(ValueError):
            allowed_output(name)
    (tmp_path / "alias").symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(ValueError):
        allowed_output("alias")
