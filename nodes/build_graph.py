from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_constants_messages_pb2 import Catalog, GraphReport
from nodes import catalog_lib


def nx_graph(cat: catalog_lib.Cat):
    """The exact relationship graph: constants/quantities as nodes, formulas linked
    to every symbol they involve (shared by BuildGraph and AnalyzeStructure)."""
    import networkx as nx

    G = nx.Graph()
    for c in cat.constants.values():
        G.add_node(c.symbol, kind="constant")
    for q in cat.quantities.values():
        if q.symbol not in G:
            G.add_node(q.symbol, kind="quantity")
    for f in cat.formulas.values():
        G.add_node(f.id, kind="formula")
        for s in f.symbols:
            if s in G and s != f.id:
                G.add_edge(f.id, s, relation="involves")
    return G


def build_graph(ax: AxiomContext, input: Catalog) -> GraphReport:
    """Build the exact bipartite relationship map of the catalog: formula nodes
    linked to every constant/quantity symbol they involve, plus a markdown digest."""
    cat = catalog_lib.decode(input)
    G = nx_graph(cat)
    m = GraphReport()
    for n, d in sorted(G.nodes(data=True)):
        m.nodes.add(id=n, kind=d.get("kind", ""))
    for u, v in sorted(G.edges()):
        m.edges.add(source=u, target=v)

    lines = ["# Formularium catalog digest", "",
             f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges "
             f"({len(cat.formulas)} formulas, {len(cat.constants)} constants, "
             f"{len(cat.quantities)} quantities).", "", "## Constants"]
    for c in sorted(cat.constants.values(), key=lambda c: c.symbol):
        tag = "dimensionless" if c.mass_dim == 0 else f"mass_dim {c.mass_dim:g}"
        lines.append(f"- **{c.symbol}** ({c.name}): {c.value:g} {c.unit} [{tag}, {c.source}]")
    lines += ["", "## Formulas (relationships)"]
    for f in sorted(cat.formulas.values(), key=lambda f: f.id):
        lines.append(f"- **{f.name}**: `{f.expression}` relates {', '.join(f.symbols)}. [{f.tier}]")
    m.digest_markdown = "\n".join(lines) + "\n"
    return m
