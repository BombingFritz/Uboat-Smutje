# Changelog

## [Unveröffentlicht]

### Neu
- Phase 1: neue Symbole für Gemüse (weißer Spargel), Dosenbrot (Bierdose) und Exotische Früchte (Ananas)
  als Asset-Bundle `uboat-smutje`, Version 0.1.0 im Manifest. Bilder vom Nutzer (ersetzen die ersten
  gezeichneten Entwürfe).
- Werkzeuge zum Bauen des Bundles und für das Vorschaubild; Test des Bundles.
  `tools/draw_icons.py` (Entwürfe) überschreibt vorhandene Bilder nur noch mit `--force`.
- Doku zum Aufbau von UBOAT-Mods und Entwurf für Phase 2.

- Symbole beim Bau verschiebbar über `icons/verschiebung.json`; alle drei 4 px nach links und 2 px nach oben,
  damit die Mengenzahl weniger verdeckt.

- Kaffee (`Coffee`) zeigt ein Pervitin-Röhrchen (Bild vom Nutzer); Name und Wirkung unverändert.

### Behoben
- Oberer Teil der Bierdose (Deckel) fehlte im Spiel: Die Sprites hatten noch den engen Umriss der Gerüst-Bilder.
  Umriss und Zeichenbereich sind jetzt das volle Bild 102 x 98.

### Geprüft
- Im Spiel (Nutzer): Mod lädt, Spargel, Ananas und Bierdose erscheinen.

### Noch nicht geprüft
- Im Spiel: Kaffee-Symbol; vollständige Bierdose nach der Korrektur des Umrisses und Lage der Symbole nach der Verschiebung.
