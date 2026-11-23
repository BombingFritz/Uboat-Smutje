# Technik

## Aufbau eines UBOAT-Mods (beobachtet an Workshop-Mods 3247807531 und 2904931827)

```
<Mod>/
  Manifest.json        Name, Version, Beschreibung, Autor, supportedGameVersions, assemblyName, permissions, steamFileId
  Preview.png          Vorschaubild
  Data Sheets/*.xlsx   überschreiben Spielwerte zeilenweise über den Namen (Spalte "/" bzw. "Key")
  Bundles/<name>       Unity-Asset-Bundle (Bilder u. a.)
  Bundles/<name>.manifest
```

## Wie Symbole ersetzt werden

- Das Spiel sucht das Symbol eines Gegenstands unter dem Pfad `Icons/Equipment/<interner Name>`.
- Ein Mod liefert dazu ein Asset-Bundle mit je einem `Texture2D` und einem `Sprite` pro Symbol.
  Container-Pfade im Bundle sind klein geschrieben (`icons/equipment/vegetables`).
- Im Bundle steckt zusätzlich ein `Manifest`-Objekt der Spielklasse
  `DWS.Common.Resources.AssetBundleDescriptor` (Assembly `com.uboat.game.dll`) mit der Liste
  `containedAssets` (`path` wie `Icons/Equipment/Vegetables`, dazu eine `guid`).
- Lebensmittelsymbole: 102 x 98 px, RGBA32, ohne Mipmaps, Sprite mit 100 Pixeln pro Einheit.
- Die beobachteten Bundles sind mit Unity 2018.2.21f1 gebaut.
- Für Symbole ist keine Tabelle in `Data Sheets` nötig.

## Wie unser Bundle entsteht

Unity und die UBOAT-Modding-Werkzeuge stehen in der Cloud-Umgebung nicht zur Verfügung. `tools/build_bundle.py`
nimmt deshalb ein vorhandenes Symbol-Bundle als Gerüst, entfernt alle fremden Objekte samt `.resS`-Datei,
ersetzt die Bilddaten der drei Symbole durch unsere PNGs, baut Container, Preload-Tabelle und Manifest neu
auf und vergibt eigenen Bundle- und CAB-Namen (`uboat-smutje`). Ein eigener CAB-Name ist nötig, weil Unity
zwei Bundles mit gleichem CAB-Namen nicht gleichzeitig laden kann. `tests/test_bundle.py` prüft das Ergebnis.

Die `.manifest`-Datei neben dem Bundle hat `CRC: 0`. Ob das Spiel diese Datei überhaupt liest, ist
[UNGEKLÄRT]; mit CRC 0 prüft Unity beim Laden keine Prüfsumme.

## Spieltest (Nutzer, 23.11.2026)

- Das Spiel lädt den Mod samt Bundle im Format von Unity 2018.2; Manifest mit
  `supportedGameVersions: ["2026.1"]` und `steamFileId: 0` wird angenommen.
- Ananas und Bierdose erscheinen im Lager; das Spargel-Symbol war auf dem Screenshot nicht zu sehen.
- Die Mengenzahl steht oben rechts über dem Symbol. Symbole deshalb leicht nach links oben gesetzt
  (`icons/verschiebung.json`, zunächst 4 px links, 2 px oben); im Spiel noch nicht geprüft.

## Kombüse (für Phase 2)

Mod 3247807531 ändert in `Data Sheets/Entities.xlsx`, Blatt `Equipment`, die Zeile `Kitchen`, Spalte
`Parameters`: `ItemsMassLimit = 2000, DisciplinePerFoodType = 0.00002, FoodConsumptionRate = 0.00016`.
Das Spiel kennt also bereits einen Bonus je Lebensmittelsorte in der Kombüse (Disziplin), aber keine
Kombinationen. Die Werte des Grundspiels sind nicht bekannt.
