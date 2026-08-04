import itertools
import math

from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_types_messages_pb2 import Catalog, DiscoverReport
from nodes import catalog_lib

MATH = {"pi": (math.pi, 0.0, 0), "2": (2.0, 0.0, 0), "3": (3.0, 0.0, 0)}

# orphan constant -> curated basis to scan against (ported from engine/discover.py)
ORPHAN_BASES = {
    "s12sq": ["s23sq", "s13sq", "V_us"],
    "s13sq": ["s12sq", "s23sq", "V_us"],
    "s23sq": ["s12sq", "s13sq"],
    "V_ub": ["V_us", "V_cb", "A_wolf"],
    "alpha_s": ["alpha", "sin2_thetaW"],
    "m_n": ["m_p", "m_e"],
    "Delta_m21_sq": ["Delta_m31_sq", "s12sq"],
    "Delta_m31_sq": ["Delta_m21_sq", "s23sq"],
}


def _cat_values(cat: catalog_lib.Cat) -> dict[str, tuple[float, float, float]]:
    """symbol -> (value, sigma, mass_dim) in the constant's own conventional unit.

    The scan works in log-space on multiplicative relations, so the unit convention
    cancels for dimensionally balanced candidates (the dimensional filter enforces
    balance) — this mirrors the original engine exactly."""
    return {
        c.symbol: (float(c.value), float(c.uncertainty or 0.0), float(c.mass_dim))
        for c in cat.constants.values()
    }


def _deg(sin2):
    return math.degrees(math.asin(math.sqrt(sin2)))


def _sigma_deg(sin2, sig):
    if sin2 <= 0 or sin2 >= 1:
        return 0.0
    return math.degrees(sig / (2 * math.sqrt(sin2 * (1 - sin2))))


def _named_hypotheses(cat_vals) -> list[str]:
    need = ("s12sq", "s13sq", "s23sq", "V_us")
    if any(s not in cat_vals for s in need):
        return ["named hypotheses SKIPPED: neutrino-sector constants missing"]
    out = []
    s12, s12e = cat_vals["s12sq"][0], cat_vals["s12sq"][1]
    s13, s13e = cat_vals["s13sq"][0], cat_vals["s13sq"][1]
    s23, s23e = cat_vals["s23sq"][0], cat_vals["s23sq"][1]
    gr = (5 - math.sqrt(5)) / 10

    def line(label, obs, obse, pred):
        d = abs(obs - pred) / obse if obse else float("inf")
        verdict = ("consistent" if d < 1 else "mild tension" if d < 2
                   else "disfavored" if d < 3 else "excluded")
        return (f"{label}: pred {pred:.4f} vs {obs:.4f}+/-{obse:.4f} -> "
                f"{d:.1f} sigma [{verdict}]")

    out.append(line("sin2(th12) tribimaximal (1/3)", s12, s12e, 1 / 3))
    out.append(line("sin2(th12) golden ratio (5-sqrt5)/10", s12, s12e, gr))
    out.append(line("sin2(th12) bimaximal (1/2)", s12, s12e, 1 / 2))
    out.append(line("sin2(th23) maximal (1/2)", s23, s23e, 1 / 2))
    out.append(line("sin2(th13) tribimaximal (0)", s13, s13e, 0.0))
    th12, th12e = _deg(s12), _sigma_deg(s12, s12e)
    thC = math.degrees(math.asin(cat_vals["V_us"][0]))
    tot = th12 + thC
    d = abs(tot - 45.0) / th12e if th12e else float("inf")
    out.append(f"quark-lepton complementarity: th12 + thC = {tot:.2f} deg -> "
               f"{d:.1f} sigma from 45 deg")
    return out


def _scan_relations(target, basis, vals_map, max_coeff=2, complexity_cap=4,
                    math_keys=("pi", "2")):
    """Enumerate simple power-law relations target^a0 * prod(b^ai) = 1, dimensionally
    filtered, sigma-scored against propagated measurement uncertainty."""
    names = [target] + list(basis) + list(math_keys)
    vals = {n: (vals_map[n] if n in vals_map else MATH[n]) for n in names}
    lnv = {n: math.log(vals[n][0]) for n in names}
    cands, n_tested = [], 0
    others = names[1:]
    for a0 in (1, 2):
        for combo in itertools.product(range(-max_coeff, max_coeff + 1), repeat=len(others)):
            if not any(combo):
                continue
            coeffs = {target: a0, **dict(zip(others, combo))}
            complexity = sum(abs(a) for a in coeffs.values())
            if complexity > complexity_cap:
                continue
            if abs(sum(a * vals[n][2] for n, a in coeffs.items())) > 1e-9:
                continue
            n_tested += 1
            r = sum(a * lnv[n] for n, a in coeffs.items())
            var = sum((a * vals[n][1] / vals[n][0]) ** 2
                      for n, a in coeffs.items() if vals[n][1] > 0)
            sig = math.sqrt(var)
            score = abs(r) / sig if sig > 0 else (0.0 if abs(r) < 1e-9 else float("inf"))
            cands.append((score, complexity, {n: a for n, a in coeffs.items() if a}))
    cands.sort(key=lambda t: (t[0], t[1]))
    return cands, n_tested


