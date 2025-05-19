import os
import argparse
from PIL import Image
from collections import Counter, defaultdict

colors = [
    "#000000",
    "#0000bc",
    "#0000fc",
    "#004058",
    "#005800",
    "#0058f8",
    "#006800",
    "#007800",
    "#0078f8",
    "#008888",
    "#00a800",
    "#00a844",
    "#00b800",
    "#00e8d8",
    "#00fcfc",
    "#3cbcfc",
    "#4428bc",
    "#503000",
    "#58d854",
    "#58f898",
    "#6844fc",
    "#6888fc",
    "#787878",
    "#7c7c7c",
    "#881400",
    "#940084",
    "#9878f8",
    "#a4e4fc",
    "#a80020",
    "#a81000",
    "#ac7c00",
    "#b8b8f8",
    "#b8f818",
    "#b8f8b8",
    "#b8f8d8",
    "#bcbcbc",
    "#d800cc",
    "#d8b8f8",
    "#d8f878",
    "#e40058",
    "#e45c10",
    "#f0d0b0",
    "#f83800",
    "#f85898",
    "#f87858",
    "#f878f8",
    "#f8a4c0",
    "#f8b800",
    "#f8b8f8",
    "#f8d878",
    "#f8d8f8",
    "#f8f8f8",
    "#fca044",
    "#fce0a8",
    "#fcfcfc",
]


