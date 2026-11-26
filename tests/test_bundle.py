"""Prüft das gebaute Bundle: nur unsere drei Symbole, Bilder pixelgleich, keine fremden Reste.

Aufruf: python tests/test_bundle.py   (aus dem Repo-Wurzelordner; braucht UnityPy und Pillow)
"""
import struct
import sys
from pathlib import Path

import UnityPy
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from icon_offsets import load_offsets, shifted_icon  # noqa: E402

BUNDLE = ROOT / "mod" / "Uboat-Smutje" / "Bundles" / "uboat-smutje"
ICONS = ROOT / "icons"
EXPECTED = {"Vegetables", "Canned Bread", "Exotic Fruits", "Coffee"}
fails = 0


def check(ok, msg):
    global fails
    print(("OK   " if ok else "FAIL ") + msg)
    fails += 0 if ok else 1


env = UnityPy.load(str(BUNDLE))
bundle = next(iter(env.files.values()))
check(len(bundle.files) == 1 and not any(n.endswith(".resS") for n in bundle.files),
      f"genau eine Datei im Bundle, keine .resS ({list(bundle.files)})")

types = {}
for obj in env.objects:
    types.setdefault(obj.type.name, []).append(obj)
check(sorted(types) == ["AssetBundle", "MonoBehaviour", "MonoScript", "Sprite", "Texture2D"],
      f"nur erwartete Objekttypen ({sorted(types)})")

tex_names = {o.read().m_Name for o in types.get("Texture2D", [])}
spr_names = {o.read().m_Name for o in types.get("Sprite", [])}
check(tex_names == EXPECTED, f"Texturen: {sorted(tex_names)}")
check(spr_names == EXPECTED, f"Sprites: {sorted(spr_names)}")

for o in types.get("Texture2D", []):
    tex = o.read()
    src = shifted_icon(ICONS, tex.m_Name)
    diff = ImageChops.difference(tex.image.convert("RGBA"), src).getbbox()
    off = load_offsets(ICONS).get(tex.m_Name, (0, 0))
    check(diff is None, f"{tex.m_Name}: Bild im Bundle pixelgleich mit icons/{tex.m_Name}.png, verschoben um {off}")
    orig = Image.open(ICONS / f"{tex.m_Name}.png").convert("RGBA")
    check(src.getchannel("A").histogram() == orig.getchannel("A").histogram(),
          f"{tex.m_Name}: durch die Verschiebung nichts abgeschnitten")
    check((tex.m_Width, tex.m_Height) == (102, 98), f"{tex.m_Name}: 102 x 98 px")

for o in types.get("Sprite", []):
    spr = o.read()
    check(spr.m_RD.texture.read().m_Name == spr.m_Name, f"Sprite {spr.m_Name} zeigt auf eigene Textur")
    # Früherer Fehler: Umriss aus dem Gerüst schnitt im Spiel den Deckel der Bierdose ab
    t = o.read_typetree()
    rd = t["m_RD"]
    n = rd["m_VertexData"]["m_VertexCount"]
    pts = struct.unpack(f"<{n * 3}f", bytes(rd["m_VertexData"]["m_DataSize"])[:n * 12])
    xs, ys = pts[0::3], pts[1::3]
    ppu = t["m_PixelsToUnits"]
    full = (round((max(xs) - min(xs)) * ppu, 3), round((max(ys) - min(ys)) * ppu, 3)) == (102.0, 98.0)
    tr = rd["textureRect"]
    check(n == 4 and full and rd["settingsRaw"] == 0, f"Sprite {spr.m_Name}: Umriss ist das volle Rechteck 102 x 98")
    check((tr["x"], tr["y"], tr["width"], tr["height"]) == (0, 0, 102, 98), f"Sprite {spr.m_Name}: Zeichenbereich ist das volle Bild")

ab = types["AssetBundle"][0].read_typetree()
check(ab["m_Name"] == ab["m_AssetBundleName"] == "uboat-smutje", "Bundle-Name uboat-smutje")
paths = {p for p, _ in ab["m_Container"]}
check(paths == {f"icons/equipment/{n.lower()}" for n in EXPECTED} | {"manifest"}, f"Container: {sorted(paths)}")
pids = {o.path_id for objs in types.values() for o in objs}
check(all(p["m_PathID"] in pids for p in ab["m_PreloadTable"]), "Preload-Tabelle verweist nur auf vorhandene Objekte")
for _, info in ab["m_Container"]:
    i, n = info["preloadIndex"], info["preloadSize"]
    check(info["asset"]["m_PathID"] in [p["m_PathID"] for p in ab["m_PreloadTable"][i:i + n]],
          f"Container-Eintrag {info['asset']['m_PathID']} liegt in seinem Preload-Bereich")

man = types["MonoBehaviour"][0].read_typetree()
check({a["path"] for a in man["containedAssets"]} == {f"Icons/Equipment/{n}" for n in EXPECTED} | {"Manifest"},
      "Manifest listet nur unsere Pfade")
script = types["MonoScript"][0].read_typetree()
check((script["m_Namespace"], script["m_ClassName"]) == ("DWS.Common.Resources", "AssetBundleDescriptor"),
      "Manifest-Skript ist die Spielklasse AssetBundleDescriptor")

raw = b"".join(f.save() for f in bundle.files.values())
for word in (b"authentic", b"Pervitin", b"MedKit", b"Sausages", b"Cheese", b"Potatoes"):
    check(word.lower() not in raw.lower(), f"keine Reste von {word.decode()} im Bundle")

print(f"\n{fails} Fehler" if fails else "\nAlle Prüfungen bestanden")
sys.exit(1 if fails else 0)
