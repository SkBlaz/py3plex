"""Execute complete construction and export guides against the installed wheel."""

import os
from pathlib import Path
import re
import tempfile
import textwrap
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]


def python_blocks(path: Path):
    """Yield Python blocks and their source line numbers from an RST page."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        match = re.fullmatch(r"(\s*)\.\. code-block:: python\s*", line)
        if not match:
            continue
        indent = len(match.group(1))
        block = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) <= indent:
                break
            block.append(following)
        yield index + 1, textwrap.dedent("\n".join(block))


def main() -> None:
    os.environ.setdefault("MPLBACKEND", "Agg")
    old_cwd = Path.cwd()
    try:
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            for name in ("load_and_build_networks", "export_serialize"):
                namespace = {"__name__": "__main__"}
                path = ROOT / "docfiles" / "how-to" / f"{name}.rst"
                count = 0
                for line, code in python_blocks(path):
                    print(f"Executing {path.name}:{line}", flush=True)
                    exec(compile(code, f"{path}:{line}", "exec"), namespace)
                    count += 1
                assert count, f"No Python examples found in {path}"
                print(f"PASS: {name} ({count} blocks)", flush=True)
            # Exercise the exact text/CSV/JSON blocks with isolated nodes and
            # parallel edges, whose weights must remain attached to each edge.
            from py3plex.core.multinet import multi_layer_network
            network = multi_layer_network(directed=True)
            network.add_nodes([{"source": "isolated", "type": "one", "label": "keep"}])
            network.add_edges([
                {"source": "a", "target": "b", "source_type": "one", "target_type": "two", "weight": weight}
                for weight in (0.0, 2.5, -1.0)
            ])
            namespace = {"network": network}
            blocks = list(python_blocks(ROOT / "docfiles/how-to/export_serialize.rst"))
            for _, code in blocks[1:5]:
                exec(code, namespace)
            restored = namespace["network"]
            assert restored.directed
            assert restored.core_network.nodes[("isolated", "one")]["label"] == "keep"
            expected = Counter([0.0, 2.5, -1.0])
            for filename, kind in (("edges.txt", "multiedgelist"), ("network_edges.csv", "multiedgelist")):
                loaded = multi_layer_network(directed=True).load_network(filename, input_type=kind)
                assert Counter(data["weight"] for _, _, data in loaded.get_edges(data=True)) == expected
            assert Counter(data["weight"] for _, _, data in restored.get_edges(data=True)) == expected
            print("PASS: documented weighted parallel-edge and JSON isolated-node round trips", flush=True)
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    main()
