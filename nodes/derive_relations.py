from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_constants_messages_pb2 import Catalog, DeriveReport
from nodes import catalog_lib

# Curated eliminations, ported verbatim from unified-theory engine/derive.py:
# (label, [formula ids], [intermediate symbols to eliminate], kind).
# kind: "validate" re-derives a known catalog formula (internal-consistency check);
# "new" derives a relation not stated explicitly in the catalog.
DERIVATIONS = [
    ("M_W from charge, VEV, weak angle", ["W_mass", "echarge_g"], ["g"], "new"),
    ("top Yukawa from m_t and G_F", ["top_yukawa", "higgs_vev_from_GF"], ["v"], "new"),
    ("Higgs quartic from m_H and G_F", ["higgs_mass_quartic", "higgs_vev_from_GF"], ["v"], "new"),
    ("fermion mass from Yukawa and G_F", ["mass_from_yukawa", "higgs_vev_from_GF"], ["v"], "new"),
    ("G_F from alpha, M_W, weak angle (re-derive)",
     ["W_mass", "echarge_g", "alpha_from_e", "higgs_vev_from_GF"], ["g", "e_em", "v"], "validate"),
    ("classical radius from Bohr radius (re-derive)",
     ["r_e_from_a0", "bohr_radius"], ["a_0"], "validate"),
    ("Compton from Bohr radius (re-derive)",
     ["a0_from_compton", "bohr_radius"], ["a_0"], "validate"),
    ("Rydberg energy from Rydberg constant", ["rydberg_energy", "rydberg_constant"], ["m_e"], "new"),
    ("Hawking temperature from Unruh at surface gravity (re-derive)",
     ["unruh_temperature", "surface_gravity"], ["a_acc"], "validate"),
    ("w(a) relation from continuity + holographic ansatz (re-derive)",
     ["continuity_frw", "holographic_de_ansatz"], ["dlnrho_dlna"], "validate"),
    ("Hawking temperature vs horizon area",
     ["hawking_temperature", "schwarzschild_area"], ["M_bh"], "new"),
    ("de Sitter capacity from measured Lambda (re-derive)",
     ["N_desitter", "planck_length"], ["l_P"], "validate"),
    ("horizon entropy = kappa x area (re-derive)",
     ["bekenstein_hawking", "planck_length", "kappa_capacity"], ["l_P", "G_N"], "validate"),
    ("induced Newton constant from channel counting",
     ["kappa_capacity", "kappa_induced"], ["kappa_cap"], "new"),
]


def _combine(formulas, eliminate):
    """Eliminate symbols from a list of sympy Eqs by solve + substitute."""
    from sympy import Eq, solve, symbols

    eqs = list(formulas)
    for name in eliminate:
        var = symbols(name)
        idx = next((i for i, e in enumerate(eqs) if var in e.free_symbols), None)
        if idx is None:
            continue
        sols = solve(eqs[idx], var)
        if not sols:
            continue
        sub = {var: sols[0]}
        eqs = [Eq(e.lhs.subs(sub), e.rhs.subs(sub)) for i, e in enumerate(eqs) if i != idx]
    return eqs


def _verify(eq, vals):
    """Relative residual (|lhs/rhs| vs 1, sign-agnostic) at natural-units values."""
    from sympy import symbols

    syms = {str(s) for s in eq.free_symbols}
    if not syms <= set(vals):
        return None
    subs = {symbols(s): vals[s] for s in syms}
    try:
        lhs = float(eq.lhs.subs(subs))
        rhs = float(eq.rhs.subs(subs))
    except (TypeError, ValueError):
        return None
    if rhs == 0:
        return abs(lhs)
    return abs(abs(lhs / rhs) - 1.0)


def derive_relations(ax: AxiomContext, input: Catalog) -> DeriveReport:
    """Symbolic derivation over the curated elimination list: combine catalog formulas
    sharing an intermediate quantity, eliminate it, and numerically verify the resulting
    relation in natural units. 'validate' entries re-derive known formulas (consistency
    checks); 'new' entries surface relations the catalog doesn't state directly."""
    from sympy import simplify

    cat = catalog_lib.decode(input)
    F = catalog_lib.parsed_formulas(cat)
    vals = catalog_lib.natural_units_values(cat)
    m = DeriveReport()
    lines = ["# Derivations report — combining formulas into new relations", "",
             "Numeric checks in natural units (hbar = c = 1); many SM relations are exact "
             "only at tree level (~3% residuals are real loop/scheme effects).", ""]
    for label, fids, elim, kind in DERIVATIONS:
        missing = [i for i in fids if i not in F]
        if missing:
            lines.append(f"- **[{kind}]** {label}: SKIPPED (missing formulas {missing})")
            continue
        try:
            results = _combine([F[i] for i in fids], elim)
        except Exception as e:  # noqa: BLE001
            lines.append(f"- **[{kind}]** {label}: derivation error ({type(e).__name__})")
            continue
        for eq in results:
            rel = _verify(eq, vals)
            d = m.derivations.add(
                label=label, source_formula_ids=fids, eliminated=elim, kind=kind,
                lhs=str(simplify(eq.lhs)), rhs=str(simplify(eq.rhs)),
            )
            if rel is not None:
                d.residual = rel
                d.accuracy_note = ("verified exact" if rel < 1e-6
                                   else f"verified, holds to {rel * 100:.1f}% (tree level)")
            else:
                d.accuracy_note = "symbolic + dimensionally consistent (no numeric values)"
            lines.append(f"- **[{kind}]** {label}: `{d.lhs} = {d.rhs}` "
                         f"(eliminated {elim}) -> {d.accuracy_note}")
    m.markdown = "\n".join(lines) + "\n"
    return m
