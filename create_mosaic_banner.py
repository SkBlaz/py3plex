"""
Create a mosaic banner showcasing all py3plex visualization types.

This script creates an attractive mosaic banner combining the best examples
of py3plex visualizations for use in the README.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec
import numpy as np
from PIL import Image


def load_and_resize_image(image_path, target_height=None, target_width=None):
    """Load and optionally resize an image."""
    try:
        img = Image.open(image_path)
        
        if target_height or target_width:
            # Calculate aspect ratio
            aspect_ratio = img.width / img.height
            
            if target_height and not target_width:
                target_width = int(target_height * aspect_ratio)
            elif target_width and not target_height:
                target_height = int(target_width / aspect_ratio)
            
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        return np.array(img)
    except Exception as e:
        print(f"Error loading {image_path}: {e}")
        return None


def create_mosaic_banner():
    """Create a mosaic banner from existing example images."""
    
    base_dir = "/home/runner/work/py3plex/py3plex/example_images"
    
    # Select the most representative and attractive visualizations
    # These showcase different visualization types
    selected_images = [
        # Row 1: Multilayer visualizations
        "multilayer.png",
        "multilayer_edge_projection_spring.png",
        "multilayer_radial_with_inter.png",
        
        # Row 2: Different layout styles
        "multilayer_small_multiples_shared.png",
        "multilayer_supra_heatmap_inter.png",
        "hairball.png",
        
        # Row 3: Analysis and special visualizations
        "communities.png",
        "embedding.png",
        "temporal.png",
    ]
    
    # Create figure with a nice layout
    fig = plt.figure(figsize=(20, 12), facecolor='white')
    
    # Use GridSpec for flexible layout
    gs = GridSpec(3, 3, figure=fig, wspace=0.05, hspace=0.05,
                  left=0.02, right=0.98, top=0.98, bottom=0.02)
    
    # Load and display images
    for idx, img_name in enumerate(selected_images):
        if idx >= 9:  # Safety check
            break
        
        img_path = os.path.join(base_dir, img_name)
        
        if not os.path.exists(img_path):
            print(f"Warning: {img_path} not found, skipping")
            continue
        
        row = idx // 3
        col = idx % 3
        
        ax = fig.add_subplot(gs[row, col])
        
        try:
            img = mpimg.imread(img_path)
            ax.imshow(img)
            ax.axis('off')
            
            # Add subtle title/caption
            viz_name = img_name.replace('_', ' ').replace('.png', '').title()
            if viz_name.startswith('Multilayer'):
                viz_name = viz_name.replace('Multilayer', 'Multilayer:')
            
            # Add text label at the top
            ax.text(0.5, 0.98, viz_name,
                   transform=ax.transAxes,
                   fontsize=10,
                   weight='bold',
                   ha='center',
                   va='top',
                   bbox=dict(boxstyle='round,pad=0.5',
                           facecolor='white',
                           edgecolor='none',
                           alpha=0.8))
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            ax.text(0.5, 0.5, f'Image not available:\n{img_name}',
                   ha='center', va='center', fontsize=10)
            ax.axis('off')
    
    # Save the mosaic
    output_path = os.path.join(base_dir, "py3plex_mosaic_banner.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"\n✓ Mosaic banner created: {output_path}")
    
    plt.close()
    
    return output_path


def create_compact_banner():
    """Create a more compact horizontal banner for README header."""
    
    base_dir = "/home/runner/work/py3plex/py3plex/example_images"
    
    # Select 5-6 most visually striking images for a compact banner
    selected_images = [
        "multilayer.png",
        "multilayer_edge_projection_spring.png",
        "multilayer_radial_with_inter.png",
        "multilayer_supra_heatmap_inter.png",
        "hairball.png",
        "communities.png",
    ]
    
    # Create horizontal banner
    fig = plt.figure(figsize=(24, 4), facecolor='white')
    gs = GridSpec(1, 6, figure=fig, wspace=0.03, hspace=0.03,
                  left=0.01, right=0.99, top=0.95, bottom=0.05)
    
    for idx, img_name in enumerate(selected_images):
        if idx >= 6:
            break
        
        img_path = os.path.join(base_dir, img_name)
        
        if not os.path.exists(img_path):
            print(f"Warning: {img_path} not found, skipping")
            continue
        
        ax = fig.add_subplot(gs[0, idx])
        
        try:
            img = mpimg.imread(img_path)
            ax.imshow(img)
            ax.axis('off')
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
    
    # Save the compact banner
    output_path = os.path.join(base_dir, "py3plex_banner_horizontal.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"✓ Compact banner created: {output_path}")
    
    plt.close()
    
    return output_path


def create_showcase_collage():
    """Create a sophisticated showcase collage with diagonal layout featured prominently."""
    
    base_dir = "/home/runner/work/py3plex/py3plex/example_images"
    
    # Create a figure with custom layout emphasizing the diagonal layout
    fig = plt.figure(figsize=(24, 10), facecolor='#f8f9fa')
    
    # Create a custom grid with tighter spacing and diagonal layout as hero
    # Reduced spacing: wspace and hspace from 0.08 to 0.03
    gs = GridSpec(4, 7, figure=fig, wspace=0.03, hspace=0.03,
                  left=0.01, right=0.99, top=0.96, bottom=0.04)
    
    # Define layout: (row_start, row_end, col_start, col_end, image_name)
    # Featured: diagonal/multilayer visualization takes prominent center-left position
    layout = [
        # HERO: Large diagonal layout visualization (featured prominently)
        (0, 3, 0, 3, "multilayer.png"),
        
        # Secondary visualizations - compact grid on right
        # Top row - different multilayer visualization styles
        (0, 1, 3, 4, "multilayer_edge_projection_spring.png"),
        (0, 1, 4, 5, "multilayer_radial_with_inter.png"),
        (0, 1, 5, 6, "multilayer_small_multiples_shared.png"),
        (0, 1, 6, 7, "multilayer_supra_heatmap_inter.png"),
        
        # Middle row - analysis visualizations
        (1, 2, 3, 4, "communities.png"),
        (1, 2, 4, 5, "embedding.png"),
        (1, 2, 5, 6, "hairball.png"),
        (1, 2, 6, 7, "temporal.png"),
        
        # Bottom row - compact secondary images
        (2, 3, 3, 4, "multilayer_ego_circular.png"),
        (2, 3, 4, 5, "multilayer_radial_compact.png"),
        (2, 3, 5, 6, "networkx_wrapper.png"),
        (2, 3, 6, 7, "spreading.png"),
        
        # Bottom row spanning full width - wider analysis examples
        (3, 4, 0, 2, "biomine_community.png"),
        (3, 4, 2, 4, "complete_analysis.png"),
        (3, 4, 4, 7, "multiplex.png"),
    ]
    
    for row_start, row_end, col_start, col_end, img_name in layout:
        img_path = os.path.join(base_dir, img_name)
        
        if not os.path.exists(img_path):
            print(f"Warning: {img_path} not found, skipping")
            continue
        
        ax = fig.add_subplot(gs[row_start:row_end, col_start:col_end])
        
        try:
            img = mpimg.imread(img_path)
            ax.imshow(img)
            ax.axis('off')
            
            # Add subtle border only for hero image to emphasize it
            if img_name == "multilayer.png":
                for spine in ax.spines.values():
                    spine.set_edgecolor('#0066cc')
                    spine.set_linewidth(3)
            
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            ax.axis('off')
    
    # Add title with emphasis on diagonal layout feature
    fig.text(0.5, 0.98, 'Py3plex: Multilayer Network Analysis & Visualization',
             ha='center', va='top', fontsize=20, weight='bold',
             color='#212529')
    fig.text(0.5, 0.965, 'Featuring diagonal projection-based multilayer network visualization',
             ha='center', va='top', fontsize=11, style='italic',
             color='#495057')
    
    # Save the showcase
    output_path = os.path.join(base_dir, "py3plex_showcase.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor='#f8f9fa', edgecolor='none')
    print(f"✓ Showcase collage created: {output_path}")
    
    plt.close()
    
    return output_path


if __name__ == "__main__":
    print("=" * 70)
    print("CREATING PY3PLEX VISUALIZATION MOSAIC BANNERS")
    print("=" * 70)
    
    # Create all three styles
    print("\n1. Creating main mosaic banner (3x3 grid)...")
    mosaic_path = create_mosaic_banner()
    
    print("\n2. Creating compact horizontal banner...")
    banner_path = create_compact_banner()
    
    print("\n3. Creating showcase collage...")
    showcase_path = create_showcase_collage()
    
    print("\n" + "=" * 70)
    print("BANNER CREATION COMPLETE")
    print("=" * 70)
    print(f"\nGenerated files:")
    print(f"  - {mosaic_path}")
    print(f"  - {banner_path}")
    print(f"  - {showcase_path}")
    print(f"\nThese banners showcase the diverse visualization capabilities of py3plex")
    print(f"and can be used in README.md or documentation.")
