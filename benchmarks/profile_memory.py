"""Profile Linux process memory. Set PYTHONPATH to the checkout under test."""

import argparse
import csv
import gc
import hashlib
from itertools import islice
import gzip
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

CASES = (
    "temporal",
    "temporal_packed",
    "bootstrap",
    "noop",
    "build",
    "degree",
    "cache_hit",
    "cache_stream",
    "supra",
    "supra_direct",
    "capture",
    "gzip",
    "gzip_stream",
    "pandas",
    "arrow",
    "networkx",
    "netmf",
    "netmf_sparse",
    "ooc_file_coverage",
    "ooc_all",
    "ooc_stream",
    "ooc_top",
    "ooc_coverage",
    "cache_churn",
)


def rss_kib(field="VmRSS"):
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(field + ":"):
            return int(line.split()[1])
    raise RuntimeError(f"Missing {field} in /proc/self/status")


def rows(n):
    # Four layers, one ring, two chords and one cross-layer edge per replica.
    for layer in range(4):
        for i in range(n):
            for step in (1, 7, 19):
                yield str(i), str(layer), str((i + step) % n), str(layer), 1.0
            yield str(i), str(layer), str(i), str((layer + 1) % 4), 1.0


def import_case(case, mode):
    import importlib

    targets = {
        "import_package": "py3plex",
        "import_core": "py3plex.core.multinet",
        "import_dsl": "py3plex.dsl",
    }
    gc.collect()
    if mode == "trace":
        tracemalloc.start()
    Path("/proc/self/clear_refs").write_text("5")
    before = rss_kib()
    start = time.perf_counter_ns()
    importlib.import_module(targets[case])
    ms = (time.perf_counter_ns() - start) / 1e6
    live, peak = tracemalloc.get_traced_memory()
    peak_rss = rss_kib("VmHWM")
    live_rss = rss_kib()
    gc.collect()
    print(
        json.dumps(
            {
                "case": case,
                "n": 0,
                "mode": mode,
                "ms": ms,
                "baseline_kib": before,
                "peak_delta_kib": max(0, peak_rss - before),
                "live_delta_kib": live_rss - before,
                "live_bytes": live,
                "peak_bytes": peak,
                "after_gc_bytes": tracemalloc.get_traced_memory()[0],
                "after_gc_delta_kib": rss_kib() - before,
                "loaded": [
                    m
                    for m in (
                        "numpy",
                        "scipy",
                        "networkx",
                        "matplotlib.pyplot",
                        "pandas",
                        "sklearn",
                        "pyarrow",
                    )
                    if m in sys.modules
                ],
            }
        ),
        flush=True,
    )


