from nodes.check_dimensions import check_dimensions
from nodes.testlib import broken_catalog, small_catalog


def test_consistent_catalog():
    m = check_dimensions(None, small_catalog())
    assert m.n_inconsistent == 0
    assert len(m.checks) == 3
    w = next(c for c in m.checks if c.formula_id == "W_mass")
    assert w.consistent and w.lhs_mass_dim == 1.0 and w.rhs_mass_dim == 1.0
    assert "consistent" in m.markdown


def test_inconsistent_formula_flagged():
    m = check_dimensions(None, broken_catalog())
    bad = next(c for c in m.checks if c.formula_id == "inconsistent")
    assert not bad.consistent
    assert m.n_inconsistent >= 1
