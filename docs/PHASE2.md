# Phase 2: Gerichte aus Lebensmittelkombinationen (Entwurf, nicht begonnen)

## Ziel

Liegen bestimmte Lebensmittel gleichzeitig in der Kombüse, gibt es einen Bonus.

| Gericht | Zutaten | Bonus |
|---|---|---|
| Toast Hawaii | Exotische Früchte + Frisches Brot + Käse + Konserviertes Schweinefleisch | Stimmung +3 |

Weitere Gerichte legt der Nutzer fest.

## Was bekannt ist

- Lebensmittel sind Einträge im Blatt `Equipment` von `Entities.xlsx` mit dem Tag `Purpose:Food`.
- Die Kombüse (`Kitchen`) hat den Parameter `DisciplinePerFoodType`: Bonus je Sorte, nicht je Kombination.
- Mods können eigenen Code mitbringen (`assemblyName` im Manifest).

## Offene Fragen

- Was heißt „Stimmung +3“ im Spiel? Disziplin, Moral oder ein Wert der Besatzung? Und +3 pro was
  (einmalig, pro Tag, solange die Zutaten vorrätig sind)? [UNGEKLÄRT]
- Zählt „in der Kombüse vorhanden“ oder „verbraucht“?
- Gibt es im Spielcode einen Einstiegspunkt, an dem ein Code-Mod den Kombüsen-Vorrat lesen und einen
  Effekt vergeben kann? Dafür werden die Spieldateien (`UBOAT_Data\Managed\com.uboat.game.dll`) oder ein
  bestehender Code-Mod als Vorbild gebraucht.