def _fmt_rel(coeffs):
    num = [f"{n}^{a}" if a != 1 else n for n, a in coeffs.items() if a > 0]
    den = [f"{n}^{-a}" if a != -1 else n for n, a in coeffs.items() if a < 0]
    return (" * ".join(num) or "1") + " = " + (" * ".join(den) or "1")


def _pslq_validate(vals_map) -> list[str]:
    import mpmath as mp

    mp.mp.dps = 40
    out = []
    if "e_em" in vals_map and "alpha" in vals_map:
        xs = [mp.log(mp.mpf(vals_map["e_em"][0])), mp.log(mp.mpf(vals_map["alpha"][0])),
              mp.log(mp.pi), mp.log(mp.mpf(2))]
        rel = mp.pslq(xs, tol=mp.mpf(10) ** -10, maxcoeff=10, maxsteps=10**4)
        found = rel in ([2, -1, -1, -2], [-2, 1, 1, 2])
        out.append(f"exact (e_em, alpha, pi, 2): PSLQ -> {rel} "
                   f"{'(e_em^2 = 4 pi alpha) FOUND' if found else 'NOT FOUND'}")
    if all(s in vals_map for s in ("V_us", "m_d", "m_s")):
        cands, _ = _scan_relations("V_us", ["m_d", "m_s"], vals_map, math_keys=())
        g = next((c for c in cands if c[2] == {"V_us": 2, "m_d": -1, "m_s": 1}), None)
        if g:
            out.append(f"approximate Gatto (V_us^2 = m_d/m_s): consistent at "
                       f"{g[0]:.2f} sigma (real relation, surfaced)")
    return out


def discover_relations(ax: AxiomContext, input: Catalog) -> DiscoverReport:
    """Numeric relation search over the catalog's orphan constants: pre-registered
    symmetry-hypothesis sigma tests, a blind small-integer power-law scan (dimensionally
    filtered, look-elsewhere counted), and PSLQ validation that known relations are
    recovered. Built to falsify: a candidate counts only if simple, consistent within
    measured uncertainty, and better than the look-elsewhere expectation."""
    cat = catalog_lib.decode(input)
    vals_map = _cat_values(cat)
    m = DiscoverReport()

    for line in _named_hypotheses(vals_map):
        m.named_hypothesis_lines.append(line)

    scan_lines = []
    for orphan, basis in ORPHAN_BASES.items():
        if orphan not in vals_map:
            continue
        basis = [b for b in basis if b in vals_map]
        cands, n = _scan_relations(orphan, basis, vals_map)
        if not cands:
            scan_lines.append(f"{orphan}: no dimensionally-valid candidate")
            continue
        score, cx, coeffs = cands[0]
        c = m.candidates.add(target=orphan, sigma_score=score, complexity=cx,
                             formatted=_fmt_rel(coeffs))
        for name, a in coeffs.items():
            c.coefficients[name] = a
        if score > 3:
            c.verdict = f"no consistent simple relation ({n} tried)"
        else:
            expected = n * math.erf(score / math.sqrt(2)) if score < 6 else float(n)
            c.verdict = ("CANDIDATE worth investigating"
                         if expected < 0.3 and score < 1
                         else f"not significant (~{expected:.0f} of {n} expected by chance)")
        scan_lines.append(f"{orphan}: `{c.formatted}` at {score:.1f} sigma -> {c.verdict}")

    pslq_lines = _pslq_validate(vals_map)
    m.markdown = "\n".join(
        ["# Discovery report — connecting the orphans", "",
         "## Named symmetry hypotheses (pre-registered)", ""]
        + [f"- {x}" for x in m.named_hypothesis_lines]
        + ["", "## Blind multiplicative-relation scan (look-elsewhere reported)", ""]
        + [f"- {x}" for x in scan_lines]
        + ["", "## Engine validation (recovers known relations?)", ""]
        + [f"- {x}" for x in pslq_lines]
    ) + "\n"
    return m
