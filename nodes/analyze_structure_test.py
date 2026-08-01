from nodes.analyze_structure import analyze_structure
from nodes.testlib import small_catalog


def test_v_is_a_bridge():
    """In the miniature catalog, v links the W-mass and Yukawa sides: it must be an
    articulation point ranking in the top bridges (the miniature version of the real
    catalog's Higgs-VEV finding — the full-catalog v-#1 check runs in the live sweep)."""
    m = analyze_structure(None, small_catalog())
    top3 = [c.node for c in m.centrality[:3]]
    assert "v" in top3
    v_entry = next(c for c in m.centrality if c.node == "v")
    assert v_entry.articulation_point
    assert "v" in m.articulation_points
    assert "`v`" in m.markdown
