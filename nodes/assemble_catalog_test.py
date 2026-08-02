from google.protobuf import json_format

from gen.hamiltonjlucas_formularium_constants_messages_pb2 import Catalog, DomainCatalog
from gen.messages_pb2 import AssembleCatalogInput
from nodes.assemble_catalog import assemble_catalog
from nodes.testlib import small_catalog


def test_assemble_catalog():
    constants_only = Catalog()
    constants_only.CopyFrom(small_catalog())
    del constants_only.domains[:]

    ew = DomainCatalog(domain="electroweak")
    ew.formulas.add(id="W_mass", expression="Eq(M_W, g*v/2)")
    fl = DomainCatalog(domain="flavor")
    fl.formulas.add(id="koide", expression="Eq(Q, 2/3)")

    inp = AssembleCatalogInput(
        constants_json=json_format.MessageToJson(constants_only),
        electroweak_json=json_format.MessageToJson(ew),
        flavor_json=json_format.MessageToJson(fl),
    )
    out = assemble_catalog(None, inp)
    assert len(out.constants) == 6
    assert [d.domain for d in out.domains] == ["electroweak", "flavor"]
    assert out.domains[0].formulas[0].id == "W_mass"


def test_empty_slices_skipped():
    out = assemble_catalog(None, AssembleCatalogInput())
    assert len(out.constants) == 0
    assert len(out.domains) == 0
