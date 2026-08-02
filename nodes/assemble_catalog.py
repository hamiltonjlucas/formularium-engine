from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_constants_messages_pb2 import Catalog
from gen.messages_pb2 import AssembleCatalogInput

_DOMAIN_FIELDS = (
    "electroweak", "flavor", "bz_cascade", "atomic", "em_si",
    "gravity_thermo", "cosmology", "quantum_info",
)


def assemble_catalog(ax: AxiomContext, input: AssembleCatalogInput) -> Catalog:
    """Merge the per-package catalog slices (formularium-constants + the 8 domain
    packages) into the single assembled Formularium Catalog."""
    m = Catalog()
    m.constants.extend(input.constants.constants)
    for name in _DOMAIN_FIELDS:
        dom = getattr(input, name)
        if dom.domain or dom.formulas:
            m.domains.append(dom)
    return m
