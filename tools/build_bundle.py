"""Baut das Asset-Bundle von Uboat-Smutje aus den eigenen PNG-Symbolen.

Unity selbst wird nicht gebraucht. Als Gerüst dient ein vorhandenes UBOAT-Symbol-Bundle
(Unity 2018.2, Klasse DWS.Common.Resources.AssetBundleDescriptor). Aus dem Gerüst bleiben nur
die technischen Objekte (AssetBundle, MonoScript, Manifest) und je Symbol ein Texture2D/Sprite-Paar,
deren Bilddaten vollständig durch unsere PNGs ersetzt werden. Alle übrigen Objekte und die
.resS-Datei mit fremden Bilddaten werden entfernt; danach wird geprüft, dass nichts davon übrig ist.

Aufruf:
  python tools/build_bundle.py <gerüst-bundle> <symbolordner> <ausgabe-bundle>
"""
import hashlib
import sys
import uuid
from pathlib import Path

import UnityPy
from PIL import Image

BUNDLE_NAME = "uboat-smutje"
# Spielinterner Name des Gegenstands -> PNG-Datei im Symbolordner
ICONS = ["Vegetables", "Canned Bread", "Exotic Fruits"]
KEEP_TYPES = {"AssetBundle", "MonoScript"}
GUID_NS = uuid.UUID("6f0e1c8e-3b5a-4a59-9d0e-5b0a7a1f5e11")


def guid_for(path):
    return uuid.uuid5(GUID_NS, f"{BUNDLE_NAME}/{path}").hex


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
            img = Image.open(icon_dir / f"{tex.m_Name}.png").convert("RGBA")
            if img.size != (tex.m_Width, tex.m_Height):
                raise SystemExit(f"{tex.m_Name}: {img.size} statt {(tex.m_Width, tex.m_Height)}")
            tex.image = img
            tex.save()
            tex_by_name[tex.m_Name] = obj.path_id
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
