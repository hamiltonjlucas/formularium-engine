"""Synthetic Catalog fixtures for engine node tests (not a node — ships as a helper)."""

from gen.hamiltonjlucas_formularium_types_messages_pb2 import Catalog

ALPHA = 0.0072973525693
E_EM = 0.30282212088  # sqrt(4 pi alpha)


def _constant(m, symbol, name, value, unit, mass_dim, uncertainty=None,
              tier="established", source="PDG"):
    c = m.constants.add(symbol=symbol, name=name, value=value, unit=unit,
                        mass_dim=mass_dim, tier=tier, source=source)
    if uncertainty is not None:
        c.uncertainty = uncertainty
    return c


def _formula(dom, fid, expression, symbols, input_symbols, computes,
             tier="established"):
    dom.formulas.add(id=fid, name=fid.replace("_", " "), expression=expression,
                     symbols=symbols, input_symbols=input_symbols,
                     computes=computes, tier=tier, provenance="test",
                     dimensional_check="", domain=dom.domain)


def small_catalog() -> Catalog:
    """A consistent miniature catalog: v links the W-mass and electron-Yukawa sides,
    so it is both the top betweenness bridge and an articulation point."""
    m = Catalog()
    g = 0.65
    s_w = E_EM / g  # so e_em = g*s_w holds exactly AND e_em^2 = 4*pi*alpha for PSLQ
    v = 246.22
    _constant(m, "v", "Higgs VEV", v, "GeV", 1)
    _constant(m, "M_W", "W mass", g * v / 2, "GeV", 1, uncertainty=0.012)
    _constant(m, "m_e", "electron mass", 0.000511, "GeV", 1)
    _constant(m, "e_em", "EM coupling", E_EM, "dimensionless", 0, uncertainty=1e-9)
    _constant(m, "s_w", "sin thetaW analogue", s_w, "dimensionless", 0)
    _constant(m, "alpha", "fine structure", ALPHA, "dimensionless", 0, uncertainty=1e-12,
              source="CODATA")

    dom = m.domains.add(domain="test")
    dom.quantities.add(symbol="g", name="weak coupling", mass_dim=0, kind="coupling")
    dom.quantities.add(symbol="y_e", name="electron Yukawa", mass_dim=0, kind="coupling")
    _formula(dom, "W_mass", "Eq(M_W, g*v/2)", ["M_W", "g", "v"], ["g", "v"], "M_W")
    _formula(dom, "echarge_g", "Eq(e_em, g*s_w)", ["e_em", "g", "s_w"], ["g", "s_w"], "e_em")
    _formula(dom, "yukawa_e_rel", "Eq(m_e, y_e*v/sqrt(2))", ["m_e", "v", "y_e"],
             ["v", "y_e"], "m_e")
    return m


def broken_catalog() -> Catalog:
    """Deliberately broken: duplicate formula id, bad tier, unknown symbol, bad unit
    annotation, dimensionally inconsistent formula."""
    m = Catalog()
    _constant(m, "v", "Higgs VEV", 246.22, "GeV", 1)
    _constant(m, "M_W", "W mass", 80.377, "GeV", 0)  # wrong mass_dim vs unit
    dom = m.domains.add(domain="broken")
    dom.quantities.add(symbol="g", name="weak coupling", mass_dim=0, kind="coupling")
    _formula(dom, "dup", "Eq(M_W, g*v/2)", ["M_W", "g", "v"], ["g", "v"], "M_W")
    _formula(dom, "dup", "Eq(M_W, g*v/2)", ["M_W", "g", "v"], ["g", "v"], "M_W")
    _formula(dom, "bad_tier", "Eq(M_W, g*v/2)", ["M_W", "g", "v"], ["g", "v"], "M_W",
             tier="guess")
    _formula(dom, "unknown_sym", "Eq(M_W, g*v*zzz)", ["M_W", "g", "v", "zzz"],
             ["g", "v", "zzz"], "M_W")
    _formula(dom, "inconsistent", "Eq(M_W, g*v*v)", ["M_W", "g", "v"], ["g", "v"], "M_W")
    return m
