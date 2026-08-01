from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_types_messages_pb2 import Catalog, UnitsReport
from nodes import catalog_lib, units_lib


def check_units(ax: AxiomContext, input: Catalog) -> UnitsReport:
    """Parse every constant's unit string into the six SI base dimensions and verify
    the natural mass dimension derived from it (M - L - T + I + Theta) equals the
    stored hand-annotated mass_dim."""
    cat = catalog_lib.decode(input)
    m = UnitsReport()
    lines = ["# Unit-system validation", "",
             "| symbol | unit | derived mass_dim | stored | match |", "|---|---|---|---|---|"]
    for c in sorted(cat.constants.values(), key=lambda c: c.symbol):
        chk = m.checks.add(symbol=c.symbol, unit=c.unit, stored_mass_dim=c.mass_dim)
        try:
            _scale, dim = units_lib.parse(c.unit)
            chk.derived_mass_dim = units_lib.natural_mass_dim(dim)
            chk.matches = chk.derived_mass_dim == c.mass_dim
        except ValueError:
            chk.matches = False
        if not chk.matches:
            m.n_mismatches += 1
        lines.append(
            f"| {c.symbol} | {c.unit} | {chk.derived_mass_dim:g} | {c.mass_dim:g} "
            f"| {'yes' if chk.matches else 'NO'} |"
        )
    lines.insert(2, f"{len(cat.constants)} constants checked, {m.n_mismatches} mismatch(es).\n")
    m.markdown = "\n".join(lines) + "\n"
    return m
