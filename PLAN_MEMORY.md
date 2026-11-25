# py3plex RAM profile and optimization plan

**Start with cold imports, NetMF, and cache fingerprinting.** A bare `import py3plex` added **201.12 MiB** of resident memory in this environment, before creating a graph. On a sparse 2,048-node embedding problem, changing how NetMF represents its intermediate matrix cut incremental peak RSS from **96.56 to 2.88 MiB**. A streaming graph fingerprint reduced the peak of an explicitly cached degree lookup from **75.52 to 0.28 MiB**. The latter two comparisons use benchmark prototypes on the same inputs.

This scan measures py3plex **2.0.94** at `845c9dec50336e762fe16069d29750ad70cf74d6` on `master`, including the seven merged CPU optimizations. Each candidate below is a benchmark or an engineering proposal. The measurements cover CPU process memory on Linux.

## Prioritized work

| Priority | Finding and evidence | Implementation and acceptance test |
|---|---|---|
| 1 | **Import footprint affects every process.** Importing the root package alone loaded NumPy, SciPy, NetworkX, pyplot, pandas, scikit-learn and, on this installation, PyArrow. The incremental RSS remained resident after GC. | Make heavyweight public re-exports lazy, then defer plotting imports inside plotting methods where possible. First target ≤50 MiB incremental RSS for bare import on this environment. Measure first graph construction and first plot separately to show how much cost moves to first use. Check public imports, `__all__`, introspection, CLI startup and optional-dependency environments. [Package initialization](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/__init__.py) · [Core graph imports](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/core/multinet.py) |
| 2 | **NetMF densifies sparse walk statistics before factorization.** At four times the node count, peak RSS grew from 7.36 to 96.56 MiB. Traced peak at the larger size was 101,866,048 bytes for a 65,536-byte float32 embedding. | For sparse contexts, apply scaling and positive pointwise mutual information (PPMI) to stored values, eliminate zeros and pass CSR to the solver. Zero entries remain zero after the existing log/clamp. The prototype used 2.88 MiB peak RSS. Target <8 MiB on this fixture. Test zero-degree nodes, window length, negative sampling, union and supra modes and both solver paths. Check matrix and embedding geometry with tolerances for degenerate singular subspaces. Measure fill-in on long windows before choosing sparse storage unconditionally. [NetMF kernel](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/embeddings/netmf.py) |
| 3 | **Fingerprinting allocates a second representation of graph content on every explicit cache hit.** The current code constructs lists of nodes and edges, a recursively type-tagged tree, a JSON string and encoded bytes. The large cache-hit trace peaked at **72,155,480 bytes**. The record-by-record hash probe peaked at **447,023 bytes**. | Stream canonical bytes into SHA-256, including traversal order and type tags. Preserve rejection of unsupported inputs and detection of direct graph/attribute mutations. The probe produced the same digest and hit an entry populated by the production hasher. Extend parity to partitions, temporal metadata, edge keys, multibyte strings and unsupported types. Target <4 MiB incremental RSS for an enabled hit. Ordinary unseeded degree used only 1.28 MiB. [Graph fingerprint](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/dsl/program/cache.py) |
| 4 | **CSV out-of-core coverage holds a database in RAM and writes a serialized copy of every row to a table that reconstruction never reads.** A real-data run returned 3,360 edges, with **21.44 MiB** incremental peak RSS. A file-backed key index with a 1 MiB SQLite cache and a second input pass returned the same ordered output at **2.70 MiB**. | Remove the unused row table. Spill distinct layer-pair keys and qualifying pairs to the configured work directory. Bound SQLite cache use and avoid collecting qualifying pairs into a Python set. Target <6 MiB on the MLKing sample. Test duplicates, both direction modes, limits, ordering, zero matches and cleanup on errors. For ungrouped all-edge reads, build result columns in one pass. This alone cut peak RSS from **13.50 to 7.15 MiB**, with the materialized result still available. [CSV execution and result materialization](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/out_of_core/executor.py) |
| 5 | **First sparse supra-adjacency construction builds an intermediate numeric NetworkX graph.** The large run peaked at 20.66 MiB RSS. Direct coordinate assembly peaked at 3.11 MiB. | Construct CSR directly from numeric replica indices and weighted edges. Preserve the cached matrix and its replica-order contract. Target <6 MiB incremental peak. Test parallel-edge sums, non-numeric and missing weights, isolated nodes, directed edges, self-loops, dtype and index width. The probe covers undirected construction; the multiplex encoder has a separate ordering contract. [Numeric conversion](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/core/multinet.py) |
| 6 | **Replay snapshot compression holds a complete JSON string and byte buffer.** Compressing an existing 32,768-edge capture took 15.58 MiB peak RSS for a 300,604-byte gzip output. Streaming JSON to gzip used 0.41 MiB and produced the same decompressed bytes on the parity fixtures. | Buffer encoder output in bounded chunks. Target <2 MiB additional RSS during compression and measure wall time at several chunk sizes. Preserve JSON defaults, Unicode, ordering and round-trip behavior. Capture creation has its own 17.30 MiB peak. An end-to-end streaming writer would also need to address the public in-memory capture object. [Capture and compression](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/provenance/capture.py) |
| 7 | **The new temporal index retains a Python tuple and insertion position per event.** After dropping a 22-record result, the 32,768-event lookup still held **3,023,372 traced bytes**. A pair of packed timestamp and position arrays retained **525,256 bytes**. | Preserve lazy creation and the mutable-record fallback. Use packed timestamps and stable positions for shuffled point events; measure a simpler path for monotonic inserts. Target <1 MiB retained on this fixture. Compare inclusive endpoints, repeated timestamps, insertion order, late arrivals, direct edits and broad windows. Check first-query cost and warm lookup latency alongside bytes. [Temporal index](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/core/temporal_multinet.py) |

