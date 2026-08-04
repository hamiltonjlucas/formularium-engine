from gen.axiom_context import AxiomContext
from gen.hamiltonjlucas_formularium_types_messages_pb2 import Catalog, StructureReport
from nodes import catalog_lib
from nodes.build_graph import nx_graph

TOP_N = 12


def analyze_structure(ax: AxiomContext, input: Catalog) -> StructureReport:
    """Graph-theoretic interrogation of the relationship map: betweenness centrality
    (which nodes the connectivity of physics routes through), articulation points
    (cut vertices), and what removing each top bridge severs from the main web."""
    import networkx as nx

    cat = catalog_lib.decode(input)
    G = nx_graph(cat)
    bt = nx.betweenness_centrality(G)
    arts = set(nx.articulation_points(G))
    top = sorted(bt.items(), key=lambda kv: -kv[1])[:TOP_N]
    main_before = max(nx.connected_components(G), key=len) if G.number_of_nodes() else set()

    m = StructureReport()
    for node, b in sorted(bt.items(), key=lambda kv: -kv[1]):
        if b == 0 and node not in arts:
            continue
        m.centrality.add(node=node, betweenness=b, articulation_point=node in arts)
    m.articulation_points.extend(sorted(arts))

    lines = ["# Structural analysis of the catalog graph", "",
             f"{G.number_of_nodes()} nodes / {G.number_of_edges()} edges, largest connected "
             f"component {len(main_before)} nodes, {len(arts)} articulation points.", "",
             "## Betweenness centrality — the bridges", "",
             "| rank | node | betweenness | cut vertex? |", "|---|---|---|---|"]
    for i, (n, b) in enumerate(top, 1):
        lines.append(f"| {i} | `{n}` | {b:.3f} | {'yes' if n in arts else 'no'} |")

    lines += ["", "## What the top bridges hold together", ""]
    for node, _b in top:
        if node not in arts:
            continue
        H = G.copy()
        H.remove_node(node)
        comps = sorted(nx.connected_components(H), key=len, reverse=True)
        severed = [sorted(c) for c in comps[1:] if c <= main_before]
        if not severed:
            continue
        lines.append(
            f"- `{node}` (degree {G.degree(node)}) severs {len(severed)} fragment(s): "
            + "; ".join(", ".join(f"`{x}`" for x in c) for c in severed[:6])
        )
    m.markdown = "\n".join(lines) + "\n"
    return m
