"""Verschiebt Symbole innerhalb ihrer 102 x 98 px nach icons/verschiebung.json (ohne etwas abzuschneiden)."""
import json
from pathlib import Path

from PIL import Image


def load_offsets(icon_dir):
    f = Path(icon_dir) / "verschiebung.json"
    if not f.exists():
        return {}
    data = json.loads(f.read_text(encoding="utf-8"))
    return {k: tuple(v) for k, v in data.items() if not k.startswith("_")}


def shifted_icon(icon_dir, name):
    """Liefert das Symbol als RGBA, verschoben um den Wert aus verschiebung.json."""
    img = Image.open(Path(icon_dir) / f"{name}.png").convert("RGBA")
    dx, dy = load_offsets(icon_dir).get(name, (0, 0))
    if (dx, dy) == (0, 0):
        return img
    bbox = img.getchannel("A").getbbox()
    if bbox:
        x0, y0, x1, y1 = bbox
        if x0 + dx < 0 or y0 + dy < 0 or x1 + dx > img.width or y1 + dy > img.height:
            raise SystemExit(f"{name}: Verschiebung {dx},{dy} würde sichtbare Pixel abschneiden (Inhalt {bbox})")
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (dx, dy))
    return out
