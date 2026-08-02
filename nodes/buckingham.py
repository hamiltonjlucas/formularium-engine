import math
from functools import reduce

from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_constants_messages_pb2 import BuckinghamReport, Catalog
from nodes import catalog_lib

# Catalog-mode quantity sets (natural units, one base dimension = mass).
CATALOG_SETS = [
    ("charged-lepton masses", ["m_e", "m_mu", "m_tau"]),
    ("up-type quark masses", ["m_u", "m_c", "m_t"]),
    ("electroweak scales", ["M_W", "M_Z", "v", "m_H"]),
    ("top mass + Higgs VEV", ["m_t", "v"]),
    ("Fermi scale + a fermion mass", ["G_F", "m_t", "v"]),
]

# Classic-mode dimension vectors (M, L, T, Q, Theta) and consistent SI values.
SI = {
    "c": ((0, 1, -1, 0, 0), 2.99792458e8),
    "hbar": ((1, 2, -1, 0, 0), 1.054571817e-34),
    "G": ((-1, 3, -2, 0, 0), 6.67430e-11),
    "e": ((0, 0, 0, 1, 0), 1.602176634e-19),
    "eps0": ((-1, -3, 2, 2, 0), 8.8541878188e-12),
    "k_B": ((1, 2, -2, 0, -1), 1.380649e-23),
    "m_e": ((1, 0, 0, 0, 0), 9.1093837015e-31),
}
CLASSIC_SETS = [
    ("electromagnetism {e, eps0, hbar, c}", ["e", "eps0", "hbar", "c"]),
    ("gravity+quantum {c, hbar, G}", ["c", "hbar", "G"]),
    ("a fuller fundamental set", ["c", "hbar", "G", "e", "eps0", "k_B", "m_e"]),
]


def _int_nullspace(matrix_rows):
    """Integer basis of the nullspace of the dimension matrix (rows = base dims)."""
    from sympy import Matrix, Rational, igcd, ilcm

    M = Matrix(matrix_rows) if matrix_rows and matrix_rows[0] else Matrix([[0]])
    out = []
    for vec in M.nullspace():
        denom = reduce(ilcm, [Rational(x).q for x in vec], 1)
        ivec = [int(Rational(x) * denom) for x in vec]
        g = reduce(igcd, [a for a in ivec if a], 0) or 1
        ivec = [a // g for a in ivec]
        if next((a for a in ivec if a), 0) < 0:
            ivec = [-a for a in ivec]
        out.append(ivec)
    return out


def _value(symbols, exps, vals):
    try:
        return math.prod(vals[s] ** e for s, e in zip(symbols, exps))
    except (KeyError, OverflowError, ValueError):
        return None


def _monomial(symbols, exps):
    num = [f"{s}^{e}" if e != 1 else s for s, e in zip(symbols, exps) if e > 0]
    den = [f"{s}^{-e}" if e != -1 else s for s, e in zip(symbols, exps) if e < 0]
    return (" ".join(num) or "1") + (" / " + " ".join(den) if den else "")


def buckingham(ax: AxiomContext, input: Catalog) -> BuckinghamReport:
    """Buckingham-pi enumeration of independent dimensionless groups: catalog mode
    (natural units, one base dimension) and the classic full-SI theorem, self-validated
    against {e, eps0, hbar, c} -> 4*pi*alpha and {c, hbar, G} -> 0 (Planck uniqueness)."""
    cat = catalog_lib.decode(input)
    vals = catalog_lib.natural_units_values(cat)
    m = BuckinghamReport()
    lines = ["# Buckingham-pi report — the independent dimensionless groups", "",
             "## Mode 1 — within the catalog (natural units, one base dimension = mass)", ""]

    for label, syms in CATALOG_SETS:
        syms = [s for s in syms if s in cat.constants]
        if not syms:
            continue
        md = [cat.constants[s].mass_dim for s in syms]
        groups = _int_nullspace([list(md)])
        bset = m.catalog_mode.add(label=label, symbols=syms)
        lines.append(f"**{label}** ({', '.join(syms)}): {len(groups)} group(s)")
        for exps in groups:
            g = bset.groups.add(symbols=syms, exponents=exps)
            v = _value(syms, exps, vals)
            if v is not None:
                g.value = v
            lines.append(f"  - {_monomial(syms, exps)}"
                         + (f" = {v:.4g}" if v is not None else ""))

    lines += ["", "## Mode 2 — the classic theorem in full SI dimensions (M, L, T, Q, Theta)", ""]
    for label, syms in CLASSIC_SETS:
        cols = [SI[s][0] for s in syms]
        rows = [[cols[j][i] for j in range(len(syms))] for i in range(5)]
        groups = _int_nullspace(rows)
        bset = m.classic_mode.add(label=label, symbols=syms)
        si_vals = {s: SI[s][1] for s in syms}
        rank = len(syms) - len(groups)
        lines.append(f"**{label}**: {len(syms)} quantities, rank {rank} -> "
                     f"{len(groups)} group(s)")
        for exps in groups:
            g = bset.groups.add(symbols=syms, exponents=exps)
            v = _value(syms, exps, si_vals)
            if v is not None:
                g.value = v
            lines.append(f"  - {_monomial(syms, exps)}"
                         + (f" = {v:.5g}" if v is not None else ""))
        if not groups:
            lines.append("  - (none — the Planck units built from these are uniquely fixed)")

    # self-check: EM set gives exactly one group ~ 4*pi*alpha; {c,hbar,G} gives zero
    em = next((s for s in m.classic_mode if s.label.startswith("electromagnetism")), None)
    pl = next((s for s in m.classic_mode if s.label.startswith("gravity+quantum")), None)
    ok = False
    if em is not None and pl is not None and len(em.groups) == 1 and len(pl.groups) == 0:
        v = em.groups[0].value
        target = 4 * math.pi * 0.0072973525643
        ok = v is not None and (abs(v - target) < 1e-4 or abs(1 / v - target) < 1e-4)
    lines += ["", f"## Self-check: {'PASS' if ok else 'FAIL'}"]
    m.markdown = "\n".join(lines) + "\n"
    return m
