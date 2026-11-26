"""Baut das Asset-Bundle von Uboat-Smutje aus den eigenen PNG-Symbolen.

Unity selbst wird nicht gebraucht. Als Gerüst dient ein vorhandenes UBOAT-Symbol-Bundle
(Unity 2018.2, Klasse DWS.Common.Resources.AssetBundleDescriptor). Aus dem Gerüst bleiben nur
die technischen Objekte (AssetBundle, MonoScript, Manifest) und je Symbol ein Texture2D/Sprite-Paar,
deren Bilddaten vollständig durch unsere PNGs ersetzt werden (verschoben nach icons/verschiebung.json). Alle übrigen Objekte und die
.resS-Datei mit fremden Bilddaten werden entfernt; danach wird geprüft, dass nichts davon übrig ist.

Aufruf:
  python tools/build_bundle.py <gerüst-bundle> <symbolordner> <ausgabe-bundle>
"""
import hashlib
import struct
import sys
import uuid
from pathlib import Path

import UnityPy
from icon_offsets import shifted_icon

BUNDLE_NAME = "uboat-smutje"
# Spielinterner Name des Gegenstands -> PNG-Datei im Symbolordner
ICONS = ["Vegetables", "Canned Bread", "Exotic Fruits", "Coffee"]
KEEP_TYPES = {"AssetBundle", "MonoScript"}
GUID_NS = uuid.UUID("6f0e1c8e-3b5a-4a59-9d0e-5b0a7a1f5e11")


def guid_for(path):
    return uuid.uuid5(GUID_NS, f"{BUNDLE_NAME}/{path}").hex


def full_rect_sprite(tree):
    """Setzt Umriss und Zeichenbereich eines Sprites auf das volle Bildrechteck.

    Die Sprites im Gerüst haben einen engen Umriss ("Tight Mesh") nach den alten Bildern; das Spiel zeichnet
    nur innerhalb davon. Mit einem vollen Rechteck (Unity: Mesh Type "Full Rect") erscheint das ganze Bild.
    """
    rect, rd = tree["m_Rect"], tree["m_RD"]
    w, h, ppu = rect["width"], rect["height"], tree["m_PixelsToUnits"]
    px, py = tree["m_Pivot"]["x"] * w, tree["m_Pivot"]["y"] * h
    x0, x1, y0, y1 = -px / ppu, (w - px) / ppu, -py / ppu, (h - py) / ppu
    verts = [(x0, y1), (x1, y1), (x0, y0), (x1, y0)]
    pos = b"".join(struct.pack("<3f", x, y, 0.0) for x, y in verts)
    pos += b"\0" * (-len(pos) % 16)                     # Stream 1 beginnt 16-Byte-ausgerichtet
    rd["m_VertexData"]["m_VertexCount"] = 4
    rd["m_VertexData"]["m_DataSize"] = pos + b"\0" * (4 * 8)  # UV-Stream (2 x float), wie im Gerüst leer
    rd["m_IndexBuffer"] = struct.pack("<6H", 0, 1, 2, 2, 1, 3)
    sm = rd["m_SubMeshes"][0]
    sm.update({"firstByte": 0, "indexCount": 6, "baseVertex": 0, "firstVertex": 0, "vertexCount": 4})
    rd["m_SubMeshes"] = [sm]
    rd["textureRect"] = {"x": 0.0, "y": 0.0, "width": float(w), "height": float(h)}
    rd["textureRectOffset"] = {"x": 0.0, "y": 0.0}
    rd["settingsRaw"] = 0                                # nicht gepackt, Mesh Type Full Rect
    tree["m_PhysicsShape"] = [[{"x": x0, "y": y1}, {"x": x0, "y": y0}, {"x": x1, "y": y0}, {"x": x1, "y": y1}]]
    return tree


