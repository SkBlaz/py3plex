"""
Save and reload a network using the gpickle format.

Loads the optional `imdb_gml.gml` dataset (if available), saves it to gpickle,
reloads it, and prints basic statistics. Prerequisite: IMDB dataset from
`py3plex/utils/get_dataset_path`.

SKIP_CI: external_deps - Requires optional dataset files.
"""

from __future__ import annotations

from pathlib import Path

from py3plex.core import multinet
from py3plex.utils import get_data_path, get_dataset_path


def main() -> int:
    """Convert the IMDB sample to/from gpickle."""
    dataset = Path(get_dataset_path("imdb_gml.gml"))
    if not dataset.exists():
        print(f"Dataset not found: {dataset}")
        print("Skipping example. Please download the IMDB dataset first.")
        return 0

    print("Loading network from GML format...")
    multilayer_network = multinet.multi_layer_network().load_network(
        input_file=str(dataset),
        directed=True,
        input_type=dataset.suffix.lstrip("."),
    )

    print(f"Network loaded successfully from {dataset}")

    datasets_dir = Path(get_data_path("datasets"))
    output_path = datasets_dir / "imdb.gpickle"

    print(f"\nSaving network to gpickle format: {output_path}")
    multilayer_network.save_network(str(output_path), output_type="gpickle")
    print("Network saved successfully!")

    print("\nReloading network from gpickle format...")
    multilayer_network_new = multinet.multi_layer_network()
    multilayer_network_new.load_network(
        str(output_path),
        input_type="gpickle",
        directed=True,
    )

    print("Network reloaded successfully!")
    print("\nDisplaying basic network statistics:")
    print("-" * 50)
    multilayer_network_new.basic_stats()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
