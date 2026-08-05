# CLI Tool Coverage Analysis and Implementation Plan

## Current State

The py3plex CLI tool (cli.py) currently has 17 commands covering basic functionality:

### Existing Commands (Comprehensive)
1. **create** - Create random multilayer networks (ER, BA, WS models) ✓
2. **load** - Load and inspect networks ✓
3. **community** - Community detection (Louvain, Infomap, Label Propagation) ✓
4. **centrality** - Node centrality measures (degree, betweenness, closeness, eigenvector, pagerank) ✓
5. **stats** - Multilayer network statistics (density, clustering, versatility, etc.) ✓
6. **visualize** - Network visualization (multiple layouts) ✓
7. **aggregate** - Aggregate multilayer to single layer ✓
8. **convert** - Format conversion (GraphML, GEXF, JSON, etc.) ✓
9. **query** - DSL queries (both legacy string and DSL v2 builder) ✓
10. **dsl-lint** - Static analysis of DSL queries ✓
11. **selftest** - Installation verification ✓
12. **quickstart** - Quick demo guide ✓
13. **run-config** - YAML/JSON workflow execution ✓
14. **tutorial** - Interactive tutorial ✓
15. **capabilities** - Runtime capability report ✓
16. **check** - File validation and linting ✓
17. **experiment** - Experiment tracking (via experiments.cli subparser) ✓
18. **out-of-core** - Out-of-core streaming queries (via out_of_core.cli subparser) ✓

## Missing Features (High Priority)

Based on AGENTS.md documentation and available library modules, the following major features are **not exposed via CLI**:

### 1. **Dynamics Simulations** (HIGH PRIORITY)
**Module:** `py3plex/dynamics/`
**Functionality:** Epidemic models (SIS, SIR, SEIR), custom processes
**Proposed command:** `py3plex dynamics`
```bash
# Example usage:
py3plex dynamics network.edgelist --model sir --beta 0.3 --gamma 0.1 --steps 100 --output results.json
py3plex dynamics network.edgelist --model sis --beta 0.3 --mu 0.1 --seed-fraction 0.01 --replicates 10
```

### 2. **Node Embeddings** (HIGH PRIORITY)
**Module:** `py3plex/embeddings/`, `py3plex/ml/embedding/`
**Functionality:** NetMF, MetaPath2Vec, Node2Vec embeddings
**Proposed command:** `py3plex embed`
```bash
# Example usage:
py3plex embed network.edgelist --method netmf --dimensions 128 --output embeddings.npy
py3plex embed network.edgelist --method metapath2vec --meta-path "ABA" --output embeddings.json
py3plex embed network.edgelist --method node2vec --p 1.0 --q 1.0 --walks 10
```

### 3. **Temporal Network Analysis** (MEDIUM PRIORITY)
**Module:** `py3plex/core/temporal_multinet.py`, `py3plex/temporal_utils.py`
**Functionality:** Temporal snapshots, windows, temporal queries
**Proposed command:** `py3plex temporal`
```bash
# Example usage:
py3plex temporal network.edgelist --snapshot 150.0 --output snapshot.json
py3plex temporal network.edgelist --window 100.0 --step 50.0 --output windows/
py3plex temporal network.edgelist --during 100.0 200.0 --compute degree
```

### 4. **Uncertainty Quantification** (MEDIUM PRIORITY)
**Module:** `py3plex/uncertainty/`
**Functionality:** Bootstrap, perturbation, confidence intervals
**Proposed command:** `py3plex uq`
```bash
# Example usage:
py3plex uq network.edgelist --metric betweenness --method bootstrap --samples 100 --output uq_results.json
py3plex uq network.edgelist --metric pagerank --method perturbation --samples 50 --ci 0.95
```

### 5. **Null Model Generation** (MEDIUM PRIORITY)
**Module:** `py3plex/nullmodels/`
**Functionality:** Configuration model, ER, edge swapping
**Proposed command:** `py3plex nullmodel`
```bash
# Example usage:
py3plex nullmodel network.edgelist --model configuration --samples 10 --output nullmodels/
py3plex nullmodel network.edgelist --model erdos_renyi --samples 5 --seed 42
```

### 6. **Network Comparison** (LOW PRIORITY)
**Module:** `py3plex/comparison/`
**Functionality:** Network similarity metrics, structural comparison
**Proposed command:** `py3plex compare`
```bash
# Example usage:
py3plex compare network1.edgelist network2.edgelist --metric multiplex_jaccard --output comparison.json
py3plex compare network1.edgelist network2.edgelist --metric edit_distance
```

### 7. **Path Finding** (LOW PRIORITY)
**Module:** `py3plex/semiring/`, `py3plex/paths/`
**Functionality:** Shortest paths, most reliable paths, semiring algebra
**Proposed command:** `py3plex paths`
```bash
# Example usage:
py3plex paths network.edgelist --source A --target B --semiring min_plus --output paths.json
py3plex paths network.edgelist --source A --semiring boolean --witness
```

### 8. **Counterexample Generation** (LOW PRIORITY)
**Module:** `py3plex/counterexamples/`
**Functionality:** Find violations of network claims
**Proposed command:** `py3plex counterexample`
```bash
# Example usage:
py3plex counterexample network.edgelist --claim "degree__ge(10) -> pagerank__rank_le(50)" --seed 42
```

### 9. **Meta-Analysis** (LOW PRIORITY)
**Module:** `py3plex/meta/`
**Functionality:** Meta-analytic pooling across networks
**Proposed command:** `py3plex meta`
```bash
# Example usage:
py3plex meta network1.edgelist network2.edgelist network3.edgelist --metric pagerank --model random --output meta_results.json
```

## Implementation Plan

### Phase 1: High Priority Commands (Current Focus)
1. **dynamics** - Epidemic simulations
2. **embed** - Node embeddings

### Phase 2: Medium Priority Commands
3. **temporal** - Temporal network analysis
4. **uq** - Uncertainty quantification
5. **nullmodel** - Null model generation

### Phase 3: Low Priority Commands (Future)
6. **compare** - Network comparison
7. **paths** - Path finding
8. **counterexample** - Counterexample generation
9. **meta** - Meta-analysis

## Testing Strategy

For each new command:
1. Add unit tests in `tests/test_cli.py`
2. Test both success and error cases
3. Test stdin piping support (where applicable)
4. Verify output formats (JSON, CSV)
5. Test with various network sizes and types

## Documentation Updates

For each new command:
1. Update AGENTS.md with CLI examples
2. Update --help text with clear examples
3. Add to quickstart guide if appropriate
4. Document in main README.md

## Next Steps

1. Implement `dynamics` command (Phase 1 - High Priority)
2. Add comprehensive tests for dynamics
3. Implement `embed` command (Phase 1 - High Priority)
4. Add comprehensive tests for embeddings
5. Move to Phase 2 commands based on user feedback
