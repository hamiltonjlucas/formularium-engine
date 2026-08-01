from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_types_messages_pb2 import Catalog, ValidationReport
from nodes import catalog_lib


def validate_catalog(ax: AxiomContext, input: Catalog) -> ValidationReport:
    """Cross-package catalog validation: duplicate symbols/ids, tier/source/kind
    whitelists, and symbol cross-references (every formula symbol must resolve to a
    constant or quantity). Runs on the assembled Catalog — the checks span package
    boundaries, so no single package can perform them alone."""
    m = ValidationReport(passed=True)

    seen_syms: set[str] = set()
    known: set[str] = set()
    n_constants = 0
    for c in input.constants:
        n_constants += 1
        if c.symbol in seen_syms:
            _issue(m, "error", c.symbol, "duplicate constant symbol")
        seen_syms.add(c.symbol)
        known.add(c.symbol)
        known.update(c.aliases)
        if c.tier not in catalog_lib.TIERS:
            _issue(m, "error", c.symbol, f"bad tier '{c.tier}'")
        if c.source not in catalog_lib.SOURCES:
            _issue(m, "error", c.symbol, f"bad source '{c.source}'")

    quantity_syms: set[str] = set()
    for d in input.domains:
        for q in d.quantities:
            if q.symbol in quantity_syms:
                continue  # quantities legitimately repeat across domain packages
            quantity_syms.add(q.symbol)
            known.add(q.symbol)
            if q.kind not in catalog_lib.QUANTITY_KINDS:
                _issue(m, "error", q.symbol, f"bad quantity kind '{q.kind}'")

    seen_ids: set[str] = set()
    n_formulas = 0
    for d in input.domains:
        for f in d.formulas:
            n_formulas += 1
            if f.id in seen_ids:
                _issue(m, "error", f.id, "duplicate formula id")
            seen_ids.add(f.id)
            if f.tier not in catalog_lib.TIERS:
                _issue(m, "error", f.id, f"bad tier '{f.tier}'")
            for s in f.symbols:
                if s not in known:
                    _issue(m, "error", f.id, f"references unknown symbol '{s}'")
            for s in f.input_symbols:
                if s not in f.symbols:
                    _issue(m, "warning", f.id, f"input symbol '{s}' missing from symbols list")

    m.n_constants = n_constants
    m.n_quantities = len(quantity_syms)
    m.n_formulas = n_formulas
    return m


def _issue(m, severity: str, scope: str, message: str) -> None:
    m.issues.add(severity=severity, scope=scope, message=message)
    if severity == "error":
        m.passed = False
