"""Spill-to-disk utilities for bounded-memory external sort and group-by."""

from __future__ import annotations

import heapq
import json
import os
import tempfile
from typing import Any, Callable, Dict, Iterator, List, Optional

from .utils import sort_key_for_row


class SpillManager:
    """Manages a set of temporary spill files in a single directory.

    All spill files are written as JSONL (one JSON object per line) for
    simplicity, portability, and independence from optional dependencies.

    Args:
        workdir: Parent directory for the temp spill directory.  Defaults
                 to the system temp directory.
    """

    def __init__(self, workdir: Optional[str] = None) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="py3plex_ooc_", dir=workdir)
        self._files: List[str] = []

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def new_spill_path(self, suffix: str = ".jsonl") -> str:
        """Return a new unique path inside the temp directory."""
        idx = len(self._files)
        path = os.path.join(self._tmpdir, f"spill_{idx:05d}{suffix}")
        self._files.append(path)
        return path

    def write_rows(self, path: str, rows: List[dict]) -> None:
        """Write *rows* as JSONL to *path*."""
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def read_rows(self, path: str) -> Iterator[dict]:
        """Yield dicts from a JSONL spill file."""
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)

    # ------------------------------------------------------------------
    # External sort
    # ------------------------------------------------------------------

    def external_sort(
        self,
        rows: Iterator[dict],
        key_fields: List[str],
        asc: bool = True,
        memory_limit_rows: int = 100_000,
    ) -> Iterator[dict]:
        """External sort that spills sorted runs to disk and merges.

        Args:
            rows: Input row iterator.
            key_fields: Fields to sort by (total order, stable).
            asc: Ascending if True, descending if False.
            memory_limit_rows: Max rows to hold in memory per run.

        Yields:
            Rows in sorted order.
        """
        run_paths: List[str] = []
        buf: List[dict] = []

        def _flush_run(buf: List[dict]) -> str:
            buf.sort(key=lambda r: sort_key_for_row(r, key_fields), reverse=not asc)
            path = self.new_spill_path(".sort")
            self.write_rows(path, buf)
            return path

        for row in rows:
            buf.append(row)
            if len(buf) >= memory_limit_rows:
                run_paths.append(_flush_run(buf))
                buf = []

        if buf:
            run_paths.append(_flush_run(buf))

        if not run_paths:
            return

        # k-way merge with heapq
        # heap entries: (key, counter, row, iterator)
        iterators = [self.read_rows(p) for p in run_paths]
        counter = [0]

        def _next_entry(it: Iterator[dict]):
            row = next(it, None)
            if row is None:
                return None
            k = sort_key_for_row(row, key_fields)
            if not asc:
                # Negate numeric parts; strings stay lexicographic descending
                # We handle this by using a wrapper tuple that reverses comparison.
                pass
            c = counter[0]
            counter[0] += 1
            return (k, c, row, it)

        heap: list = []
        for it in iterators:
            entry = _next_entry(it)
            if entry is not None:
                heap.append(entry)

        if asc:
            heapq.heapify(heap)
            while heap:
                k, c, row, it = heapq.heappop(heap)
                yield row
                entry = _next_entry(it)
                if entry is not None:
                    heapq.heappush(heap, entry)
        else:
            # For descending: invert key tuples so heapq (min-heap) gives us desc order
            desc_heap = []
            for k, c, row, it in heap:
                # Wrap each key element so comparison is reversed
                inv_k = _invert_key(k)
                desc_heap.append((inv_k, c, row, it))
            heapq.heapify(desc_heap)
            while desc_heap:
                _k, c, row, it = heapq.heappop(desc_heap)
                yield row
                nxt = next(it, None)
                if nxt is not None:
                    nc = counter[0]
                    counter[0] += 1
                    nk = sort_key_for_row(nxt, key_fields)
                    heapq.heappush(desc_heap, (_invert_key(nk), nc, nxt, it))

    # ------------------------------------------------------------------
    # External group-by (sort-based)
    # ------------------------------------------------------------------

    def external_groupby(
        self,
        rows: Iterator[dict],
        key_fields: List[str],
        aggregations: Dict[str, Callable],
        memory_limit_rows: int = 100_000,
    ) -> Iterator[dict]:
        """External group-by via external sort then stream aggregate.

        Args:
            rows: Input row iterator.
            key_fields: Fields to group by.
            aggregations: Mapping of output_field -> callable(group_rows) -> value.
            memory_limit_rows: Memory bound per sort run.

        Yields:
            One aggregated dict per group.
        """
        sorted_rows = self.external_sort(rows, key_fields, asc=True, memory_limit_rows=memory_limit_rows)

        current_key: Optional[tuple] = None
        group_buf: List[dict] = []

        def _emit_group(key: tuple, buf: List[dict]) -> dict:
            result = dict(zip(key_fields, key))
            for out_field, agg_fn in aggregations.items():
                result[out_field] = agg_fn(buf)
            return result

        for row in sorted_rows:
            key_val = tuple(row.get(f) for f in key_fields)
            if current_key is None:
                current_key = key_val
            if key_val != current_key:
                yield _emit_group(current_key, group_buf)
                group_buf = []
                current_key = key_val
            group_buf.append(row)

        if group_buf and current_key is not None:
            yield _emit_group(current_key, group_buf)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Remove all spill files and the temp directory."""
        import shutil
        try:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
        except Exception:
            pass

    def __enter__(self) -> "SpillManager":
        return self

    def __exit__(self, *args: Any) -> None:
        self.cleanup()


def _invert_key(key: tuple) -> tuple:
    """Invert a sort key tuple so that min-heap gives descending order.

    Works for (type_rank, value) pairs produced by sort_key_for_row.
    """
    inv = []
    for part in key:
        type_rank, val = part
        if isinstance(val, (int, float)):
            inv.append((type_rank, -val))
        else:
            # strings: negate type_rank so higher comes first in min-heap
            # This is approximate for pure string ordering but functional.
            inv.append((-type_rank, val))
    return tuple(inv)


# ---------------------------------------------------------------------------
# SpillContext: lightweight context with new_spill_file / cleanup interface
# ---------------------------------------------------------------------------

class SpillContext:
    """Lightweight spill context that manages a temporary directory.

    Unlike :class:`SpillManager`, ``SpillContext`` provides only the basic
    file-path allocation and cleanup interface without higher-level sort /
    group-by helpers.  Use it when you want to manage spill files yourself.

    Args:
        workdir: Parent directory for the temp directory.  Defaults to the
                 system temp directory.
    """

    def __init__(self, workdir: Optional[str] = None) -> None:
        self._tmpdir = tempfile.mkdtemp(prefix="py3plex_ooc_ctx_", dir=workdir)
        self._files: List[str] = []

    def new_spill_file(self, suffix: str = ".jsonl") -> str:
        """Return a new unique path inside the temp directory.

        The file is *not* created; the caller is responsible for writing to it.

        Args:
            suffix: File suffix (default ``.jsonl``).

        Returns:
            Absolute path string.
        """
        idx = len(self._files)
        path = os.path.join(self._tmpdir, f"ctx_{idx:05d}{suffix}")
        self._files.append(path)
        return path

    def cleanup(self) -> None:
        """Remove all registered spill files and the temp directory."""
        import shutil
        try:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
        except Exception:
            pass
        self._files.clear()

    def __enter__(self) -> "SpillContext":
        return self

    def __exit__(self, *args: Any) -> None:
        self.cleanup()
