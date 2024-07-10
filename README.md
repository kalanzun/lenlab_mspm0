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
lenlab/Scripts/lenlab
```

## Development

```shell
git clone git@github.com:kalanzun/lenlab_mspm0.git
cd lenlab_mspm0

python -m venv .venv
.venv/Scripts/activate

python -m pip install -e .[dev]
```
