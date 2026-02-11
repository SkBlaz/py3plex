# DSL Zoo: Runnable Examples for Multilayer Network Analysis

This directory contains 61 runnable examples demonstrating the full multilayer analysis surface of py3plex using single-invocation DSL calls.

## Overview

Each example demonstrates a specific DSL feature with:
- Minimal imports and network creation
- **Exactly one** DSL chain ending in `.execute(net)` or `.execute(tnet)`
- Minimal output (typically `print(result.to_pandas().head())` or equivalent)
- Fast execution (<3 seconds typical runtime)

## Examples by Category

### Layer Algebra and Selection (01-04)
- `01_per_layer_top_hubs.py` - Golden Path: Per-layer grouping, multi-metric compute, top-k selection
- `02_union_layers_centrality.py` - Layer union with L["social"] + L["work"]
- `03_difference_layers.py` - Layer difference with L["*"] - L["coupling"]
- `04_intersection_layers.py` - Layer intersection with L["gene"] & L["drug"]

### Node Queries and Filtering (05-07)
- `05_node_filtering_compute.py` - Attribute filtering with where(degree__gt=5)
- `06_multi_metric_select.py` - Multi-metric computation with column selection
- `07_per_layer_multi_metric.py` - Per-layer multi-metric with top-k by pagerank

### Edge Queries and Aggregation (08-12)
- `08_edge_counts_per_layer_pair.py` - Edge counts grouped by (src_layer, dst_layer)
- `09_intra_layer_edges.py` - Intra-layer edges using where(intralayer=True)
- `10_inter_layer_edges.py` - Inter-layer edges using where(interlayer=True)
- `11_interlayer_specific_pair.py` - Specific layer pair with where(interlayer=("gene","disease"))
- `12_edge_weight_summary.py` - Per-layer-pair aggregation with summarise()

### Temporal Network Queries (13-14, 27)
- `13_temporal_during_interval.py` - Filter edges during time interval using .during(t0, t1)
- `14_temporal_sliding_windows.py` - Sliding window aggregation with .window(size, step)
- `27_temporal_at_time.py` - Query network at specific time point with .at(t)

### Uncertainty Quantification (15-16, 42)
- `15_uq_pagerank_bootstrap.py` - Bootstrap uncertainty for pagerank with confidence intervals
- `16_uq_per_layer_ranking.py` - Per-layer UQ with seed method, showing expanded uncertainty
- `42_compositional_uq.py` - Compositional UQ with aggregate operations (per-layer mean/max with uncertainty)

### Community Detection (17-21)
- `17_community_attach.py` - Attach community partition to network with .community()
- `18_query_communities.py` - Query communities via Q.communities() with summarise
- `19_community_uq.py` - Community detection with uncertainty quantification
- `20_auto_community_shortcut.py` - AutoCommunity DSL shortcut with auto_select()
- `21_auto_community_flagship.py` - Full AutoCommunity with Pareto + null calibration

### Advanced Features (22-25)
- `22_null_model_testing.py` - Null model generation using N.configuration()
- `23_pattern_matching.py` - Cypher-like pattern matching with Q.pattern()
- `24_semiring_closure.py` - Semiring algebra closure computation with S.closure()
- `25_arrow_export.py` - Export query results to Apache Arrow format

### Extended DSL Features (26-35)
- `26_coverage_cross_layer.py` - Cross-layer coverage filtering with .coverage(mode="all")
- `28_field_expressions.py` - Complex filtering with F expressions (F.degree > 2) & (F.clustering < 0.5)
- `29_parameterized_queries.py` - Parameterized queries with Param placeholders
- `30_column_rename_drop.py` - Column manipulation with .rename() and .drop()
- `31_network_comparison.py` - Network comparison using C.compare()
- `32_shortest_paths.py` - Path queries with P.shortest()
- `33_zscore_normalization.py` - Z-score normalization per layer with .zscore()
- `34_random_sampling.py` - Random sampling of results with .sample()
- `35_distinct_unique.py` - Get unique/distinct rows with .distinct()

