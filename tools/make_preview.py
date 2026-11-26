"""Erzeugt mod/Uboat-Smutje/Preview.png aus den Symbolen (für Launcher und Workshop)."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

icons = Path(sys.argv[1] if len(sys.argv) > 1 else "icons")
out = Path(sys.argv[2] if len(sys.argv) > 2 else "mod/Uboat-Smutje/Preview.png")
names = ["Vegetables", "Canned Bread", "Exotic Fruits", "Coffee"]
img = Image.new("RGBA", (512, 512), (40, 46, 43, 255))
d = ImageDraw.Draw(img)
d.rectangle((0, 0, 511, 511), outline=(120, 96, 60, 255), width=8)
for i, n in enumerate(names):
    ic = Image.open(icons / f"{n}.png").convert("RGBA").resize((204, 196), Image.LANCZOS)
    x = 40 + (i % 2) * 228
    y = 40 + (i // 2) * 236
    d.rounded_rectangle((x - 6, y - 6, x + 210, y + 202), 10, fill=(58, 66, 62, 255))
    img.alpha_composite(ic, (x, y))
img.convert("RGB").save(out)
print("geschrieben:", out)
