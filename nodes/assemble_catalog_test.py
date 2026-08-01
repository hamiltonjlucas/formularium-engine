from gen.messages_pb2 import AssembleCatalogInput
from nodes.assemble_catalog import assemble_catalog
from nodes.testlib import small_catalog


def test_assemble_catalog():
    inp = AssembleCatalogInput()
    inp.constants.CopyFrom(small_catalog())
    del inp.constants.domains[:]
    inp.electroweak.domain = "electroweak"
    inp.electroweak.formulas.add(id="W_mass", expression="Eq(M_W, g*v/2)")
    inp.flavor.domain = "flavor"
    inp.flavor.formulas.add(id="koide", expression="Eq(Q, 2/3)")
    out = assemble_catalog(None, inp)
    assert len(out.constants) == 6
    assert [d.domain for d in out.domains] == ["electroweak", "flavor"]
    assert out.domains[0].formulas[0].id == "W_mass"
