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

Starten Sie Lenlab:

```shell
uvx lenlab
```

`uvx` lädt Lenlab herunter und führt es aus.

## Flashen

```shell
uvx lenlab flash
```

## Testen

```shell
uvx lenlab test
```

## Stresstest

Laufzeit etwa 10 Minuten.

```shell
uvx lenlab stress
```
