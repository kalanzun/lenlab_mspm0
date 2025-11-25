# Lenlab 8 for MSPM0G3507 (DE)

English version below

## Terminal

Lenlab und `uv` werden mit der Kommandozeile gestartet. Starten Sie das Programm "Terminal" auf Ihrem Computer.
Sie sehen ein weitgehend leeres Fenster mit einem Prompt (`...>` oder `...$`). An diesem Prompt können Sie einen
Befehl eingeben (oder kopieren und einfügen) und mit der Enter-Taste ausführen. Das Fenster zeigt dann die Ausgabe
des Befehls und ein neuer Prompt, wenn der Befehl abgeschlossen ist. An dem neuen Prompt können Sie
den nächsten Befehl eingeben. Die folgende Anleitung beschreibt die Befehle für Lenlab.

## Installation (uv)

Installieren Sie zunächst `uv`:

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

## Update (uv)

Falls Sie `uv` bereits installiert haben, aktualisieren Sie es bitte:

```shell
uv self update
```

## Lenlab starten

```shell
uvx lenlab
```

`uvx` lädt Lenlab in der neuesten Version herunter und führt es aus. Es speichert den Download beim ersten Mal
und führt danach nur die lokale Kopie aus ohne Zugriff auf das Internet.

```shell
uvx lenlab@latest
```

Mit diesem Befehl lädt `uvx` zunächst eine neuere Version von Lenlab herunter, falls es eine gibt.
Danach führt es Lenlab aus.

### Mac realpath Fehler

Auf manchen Macs fehlt das Kommando `realpath`. Lenlab startet dann nicht mit der Fehlermeldung
"realpath: command not found". Bitte verwenden Sie in diesem Fall den Befehl:

```shell
uvx --from lenlab python -m lenlab
```

# Lenlab 8 for MSPM0G3507 (EN)

## Terminal

Lenlab and `uv` are started from the command line. Start the program "terminal" on your computer.
You see a mostly empty window with a prompt (`...>` oder `...$`). You can type (or copy and paste) a command
at that prompt and run it with the enter key. Then, the window shows the output of the command and a new prompt
after the command is finished. At the new prompt, you can enter the next command.
The following manual describes the commands for Lenlab.

## Installation (uv)

First, install `uv`:

Windows:

```shell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

MacOS or Linux:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You may find further information about the installation in the documentation of `uv`: 
https://docs.astral.sh/uv/getting-started/installation/

Close the terminal and restart it, then it finds the newly installed commands `uv` and `uvx`.

## Update (uv)

Please update `uv`, if it is already installed.

```shell
uv self update
```

## Start Lenlab

```shell
uvx lenlab
```

`uvx` downloads Lenlab and runs it. It saves the download the first time and only runs the local copy later
without access to the internet.

```shell
uvx lenlab@latest
```

With this command, `uvx` downloads a newer version of Lenlab, if available.
Then, it runs Lenlab.

### Mac realpath Fehler

The command `realpath` is missing on some Macs. Lenlab does not start then with the error message
"realpath: command not found". In that case, please use the command:

```shell
uvx --from lenlab python -m lenlab
```
