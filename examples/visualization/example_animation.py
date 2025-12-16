"""
Visualization Example: Creating Network Growth Animations

Generates snapshots of increasingly large multilayer Erdős–Rényi networks
and stitches them into an animated GIF.

Requirements:
- matplotlib
- imagemagick (for GIF creation)

SKIP_CI: external_deps - Requires imagemagick and takes >10s
"""

from __future__ import annotations

import os
from typing import Iterable, List

import matplotlib

matplotlib.use("Agg")  # Avoid GUI usage
import matplotlib.animation as animation
import matplotlib.image as mgimg
import matplotlib.pyplot as plt
import numpy as np
from py3plex.core import random_generators
from py3plex.utils import get_example_image_path

FRAME_NODE_COUNTS: List[int] = [100, 150, 200, 300, 500, 250, 600]
TMP_DIR = "/tmp/py3plex_animation"
OUTPUT_ANIMATION = get_example_image_path("animation.gif")
N_LAYERS = 6
EDGE_PROBABILITY = 0.005


def generate_frame(num_nodes: int, folder_tmp_files: str) -> str:
    """Generate and save a single snapshot for the animation."""
    print(f"  Generating network with {num_nodes} nodes...")
    multilayer_network = random_generators.random_multilayer_ER(
        num_nodes,
        N_LAYERS,
        EDGE_PROBABILITY,
        directed=False,
    )
    multilayer_network.visualize_network(show=False)
    output_file = os.path.join(folder_tmp_files, f"{num_nodes}.png")
    plt.savefig(output_file)
    plt.close()
    return output_file


def build_frames(folder_tmp_files: str, sizes: Iterable[int]) -> List[str]:
    """Render all frames and return their file paths."""
    frame_paths: List[str] = []
    for num_nodes in sizes:
        frame_paths.append(generate_frame(num_nodes, folder_tmp_files))
    return frame_paths


def create_animation(frame_paths: Iterable[str], destination: str) -> None:
    """Create a GIF animation from saved frame images."""
    fig = plt.figure(figsize=(10, 10))
    frames = []
    for frame_path in frame_paths:
        img = mgimg.imread(frame_path)
        imgplot = plt.imshow(img)
        frames.append([imgplot])

    print(f"Loaded {len(frames)} frames")
    anim = animation.ArtistAnimation(
        fig,
        frames,
        interval=1000,
        blit=True,
    )

    print(f"\nSaving animation as GIF...")
    try:
        anim.save(destination, writer="imagemagick", fps=1)
    except Exception as exc:  # pragma: no cover - logging only
        print(f"[X] Error saving animation: {exc}")
        print("  Note: This requires imagemagick to be installed.")
    else:
        print(f"[OK] Animation saved successfully to: {destination}")


def main() -> int:
    np.random.seed(42)

    print("=" * 70)
    print("NETWORK ANIMATION GENERATOR")
    print("=" * 70)

    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_ANIMATION), exist_ok=True)

    print(f"\nTemporary files will be saved to: {TMP_DIR}")
    print(f"Final animation will be saved to: {OUTPUT_ANIMATION}")

    print("\nGenerating network snapshots:")
    print("-" * 70)
    frame_paths = build_frames(TMP_DIR, FRAME_NODE_COUNTS)

    print("\nCreating animation from snapshots...")
    print("-" * 70)
    create_animation(frame_paths, OUTPUT_ANIMATION)

    print("\n" + "=" * 70)
    print("Animation generation complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
