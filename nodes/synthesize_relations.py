import itertools
import math
import time
import zlib
from typing import Iterator

from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_types_messages_pb2 import (
    SynthesizeEvent,
    SynthesizeShardRequest,
)
from nodes import catalog_lib

MAX_OPS_RAW = 90
MAX_OPS_KEEP = 45
MAX_SYMS = 7
# Never eliminate the unit-defining constants (hbar = c = k_B = 1 in natural units):
# they appear in every dimensionful formula, so "eliminating" one merely multiplies two
# unrelated formulas together and fabricates a bridge with no physical content.
NEVER_ELIMINATE = {"hbar", "c", "k_B"}
MAX_BRANCHES = 2
DEPTH2_SEEDS = 40
TIER_RANK = {"established": 0, "derived": 1, "conjecture": 2}
DEFAULT_WALL_MS = 600_000


def _syms(expr):
    return frozenset(str(s) for s in expr.free_symbols)


def _sample_points(sym_tuple, n=4):
    """Deterministic per-symbol-set sample points (stable across expressions on the
    same symbols, so fingerprints are comparable)."""
    import random

    from sympy import Symbol

    rng = random.Random(zlib.crc32(",".join(sym_tuple).encode()))
    return [{Symbol(s): rng.uniform(0.5, 2.5) for s in sym_tuple} for _ in range(n)]


def _fingerprint(eq):
    """Equivalence-class key: normalized log|lhs/rhs| vector at seeded points.
    Proportional and power restatements map to the same key."""
    st = tuple(sorted(_syms(eq.lhs - eq.rhs)))
    logs = []
    for subs in _sample_points(st):
        try:
            lv, rv = complex(eq.lhs.subs(subs)), complex(eq.rhs.subs(subs))
            if abs(rv) < 1e-300 or abs(lv) < 1e-300:
                return None
            logs.append(math.log(abs(lv / rv)))
        except (TypeError, ValueError, ZeroDivisionError, OverflowError):
            return None
    base = next((x for x in logs if abs(x) > 1e-9), None)
    if base is None:
        return ("TAUTOLOGY", st)
    return (st, tuple(round(x / base, 6) for x in logs))


def _eliminate(eq_a, eq_b, sym):
    """Solve eq_a for sym, substitute into eq_b; returns candidate Eqs.

    NOTE: no hard per-call timeout — SIGALRM is unavailable off the main thread in the
    node sandbox, so pathological solve/simplify calls are bounded only by the outer
    wall-clock budget plus the node's overall_timeout_ms. Complexity caps keep the
    common path fast."""
    from sympy import Eq, count_ops, simplify, solve

    try:
        sols = solve(eq_a, sym, check=False)
    except Exception:  # noqa: BLE001  (sympy raises everything)
        return []
    out = []
    for sol in (sols or [])[:MAX_BRANCHES]:
        try:
            cand = eq_b.subs(sym, sol)
            if not isinstance(cand, Eq):
                continue
            if count_ops(cand.lhs - cand.rhs) > MAX_OPS_RAW:
                continue
            try:
                simple = Eq(simplify(cand.lhs), simplify(cand.rhs))
                if isinstance(simple, Eq):
                    cand = simple
            except Exception:  # noqa: BLE001
                pass
            if not isinstance(cand, Eq) or count_ops(cand.lhs - cand.rhs) > MAX_OPS_KEEP:
                continue
            out.append(cand)
        except Exception:  # noqa: BLE001
            continue
    return out


def _verify(eq, vals):
    from sympy import Symbol

    st = _syms(eq.lhs - eq.rhs)
    if not st <= set(vals):
        return None
    subs = {Symbol(s): vals[s] for s in st}
    try:
        lv, rv = float(eq.lhs.subs(subs)), float(eq.rhs.subs(subs))
    except (TypeError, ValueError, OverflowError):
        return None
    if rv == 0:
        return abs(lv)
    return abs(abs(lv / rv) - 1.0)


