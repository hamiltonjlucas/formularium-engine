from nodes.check_units import check_units
from nodes.testlib import broken_catalog, small_catalog


def test_units_all_match():
    m = check_units(None, small_catalog())
    assert m.n_mismatches == 0
    assert len(m.checks) == 6


def test_bad_mass_dim_annotation_flagged():
    m = check_units(None, broken_catalog())
    bad = next(c for c in m.checks if c.symbol == "M_W")
    assert not bad.matches
    assert bad.derived_mass_dim == 1.0 and bad.stored_mass_dim == 0.0
    assert m.n_mismatches == 1