**Persistent cache growth needs a separate limit.** Eight distinct explicitly cached seeds on the same graph left 3,719,156 traced bytes after caller cleanup. Clearing the program cache reduced this to 775,039 bytes, a release of **2,944,117 bytes**. The cache currently keeps every distinct key until `clear()`. Streaming the fingerprint reduces temporary allocation; it does not evict result objects. Add an observable entry or byte budget with eviction, and test repeat hits, eviction order and release across many distinct graphs and seeds. RSS after GC also includes allocator arenas and runtime caches, so the 20.91 MiB resident increase is not an estimate of cache entry size. [Program cache storage](https://github.com/SkBlaz/py3plex/blob/845c9dec50336e762fe16069d29750ad70cf74d6/py3plex/dsl/program/cache.py)

**Bootstrap warrants a phase-by-phase follow-up.** Eight serial degree replicates peaked at **53.45 MiB** incremental RSS versus **1.28 MiB** for ordinary degree. The result, sample graphs, draw matrix and quantile workspace have different lifetimes. Measure those phases independently across draw counts and worker counts before choosing a rewrite. Exact quantiles and seeded samples are part of the correctness check.

## Measurements

The small synthetic graph has 512 physical nodes, 2,048 replicas and 8,192 edges. The large graph has 2,048 physical nodes, 8,192 replicas and 32,768 edges. Four layers contain a ring, two chords and one interlayer edge per replica, all with unit weight. NetMF operates on a prebuilt union adjacency over **physical nodes**, using window 2, dimension 8, negative sampling factor 1 and seed 42. Temporal cases use one point event per input edge count, shuffled with seed 42 and two records per timestamp.

Each RSS value is the median of three fresh, uninstrumented processes. Δ peak RSS is the increase in resident high-water mark above the post-setup baseline. Traced bytes come from a fourth process using `tracemalloc`. “After GC” means after dropping the operation's return value and collecting garbage, with input fixtures and library caches still alive. Rounded zero can mean the process reused already resident pages. A traced peak and an RSS delta measure different things.

| Workload | 8,192 edges Δ peak RSS (MiB) | 32,768 edges Δ peak RSS (MiB) | Large peak traced (MiB) | Large traced after GC (MiB) | Large RSS after GC, Δ MiB |
|---|---:|---:|---:|---:|---:|
| No-op control | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 |
| Construct weighted multigraph | 6.76 | 27.09 | 25.47 | 0.00 | 3.45 |
| DSL degree | 0.94 | 1.28 | 1.25 | 0.74 | 1.28 |
| Warm explicitly enabled degree cache hit | 15.37 | 75.52 | 68.81 | 0.00 | 6.71 |
| Cache hit with streaming fingerprint | 0.00 | 0.28 | 0.43 | 0.00 | 0.28 |
| Eight distinct seeded cache entries | 21.48 | 83.66 | 72.01 | 3.55 | 20.91 |
| First sparse supra-adjacency request | 5.66 | 20.66 | 20.00 | 2.10 | 11.81 |
| Direct coordinate assembly probe | 1.30 | 3.11 | 2.28 | 0.01 | 1.07 |
| Full replay snapshot capture | 4.34 | 17.30 | 16.80 | 0.00 | 2.54 |
| Compress existing snapshot | 4.36 | 15.58 | 15.45 | 0.00 | 0.85 |
| Incremental JSON → gzip probe | 0.36 | 0.41 | 0.66 | 0.00 | 0.41 |
| Node degree result → pandas | 0.55 | 1.91 | 2.09 | 0.00 | 1.91 |
| Node degree result → Arrow | 0.27 | 0.40 | 0.20 | 0.00 | 0.40 |
| Full node result → NetworkX | 4.66 | 18.58 | 17.51 | 0.00 | 2.83 |
| NetMF factorization, baseline | 7.36 | 96.56 | 97.15 | 0.02 | 3.55 |
| NetMF with sparse PPMI probe | 2.16 | 2.88 | 2.03 | 0.02 | 2.88 |
| First indexed temporal window | 0.82 | 3.27 | 3.01 | 2.88 | 3.27 |
| Packed temporal index probe | 0.31 | 0.88 | 0.75 | 0.50 | 0.88 |
| DSL bootstrap degree, eight draws | 21.58 | 53.45 | 51.24 | 0.76 | 6.19 |
| CSV backend, all edges | 3.34 | 13.50 | 12.32 | 0.00 | 2.99 |
| CSV backend, one-pass result probe | 1.81 | 7.15 | 6.34 | 0.00 | 3.02 |
| CSV backend, top 20 by weight | 0.02 | 0.02 | 0.07 | 0.00 | 0.02 |
| CSV backend, coverage ≥5 | 2.17 | 6.46 | 0.06 | 0.00 | 0.88 |
| File-backed coverage probe, ≥5 | 0.92 | 1.45 | 0.06 | 0.00 | 1.45 |

### Cold imports

| Entry point | RSS before import (KiB) | Incremental peak RSS (KiB) | Incremental RSS after GC (KiB) |
|---|---:|---:|---:|
| `import py3plex` | 20,052 | 205,952 | 205,952 |
| `import py3plex.core.multinet` | 20,032 | 206,048 | 206,052 |
| `import py3plex.dsl` | 19,916 | 206,168 | 206,172 |

Each column gives the median of three fresh processes. GC and measurement bookkeeping ran after the import peak reading. RSS includes shared library pages, so multiplying the import footprint by a worker count can overstate physical RAM usage.

### Real edge-list coverage

The input took every fourth record starting with the first of 396,671 MLKing2013 edge records. Coverage of at least two layer pairs selected 3,360 weighted edges from 99,168 input rows. Production and prototype returned those edges in the same order, with the same SHA-256 over the ordered weighted output (`1cfeab0376152021c81ee667ab659bb5d62543426741fced0cf704337b563468`).

| Coverage implementation | Incremental peak RSS (KiB) | Peak traced bytes | SQLite scratch file (bytes) |
|---|---:|---:|---:|
| Current in-memory SQL | 21,952 | 1,831,787 | 0 |
| File-backed keys and second input pass | 2,764 | 756,913 | 2,330,624 |

The scratch file trades process memory for disk space and filesystem cache. SQLite's native page allocations explain why Python allocation tracing alone misses much of this saving. Both paths materialize the selected edges, so RSS still depends on how many edges qualify.

### Measurement scope and correctness

The machine ran Linux 6.8.0-149-generic on an Intel Core i7-8565U with 15 GiB of RAM. The environment used CPython 3.12.8, NumPy 1.26.4, SciPy 1.13.1, pandas 2.2.3, NetworkX 3.5, PyArrow 20.0.0, scikit-learn 1.7.1 and SQLite 3.50.2. Workers used one CPU and one BLAS/OpenMP thread. Independent workload families could overlap during memory measurement. After fixture preparation and GC, each worker reset its Linux RSS high-water mark through `/proc/self/clear_refs`. Measurements cover one process. GPU memory, memory across worker pools and system-wide filesystem cache require separate instrumentation.

All seven candidate implementations passed comparisons with the production path at 64 and 512 physical nodes. The direct supra probe returns the matrix only, whereas the production call retains graph conversion state. Its post-GC numbers therefore describe different cache lifetimes. The streaming fingerprint covers the synthetic undirected multigraph without partitions. NetMF parity checks the matrix supplied to the solver and embedding column norms. The NetMF measurements exclude graph preparation and cover one short walk window. These results establish where to spend implementation effort. The broader acceptance cases in the plan still need production tests.

### Wall-time tradeoffs

Median operation time across three additional fresh processes per case, run sequentially on CPU 3. Setup is outside the timer. Synthetic workloads use the larger fixture. Coverage uses the MLKing sample.

| Workload | Current (ms) | Prototype (ms) |
|---|---:|---:|
| Snapshot compression | 507.078 | 1066.403 |
| Warm explicit cache hit | 1196.935 | 447.211 |
| NetMF factorization | 212.756 | 28.408 |
| MLKing coverage | 1725.540 | 1965.988 |

## Reproduce

Run from the checkout containing the [benchmark harness](benchmarks/profile_memory.py), with the dependencies above installed. Choose an available CPU for `cpu`. The default sweep runs 24 synthetic cases at two sizes. The two extra invocations cover imports and real-data coverage.

```bash
harness="$PWD/benchmarks/profile_memory.py"
source_tree=$(mktemp -d)
git worktree add --detach "$source_tree" 845c9dec50336e762fe16069d29750ad70cf74d6
cd "$source_tree"
export PYTHONPATH="$PWD" PYTHONHASHSEED=0 MPLBACKEND=Agg
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cpu=3
taskset -c "$cpu" python "$harness" > /tmp/py3plex-memory.jsonl
taskset -c "$cpu" python "$harness" --cases import_package import_core import_dsl --sizes 0 >> /tmp/py3plex-memory.jsonl
taskset -c "$cpu" python "$harness" --cases mlking mlking_file --sizes 99168 >> /tmp/py3plex-memory.jsonl

for n in 64 512; do
  for probe in supra_direct cache_stream netmf_sparse gzip_stream ooc_stream ooc_file_coverage temporal_packed; do
    taskset -c "$cpu" python "$harness" --worker "$probe" "$n" verify || exit 1
  done
done
for round in 1 2 3; do
  for name in gzip gzip_stream cache_hit cache_stream netmf netmf_sparse mlking mlking_file; do
    case "$name" in mlking*) n=99168 ;; *) n=2048 ;; esac
    taskset -c "$cpu" python "$harness" --worker "$name" "$n" rss >> /tmp/py3plex-walltime.jsonl
  done
done
```

The [raw measurements](benchmarks/memory-845c9dec.tsv) contain the 212 memory workers and 24 supplemental wall-time workers. Filter by `series=memory, mode=rss` to reproduce the resident-memory medians. Use `mode=trace` for byte-level allocation counts and `series=timing` for elapsed milliseconds. MiB values use 1,048,576 bytes. Blank fields indicate an inapplicable measurement.

## Bootstrap phase attribution and implementation

For eight serial edge resamples on the large graph, the original path reached 54,430,326 traced bytes during construction of the fourth sampled graph. The first sample alone grew traced live memory from 4,617,093 to 18,583,328 bytes. The first degree calculation on that sample added 510,008 bytes at its peak. The final quantile call added 1,256,912 bytes at its peak. These numbers come from a separate instrumented process. Each measurement includes allocations still live at phase entry. To reproduce on the baseline checkout, run the harness with `--worker bootstrap 2048 phases`.

For the built-in, full-topology, unweighted degree metric, a sampled edge contributes one count to each endpoint, including both endpoints of a loop. Count the endpoints of exactly the same seeded edge draws and add fixed multiplex coupling degrees. This uses the existing quantile and sample-count code. The production change reduced median incremental RSS from **54,728 KiB to 11,144 KiB** on the eight-draw fixture. The branch's traced peak was **9,772,425 bytes**. Comparisons against materialized draws cover directed and undirected graphs, parallel edges, loops, restricted output nodes, isolates and fixed coupling.
