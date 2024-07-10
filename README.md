# Lenlab 8

Voltmeter, oscilloscope, signal generator, and Bode plotter for a TI Launchpad LP-MSPM0G3507

## Installation

```shell
python -m venv lenlab
lenlab/Scripts/activate

python -m pip install lenlab
```

## Startup

```shell
lenlab/Scripts/lenlab.exe
```

## Development

```shell
git clone git@github.com:kalanzun/lenlab_mspm0.git
cd lenlab_mspm0
```

With "python -m":

```shell
python -m venv .venv
.venv/Scripts/activate

python -m pip install -e .[dev]
```

With "uv":

```shell
uv venv
.venv/Scripts/activate

uv pip install -e .[dev]
```
