"""
Visualization Example: Creating Network Growth Animations

This example demonstrates how to:
1. Generate multiple network snapshots with varying sizes
2. Visualize each snapshot
3. Create an animated GIF showing network growth

The animation shows how network structure evolves as the number
of nodes increases, useful for understanding scaling properties.

Requirements:
- matplotlib
- imagemagick (for GIF creation)

SKIP_CI: external_deps - Requires imagemagick and takes >10s
"""

import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from py3plex.core import random_generators
import matplotlib.image as mgimg
from py3plex.utils import get_dataset_path, get_example_image_path

print("=" * 70)
print("NETWORK ANIMATION GENERATOR")
print("=" * 70)

# Configure animation settings
folder_tmp_files = get_dataset_path("animation")
output_animation = get_example_image_path("animation.gif")

# Ensure output directory exists
os.makedirs(folder_tmp_files, exist_ok=True)
os.makedirs(os.path.dirname(output_animation), exist_ok=True)

print(f"\nTemporary files will be saved to: {folder_tmp_files}")
print(f"Final animation will be saved to: {output_animation}")


def animate(num_nodes):
    """
    Generate and save a network visualization for a given number of nodes.
    
    Args:
        num_nodes: Number of nodes in the generated network
    """
    print(f"  Generating network with {num_nodes} nodes...")
    
    # Generate random Erdős-Rényi multilayer network
    ER_multilayer = random_generators.random_multilayer_ER(
        num_nodes,  # Number of nodes (varies)
        6,          # Number of layers (constant)
        0.005,      # Edge probability (sparse network)
        directed=False
    )
    
    # Visualize without showing (save directly)
    ER_multilayer.visualize_network(show=False)
    
    # Save the visualization
    output_file = f"{folder_tmp_files}{num_nodes}.png"
    plt.savefig(output_file)
    plt.close()  # Close figure to free memory


# Define network sizes for animation frames
# Shows growth from 100 to 600 nodes with non-linear progression
imrange = [100, 150, 200, 300, 500, 250, 600]

print("\nGenerating network snapshots:")
print("-" * 70)

# Generate all network visualizations
for num_nodes in imrange:
    animate(num_nodes)

print("\nCreating animation from snapshots...")
print("-" * 70)

# Create figure for animation
fig = plt.figure(figsize=(10, 10))

# Load all images into animation frames
myimages = []
for num_nodes in imrange:
    img_path = f"{folder_tmp_files}{num_nodes}.png"
    img = mgimg.imread(img_path)
    imgplot = plt.imshow(img)
    myimages.append([imgplot])

print(f"Loaded {len(myimages)} frames")

# Create the animation
# interval=1000 means 1 second per frame
my_anim = animation.ArtistAnimation(
    fig, 
    myimages, 
    interval=1000,  # Milliseconds between frames
    blit=True       # Optimize rendering
)

print(f"\nSaving animation as GIF...")
try:
    # Save as GIF using imagemagick
    # fps=1 means 1 frame per second
    my_anim.save(output_animation, writer='imagemagick', fps=1)
    print(f"✓ Animation saved successfully to: {output_animation}")
except Exception as e:
    print(f"✗ Error saving animation: {e}")
    print("  Note: This requires imagemagick to be installed.")
    print("  Install with: sudo apt-get install imagemagick (Linux)")
    print("               or: brew install imagemagick (macOS)")

print("\n" + "=" * 70)
print("Animation generation complete!")
print("=" * 70)
