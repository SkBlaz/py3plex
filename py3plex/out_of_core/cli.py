"""CLI subcommands for out-of-core (``ooc``) operations.

These subcommands are registered under the ``ooc`` top-level command in the
main py3plex CLI::

    py3plex ooc convert --input edges.csv --output edges_ooc/
    py3plex ooc info    edges.csv
    py3plex ooc scan    edges.csv --limit 5

Subcommands
-----------
convert
    Convert a standard multilayer edge-list CSV into an out-of-core
    compatible CSV (validates schema; optionally writes a Parquet copy if
    pyarrow is available).

info
    Print metadata about an out-of-core network file (format, column
    names, row count estimate, layer names).

scan
    Stream the first *N* rows of an edge file and print them as a table
    or JSON.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Optional

from .errors import OutOfCoreIOError, SchemaError
from .network import OutOfCoreNetwork
from .readers import make_edge_reader
from .schema import EDGE_REQUIRED_COLUMNS


# ---------------------------------------------------------------------------
# ``convert`` subcommand
# ---------------------------------------------------------------------------


def cmd_ooc_convert(args: argparse.Namespace) -> int:
    """Convert and validate an edge-list CSV for out-of-core use.

    Reads the input file, validates the required schema columns, and writes a
    clean copy to the output path.  If ``--parquet`` is given and ``pyarrow``
    is available the file is also saved as Parquet.

    Args:
        args: Parsed arguments from ``build_ooc_parser``.

    Returns:
        Exit code (0 = success).
    """
    input_path: str = args.input
    output_path: str = args.output
    fmt: str = args.format.lower()
    directed: bool = args.directed

    if not os.path.isfile(input_path):
        print(f"[ERROR] Input file not found: {input_path!r}", file=sys.stderr)
        return 1

    print(f"Converting {input_path!r} -> {output_path!r} (format={fmt!r}) …")

    # Validate schema by reading a few rows
    try:
        reader = make_edge_reader(input_path, "csv")
        sample_rows = []
        for i, row in enumerate(reader.scan()):
            if i == 0:
                missing = set(EDGE_REQUIRED_COLUMNS) - set(row)
                if missing:
                    raise SchemaError(
                        f"Input CSV is missing required columns: {sorted(missing)}. "
                        f"Required: {sorted(EDGE_REQUIRED_COLUMNS)}."
                    )
            sample_rows.append(row)
            if i >= 4:
                break
    except SchemaError as exc:
        print(f"[ERROR] Schema validation failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Failed to read input: {exc}", file=sys.stderr)
        return 1

    if fmt == "csv":
        # Read all rows and write clean CSV
        try:
            all_rows = list(make_edge_reader(input_path, "csv").scan())
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] Failed to read input: {exc}", file=sys.stderr)
            return 1

        if not all_rows:
            print("[WARNING] Input file appears to be empty.")
            all_rows = []

        fieldnames = list(all_rows[0].keys()) if all_rows else list(EDGE_REQUIRED_COLUMNS)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"  Written {len(all_rows)} rows to {output_path!r}")

    elif fmt == "parquet":
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            print(
                "[ERROR] pyarrow is required for Parquet output. "
                "Install with: pip install pyarrow",
                file=sys.stderr,
            )
            return 1

        try:
            all_rows = list(make_edge_reader(input_path, "csv").scan())
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] Failed to read input: {exc}", file=sys.stderr)
            return 1

        import pandas as pd

        df = pd.DataFrame(all_rows)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        pq.write_table(pa.Table.from_pandas(df), output_path)
        print(f"  Written {len(df)} rows to {output_path!r} (Parquet)")

    else:
        print(f"[ERROR] Unsupported output format {fmt!r}. Use 'csv' or 'parquet'.", file=sys.stderr)
        return 1

    # Write companion info JSON
    info_path = output_path + ".ooc.json"
    info = {
        "edges_path": os.path.abspath(output_path),
        "edges_format": fmt,
        "directed": directed,
        "source_input": os.path.abspath(input_path),
        "row_count": len(all_rows) if "all_rows" in dir() else "unknown",
    }
    with open(info_path, "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=2)
    print(f"  Metadata written to {info_path!r}")
    return 0


# ---------------------------------------------------------------------------
# ``info`` subcommand
# ---------------------------------------------------------------------------


def cmd_ooc_info(args: argparse.Namespace) -> int:
    """Print metadata about an out-of-core network edge file.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    input_path: str = args.input
    fmt: str = args.format.lower()
    output_json: bool = getattr(args, "json", False)

    if not os.path.exists(input_path):
        print(f"[ERROR] File not found: {input_path!r}", file=sys.stderr)
        return 1

    try:
        net = OutOfCoreNetwork(edges_path=input_path, edges_format=fmt)
    except OutOfCoreIOError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    # Scan to collect basic statistics
    reader = make_edge_reader(input_path, fmt)
    row_count = 0
    layers: set = set()
    columns: Optional[list] = None

    for row in reader.scan():
        if columns is None:
            columns = list(row.keys())
        row_count += 1
        sl = row.get("source_layer")
        tl = row.get("target_layer")
        if sl:
            layers.add(sl)
        if tl:
            layers.add(tl)

    info = {
        "edges_path": os.path.abspath(input_path),
        "edges_format": fmt,
        "directed": net.directed,
        "row_count": row_count,
        "layers": sorted(layers),
        "layer_count": len(layers),
        "columns": columns or [],
        "fingerprint": net.fingerprint,
    }

    if output_json:
        print(json.dumps(info, indent=2))
    else:
        print(f"Path         : {info['edges_path']}")
        print(f"Format       : {info['edges_format']}")
        print(f"Directed     : {info['directed']}")
        print(f"Rows         : {info['row_count']}")
        print(f"Layers ({info['layer_count']})  : {', '.join(info['layers'])}")
        print(f"Columns      : {', '.join(info['columns'])}")

    return 0


