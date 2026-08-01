from nodes.buckingham import buckingham
from nodes.testlib import small_catalog


def test_classic_mode_self_check():
    """Classic full-SI mode is catalog-independent: {e, eps0, hbar, c} must yield
    exactly one dimensionless group (~4*pi*alpha) and {c, hbar, G} zero (Planck
    uniqueness) — the engine's own falsification anchor."""
    m = buckingham(None, small_catalog())
    em = next(s for s in m.classic_mode if s.label.startswith("electromagnetism"))
    pl = next(s for s in m.classic_mode if s.label.startswith("gravity+quantum"))
    assert len(em.groups) == 1
    assert len(pl.groups) == 0
    assert "PASS" in m.markdown


def test_catalog_mode_groups():
    m = buckingham(None, small_catalog())
    ew = next((s for s in m.catalog_mode if s.label == "electroweak scales"), None)
    assert ew is not None
    # of {M_W, M_Z, v, m_H} only M_W and v exist in the miniature catalog -> 1 group
    assert ew.symbols == ["M_W", "v"]
    assert len(ew.groups) == 1
