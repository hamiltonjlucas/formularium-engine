from nodes.discover_relations import discover_relations
from nodes.testlib import small_catalog


def test_pslq_recovers_known_relation():
    """e_em and alpha are seeded with e_em^2 = 4*pi*alpha exactly — PSLQ must
    recover it; the neutrino-sector hypotheses are skipped (constants absent)."""
    m = discover_relations(None, small_catalog())
    assert "FOUND" in m.markdown
    assert any("SKIPPED" in x for x in m.named_hypothesis_lines)
