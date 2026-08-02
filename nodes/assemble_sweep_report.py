from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_constants_messages_pb2 import SweepReport


def assemble_sweep_report(ax: AxiomContext, input: SweepReport) -> SweepReport:
    """Fan-in terminal of the full-sweep flow: takes the per-engine report fields
    (filled by the incoming edges) and returns the same SweepReport with the
    markdown_summary rendered."""
    m = SweepReport()
    m.CopyFrom(input)
    lines = ["# Formularium full-sweep report", ""]
    v = m.validation
    lines.append(f"- **Validation**: {'PASSED' if v.passed else 'FAILED'} "
                 f"({v.n_constants} constants, {v.n_quantities} quantities, "
                 f"{v.n_formulas} formulas, {len(v.issues)} issue(s))")
    lines.append(f"- **Dimensions**: {len(m.dimensions.checks)} formulas checked, "
                 f"{m.dimensions.n_inconsistent} inconsistent")
    lines.append(f"- **Units**: {len(m.units.checks)} constants checked, "
                 f"{m.units.n_mismatches} mismatch(es)")
    lines.append(f"- **Graph**: {len(m.graph.nodes)} nodes, {len(m.graph.edges)} edges")
    lines.append(f"- **Buckingham**: {len(m.buckingham.catalog_mode)} catalog sets, "
                 f"{len(m.buckingham.classic_mode)} classic sets")
    lines.append(f"- **Derivations**: {len(m.derive.derivations)} curated eliminations")
    lines.append(f"- **Discovery**: {len(m.discover.named_hypothesis_lines)} named hypotheses, "
                 f"{len(m.discover.candidates)} orphan scan candidates")
    top = m.structure.centrality[0].node if m.structure.centrality else "n/a"
    lines.append(f"- **Structure**: top bridge `{top}`, "
                 f"{len(m.structure.articulation_points)} articulation points")
    m.markdown_summary = "\n".join(lines) + "\n"
    return m
