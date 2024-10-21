# Lenlab 8 for MSPM0G3507

This project is under development and not ready for use.

Dieses Projekt ist in Entwicklung und nicht bereit zur Nutzung.

## Installation (uv)

Starten Sie das Programm "Terminal".

Installieren Sie `uv`:

```ps1
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

https://docs.astral.sh/uv/getting-started/installation/

Schließen Sie das Terminal und starten Sie es neu, dann findet es die eben installierten Kommandos `uv` und `uvx`.

Starten Sie Lenlab:

```ps1
uvx lenlab
```

`uvx` installiert Lenlab automatisch und führt es aus.

https://pypi.org/project/lenlab/

## Testen

Erstellen Sie ein Projektverzeichnis (ein python virtual environment) und wechseln Sie in das Verzeichnis:

```ps1
uv venv lenlab
cd lenlab
```

Installieren Sie Python, Lenlab und pytest:

```ps1
uv pip install lenlab pytest pytest-random-order pytest-repeat
```

Sie können Lenlab starten, falls Sie das Launchpad noch flashen möchten:

```ps1
uv run lenlab
```

Führen Sie die Tests aus:

```ps1
uv run pytest --pyargs lenlab
```

Wenn Sie etwas Zeit haben, führen Sie den großen Stresstest aus:

```ps1
uv run pytest --pyargs lenlab --random-order --random-order-bucket package --count=10
```

Der Befehl führt die Tests zehnmal aus in zufälliger Reihenfolge.
