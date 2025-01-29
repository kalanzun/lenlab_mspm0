# Lenlab 8 for MSPM0G3507

## Liebe Studierende im LEN Workshop B am KIT!

Lenlab ab der Version 8.2 funktioniert für den LEN Workshop B.

Starten Sie Lenlab, nachdem `uv` installiert ist und wenn Sie Internet haben, mit 

```shell
uvx --refresh lenlab
```

Dann lädt `uvx` automatisch Updates herunter.

Wenn Sie nicht weiterkommen, fragen Sie bitte im Ilias und in den Tutorien.

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
uvx --refresh lenlab
```

`uvx` lädt Lenlab in der neuesten Version herunter und führt es aus.

Wenn Sie keine Internetverbindung haben starten Sie Lenlab ohne `--refresh`

```shell
uvx lenlab
```

`uvx` hat den Download beim ersten Mal gespeichert und führt nun die lokale Kopie aus ohne Zugriff auf das Internet.

### Mac realpath Fehler

Auf manchen Mac fehlt das Kommando `realpath`. Lenlab startet dann nicht mit der Fehlermeldung
"realpath: command not found". Bitte verwenden Sie in diesem Fall den Befehl

```shell
uvx --refresh --from lenlab python -m lenlab
```

### TI UniFlash, Programmieren funktioniert nicht

TI UniFlash programmiert das Launchpad auf eine andere Weise und kann funktionieren,
wenn der Programmierer in Lenlab nicht funktioniert.

- Installieren Sie https://www.ti.com/tool/UNIFLASH
- Starten Sie Lenlab und exportieren Sie das Firmware-Binary
  - Klicken Sie im Programmierer auf "Firmware Exportieren" und Speichern Sie das Firmware-Binary
- Starten Sie UniFlash. Wählen Sie als "Flash Image" das exportierte Firmware-Binary
- Führen Sie "Load Image" aus
  - Bei Erfolg schreibt es in die "Console": "\[SUCCESS\] Program Load completed successfully."
