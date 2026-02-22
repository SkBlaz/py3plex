"""CLI subcommands for the Network Experiment Registry.

Registers an ``experiment`` sub-group into the main py3plex CLI with five
commands:

* ``py3plex experiment list``   – list stored experiments
* ``py3plex experiment show``   – show full detail of one experiment
* ``py3plex experiment run``    – record a query result as an experiment (via
  a simple JSON config file)
* ``py3plex experiment reproduce`` – reproduce a stored experiment
* ``py3plex experiment export`` – export experiment metadata to JSON or CSV

All commands accept ``--store-dir`` to override the default registry path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _get_store(args: argparse.Namespace) -> "Any":
    """Return an ExperimentStore, using --store-dir if provided."""
    from py3plex.experiments.store import ExperimentStore

    path = getattr(args, "store_dir", None)
    return ExperimentStore(path=path)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def cmd_experiment_list(args: argparse.Namespace) -> int:
    """List stored experiments."""
    store = _get_store(args)
    tags: Optional[List[str]] = args.tags.split(",") if getattr(args, "tags", None) else None
    engine: Optional[str] = getattr(args, "engine", None)
    limit: Optional[int] = getattr(args, "limit", None)

    entries = store.list(tags=tags, engine=engine, limit=limit)
    if not entries:
        print("No experiments found.")
        return 0

    fmt = getattr(args, "format", "table")
    if fmt == "json":
        print(json.dumps(entries, indent=2, default=str))
    else:
        # table format
        header = f"{'ID':<26} {'Engine':<20} {'Created':<28} {'Tags'}"
        print(header)
        print("-" * 90)
        for e in entries:
            tags_str = ",".join(e.get("tags") or [])
            print(
                f"{e.get('id', ''):<26} {e.get('engine', ''):<20} "
                f"{e.get('created_utc', ''):<28} {tags_str}"
            )
    return 0


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def cmd_experiment_show(args: argparse.Namespace) -> int:
    """Show full detail of one experiment."""
    from py3plex.experiments.errors import ExperimentNotFound

    store = _get_store(args)
    exp_id: str = args.id
    try:
        exp = store.load(exp_id)
    except ExperimentNotFound as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    data = exp.to_dict()
    print(json.dumps(data, indent=2, default=str))
    return 0


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


def cmd_experiment_run(args: argparse.Namespace) -> int:
    """Record a query result as an experiment from a JSON config file.

    Config file schema (all optional fields marked with ?):

    .. code-block:: json

        {
          "network": "/path/to/network.csv",
          "input_type": "multiedgelist",
          "directed": false,
          "query": "SELECT nodes COMPUTE degree",
          "tags": ["demo", "v1"],
          "notes": "exploratory run"
        }
    """
    from py3plex.core import multinet
    from py3plex.dsl import execute_query
    from py3plex.experiments.runner import ExperimentRunner
    from py3plex.experiments.store import ExperimentStore

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        return 1

    try:
        with config_path.open() as fh:
            cfg: Dict[str, Any] = json.load(fh)
    except Exception as exc:
        print(f"Error reading config: {exc}", file=sys.stderr)
        return 1

    # Load network
    net_path = cfg.get("network", "")
    if not net_path:
        print("Error: 'network' key required in config", file=sys.stderr)
        return 1

    try:
        net = multinet.multi_layer_network(directed=cfg.get("directed", False))
        net.load_network(net_path, input_type=cfg.get("input_type", "multiedgelist"))
    except Exception as exc:
        print(f"Error loading network: {exc}", file=sys.stderr)
        return 1

    query_str = cfg.get("query", "SELECT nodes")
    try:
        result = execute_query(net, query_str)
    except Exception as exc:
        print(f"Error executing query: {exc}", file=sys.stderr)
        return 1

    store_path = getattr(args, "store_dir", None)
    runner = ExperimentRunner(store=ExperimentStore(path=store_path))
    exp = runner.record_query_result(
        result,
        notes=cfg.get("notes"),
        tags=cfg.get("tags", []),
    )
    print(f"Experiment recorded: {exp.id}")
    return 0


# ---------------------------------------------------------------------------
# reproduce
# ---------------------------------------------------------------------------


def cmd_experiment_reproduce(args: argparse.Namespace) -> int:
    """Attempt to reproduce a stored experiment."""
    from py3plex.experiments.errors import ExperimentNotFound, ReproductionError
    from py3plex.experiments.runner import ExperimentRunner

    store = _get_store(args)
    exp_id: str = args.id
    runner = ExperimentRunner(store=store)

    try:
        runner.reproduce(exp_id, network=None)
    except ExperimentNotFound as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ReproductionError as exc:
        # Provide guidance
        print(f"Reproduction info: {exc}", file=sys.stderr)
        return 2
    return 0


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------


def cmd_experiment_export(args: argparse.Namespace) -> int:
    """Export experiment metadata to JSON or CSV."""
    from py3plex.experiments.errors import ExperimentNotFound

    store = _get_store(args)
    exp_id: str = args.id
    out_path = Path(args.output) if getattr(args, "output", None) else None
    fmt: str = getattr(args, "format", "json")

    try:
        exp = store.load(exp_id)
    except ExperimentNotFound as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    data = exp.to_dict()

    if fmt == "json":
        text = json.dumps(data, indent=2, default=str)
        if out_path:
            out_path.write_text(text)
            print(f"Exported to {out_path}")
        else:
            print(text)
    elif fmt == "csv":
        # Flatten top-level scalar fields to CSV
        try:
            import csv as _csv
            import io

            flat: Dict[str, Any] = {
                k: v
                for k, v in data.items()
                if isinstance(v, (str, int, float, bool, type(None)))
            }
            buf = io.StringIO()
            writer = _csv.DictWriter(buf, fieldnames=list(flat.keys()))
            writer.writeheader()
            writer.writerow(flat)
            text = buf.getvalue()
            if out_path:
                out_path.write_text(text)
                print(f"Exported to {out_path}")
            else:
                print(text)
        except Exception as exc:
            print(f"CSV export error: {exc}", file=sys.stderr)
            return 1
    else:
        print(f"Unknown format: {fmt!r}. Use 'json' or 'csv'.", file=sys.stderr)
        return 1

    return 0


# ---------------------------------------------------------------------------
# Parser factory
# ---------------------------------------------------------------------------


def add_experiment_subparser(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    """Register the ``experiment`` command group into *subparsers*.

    Args:
        subparsers: The ``_SubParsersAction`` returned by
            ``parser.add_subparsers()``.
    """
    exp_parser = subparsers.add_parser(
        "experiment",
        help="Network Experiment Registry commands",
    )
    exp_parser.add_argument(
        "--store-dir",
        metavar="DIR",
        default=None,
        help="Override the experiment registry directory.",
    )

    exp_sub = exp_parser.add_subparsers(dest="exp_command", help="Experiment sub-commands")

    # list
    list_p = exp_sub.add_parser("list", help="List stored experiments")
    list_p.add_argument("--tags", default=None, help="Comma-separated tag filter")
    list_p.add_argument("--engine", default=None, help="Filter by engine name")
    list_p.add_argument("--limit", type=int, default=None, help="Maximum rows to show")
    list_p.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # show
    show_p = exp_sub.add_parser("show", help="Show full detail of an experiment")
    show_p.add_argument("id", help="Experiment ID (full or prefix)")

    # run
    run_p = exp_sub.add_parser(
        "run", help="Run a query from a JSON config and record it as an experiment"
    )
    run_p.add_argument("config", help="Path to JSON experiment config file")

    # reproduce
    repr_p = exp_sub.add_parser("reproduce", help="Reproduce a stored experiment")
    repr_p.add_argument("id", help="Experiment ID to reproduce")

    # export
    export_p = exp_sub.add_parser("export", help="Export experiment metadata")
    export_p.add_argument("id", help="Experiment ID to export")
    export_p.add_argument(
        "--output", "-o", default=None, metavar="FILE", help="Output file path"
    )
    export_p.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Export format"
    )


def dispatch_experiment(args: argparse.Namespace) -> int:
    """Dispatch ``experiment <sub-command>`` to the right handler.

    Args:
        args: Parsed arguments (``args.command == "experiment"``).

    Returns:
        Exit code.
    """
    handlers = {
        "list": cmd_experiment_list,
        "show": cmd_experiment_show,
        "run": cmd_experiment_run,
        "reproduce": cmd_experiment_reproduce,
        "export": cmd_experiment_export,
    }

    sub = getattr(args, "exp_command", None)
    if sub is None:
        print("Usage: py3plex experiment <list|show|run|reproduce|export>")
        return 0

    handler = handlers.get(sub)
    if handler is None:
        print(f"Unknown experiment sub-command: {sub!r}", file=sys.stderr)
        return 1

    return handler(args)
