"""
Save a multilayer network to multiple edgelist formats.

Loads the bundled `goslim_mirna.gpickle` example (if present) and writes three
variants: human-readable multiedgelist, compact edgelist, and encoded
multiedgelist. Prerequisite: the optional goslim_mirna dataset downloaded via
`py3plex/utils/get_dataset_path`.

SKIP_CI: external_deps - Requires optional dataset files.
"""

from __future__ import annotations

from pathlib import Path

from py3plex.core import multinet
from py3plex.utils import get_data_path, get_dataset_path


def main() -> int:
    """Load the MIRNA dataset (if available) and save to multiple formats."""
    dataset_path = Path(get_dataset_path("goslim_mirna.gpickle"))
    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        print("Skipping example. Please download the goslim_mirna dataset first.")
        return 0

    print("Loading multilayer network...")
    multilayer_network = multinet.multi_layer_network().load_network(
        str(dataset_path),
        directed=False,
        input_type="gpickle_biomine",
    )

    print("Network loaded successfully!")
    print("\nSaving network in different edgelist formats...\n")

    datasets_dir = Path(get_data_path("datasets"))

    output_path1 = datasets_dir / "mirna_multiedgelist.list"
    multilayer_network.save_network(str(output_path1), output_type="multiedgelist")
    print("1. Saved as multiedgelist (human-readable):")
    print(f"   {output_path1}")

    output_path2 = datasets_dir / "mirna_edgelist.list"
    multilayer_network.save_network(str(output_path2), output_type="edgelist")
    print("\n2. Saved as edgelist (compact numeric):")
    print(f"   {output_path2}")

    output_path3 = datasets_dir / "mirna_multiedgelist_encoded.list"
    multilayer_network.save_network(str(output_path3), output_type="multiedgelist_encoded")
    print("\n3. Saved as encoded multiedgelist (numeric with layer IDs):")
    print(f"   {output_path3}")

    print("\nAll formats saved successfully!")
    print("Mappings are stored on the network object:")
    print("  - Node mapping: multilayer_network.node_map")
    print("  - Layer mapping: multilayer_network.layer_map")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
