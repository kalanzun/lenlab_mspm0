# Lenlab 8 for MSPM0G3507

This project is under development and not ready for use.

Dieses Projekt ist in Entwicklung und nicht bereit zur Nutzung.

## Installation (uv)

Starten Sie das Programm "Terminal".

Installieren Sie `uv`:

Windows:

```shell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

MacOS oder Linux:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Weitere Informationen zur Installation finden Sie in der Dokumentation zu `uv`:
https://docs.astral.sh/uv/getting-started/installation/

Schließen Sie das Terminal und starten Sie es neu, dann findet es die eben installierten Kommandos `uv` und `uvx`.

## Lenlab Starten

```shell
uvx lenlab
```

`uvx` lädt Lenlab herunter und führt es aus.

## Lenlab Testen

Halten Sie die Taste S1 des Launchpads neben der grünen LED gedrückt und drücken Sie kurz auf die Taste RESET (NRST) neben
dem USB-Stecker. Der Mikrocontroller startet den "Bootstrap Loader" für das Programmieren (Flashen) einer
neuen Firmware. Sie haben dann 10 Sekunden Zeit, das Programmieren zu starten. Danach schläft der Mikrocontroller ein
und braucht ein neues S1 + RESET zum Aufwachen. Tipp: Den folgenden Befehl ins Terminal eingeben (ohne Enter),
S1 + RESET am Launchpad drücken und dann am Computer Enter drücken.

```shell
uvx lenlab exercise --log lenlab.log
```

`uvx lenlab exercise` sammelt einige Information über Ihr System und die Verbindung zum Launchpad. Dann programmiert
es die Firmware auf das Launchpad, startet die Firmware und testet die Kommunikation. Es überträgt etwa 28 MB Daten
in etwa 6 Minuten. `lenlab exercise` kann jederzeit mit Strg+C (Command+Punkt auf Mac) unterbrochen werden.

Wenn es schreibt `ERROR:lenlab.flash:Programming failed`, versuchen Sie es bitte nochmal von Anfang an mit S1 + RESET.

Mit `--log DATEINAME` speichert es die Ausgabe in der Logdatei unter "DATEINAME". Bitte senden Sie mir diese Datei
per E-Mail. Die Datei befindet sich im Home-Verzeichnis, wenn Sie das Verzeichnis nicht gewechselt haben:

- Windows: `C:\Benutzer\BENUTZERNAME\DATEINAME` oder `C:\Users\BENUTZERNAME\DATEINAME`
- Mac: `/Users/BENUTZERNAME/DATEINAME`

Der Befehl `pwd` zeigt den Namen des Verzeichnisses an, in dem das Terminal momentan arbeitet (Linux, Mac und Windows):

```shell
pwd
```

Wenn Sie lesen möchten, welche Informationen Sie verschicken:

Windows:

```shell
ii lenlab.log
```

Mac:

```shell
open -e lenlab.log
```

## Lenlab CLI

```shell
lenlab --help 
```

### Commands

- sys_info
- profile
- flash
- exercise
