# Version

2024-09-30

Lenlab für MSPM0 hat die Lenlab Hauptversion 8.

Die Nebenversion wird für jede Veröffentlichung eins größer (8.0, 8.1, ...).
Die Nebenversion darf zweistellig werden, nicht jedoch dreistellig (8.10, 8.11, ..., 8.99)

Die Version kann ein Pre-Release-Kennzeichen erhalten (a, b, c) (alpha, beta, release candidate)
und eine einstellige Zahl (8.2a0)

Lenlab fragt die Firmware nach ihrer Version. In der Antwort ist die Version in 4 Bytes codiert,
"XXaY" wobei X die Ziffern der Nebenversion sind (ein oder zwei Ziffern),
a der Buchstabe für das Pre-Release (a, b oder c) und Y die Ziffer für das Pre-Release.
Bei kürzeren Versionen wird die Antwort rechts mit Nullen aufgefüllt.

Die Version ist einzig im Firmware-Projekt in `version.h` gespeichert.

Nach Spezifikation der Version für Python-Pakete:
https://packaging.python.org/en/latest/specifications/version-specifiers/#version-specifiers

## Python

`hatch version` gibt die Version aus.

`hatch version minor` erhöht die zweite Versionszahl nach dem Punkt.

`hatch version alpha` fügt ein "a0" an oder erhöht die Ziffer "a1".

Hatch und Hatchling lesen und schreiben die Version in der Header-Datei `version.h`.

Lenlab kennt (nur) die Version des installierten Python-Pakets.
Mit einem editable install im virtual environment funktioniert das auch während der Entwicklung.

Bei Versionsänderung muss der editable install aktualisiert werden.

`uv pip install -e .`
