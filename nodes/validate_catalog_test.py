from nodes.testlib import broken_catalog, small_catalog
from nodes.validate_catalog import validate_catalog


def test_valid_catalog_passes():
    m = validate_catalog(None, small_catalog())
    assert m.passed
    assert m.n_constants == 6
    assert m.n_quantities == 2
    assert m.n_formulas == 3
    assert not [i for i in m.issues if i.severity == "error"]


def test_broken_catalog_reports_errors():
    m = validate_catalog(None, broken_catalog())
    assert not m.passed
    msgs = [i.message for i in m.issues if i.severity == "error"]
    assert any("duplicate formula id" in x for x in msgs)
    assert any("bad tier" in x for x in msgs)
    assert any("unknown symbol" in x for x in msgs)
