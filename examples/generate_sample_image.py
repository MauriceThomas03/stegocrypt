"""
Generates a simple gradient PNG (examples/cover.png) so you have something
to test the tool with immediately, without needing to source your own image.
"""

from PIL import Image
import os

def main():
    width, height = 500, 500
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    for x in range(width):
        for y in range(height):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = int(255 * (x + y) / (width + height))
            pixels[x, y] = (r, g, b)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "cover.png")
    img.save(out_path)
    print(f"Sample cover image created at {out_path}")

if __name__ == "__main__":
    main()
