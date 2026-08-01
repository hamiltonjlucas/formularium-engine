"""Shared catalog decoding for every engine node.

Decodes the formularium-types Catalog message into plain-Python lookups, and
ports unified-theory's natural-units value builder (constants converted to GeV
powers via units_lib, plus the derived intermediate couplings).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from nodes import units_lib

TIERS = {"established", "derived", "conjecture"}
SOURCES = {"CODATA", "PDG", "NuFIT", "Planck", "derived", "definition", "convention"}
QUANTITY_KINDS = {"parameter", "coupling", "observable", "derived"}


@dataclass
class Const:
    symbol: str
    name: str
    value: float
    unit: str
    mass_dim: float
    tier: str
    source: str
    uncertainty: float | None = None
    aliases: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Quant:
    symbol: str
    name: str
    mass_dim: float
    kind: str
    notes: str = ""


@dataclass
class Form:
    id: str
    name: str
    expression: str
    symbols: list[str]
    input_symbols: list[str]
    computes: str
    tier: str
    domain: str
    dimensional_check: str = ""
    notes: str = ""


@dataclass
class Cat:
    constants: dict[str, Const]
    quantities: dict[str, Quant]
    formulas: dict[str, Form]


def decode(catalog_msg) -> Cat:
    """formularium-types Catalog message -> plain-Python catalog."""
    constants: dict[str, Const] = {}
    for c in catalog_msg.constants:
        constants[c.symbol] = Const(
            symbol=c.symbol, name=c.name, value=c.value, unit=c.unit,
            mass_dim=c.mass_dim, tier=c.tier, source=c.source,
            uncertainty=c.uncertainty if c.HasField("uncertainty") else None,
            aliases=list(c.aliases), notes=c.notes,
        )
    quantities: dict[str, Quant] = {}
    formulas: dict[str, Form] = {}
    for d in catalog_msg.domains:
        for q in d.quantities:
            quantities.setdefault(
                q.symbol,
                Quant(symbol=q.symbol, name=q.name, mass_dim=q.mass_dim,
                      kind=q.kind, notes=q.notes),
            )
        for f in d.formulas:
            formulas[f.id] = Form(
                id=f.id, name=f.name, expression=f.expression,
                symbols=list(f.symbols), input_symbols=list(f.input_symbols),
                computes=f.computes, tier=f.tier, domain=f.domain,
                dimensional_check=f.dimensional_check, notes=f.notes,
            )
    return Cat(constants=constants, quantities=quantities, formulas=formulas)


def symbol_dims(cat: Cat) -> dict[str, float]:
    d = {c.symbol: c.mass_dim for c in cat.constants.values()}
    for q in cat.quantities.values():
        d.setdefault(q.symbol, q.mass_dim)
    return d


def natural_units_values(cat: Cat) -> dict[str, float]:
    """Constants in natural units (GeV powers) plus derived intermediate couplings.

    Port of unified-theory engine/derive.py natural_units_values(), over the
    decoded Catalog instead of YAML. Derived couplings are added only when
    their ingredient constants are present.
    """
    v: dict[str, float] = {}
    for c in cat.constants.values():
        try:
            v[c.symbol] = units_lib.to_natural_gev(float(c.value), c.unit)
        except ValueError:
            pass
    if "sin2_thetaW" in v and "e_em" in v:
        s = v["sin2_thetaW"]
        v["g"] = v["e_em"] / math.sqrt(s)
        v["g_prime"] = v["e_em"] / math.sqrt(1 - s)
    if "m_H" in v and "v" in v:
        v["lambda_H"] = v["m_H"] ** 2 / (2 * v["v"] ** 2)
    if "v" in v:
        for f, m in [("t", "m_t"), ("e", "m_e"), ("mu", "m_mu"), ("tau", "m_tau"),
                     ("u", "m_u"), ("d", "m_d"), ("s", "m_s"), ("c", "m_c"), ("b", "m_b")]:
            if m in v:
                v[f"y_{f}"] = math.sqrt(2) * v[m] / v["v"]
    return v


def parsed_formulas(cat: Cat) -> dict[str, "object"]:
    """id -> sympy Eq for every formula whose expression parses to an Eq."""
    from sympy import Eq, sympify

    out = {}
    for f in cat.formulas.values():
        try:
            e = sympify(f.expression)
            if isinstance(e, Eq):
                out[f.id] = e
        except Exception:  # noqa: BLE001
            pass
    return out
