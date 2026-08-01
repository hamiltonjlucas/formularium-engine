from gen.hamiltonjlucas_formularium_types_messages_pb2 import SweepReport
from nodes.assemble_sweep_report import assemble_sweep_report


def test_assemble_sweep_report():
    inp = SweepReport()
    inp.validation.passed = True
    inp.validation.n_constants = 71
    inp.validation.n_formulas = 102
    inp.dimensions.n_inconsistent = 0
    inp.structure.centrality.add(node="v", betweenness=0.5, articulation_point=True)
    out = assemble_sweep_report(None, inp)
    assert out.validation.passed and out.validation.n_constants == 71
    assert "Validation**: PASSED" in out.markdown_summary
    assert "`v`" in out.markdown_summary
