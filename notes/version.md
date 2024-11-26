# Version

Lenlab für MSPM0 hat die Lenlab Hauptversion 8.

Die Nebenversion wird für jede Veröffentlichung eins größer (8.0, 8.1, ...).
Die Nebenversion darf zweistellig werden, nicht jedoch dreistellig (8.10, 8.11, ..., 8.99)

Die Version kann ein Pre-Release-Kennzeichen erhalten (a, b, c) (alpha, beta, release candidate)
und eine einstellige Zahl (8.2a0)

Die Version kann eine einstellige dritte Ziffer erhalten (Bugfix-Release nach einem Release) (8.2.1)
Lenlab nimmt an, die Firm

Lenlab fragt die Firmware nach ihrer Version. In der Antwort ist die Version in 4 Bytes codiert,
"XXAY" wobei X die Ziffern der Nebenversion sind (ein oder zwei Ziffern),
A der Buchstabe für das Pre-Release (a, b oder c) und Y die Ziffer für das Pre-Release.
Bei kürzeren Versionen wird die Antwort rechts mit Null-Bytes aufgefüllt.
App und Firmware müssen die gleiche Version haben (Release und Pre-Release). Lenlab achtet nicht
auf die dritte Ziffer (Bugfix-Release). Ein Bugfix-Release enthält die gleiche Firmware (seit Version 8.1).

Die Version ist einzig im Firmware-Projekt in `version.h` gespeichert.

Nach Spezifikation der Version für Python-Pakete:
https://packaging.python.org/en/latest/specifications/version-specifiers/#version-specifiers