def synthesize_relations(ax: AxiomContext, inputs: Iterator[SynthesizeShardRequest]) -> Iterator[SynthesizeEvent]:  # noqa: E501
    """Exhaustive formula synthesis: for every catalog formula pair sharing an
    eliminable quantity (deterministically sharded by pair index), solve-substitute-
    simplify, drop tautologies, dedupe by numeric fingerprint against the catalog and
    prior finds, verify in natural units, and stream each distinct new relation as it
    is found (bridge relations — those creating new symbol co-occurrence edges —
    stream first-class; a final stats frame closes the stream). A synthesized relation
    inherits its weakest parent tier: a consequence of a conjecture is still a
    conjecture. Honesty rule: synthesis creates no information — its value is
    cartographic, making implicit bridges explicit."""
    from sympy import Symbol, count_ops

    for req in inputs:
        started = time.monotonic()
        budget_s = (req.max_wall_ms or DEFAULT_WALL_MS) / 1000.0
        shard_count = max(req.shard_count, 1)
        shard_index = req.shard_index % shard_count

        cat = catalog_lib.decode(req.catalog)
        F = catalog_lib.parsed_formulas(cat)
        vals = catalog_lib.natural_units_values(cat)
        tier_of = {fid: f.tier for fid, f in cat.formulas.items()}

        def worst_tier(parents):
            return max((tier_of.get(p, "derived") for p in parents),
                       key=lambda t: TIER_RANK.get(t, 1))

        cooccur: set[frozenset] = set()
        known = set()
        for e in F.values():
            s = _syms(e.lhs - e.rhs)
            cooccur.update(frozenset(p) for p in itertools.combinations(sorted(s), 2))
            fp = _fingerprint(e)
            if fp:
                known.add(fp)

        def new_edges(eq):
            s = sorted(_syms(eq.lhs - eq.rhs))
            return ["--".join(p) for p in itertools.combinations(s, 2)
                    if frozenset(p) not in cooccur]

        stats = {"pairs": 0, "eliminations": 0, "candidates": 0, "tautologies": 0,
                 "known": 0, "dupes": 0, "kept": 0}
        seen = set(known)
        found = []
        truncated = False

        def out_of_budget():
            return time.monotonic() - started > budget_s

        def consider(cand, parents, elim_sym, depth):
            stats["candidates"] += 1
            n = len(_syms(cand.lhs - cand.rhs))
            if n < 2 or n > MAX_SYMS:
                return None
            fp = _fingerprint(cand)
            if fp is None or fp[0] == "TAUTOLOGY":
                stats["tautologies"] += 1
                return None
            if fp in known:
                stats["known"] += 1
                return None
            if fp in seen:
                stats["dupes"] += 1
                return None
            seen.add(fp)
            stats["kept"] += 1
            found.append((cand, parents))
            ev = SynthesizeEvent()
            r = ev.relation
            r.lhs = str(cand.lhs)
            r.rhs = str(cand.rhs)
            r.parent_formula_ids.extend(parents)
            r.eliminated_symbol = elim_sym
            r.depth = depth
            r.new_edges.extend(new_edges(cand))
            r.tier = worst_tier(parents)
            res = _verify(cand, vals)
            if res is not None:
                r.residual = res
            return ev

        # ---- round 1: catalog pairs sharing a symbol, sharded by pair index
        ids = sorted(F)
        pair_idx = -1
        for a, b in itertools.combinations(ids, 2):
            pair_idx += 1
            if pair_idx % shard_count != shard_index:
                continue
            if out_of_budget():
                truncated = True
                break
            shared = (_syms(F[a].lhs - F[a].rhs) & _syms(F[b].lhs - F[b].rhs)) - NEVER_ELIMINATE
            if not shared:
                continue
            stats["pairs"] += 1
            for s in sorted(shared):
                stats["eliminations"] += 1
                sym = Symbol(s)
                cands = _eliminate(F[a], F[b], sym) or _eliminate(F[b], F[a], sym)
                for c in cands:
                    ev = consider(c, (a, b), s, 1)
                    if ev is not None:
                        yield ev

        # ---- round 2: recombine this shard's best bridge survivors with the catalog
        if not truncated:
            def rank_key(t):
                eq = t[0]
                return (0 if new_edges(eq) else 1, len(_syms(eq.lhs - eq.rhs)),
                        count_ops(eq.lhs - eq.rhs))

            seeds = sorted((t for t in found if new_edges(t[0])), key=rank_key)[:DEPTH2_SEEDS]
            for (eq1, parents1), fid in itertools.product(seeds, ids):
                if out_of_budget():
                    truncated = True
                    break
                shared = (_syms(eq1.lhs - eq1.rhs)
                          & _syms(F[fid].lhs - F[fid].rhs)) - NEVER_ELIMINATE
                if fid in parents1 or not shared:
                    continue
                for s in sorted(shared):
                    stats["eliminations"] += 1
                    for c in _eliminate(F[fid], eq1, Symbol(s)):
                        ev = consider(c, tuple(parents1) + (fid,), s, 2)
                        if ev is not None:
                            yield ev

        final = SynthesizeEvent(truncated=truncated)
        fs = final.final_stats
        fs.pairs = stats["pairs"]
        fs.eliminations = stats["eliminations"]
        fs.candidates = stats["candidates"]
        fs.tautologies = stats["tautologies"]
        fs.known = stats["known"]
        fs.dupes = stats["dupes"]
        fs.kept = stats["kept"]
        yield final
