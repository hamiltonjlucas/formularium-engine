from gen.hamiltonjlucas_formularium_types_messages_pb2 import SynthesizeShardRequest
from nodes.synthesize_relations import synthesize_relations
from nodes.testlib import small_catalog


def _run(req):
    return list(synthesize_relations(None, iter([req])))


def test_synthesis_finds_relations_and_final_stats():
    req = SynthesizeShardRequest(shard_index=0, shard_count=1, max_wall_ms=120_000)
    req.catalog.CopyFrom(small_catalog())
    events = _run(req)
    final = events[-1]
    assert final.WhichOneof("payload") == "final_stats"
    assert not final.truncated
    assert final.final_stats.pairs >= 2
    relations = [e.relation for e in events[:-1]]
    assert final.final_stats.kept == len(relations) >= 1
    # eliminating g between W_mass and echarge_g must surface a relation
    assert any(set(r.parent_formula_ids) == {"W_mass", "echarge_g"} for r in relations)
    assert all(r.tier in ("established", "derived", "conjecture") for r in relations)


def test_wall_clock_budget_truncates():
    req = SynthesizeShardRequest(shard_index=0, shard_count=1, max_wall_ms=1)
    req.catalog.CopyFrom(small_catalog())
    events = _run(req)
    assert events[-1].truncated