def html_to_rgb(html_color):
    """Convert HTML color code to RGB tuple."""
    html_color = html_color.strip()
    if html_color.startswith("#"):
        html_color = html_color[1:]
    return tuple(int(html_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_html(rgb):
    """Convert RGB tuple to HTML color code."""
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def color_distance(color1, color2):
    """Calculate color distance in RGB space."""
    return sum((a - b) ** 2 for a, b in zip(color1, color2))


def find_closest_color(rgb, valid_colors):
    """Find the closest valid color to the given RGB value."""
    return min(valid_colors, key=lambda color: color_distance(rgb, color))


def quantize_image(image, valid_colors):
    """Map all colors in the image to valid NES colors."""
    result = Image.new("RGB", image.size)
    color_map = {}  # Cache for performance

    for y in range(image.height):
        for x in range(image.width):
            color = image.getpixel((x, y))
            if color not in color_map:
                color_map[color] = find_closest_color(color, valid_colors)
            result.putpixel((x, y), color_map[color])

    return result


def get_tile_colors(image, tile_x, tile_y):
    """Get unique colors in an 8x8 tile."""
    colors = set()
    for y in range(8):
        for x in range(8):
            if tile_x + x < image.width and tile_y + y < image.height:
                colors.add(image.getpixel((tile_x + x, tile_y + y)))
    return colors


def create_optimal_palettes(image, valid_colors, num_palettes=4, colors_per_palette=4):
    """Create optimal palettes for the image using color clustering."""
    # Get colors by tile and track which colors appear together
    tile_color_sets = []
    color_frequency = Counter()
    color_co_occurrence = defaultdict(Counter)

    # Process by 8x8 tiles
    for tile_y in range(0, image.height, 8):
        for tile_x in range(0, image.width, 8):
            tile_colors = list(get_tile_colors(image, tile_x, tile_y))
            if tile_colors:
                tile_color_sets.append(tile_colors)
                # Update color frequency
                for color in tile_colors:
                    color_frequency[color] += 1
                # Update co-occurrence matrix
                for color1 in tile_colors:
                    for color2 in tile_colors:
                        if color1 != color2:
                            color_co_occurrence[color1][color2] += 1

    # Find the most frequent color as the shared background color
    background_color = (
        color_frequency.most_common(1)[0][0] if color_frequency else valid_colors[0]
    )

    # Initialize palettes with the background color
    palettes = [[background_color] for _ in range(num_palettes)]

    # Get unique colors (excluding background)
    unique_colors = [c for c in color_frequency.keys() if c != background_color]

    # If we have very few colors, handle that case
    if len(unique_colors) <= num_palettes * (colors_per_palette - 1):
        # Just distribute colors evenly
        color_idx = 0
        for i in range(num_palettes):
            palette = palettes[i]
            while len(palette) < colors_per_palette and color_idx < len(unique_colors):
                palette.append(unique_colors[color_idx])
                color_idx += 1
            # Fill any remaining slots
            while len(palette) < colors_per_palette:
                palette.append(palette[-1] if palette else background_color)
        return palettes

    # For more complex images, use a clustering approach
    # Select initial seeds for each palette (besides background)
    remaining_colors = set(unique_colors)
    seeds = []

    # First seed is the most frequent non-background color
    for i in range(min(num_palettes, len(remaining_colors))):
        if i == 0:
            # Choose the most frequent color after background
            next_color = max(remaining_colors, key=lambda c: color_frequency[c])
        else:
            # Choose colors that are least similar to existing seeds
            next_color = max(
                remaining_colors,
                key=lambda c: min(color_distance(c, seed) for seed in seeds),
            )

        seeds.append(next_color)
        remaining_colors.remove(next_color)

    # Add each seed to its palette
    for i, seed in enumerate(seeds):
        palettes[i].append(seed)

    # Function to find best palette for a color based on co-occurrence
    def find_best_palette_for_color(color, palettes):
        best_score = -1
        best_palette_idx = 0

        for idx, palette in enumerate(palettes):
            if len(palette) >= colors_per_palette:
                continue  # Skip full palettes

            # Score based on co-occurrence with colors in this palette
            score = sum(color_co_occurrence[color][c] for c in palette)

            if score > best_score:
                best_score = score
                best_palette_idx = idx

        return best_palette_idx

    # Assign remaining colors to palettes based on co-occurrence
    sorted_colors = sorted(
        remaining_colors, key=lambda c: color_frequency[c], reverse=True
    )

    for color in sorted_colors:
        # Find best palette for this color
        best_idx = find_best_palette_for_color(color, palettes)

        # Add color to palette if there's room
        if len(palettes[best_idx]) < colors_per_palette:
            palettes[best_idx].append(color)

    # Fill any palettes that aren't full yet
    for palette in palettes:
        while len(palette) < colors_per_palette:
            # If palette has any colors, duplicate the last one
            if len(palette) > 1:
                palette.append(palette[-1])
            else:
                palette.append(background_color)

    return palettes


def find_best_palette(tile_colors, palettes):
    """Find the best palette for a set of tile colors."""
    best_palette_idx = 0
    best_score = -1

    for idx, palette in enumerate(palettes):
        # Count colors that can be represented
        score = sum(1 for color in tile_colors if color in palette)

        if score > best_score:
            best_score = score
            best_palette_idx = idx

    return best_palette_idx


def tile_to_chr_data(image, tile_x, tile_y, palette):
    """Convert an 8x8 tile to NES CHR format using the given palette."""
    # NES uses 2 bits per pixel, stored in 2 bit planes
    plane0 = bytearray(8)  # LSB of color index
    plane1 = bytearray(8)  # MSB of color index

    for y in range(8):
        for x in range(8):
            # Default to transparent (index 0)
            color_idx = 0

            # Get pixel color if within bounds
            if tile_x + x < image.width and tile_y + y < image.height:
                pixel = image.getpixel((tile_x + x, tile_y + y))

                # Find closest color in palette
                closest = find_closest_color(pixel, palette)
                color_idx = palette.index(closest)

            # Set bits according to color index
            if color_idx & 1:  # Bit 0
                plane0[y] |= 1 << (7 - x)
            if color_idx & 2:  # Bit 1
                plane1[y] |= 1 << (7 - x)

    # NES CHR format: 8 bytes of plane 0, then 8 bytes of plane 1
    return bytes(plane0) + bytes(plane1)


def process_image(image, valid_colors):
    """Process image into CHR data and create indexed BMP."""
    # First, quantize all colors to valid NES colors
    quantized = quantize_image(image, valid_colors)

    # Create optimal palettes
    palettes = create_optimal_palettes(quantized, valid_colors)

    # Prepare output data
    chr_data = bytearray()
    indexed_image = Image.new("RGB", image.size)

    # Process the image by pages (128x128)
    for page_y in range(0, image.height, 128):
        for page_x in range(0, image.width, 128):
            # Process each 8x8 tile within the page
            for tile_y in range(page_y, page_y + 128, 8):
                for tile_x in range(page_x, page_x + 128, 8):
                    # Skip if tile is out of image bounds
                    if tile_x >= image.width or tile_y >= image.height:
                        # Add empty tile to maintain format
                        chr_data.extend(bytes(16))
                        continue

                    # Get tile colors
                    tile_colors = get_tile_colors(quantized, tile_x, tile_y)

                    # Find best palette
                    palette_idx = find_best_palette(tile_colors, palettes)
                    palette = palettes[palette_idx]

                    # Convert tile to CHR format
                    tile_chr = tile_to_chr_data(quantized, tile_x, tile_y, palette)
                    chr_data.extend(tile_chr)

                    # Update indexed image
                    for y in range(8):
                        for x in range(8):
                            if tile_x + x < image.width and tile_y + y < image.height:
                                pixel = quantized.getpixel((tile_x + x, tile_y + y))
                                closest = find_closest_color(pixel, palette)
                                indexed_image.putpixel(
                                    (tile_x + x, tile_y + y), closest
                                )

    return chr_data, indexed_image, palettes


def save_palettes_to_dat(palettes, filename):
    """Save palette information to a .dat file."""
    with open(filename, "w") as f:
        for i, palette in enumerate(palettes):
            # Convert RGB tuples to HTML color codes
            palette_html = [rgb_to_html(color) for color in palette]
            # Write each palette on a single line, comma-separated
            f.write(",".join(palette_html) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Convert an image to NES CHR format")
    parser.add_argument("image", help="Path to the input image")
    parser.add_argument(
        "--output", "-o", help="Output base name (without extension)", default=None
    )

    args = parser.parse_args()

    # Default output name
    output_base = args.output if args.output else os.path.splitext(args.image)[0]

    # Load the image
    try:
        original_image = Image.open(args.image)
        print(
            f"Loaded image: {args.image} ({original_image.width}x{original_image.height})"
        )
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Convert to RGB mode if needed
    if original_image.mode != "RGB":
        original_image = original_image.convert("RGB")

    # Crop if needed
    width, height = original_image.size
    orig_width, orig_height = width, height

    # Crop width if needed
    if width > 128:
        print(f"Image width ({width}) exceeds 128 pixels, cropping to 128px width")
        width = 128

    # Adjust height to be divisible by 128
    height = (height // 128) * 128
    if height == 0:
        height = 128

    if width != orig_width or height != orig_height:
        print(f"Cropping image from {orig_width}x{orig_height} to {width}x{height}")
        cropped_image = original_image.crop((0, 0, width, height))
    else:
        cropped_image = original_image

    # Read valid NES colors
    try:
        with open("color.txt", "r") as f:
            valid_colors = [html_to_rgb(line) for line in colors if line.strip()]
        print(f"Loaded {len(valid_colors)} valid NES colors from color.txt")
    except Exception as e:
        print(f"Error reading color.txt: {e}")
        return

    # Process the image
    print("Processing image...")
    chr_data, indexed_image, palettes = process_image(cropped_image, valid_colors)

    # Save CHR file
    with open(f"{output_base}.chr", "wb") as f:
        f.write(chr_data)
    print(f"Saved CHR file: {output_base}.chr ({len(chr_data)} bytes)")

    # Save indexed BMP
    indexed_image.save(f"{output_base}_indexed.bmp")
    print(f"Saved indexed BMP: {output_base}_indexed.bmp")

    # Save palette to dat file
    palette_file = f"{output_base}_palette.dat"
    save_palettes_to_dat(palettes, palette_file)
    print(f"Saved palette file: {palette_file}")

    # Print palette information
    print("\nOptimal Palettes:")
    for i, palette in enumerate(palettes):
        palette_html = [rgb_to_html(color) for color in palette]
        print(f"Palette {i}: {palette_html}")


if __name__ == "__main__":
    main()
