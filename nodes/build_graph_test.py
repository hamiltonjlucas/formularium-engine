from nodes.build_graph import build_graph
from nodes.testlib import small_catalog


def test_build_graph():
    m = build_graph(None, small_catalog())
    ids = {n.id for n in m.nodes}
    # 5 constants + 3 quantities + 3 formulas
    assert len(m.nodes) == 11
    assert {"v", "M_W", "W_mass", "yukawa_e_rel"} <= ids
    edges = {(e.source, e.target) for e in m.edges} | {(e.target, e.source) for e in m.edges}
    assert ("W_mass", "v") in edges
    assert ("yukawa_e_rel", "v") in edges
    assert "Formularium catalog digest" in m.digest_markdown