# ---------------------------------------------------------------------------
# ``scan`` subcommand
# ---------------------------------------------------------------------------


def cmd_ooc_scan(args: argparse.Namespace) -> int:
    """Stream and print the first N rows of an edge file.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code.
    """
    input_path: str = args.input
    fmt: str = args.format.lower()
    limit: int = args.limit
    output_json: bool = getattr(args, "json", False)

    if not os.path.exists(input_path):
        print(f"[ERROR] File not found: {input_path!r}", file=sys.stderr)
        return 1

    reader = make_edge_reader(input_path, fmt)
    rows = []
    for i, row in enumerate(reader.scan()):
        if i >= limit:
            break
        rows.append(row)

    if output_json:
        print(json.dumps(rows, indent=2))
    else:
        if not rows:
            print("(no rows)")
            return 0
        cols = list(rows[0].keys())
        # Simple ASCII table
        col_widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}
        header = " | ".join(c.ljust(col_widths[c]) for c in cols)
        sep = "-+-".join("-" * col_widths[c] for c in cols)
        print(header)
        print(sep)
        for row in rows:
            print(" | ".join(str(row.get(c, "")).ljust(col_widths[c]) for c in cols))
        print(f"\n({len(rows)} row(s) shown)")

    return 0


# ---------------------------------------------------------------------------
# Parser builder
# ---------------------------------------------------------------------------


def build_ooc_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register ``ooc`` subcommand group into *subparsers*.

    Adds ``ooc`` with three sub-subcommands: ``convert``, ``info``, ``scan``.

    Args:
        subparsers: The top-level subparsers action from create_parser().
    """
    ooc_parser = subparsers.add_parser(
        "ooc",
        help="Out-of-core (streaming) operations for large networks",
        description=(
            "Stream and query multilayer networks stored on disk without loading "
            "the full graph into memory."
        ),
    )
    ooc_sub = ooc_parser.add_subparsers(dest="ooc_command", help="ooc subcommands")

    # ---- convert ----
    conv = ooc_sub.add_parser(
        "convert",
        help="Convert and validate an edge-list CSV for out-of-core use",
    )
    conv.add_argument("--input", "-i", required=True, help="Input CSV edge-list file")
    conv.add_argument("--output", "-o", required=True, help="Output file path")
    conv.add_argument(
        "--format",
        "-f",
        default="csv",
        choices=["csv", "parquet"],
        help="Output format (default: csv)",
    )
    conv.add_argument(
        "--directed",
        action="store_true",
        help="Treat edges as directed",
    )

    # ---- info ----
    info = ooc_sub.add_parser(
        "info",
        help="Print metadata about an out-of-core edge file",
    )
    info.add_argument("input", help="Edge file path")
    info.add_argument(
        "--format",
        "-f",
        default="csv",
        choices=["csv", "parquet", "arrow", "jsonl"],
        help="File format (default: csv)",
    )
    info.add_argument("--json", action="store_true", dest="json", help="Output as JSON")

    # ---- scan ----
    scan = ooc_sub.add_parser(
        "scan",
        help="Print the first N rows of an edge file",
    )
    scan.add_argument("input", help="Edge file path")
    scan.add_argument(
        "--format",
        "-f",
        default="csv",
        choices=["csv", "parquet", "arrow", "jsonl"],
        help="File format (default: csv)",
    )
    scan.add_argument(
        "--limit",
        "-n",
        type=int,
        default=10,
        help="Maximum rows to display (default: 10)",
    )
    scan.add_argument("--json", action="store_true", dest="json", help="Output as JSON")


def dispatch_ooc(args: argparse.Namespace) -> int:
    """Dispatch ``ooc`` subcommand to the appropriate handler.

    Args:
        args: Parsed top-level args (``args.ooc_command`` selects handler).

    Returns:
        Exit code.
    """
    ooc_cmd = getattr(args, "ooc_command", None)
    if ooc_cmd == "convert":
        return cmd_ooc_convert(args)
    elif ooc_cmd == "info":
        return cmd_ooc_info(args)
    elif ooc_cmd == "scan":
        return cmd_ooc_scan(args)
    else:
        print(
            "Usage: py3plex ooc {convert,info,scan} [options]\n"
            "       py3plex ooc --help",
            file=sys.stderr,
        )
        return 1
