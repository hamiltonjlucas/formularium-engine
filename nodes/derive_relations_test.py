from nodes.derive_relations import derive_relations
from nodes.testlib import small_catalog


def test_curated_derivation_runs():
    """The synthetic catalog carries W_mass + echarge_g, so the first curated
    elimination (eliminate g) must produce a numerically-exact relation; entries whose
    formulas are absent must be skipped, not crash."""
    m = derive_relations(None, small_catalog())
    assert len(m.derivations) >= 1
    d = m.derivations[0]
    assert d.label.startswith("M_W from charge")
    assert d.eliminated == ["g"]
    assert d.HasField("residual") and d.residual < 1e-9
    assert "SKIPPED" in m.markdown  # the entries whose formulas aren't in this catalog
