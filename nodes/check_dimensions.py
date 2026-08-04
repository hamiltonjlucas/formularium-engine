from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_types_messages_pb2 import Catalog, DimensionsReport
from nodes import catalog_lib


class DimError(Exception):
    pass


def _mdim(expr, dims: dict[str, float]) -> float:
    """Mass dimension of a sympy expression; raises DimError on an inconsistent sum.

    Products add, powers multiply, sums require all terms equal, pure numbers are 0,
    any other function head is dimensionless iff all its args are.
    """
    from sympy import Add, Mul, Number, NumberSymbol, Pow
    from sympy.core.numbers import ImaginaryUnit

    if isinstance(expr, (Number, NumberSymbol, ImaginaryUnit)):
        return 0.0
    if expr.is_Symbol:
        if expr.name not in dims:
            raise DimError(f"unknown symbol '{expr.name}'")
        return float(dims[expr.name])
    if isinstance(expr, Add):
        ds = {round(_mdim(a, dims), 9) for a in expr.args}
        if len(ds) != 1:
            raise DimError(f"sum of mixed mass-dimensions {sorted(ds)} in '{expr}'")
        return ds.pop()
    if isinstance(expr, Mul):
        return sum(_mdim(a, dims) for a in expr.args)
    if isinstance(expr, Pow):
        base, exp = expr.args
        if isinstance(exp, Number):
            return _mdim(base, dims) * float(exp)
        if _mdim(base, dims) == 0:
            return 0.0
        raise DimError(f"non-numeric exponent on a dimensionful base in '{expr}'")
    if all(_mdim(a, dims) == 0 for a in expr.args):
        return 0.0
    raise DimError(f"cannot dimension-analyze '{expr}'")


def check_dimensions(ax: AxiomContext, input: Catalog) -> DimensionsReport:
    """Verify every formula in the assembled catalog balances in natural-units mass
    dimension (hbar = c = 1): products add, powers multiply, sums must agree."""
    from sympy import sympify

    cat = catalog_lib.decode(input)
    dims = catalog_lib.symbol_dims(cat)
    m = DimensionsReport()
    lines = ["# Dimensional consistency (natural units, hbar = c = 1)", ""]
    for f in cat.formulas.values():
        chk = m.checks.add(formula_id=f.id)
        try:
            eq = sympify(f.expression)
            lhs, rhs = _mdim(eq.lhs, dims), _mdim(eq.rhs, dims)
            chk.lhs_mass_dim = lhs
            chk.rhs_mass_dim = rhs
            chk.consistent = round(lhs, 9) == round(rhs, 9)
            chk.detail = (
                f"consistent (mass_dim {lhs:g})" if chk.consistent
                else f"INCONSISTENT: lhs mass_dim {lhs:g} != rhs mass_dim {rhs:g}"
            )
        except DimError as e:
            chk.consistent = False
            chk.detail = f"ERROR: {e}"
        except Exception as e:  # noqa: BLE001
            chk.consistent = False
            chk.detail = f"ERROR: {type(e).__name__}: {e}"
        if not chk.consistent:
            m.n_inconsistent += 1
        lines.append(f"- `{f.id}`: {chk.detail}")
    lines.insert(1, f"\n{len(cat.formulas)} formulas checked, {m.n_inconsistent} inconsistent.\n")
    m.markdown = "\n".join(lines) + "\n"
    return m