def worker(case, n, mode, directory):
    if case.startswith("import_"):
        return import_case(case, mode)
    import numpy as np
    import pandas as pd
    import pyarrow as pa
    from scipy import sparse

    from py3plex.core.multinet import multi_layer_network
    from py3plex.dsl import Q
    from py3plex.dsl.program.cache import get_global_cache
    from py3plex.out_of_core.network import OutOfCoreNetwork
    from py3plex.provenance.capture import capture_network, compress_snapshot

    def build():
        graph = multi_layer_network(directed=False, verbose=False)
        for u, source_layer, v, target_layer, weight in rows(n):
            graph.add_edges(
                [[u, source_layer, v, target_layer, weight]], input_type="list"
            )
        return graph

    def degree():
        return Q.nodes().compute("degree").execute(net, progress=False)

    def direct():
        # Only the undirected unit-weight fixture. Mirror off-diagonal entries.
        graph = net.core_network
        ids = {node: i for i, node in enumerate(graph)}
        e = graph.number_of_edges()
        src = np.empty(2 * e, dtype=np.int32)
        dst = np.empty_like(src)
        weights = np.empty(2 * e)
        used = 0
        for u, v, data in graph.edges(data=True):
            a, b = ids[u], ids[v]
            src[used], dst[used], weights[used] = a, b, data["weight"]
            used += 1
            if a != b:
                src[used], dst[used], weights[used] = b, a, data["weight"]
                used += 1
        return sparse.coo_matrix(
            (weights[:used], (src[:used], dst[:used])), shape=(len(ids), len(ids))
        ).tocsr()

    def streamed_gzip():
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8") as stream:
                json.dump(snapshot, stream, default=str)
        return buf.getvalue()

    def ppmi(adj):
        degree = np.asarray(adj.sum(axis=1)).ravel()
        inverse = sparse.diags(1.0 / np.where(degree == 0, 1.0, degree))
        transition = inverse @ adj
        context = (((transition + transition @ transition) / 2) @ inverse).tocsr()
        context.data *= float(adj.sum())
        np.maximum(context.data, 1.0, out=context.data)
        np.log(context.data, out=context.data)
        context.eliminate_zeros()
        return context

    def sparse_embedding():
        from sklearn.utils.extmath import randomized_svd

        matrix = ppmi(adj)
        state = int(np.random.default_rng(42).integers(0, 2**31))
        u, singular, _ = randomized_svd(matrix, n_components=8, random_state=state)
        return (u * np.sqrt(singular)).astype(np.float32)

    def file_coverage(k=5):
        import sqlite3
        from py3plex.out_of_core.executor import QueryResultOutOfCore
        from py3plex.out_of_core.readers import make_edge_reader

        def scan():
            return make_edge_reader(disk.edges_path, disk.edges_format).scan()

        def key(row):
            return tuple(sorted((row["source"], row["target"])))

        dbfile = directory / "keys.sqlite"
        conn = sqlite3.connect(dbfile)
        try:
            conn.execute("PRAGMA cache_size=-1024")
            conn.execute("PRAGMA temp_store=FILE")
            conn.execute(
                "CREATE TABLE keys (u,v,l,m,PRIMARY KEY(u,v,l,m)) WITHOUT ROWID"
            )
            conn.executemany(
                "INSERT OR IGNORE INTO keys VALUES (?,?,?,?)",
                (
                    (*key(row), row["source_layer"], row["target_layer"])
                    for row in scan()
                ),
            )
            conn.execute("CREATE TABLE good (u,v, PRIMARY KEY(u,v)) WITHOUT ROWID")
            conn.execute(
                "INSERT INTO good SELECT u,v FROM keys GROUP BY u,v HAVING COUNT(*)>=?",
                (k,),
            )
            conn.commit()
            items, weights = [], []
            if conn.execute("SELECT 1 FROM good LIMIT 1").fetchone():
                for row in scan():
                    if conn.execute(
                        "SELECT 1 FROM good WHERE u=? AND v=?", key(row)
                    ).fetchone():
                        items.append(
                            (
                                row["source"],
                                row["target"],
                                row["source_layer"],
                                row["target_layer"],
                            )
                        )
                        weights.append(row["weight"])
            return QueryResultOutOfCore(
                target="edges",
                items=items,
                attributes={"weight": weights} if items else {},
            )
        finally:
            conn.close()

    def streamed_fingerprint(network):
        """Emit the baseline JSON type tags one node/edge record at a time."""
        from py3plex.dsl.program.cache import _cache_value

        graph = network.core_network
        assert not network.list_partitions()
        h = hashlib.sha256()

        def emit(record):
            h.update(json.dumps(_cache_value(record), allow_nan=False).encode())

        h.update(b'["tuple", [')
        for field in (
            type(graph).__name__,
            network.directed,
            network.network_type,
            network.network_version,
            network.coupling_weight,
            network.layers,
            getattr(network, "temporal_edges", None),
            graph.graph,
        ):
            emit(field)
            h.update(b", ")
        for records in (graph.nodes(data=True), graph.edges(keys=True, data=True)):
            h.update(b'["list", [')
            for i, record in enumerate(records):
                if i:
                    h.update(b", ")
                emit(record)
            h.update(b"]], ")
        emit([])
        h.update(b"]]")
        return h.hexdigest()

    def churn():
        for seed in range(8):
            program.execute(net, seed=seed, progress=False, cache_policy="enabled")
        return cache.size()

    cache = get_global_cache()
    cache.clear()
    if case == "cache_churn_bounded":
        cache.max_entries = 2
    if case not in ("noop", "build") and not case.startswith(
        ("ooc_", "temporal", "mlking")
    ):
        net = build()
    if case.startswith("temporal"):
        from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork

        events = TemporalMultiLayerNetwork()
        times = np.arange(16 * n) // 2  # tied timestamps and shuffled insertion
        np.random.default_rng(42).shuffle(times)
        for i, t in enumerate(times):
            events.add_edge(str(i % n), "a", str((i + 1) % n), "a", float(t))

        def packed_window():
            stamps = np.fromiter(
                (iv.start for _, iv in events._events),
                dtype=np.float64,
                count=len(times),
            )
            order = np.argsort(stamps, kind="stable")
            sorted_stamps = stamps[order]
            # Hold both arrays for future queries just as the library holds its index.
            events._packed_probe = (sorted_stamps, order)
            lo = sorted_stamps.searchsorted(10)
            hi = sorted_stamps.searchsorted(20, side="right")
            return [events._events[i][0] for i in np.sort(order[lo:hi])]

    if case.startswith("netmf"):
        from py3plex.embeddings.netmf import _build_union_adjacency, _netmf_embed

        adj, _ = _build_union_adjacency(net, list(net.get_nodes()))
    if case in ("pandas", "arrow", "networkx"):
        result = degree()
        assert result.count == 4 * n
        # Exclude one-time pandas/Arrow adapter initialization from the export.
        pa.table({"x": [1]})
        pd.DataFrame({"x": [1]})
    if case in ("gzip", "gzip_stream"):
        snapshot = capture_network(net).to_dict()
    if case in ("cache_hit", "cache_stream", "cache_churn", "cache_churn_bounded"):
        program = Q.nodes().compute("degree").compile()
        if case in ("cache_hit", "cache_stream"):
            if case == "cache_stream":
                from py3plex.dsl.program import cache as cache_module

                if mode == "verify":
                    assert streamed_fingerprint(net) == cache_module.graph_fingerprint(
                        net
                    )
                # Isolated worker. Warm the same production cache key using the
                # reference implementation before installing the measured probe.
            program.execute(net, seed=42, progress=False, cache_policy="enabled")
            if case == "cache_stream":
                cache_module.graph_fingerprint = streamed_fingerprint
    if case.startswith(("ooc_", "mlking")):
        path = directory / "edges.csv"
        with path.open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                ("source", "source_layer", "target", "target_layer", "weight")
            )
            if case.startswith("mlking"):
                data = Path("multilayer_datasets/MLKing/MLKing2013_multiplex.edges")
                with data.open() as source:
                    for line in islice(source, 0, 4 * n, 4):
                        layer, u, v, weight = line.split()
                        writer.writerow((u, layer, v, layer, weight))
            else:
                writer.writerows(rows(n))
        disk = OutOfCoreNetwork.from_edges_csv(str(path), workdir=str(directory))

        def stream_rows():
            from py3plex.out_of_core.readers import make_edge_reader
            from py3plex.out_of_core.executor import QueryResultOutOfCore

            items, weights = [], []
            for row in make_edge_reader(disk.edges_path, disk.edges_format).scan():
                items.append(
                    (
                        row["source"],
                        row["target"],
                        row["source_layer"],
                        row["target_layer"],
                    )
                )
                weights.append(row["weight"])
            return QueryResultOutOfCore(
                target="edges", items=items, attributes={"weight": weights}
            )

    operations = {
        "noop": lambda: None,
        "build": build,
        "degree": degree,
        "cache_hit": lambda: program.execute(
            net, seed=42, progress=False, cache_policy="enabled"
        ),
        "supra": lambda: net.get_supra_adjacency_matrix(),
        "supra_direct": direct,
        "capture": lambda: capture_network(net),
        "gzip": lambda: compress_snapshot(snapshot),
        "gzip_stream": streamed_gzip,
        "pandas": lambda: result.to_pandas(),
        "arrow": lambda: result.to_arrow(),
        "networkx": lambda: result.to_networkx(net),
        "ooc_all": lambda: disk.query_edges(),
        "ooc_top": lambda: disk.query_edges(order_by="-weight", limit=20),
        "ooc_coverage": lambda: disk.query_edges(coverage_k=5),
        "ooc_stream": lambda: stream_rows(),
        "mlking": lambda: disk.query_edges(coverage_k=2),
        "mlking_file": lambda: file_coverage(2),
        "temporal": lambda: list(events.edges_between(10, 20)),
        "temporal_packed": lambda: packed_window(),
        "bootstrap": lambda: Q.nodes()
        .compute("degree")
        .uq(method="bootstrap", n_samples=8, seed=42)
        .execute(net, progress=False),
        "cache_churn": churn,
        "cache_churn_bounded": churn,
        "ooc_file_coverage": file_coverage,
        "netmf": lambda: _netmf_embed(
            adj, dim=8, window=2, negative=1.0, approx="randomized_svd", seed=42
        ),
        "netmf_sparse": sparse_embedding,
    }
    operations["cache_stream"] = operations["cache_hit"]
    if mode == "verify":
        if case == "cache_stream":
            operations[case]()
            assert cache.statistics()["hits"] == 1
        elif case == "supra_direct":
            expected = net.get_supra_adjacency_matrix()
            assert (expected != direct()).nnz == 0
        elif case == "gzip_stream":
            assert gzip.decompress(streamed_gzip()) == gzip.decompress(
                compress_snapshot(snapshot)
            )
        elif case == "ooc_stream":
            full, streamed = disk.query_edges(), stream_rows()
            assert (
                full.items == streamed.items and full.attributes == streamed.attributes
            )
        elif case == "ooc_file_coverage":
            for threshold in (1, 4, 5):
                (directory / "keys.sqlite").unlink(missing_ok=True)
                full = disk.query_edges(coverage_k=threshold)
                probe = file_coverage(threshold)
                assert full.items == probe.items and full.attributes == probe.attributes
        elif case == "temporal_packed":
            assert packed_window() == list(events.edges_between(10, 20))
        elif case == "netmf_sparse":
            # Intercept the matrix supplied to sklearn by the library, then let
            # the original solver run so its output shape is also exercised.
            from unittest.mock import patch
            from sklearn.utils.extmath import randomized_svd

            def checked(matrix, **kwargs):
                np.testing.assert_allclose(
                    ppmi(adj).toarray(),
                    matrix.toarray() if sparse.issparse(matrix) else matrix,
                    atol=2e-6,
                    rtol=2e-6,
                )
                return randomized_svd(matrix, **kwargs)

            with patch("sklearn.utils.extmath.randomized_svd", checked):
                dense = operations["netmf"]()
            candidate = sparse_embedding()
            np.testing.assert_allclose(
                np.linalg.norm(candidate, axis=0),
                np.linalg.norm(dense, axis=0),
                rtol=5e-4,
            )
        else:
            raise ValueError("No prototype for " + case)
        print(json.dumps({"verified": case, "n": n}), flush=True)
        return
    if mode == "phases" and case == "bootstrap":
        from contextlib import ExitStack
        from functools import wraps
        from unittest.mock import patch
        from py3plex import uncertainty
        from py3plex.uncertainty import bootstrap as engine

        phases = []

        def measured(fn, label):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                start = tracemalloc.get_traced_memory()[0]
                tracemalloc.reset_peak()
                result = fn(*args, **kwargs)
                live, peak = tracemalloc.get_traced_memory()
                phases.append(dict(phase=label, start=start, live=live, peak=peak))
                return result

            return wrapped

        bootstrap_metric = uncertainty.bootstrap_metric

        def instrument_metric(*args, **kwargs):
            kwargs["metric_fn"] = measured(kwargs["metric_fn"], "metric")
            return bootstrap_metric(*args, **kwargs)

        with ExitStack() as stack:
            stack.enter_context(
                patch.object(uncertainty, "bootstrap_metric", instrument_metric)
            )
            stack.enter_context(
                patch.object(
                    engine,
                    "_resample_edges",
                    measured(engine._resample_edges, "sample"),
                )
            )
            stack.enter_context(
                patch.object(np, "quantile", measured(np.quantile, "quantile"))
            )
            gc.collect()
            tracemalloc.start()
            value = operations[case]()
            assert value.count == 4 * n
        print(json.dumps({"case": case, "n": n, "phases": phases}))
        return
    gc.collect()
    if mode == "trace":
        tracemalloc.start()
    # Reset Linux's process high-water mark after imports and fixture construction.
    Path("/proc/self/clear_refs").write_text("5")
    baseline = rss_kib()
    start = time.perf_counter_ns()
    value = operations[case]()
    elapsed_ms = (time.perf_counter_ns() - start) / 1e6
    live, peak = tracemalloc.get_traced_memory()
    peak_rss = rss_kib("VmHWM")
    live_rss = rss_kib()
    row = {
        "ms": elapsed_ms,
        "case": case,
        "n": n,
        "mode": mode,
        "baseline_kib": baseline,
        "peak_delta_kib": max(0, peak_rss - baseline),
        "live_delta_kib": live_rss - baseline,
        "peak_bytes": peak,
        "live_bytes": live,
    }
    # Inspect only after peak measurements. Avoid creating a second result here.
    if case in ("gzip", "gzip_stream"):
        row["output_bytes"] = len(value)
    elif case.startswith("temporal"):
        assert len(value) == 22
    elif case.startswith("mlking"):
        row["count"] = len(value.items)
        digest = hashlib.sha256()
        for item, weight in zip(value.items, value.attributes["weight"]):
            digest.update(json.dumps([item, weight]).encode())
        row["digest"] = digest.hexdigest()
    elif case.startswith("netmf"):
        assert value.shape == (n, 8) and np.isfinite(value).all()
    elif case.startswith("ooc_"):
        assert (
            len(value.items)
            == {
                "ooc_all": 16 * n,
                "ooc_stream": 16 * n,
                "ooc_top": 20,
                "ooc_coverage": 0,
                "ooc_file_coverage": 0,
            }[case]
        )
    elif case in ("supra", "supra_direct"):
        assert value.shape == (4 * n, 4 * n) and value.sum() == 32 * n
        row["csr_bytes"] = (
            value.data.nbytes + value.indices.nbytes + value.indptr.nbytes
        )
    elif case in ("degree", "cache_hit", "cache_stream", "bootstrap"):
        assert value.count == 4 * n
    elif case == "capture":
        assert len(value.nodes) == 4 * n and len(value.edges) == 16 * n
    elif case == "build":
        assert value.core_network.number_of_edges() == 16 * n
    elif case == "networkx":
        assert value.number_of_edges() == 16 * n
    elif case in ("pandas", "arrow"):
        assert len(value) == 4 * n
    elif case in ("cache_churn", "cache_churn_bounded"):
        assert value == (2 if case == "cache_churn_bounded" else 8)
    if case in ("cache_hit", "cache_stream"):
        assert cache.statistics()["hits"] == 1
    if case in ("ooc_file_coverage", "mlking_file"):
        row["scratch_bytes"] = (directory / "keys.sqlite").stat().st_size
    del value
    gc.collect()
    row["after_gc_bytes"] = tracemalloc.get_traced_memory()[0]
    row["after_gc_delta_kib"] = rss_kib() - baseline
    if case in ("cache_churn", "cache_churn_bounded"):
        cache.clear()
        gc.collect()
        row["after_clear_bytes"] = tracemalloc.get_traced_memory()[0]
        row["after_clear_delta_kib"] = rss_kib() - baseline
    print(json.dumps(row), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        nargs="+",
        choices=CASES
        + (
            "mlking",
            "mlking_file",
            "import_package",
            "import_core",
            "import_dsl",
            "cache_churn_bounded",
        ),
        default=list(CASES),
    )
    parser.add_argument("--sizes", nargs="+", type=int, default=[512, 2048])
    parser.add_argument("--rss-repeats", type=int, default=3)
    parser.add_argument("--worker", nargs=3, metavar=("CASE", "N", "MODE"))
    args = parser.parse_args()
    if args.worker:
        name, size, mode = args.worker
        with tempfile.TemporaryDirectory() as folder:
            worker(name, int(size), mode, Path(folder))
    else:
        env = dict(
            os.environ,
            PYTHONHASHSEED="0",
            OPENBLAS_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
            OMP_NUM_THREADS="1",
            MPLBACKEND="Agg",
        )
        for name in args.cases:
            for size in args.sizes:
                for mode in ["rss"] * args.rss_repeats + ["trace"]:
                    subprocess.run(
                        [sys.executable, __file__, "--worker", name, str(size), mode],
                        env=env,
                        check=True,
                    )
