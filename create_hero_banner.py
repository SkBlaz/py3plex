"""
Create a clean hero banner for the Py3plex README.

This script creates a modern, GitHub-friendly hero banner (1200x300 px) with:
- Left side: Text block with title, tagline, and features
- Right side: Network visualization image with semi-transparent overlay

The banner is designed to be readable on both light and dark GitHub themes.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys


def create_hero_banner(
    output_path="example_images/py3plex_hero_banner.png",
    source_image="example_images/multilayer_radial_compact.png",
    width=1200,
    height=300,
):
    """
    Create a hero banner for the Py3plex README.
    
    Args:
        output_path: Path where the banner will be saved
        source_image: Path to the network visualization to use
        width: Banner width in pixels (default: 1200)
        height: Banner height in pixels (default: 300)
    """
    
    # Create a new image with a neutral background
    # Using a light gray that works well on both light and dark themes
    banner = Image.new('RGB', (width, height), color='#F6F8FA')
    draw = ImageDraw.Draw(banner)
    
    # --- Right side: Network visualization ---
    # Load the source network image
    try:
        network_img = Image.open(source_image)
        print(f"✓ Loaded source image: {source_image} ({network_img.size})")
        
        # Calculate dimensions for the right side (about 55% of banner width)
        right_width = int(width * 0.55)
        right_x = width - right_width
        
        # Resize and crop the network image to fit the right side
        # Maintain aspect ratio and center crop
        aspect_ratio = network_img.width / network_img.height
        if aspect_ratio > (right_width / height):
            # Image is wider - fit to height
            new_height = height
            new_width = int(height * aspect_ratio)
        else:
            # Image is taller - fit to width
            new_width = right_width
            new_height = int(right_width / aspect_ratio)
        
        network_img = network_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center crop to exact dimensions
        left = (new_width - right_width) // 2
        top = (new_height - height) // 2
        network_img = network_img.crop((left, top, left + right_width, top + height))
        
        # Apply a slight blur for subtle effect
        network_img = network_img.filter(ImageFilter.GaussianBlur(radius=1))
        
        # Paste the network image on the right side
        banner.paste(network_img, (right_x, 0))
        
        # Add a semi-transparent overlay to the right side to soften the image
        overlay = Image.new('RGBA', (right_width, height), color=(246, 248, 250, 100))
        banner_rgba = banner.convert('RGBA')
        banner_rgba.paste(overlay, (right_x, 0), overlay)
        banner = banner_rgba.convert('RGB')
        draw = ImageDraw.Draw(banner)
        
        print(f"✓ Network visualization applied to right side")
        
    except Exception as e:
        print(f"Warning: Could not load source image: {e}")
        print(f"Continuing with text-only banner...")
    
    # --- Left side: Text block ---
    left_margin = 40
    text_width = int(width * 0.45) - left_margin
    
    # Try to load fonts, fall back to default if not available
    try:
        # Try to use a clean, modern font
        # These are common system fonts on Linux/macOS/Windows
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        
        title_font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                title_font = ImageFont.truetype(font_path, 60)
                tagline_font = ImageFont.truetype(font_path, 18)
                subline_font = ImageFont.truetype(font_path, 14)
                break
        
        if title_font is None:
            # Fall back to default font
            title_font = ImageFont.load_default()
            tagline_font = ImageFont.load_default()
            subline_font = ImageFont.load_default()
            print("! Using default font (consider installing DejaVu or Liberation fonts)")
        else:
            print(f"✓ Using font: {font_path}")
            
    except Exception as e:
        print(f"! Font loading issue: {e}, using default font")
        title_font = ImageFont.load_default()
        tagline_font = ImageFont.load_default()
        subline_font = ImageFont.load_default()
    
    # Text content
    title = "Py3plex"
    tagline = "Multilayer network analysis &\nvisualization for Python and R users."
    subline = "Built on NetworkX · 50+ examples · Web GUI & CLI included"
    
    # Text colors (dark gray, readable on light background)
    title_color = '#24292F'      # GitHub's primary text color
    text_color = '#57606A'       # GitHub's secondary text color
    
    # Position text vertically centered with proper spacing
    y_start = 50
    
    # Draw title
    draw.text((left_margin, y_start), title, fill=title_color, font=title_font)
    
    # Draw tagline (with line breaks)
    tagline_y = y_start + 80
    draw.text((left_margin, tagline_y), tagline, fill=text_color, font=tagline_font)
    
    # Draw subline
    subline_y = tagline_y + 75
    draw.text((left_margin, subline_y), subline, fill=text_color, font=subline_font)
    
    # Add a subtle vertical separator line between text and image
    separator_x = int(width * 0.45)
    draw.line([(separator_x, 40), (separator_x, height - 40)], 
              fill='#D0D7DE', width=2)
    
    print(f"✓ Text content rendered")
    
    # Save the banner
    banner.save(output_path, 'PNG', optimize=True)
    print(f"\n✓ Hero banner created successfully: {output_path}")
    print(f"  Dimensions: {width}x{height} px")
    print(f"  File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    
    return output_path


def main():
    """Main entry point for the script."""
    print("=" * 70)
    print("CREATING PY3PLEX HERO BANNER")
    print("=" * 70)
    print()
    
    # Configuration
    # You can change these paths if needed:
    source_image = "example_images/multilayer_radial_compact.png"
    output_path = "example_images/py3plex_hero_banner.png"
    
    # Alternative source images you can try:
    # - "example_images/multilayer.png" (simpler, cleaner)
    # - "example_images/multilayer_flow.png" (colorful flow visualization)
    # - "example_images/multilayer_sankey_diagram.png" (sankey style)
    
    print(f"Source image: {source_image}")
    print(f"Output path: {output_path}")
    print()
    
    # Create the banner
    try:
        create_hero_banner(
            output_path=output_path,
            source_image=source_image,
            width=1200,
            height=300,
        )
        
        print()
        print("=" * 70)
        print("SUCCESS")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Review the generated banner: example_images/py3plex_hero_banner.png")
        print("2. Update README.md to use the new banner:")
        print("   Replace: ![Py3plex Visualization Showcase](example_images/py3plex_showcase.png)")
        print("   With:    ![Py3plex](example_images/py3plex_hero_banner.png)")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error creating banner: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