### Stochastic Block Models (36-41)
- `36_sbm_basic.py` - Basic SBM inference with automatic K selection
- `37_sbm_degree_corrected.py` - Degree-corrected SBM (DC-SBM) for heterogeneous networks
- `38_sbm_mixed_membership.py` - Mixed-membership SBM with overlapping communities
- `39_sbm_multilayer_shared.py` - Multilayer SBM with shared memberships
- `40_sbm_multilayer_coupled.py` - Multilayer SBM with layer coupling
- `41_autocommunity_with_sbm.py` - AutoCommunity with SBM as candidate algorithm
- `42_compositional_uq.py` - Compositional UQ with per-layer aggregates and ranking stability

### Dplyr-Style Operations (43-52)
- `43_mutate_transform.py` - Transform and add columns with .mutate() lambda expressions
- `44_arrange_sort.py` - Sort results with .arrange() (alias for .order_by())
- `45_filter_alias.py` - Filter rows with .filter() (alias for .where())
- `46_filter_expr_string.py` - String-based filter expressions with .filter_expr()
- `47_tail_last_n.py` - Get last n items with .tail()
- `48_slice_range.py` - Array slicing with .slice(start, end)
- `49_first_item.py` - Get first item with .first()
- `50_last_item.py` - Get last item with .last()
- `51_pluck_column.py` - Extract single column with .pluck()
- `52_collect_noop.py` - No-op .collect() for API compatibility

### Ergonomic Features (53-57)
- `53_hint_suggestions.py` - Interactive query building with .hint() suggestions
- `54_explain_query.py` - Human-readable query explanation with .explain()
- `55_debug_technical.py` - Technical debugging information with .debug()
- `56_provenance_metadata.py` - Access provenance metadata for reproducibility
- `57_replay_provenance.py` - Replay queries from provenance metadata

### Export Formats (58-60)
- `58_export_networkx.py` - Export results to NetworkX graphs with .to_networkx()
- `59_export_json.py` - Export results to JSON format with .to_json()
- `60_export_csv.py` - Export results to CSV files with .to_csv()

### Advanced Transformations (61)
- `61_normalize_columns.py` - Column normalization and transformation utilities

## Running Examples

```bash
# Run a single example
uv run python examples/dsl_zoo/01_per_layer_top_hubs.py

# Run all examples
for f in examples/dsl_zoo/*.py; do
    echo "Running $f..."
    uv run python "$f"
done
```

## Key DSL Features Demonstrated

### Layer Algebra
- `L["*"]` - All layers
- `L["a"] + L["b"]` - Union of layers
- `L["a"] - L["b"]` - Difference
- `L["a"] & L["b"]` - Intersection
- `L["* - coupling"]` - String expressions

### Grouping and Aggregation
- `.per_layer()` - Group nodes by layer
- `.per_layer_pair()` - Group edges by (src_layer, dst_layer)
- `.summarise(count="n()", mean_w="mean(weight)")` - Aggregation expressions
- `.top_k(k, "metric")` - Top-k per group
- `.end_grouping()` - End grouping context

### Special Predicates
- `.where(intralayer=True)` - Filter to intra-layer edges
- `.where(interlayer=True)` - Filter to any inter-layer edges
- `.where(interlayer=("A", "B"))` - Filter to specific layer pair

### Temporal Queries
- `.during(t0, t1)` - Time range filter
- `.window(size=100.0, step=50.0, aggregation="list")` - Sliding windows

### Uncertainty Quantification
- `.uq(method="bootstrap", n_samples=100, ci=0.95, seed=42)`
- Methods: bootstrap, perturbation, seed
- Expandable uncertainty in to_pandas(expand_uncertainty=True)

### Community Detection
- `.community(method="leiden", gamma=1.0, omega=1.0)` - Attach partition
- `Q.communities(partition="name")` - Query communities
- `.auto_select(fast=True, seed=42)` - AutoCommunity shortcut
- `AutoCommunity().candidates(...).metrics(...).pareto()` - Full pipeline

## Design Principles

1. **Single Invocation**: Each example has exactly one `.execute()` call
2. **Self-Contained**: Minimal dependencies, in-script network creation
3. **Fast**: All examples run in <3 seconds
4. **Demonstrative**: Clear focus on one DSL feature per example
5. **Spec-Aligned**: Uses canonical method names from AGENTS.md specification

## Notes

- Examples use small toy networks for speed and clarity
- Some temporal/advanced features may have simplified implementations
- For production use, refer to full documentation in AGENTS.md
- All examples follow the py3plex coding conventions (see .github/copilot-instructions.md)
