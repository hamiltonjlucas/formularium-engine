# formularium-engine

**Formularium** discovery/analysis engines as [Axiom](https://dev.axiomide.com) nodes,
operating on the assembled physics catalog (see `formularium-types` for the contracts and
the `catalog-assemble` flow for assembly). Ported from the file-based *unified-theory*
engine suite, preserving its honesty rules.

| Node | What it does |
|---|---|
| `AssembleCatalog` | fan-in merge of the constants + 8 domain catalog slices into one `Catalog` |
| `ValidateCatalog` | duplicate ids, tier/source whitelists, cross-package symbol resolution |
| `CheckDimensions` | every formula balances in natural-units mass dimension (ħ = c = 1) |
| `CheckUnits` | unit-string-derived mass dimension vs stored annotation, per constant |
| `BuildGraph` | the exact bipartite relationship map (formulas ↔ symbols) + digest |
| `AnalyzeStructure` | betweenness centrality, articulation points, what each bridge severs |
| `DeriveRelations` | curated symbolic eliminations, numerically verified in natural units |
| `DiscoverRelations` | orphan-constant relation search: pre-registered hypotheses, blind σ-scored scan with look-elsewhere accounting, PSLQ validation |
| `Buckingham` | independent dimensionless groups (catalog + classic full-SI modes, self-validated) |
| `SynthesizeRelations` | *pipeline node*: exhaustive pairwise formula elimination, streamed as found; deterministic sharding + wall-clock budget |
| `AssembleSweepReport` | fan-in terminal of the full-sweep flow; renders the summary |

Honesty rules carried over: synthesized relations inherit the **weakest parent tier**;
ħ/c/k_B are never eliminated (they'd fabricate bridges); discovery scores against
**measurement uncertainty** with look-elsewhere accounting, never exact-relation
precision; synthesis is cartographic — it creates no information, only makes implicit
bridges explicit.

Part of the [Formularium](https://github.com/hamiltonjlucas/formularium) project.
License: Apache-2.0.
