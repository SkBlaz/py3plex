"""
Create a professional hero banner for the Py3plex README.

This script creates a modern, polished hero banner (1200x300 px) with:
- Left side: Text block with gradient background and professional typography
- Right side: Network visualization with sophisticated overlay effects

The banner uses a premium design with gradients, shadows, and accent colors.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys

# Premium design constants
# Modern gradient background (blue-tinted dark gradient)
GRADIENT_START = (15, 23, 42)  # Dark slate blue
GRADIENT_END = (30, 41, 59)  # Slightly lighter slate
ACCENT_COLOR = (59, 130, 246)  # Bright blue accent
ACCENT_RGB = (59, 130, 246)  # RGB version for accents

# Text colors for dark background
TITLE_COLOR = "#FFFFFF"  # Pure white for title
TAGLINE_COLOR = "#E2E8F0"  # Light slate for tagline
SUBLINE_COLOR = "#94A3B8"  # Muted slate for subline
ACCENT_TEXT = "#3B82F6"  # Bright blue for accents

# Visual effects
OVERLAY_GRADIENT_START = 180  # Darker overlay on left
OVERLAY_GRADIENT_END = 40  # Lighter overlay on right
BLUR_RADIUS = 2  # Slightly more blur for sophistication


def create_gradient_background(width, height, start_color, end_color):
    """Create a smooth horizontal gradient background."""
    base = Image.new("RGB", (width, height), start_color)
    draw = ImageDraw.Draw(base)

    # Create horizontal gradient
    for x in range(width):
        # Calculate color for this x position
        ratio = x / width
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        draw.line([(x, 0), (x, height)], fill=(r, g, b))

    return base


def add_glow_effect(draw, position, text, font, color, glow_color, glow_radius=2):
    """Add a subtle glow effect to text for depth."""
    x, y = position
    # Draw glow layers
    for offset in range(glow_radius, 0, -1):
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, fill=glow_color, font=font)
    # Draw main text
    draw.text(position, text, fill=color, font=font)


def create_hero_banner(
    output_path="example_images/py3plex_hero_banner.png",
    source_image="example_images/multilayer_radial_compact.png",
    width=1200,
    height=300,
):
    """
    Create a professional hero banner for the Py3plex README.

    Args:
        output_path: Path where the banner will be saved
        source_image: Path to the network visualization to use
        width: Banner width in pixels (default: 1200)
        height: Banner height in pixels (default: 300)
    """

    # Create gradient background
    banner = create_gradient_background(width, height, GRADIENT_START, GRADIENT_END)
    draw = ImageDraw.Draw(banner)

    # --- Right side: Network visualization ---
    # Load the source network image
    try:
        network_img = Image.open(source_image)
        print(f"✓ Loaded source image: {source_image} ({network_img.size})")

        # Calculate dimensions for the right side (about 50% of banner width)
        right_width = int(width * 0.50)
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

        # Use LANCZOS resampling (compatible with older Pillow versions)
        try:
            network_img = network_img.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )
        except AttributeError:
            # Fallback for older Pillow versions
            network_img = network_img.resize((new_width, new_height), Image.LANCZOS)

        # Center crop to exact dimensions
        left = (new_width - right_width) // 2
        top = (new_height - height) // 2
        network_img = network_img.crop((left, top, left + right_width, top + height))

        # Apply a moderate blur for a sophisticated look
        network_img = network_img.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))

        # Paste the network image on the right side
        banner.paste(network_img, (right_x, 0))

        # Add a sophisticated gradient overlay from left to right
        # This creates depth and ensures text is readable
        overlay = Image.new("RGBA", (right_width, height))
        overlay_draw = ImageDraw.Draw(overlay)

        for x in range(right_width):
            # Gradient from darker on left to lighter on right
            ratio = x / right_width
            alpha = int(
                OVERLAY_GRADIENT_START
                - (OVERLAY_GRADIENT_START - OVERLAY_GRADIENT_END) * ratio
            )
            # Use gradient colors for overlay
            r = int(GRADIENT_START[0] + (GRADIENT_END[0] - GRADIENT_START[0]) * ratio)
            g = int(GRADIENT_START[1] + (GRADIENT_END[1] - GRADIENT_START[1]) * ratio)
            b = int(GRADIENT_START[2] + (GRADIENT_END[2] - GRADIENT_START[2]) * ratio)
            overlay_draw.line([(x, 0), (x, height)], fill=(r, g, b, alpha))

        banner_rgba = banner.convert("RGBA")
        banner_rgba.paste(overlay, (right_x, 0), overlay)
        banner = banner_rgba.convert("RGB")
        draw = ImageDraw.Draw(banner)

        print("✓ Network visualization applied to right side")

    except Exception as e:
        print(f"Warning: Could not load source image: {e}")
        print("Continuing with text-only banner...")

    # --- Left side: Professional text block ---
    left_margin = 50

    # Add subtle accent line on the left edge
    accent_line = Image.new("RGBA", (4, height))
    accent_draw = ImageDraw.Draw(accent_line)
    # Vertical gradient accent
    for y in range(height):
        ratio = y / height
        alpha = int(100 + 155 * ratio)  # Fade from semi to full
        accent_draw.line([(0, y), (4, y)], fill=(*ACCENT_RGB, alpha))
    banner_rgba = banner.convert("RGBA")
    banner_rgba.paste(accent_line, (0, 0), accent_line)
    banner = banner_rgba.convert("RGB")
    draw = ImageDraw.Draw(banner)

    # Try to load fonts with better sizing for impact
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
                title_font = ImageFont.truetype(font_path, 72)  # Larger, bolder title
                tagline_font = ImageFont.truetype(
                    font_path, 20
                )  # Slightly larger tagline
                subline_font = ImageFont.truetype(font_path, 14)
                break

        if title_font is None:
            # Fall back to default font
            title_font = ImageFont.load_default()
            tagline_font = ImageFont.load_default()
            subline_font = ImageFont.load_default()
            print(
                "! Using default font (consider installing DejaVu or Liberation fonts)"
            )
        else:
            print(f"✓ Using font: {font_path}")

    except Exception as e:
        print(f"! Font loading issue: {e}, using default font")
        title_font = ImageFont.load_default()
        tagline_font = ImageFont.load_default()
        subline_font = ImageFont.load_default()

    # Text content
    title = "Py3plex"
    tagline = "Multilayer network analysis and\nvisualization for Python and R users."
    subline = "Built on NetworkX · 50+ examples · Web GUI & CLI included"

    # Position text with better vertical rhythm
    y_start = 45

    # Draw title with subtle glow effect for depth
    draw.text((left_margin, y_start), title, fill=TITLE_COLOR, font=title_font)

    # Add accent underline under title
    title_bbox = draw.textbbox((left_margin, y_start), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    underline_y = title_bbox[3] + 8

    # Create underline with gradient effect using RGBA layer
    underline_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    underline_draw = ImageDraw.Draw(underline_layer)

    # Draw gradient underline with varying opacity on RGBA layer
    for i in range(4):
        opacity = 255 - i * 50
        line_width = 2 if i == 0 else 1
        underline_draw.line(
            [
                (left_margin, underline_y + i),
                (left_margin + int(title_width * 0.4), underline_y + i),
            ],
            fill=ACCENT_RGB + (opacity,),
            width=line_width,
        )

    # Composite the underline onto the banner
    banner_rgba = banner.convert("RGBA")
    banner_rgba = Image.alpha_composite(banner_rgba, underline_layer)
    banner = banner_rgba.convert("RGB")
    draw = ImageDraw.Draw(banner)

    # Draw tagline with better spacing
    tagline_y = underline_y + 20
    draw.text((left_margin, tagline_y), tagline, fill=TAGLINE_COLOR, font=tagline_font)

    # Draw subline with accent color for key terms
    subline_y = tagline_y + 70
    draw.text((left_margin, subline_y), subline, fill=SUBLINE_COLOR, font=subline_font)

    print("✓ Text content rendered")

    # Save the banner
    banner.save(output_path, "PNG", optimize=True)
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
        print(
            "   Replace: ![Py3plex Visualization Showcase](example_images/py3plex_showcase.png)"
        )
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