def build(template, icon_dir, out):
    env = UnityPy.load(str(template))
    bundle = next(iter(env.files.values()))
    cab_names = [n for n in bundle.files if not n.endswith(".resS")]
    assert len(cab_names) == 1, cab_names
    sf = bundle.files[cab_names[0]]

    wanted = {name.lower() for name in ICONS}
    keep, drop = {}, []
    for pid, obj in sf.objects.items():
        t = obj.type.name
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        if t in KEEP_TYPES or (t == "MonoBehaviour" and name == "Manifest"):
            keep[pid] = obj
        elif t in ("Texture2D", "Sprite") and name.lower() in wanted:
            keep[pid] = obj
        else:
            drop.append(pid)
    for pid in drop:
        del sf.objects[pid]

    # Bilddaten ersetzen (inline, ohne .resS)
    tex_by_name = {}
    for obj in sf.objects.values():
        if obj.type.name == "Texture2D":
            tex = obj.read()
            img = shifted_icon(icon_dir, tex.m_Name)
            if img.size != (tex.m_Width, tex.m_Height):
                raise SystemExit(f"{tex.m_Name}: {img.size} statt {(tex.m_Width, tex.m_Height)}")
            tex.image = img
            tex.save()
            tex_by_name[tex.m_Name] = obj.path_id
    for obj in sf.objects.values():
        if obj.type.name == "Sprite":
            obj.save_typetree(full_rect_sprite(obj.read_typetree()))
    missing = set(ICONS) - set(tex_by_name)
    if missing:
        raise SystemExit(f"Im Gerüst fehlen Symbole: {sorted(missing)}")

    # Manifest (AssetBundleDescriptor): nur noch unsere Pfade
    for obj in sf.objects.values():
        if obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            tree["containedAssets"] = [
                {"path": f"Icons/Equipment/{n}", "guid": guid_for(f"Icons/Equipment/{n}")} for n in sorted(ICONS)
            ] + [{"path": "Manifest", "guid": guid_for("Manifest")}]
            obj.save_typetree(tree)
            manifest_pid = obj.path_id

    # AssetBundle-Objekt: Name, Container und Preload-Tabelle neu aufbauen
    by_name = {}
    for obj in sf.objects.values():
        if obj.type.name in ("Texture2D", "Sprite"):
            by_name.setdefault(obj.read_typetree()["m_Name"], []).append(obj)
    script_pid = next(o.path_id for o in sf.objects.values() if o.type.name == "MonoScript")
    for obj in sf.objects.values():
        if obj.type.name != "AssetBundle":
            continue
        tree = obj.read_typetree()
        preload, container = [], []
        for name in sorted(ICONS):
            pair = sorted(by_name[name], key=lambda o: o.type.name, reverse=True)  # Texture2D, Sprite
            idx = len(preload)
            preload += [{"m_FileID": 0, "m_PathID": o.path_id} for o in pair]
            for o in pair:
                container.append((f"icons/equipment/{name.lower()}",
                                  {"preloadIndex": idx, "preloadSize": 2,
                                   "asset": {"m_FileID": 0, "m_PathID": o.path_id}}))
        idx = len(preload)
        preload += [{"m_FileID": 0, "m_PathID": manifest_pid}, {"m_FileID": 0, "m_PathID": script_pid}]
        container.append(("manifest", {"preloadIndex": idx, "preloadSize": 2,
                                       "asset": {"m_FileID": 0, "m_PathID": manifest_pid}}))
        tree["m_Name"] = BUNDLE_NAME
        tree["m_AssetBundleName"] = BUNDLE_NAME
        tree["m_PreloadTable"] = preload
        tree["m_Container"] = container
        obj.save_typetree(tree)

    # Eigener CAB-Name (zwei Bundles mit gleichem CAB-Namen lassen sich in Unity nicht gleichzeitig laden)
    new_cab = "CAB-" + hashlib.md5(BUNDLE_NAME.encode()).hexdigest()
    bundle.files = {new_cab: sf}

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bundle.save(packer="lz4"))
    write_manifest_txt(out)
    return out


def write_manifest_txt(out):
    lines = ["ManifestFileVersion: 0", "CRC: 0", "HashAppended: 0", "Assets:"]
    lines += [f"- Assets/Packages/{BUNDLE_NAME}/Icons/Equipment/{n}.png" for n in sorted(ICONS)]
    lines += [f"- Assets/Packages/{BUNDLE_NAME}/Manifest.asset", "Dependencies: []", ""]
    out.with_name(out.name + ".manifest").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    print("geschrieben:", build(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
