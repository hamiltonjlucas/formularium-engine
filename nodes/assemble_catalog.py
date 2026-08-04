from google.protobuf import json_format

from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_types_messages_pb2 import Catalog, DomainCatalog
from gen.messages_pb2 import AssembleCatalogInput

_DOMAIN_FIELDS = (
    "electroweak_json", "flavor_json", "bz_cascade_json", "atomic_json", "em_si_json",
    "gravity_thermo_json", "cosmology_json", "quantum_info_json",
)


def assemble_catalog(ax: AxiomContext, input: AssembleCatalogInput) -> Catalog:
    """Merge the per-package catalog slices (formularium-constants + the 8 domain
    packages, each JSON-encoded by its edge's toJson adapter) into the single
    assembled Formularium Catalog."""
    m = Catalog()
    if input.constants_json:
        constants = json_format.Parse(input.constants_json, Catalog(),
                                      ignore_unknown_fields=True)
        m.constants.extend(constants.constants)
    for field in _DOMAIN_FIELDS:
        raw = getattr(input, field)
        if not raw:
            continue
        dom = json_format.Parse(raw, DomainCatalog(), ignore_unknown_fields=True)
        if dom.domain or dom.formulas:
            m.domains.append(dom)
    return m
