"""Stable machine-facing agent API for py3plex workflows."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from py3plex.core import multinet
from py3plex.dsl.builder import L, Q
from py3plex.dsl.result import QueryResult


def _extract_replay_payload(result: QueryResult) -> Dict[str, Any]:
    prov = result.provenance or {}
    query_info = prov.get("query", {}) if isinstance(prov, dict) else {}
    return {
        "is_replayable": result.is_replayable,
        "seed": (prov.get("randomness", {}) or {}).get("seed")
        if isinstance(prov, dict)
        else None,
        "ast_hash": query_info.get("ast_hash"),
        "network_fingerprint": prov.get("network_fingerprint") if isinstance(prov, dict) else None,
        "network_version": prov.get("network_version") if isinstance(prov, dict) else None,
    }


def _as_agent_response(
    *,
    result: QueryResult,
    assumptions: Optional[List[str]] = None,
    warnings: Optional[List[Dict[str, Any]]] = None,
    export_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "status": "ok",
        "assumptions": assumptions or [],
        "warnings": warnings if warnings is not None else result.meta.get("warnings", []),
        "result": result.canonical_export_dict(),
        "provenance": result.meta.get("provenance", {}),
        "replay": _extract_replay_payload(result),
        "export_paths": export_paths or [],
    }


def load_network_from_path(
    path: str, *, input_type: str = "edgelist", directed: bool = False
) -> Dict[str, Any]:
    """Load a network from path and return stable machine-facing payload."""
    net = multinet.multi_layer_network(directed=directed)
    net.load_network(path, input_type=input_type)
    layers = list(net.get_layers())
    return {
        "status": "ok",
        "assumptions": ["Network path is trusted and readable."],
        "warnings": [],
        "result": {
            "network": net,
            "network_stats": {
                "node_replicas": len(list(net.get_nodes())),
                "edges": len(list(net.get_edges())),
                "layers": layers,
                "layer_count": len(layers),
            },
        },
        "provenance": {"source_path": path, "input_type": input_type, "directed": directed},
        "replay": {},
        "export_paths": [],
    }


def top_hubs_by_layer(
    network: Any,
    *,
    top_k: int = 10,
    measure: str = "degree",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Compute per-layer hubs with reproducible defaults."""
    query = (
        Q.nodes()
        .from_layers(L["*"])
        .compute(measure, kind="aggregate")
        .per_layer()
        .top_k(top_k, measure)
        .provenance(mode="replayable", seed=seed)
    )
    result = query.execute(network)
    return _as_agent_response(
        result=result,
        assumptions=[
            "Top-k is applied independently per layer.",
            "Degree kind defaults to aggregate unless explicitly overridden.",
        ],
    )


def uncertainty_centrality(
    network: Any,
    *,
    measures: Optional[List[str]] = None,
    method: str = "bootstrap",
    n_samples: int = 50,
    ci: float = 0.95,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Compute uncertainty-aware centrality with structured output."""
    measures = measures or ["pagerank"]
    query = (
        Q.nodes()
        .compute(*measures)
        .uq(method=method, n_samples=n_samples, ci=ci, seed=seed)
        .provenance(mode="replayable", seed=seed)
    )
    result = query.execute(network)
    return _as_agent_response(
        result=result,
        assumptions=["Uncertainty summaries use canonical mean/std/CI schema."],
    )


def community_detection_with_uq(
    network: Any,
    *,
    method: str = "leiden",
    n_samples: int = 20,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Run reproducible community detection with UQ."""
    query = (
        Q.nodes()
        .community(method=method, random_state=seed)
        .uq(method="seed", n_samples=n_samples, seed=seed)
        .provenance(mode="replayable", seed=seed)
    )
    result = query.execute(network)
    return _as_agent_response(
        result=result,
        assumptions=["Community uncertainty is estimated via seed ensemble."],
    )


def temporal_slice(
    network: Any,
    *,
    t_start: Optional[float] = None,
    t_end: Optional[float] = None,
    at: Optional[float] = None,
) -> Dict[str, Any]:
    """Run temporal slice query with structured result contract."""
    query = Q.edges()
    assumptions = []
    if at is not None:
        query = query.at(float(at))
        assumptions.append("Temporal query uses point-in-time snapshot semantics.")
    else:
        if t_start is None or t_end is None:
            raise ValueError("Provide either 'at' or both 't_start' and 't_end'.")
        query = query.during(float(t_start), float(t_end))
        assumptions.append("Temporal query uses inclusive time window semantics.")
    result = query.execute(network)
    return _as_agent_response(result=result, assumptions=assumptions)


def reproducible_export_bundle(
    result: QueryResult, *, path: str, compress: bool = True
) -> Dict[str, Any]:
    """Export replay bundle and return stable path metadata."""
    out_path = str(Path(path))
    result.export_bundle(out_path, compress=compress)
    return _as_agent_response(
        result=result,
        assumptions=["Bundle includes provenance metadata for replay."],
        export_paths=[out_path],
    )


def compare_networks(
    network_a: Any,
    network_b: Any,
    *,
    measure: str = "degree",
) -> Dict[str, Any]:
    """Compare two networks via shared machine-facing summary metric."""
    res_a = Q.nodes().compute(measure).execute(network_a)
    res_b = Q.nodes().compute(measure).execute(network_b)
    vals_a = res_a.attributes.get(measure, {})
    vals_b = res_b.attributes.get(measure, {})
    mean_a = sum(vals_a.values()) / len(vals_a) if vals_a else 0.0
    mean_b = sum(vals_b.values()) / len(vals_b) if vals_b else 0.0
    return {
        "status": "ok",
        "assumptions": ["Comparison uses simple mean of selected metric over node replicas."],
        "warnings": [],
        "result": {
            "metric": measure,
            "mean_a": mean_a,
            "mean_b": mean_b,
            "delta": mean_b - mean_a,
            "count_a": len(vals_a),
            "count_b": len(vals_b),
        },
        "provenance": {},
        "replay": {},
        "export_paths": [],
    }


def summarize_result(result: QueryResult) -> Dict[str, Any]:
    """Return compact structured summary for a QueryResult."""
    return {
        "status": "ok",
        "assumptions": [],
        "warnings": result.meta.get("warnings", []),
        "result": result.summary_dict(),
        "provenance": result.meta.get("provenance", {}),
        "replay": _extract_replay_payload(result),
        "export_paths": [],
    }
