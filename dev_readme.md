# Testing

`pytest --random-order` by `pytest-random-order` plugin shuffles the test functions inside modules

`pytest-repeat` plugin repeats tests multiple times

- if marked with `@pytest.mark.repeat(1000)`
- or with `pytest --count=10` 

## Stress test

`pytest --random-order --random-order-bucket package --count=10`

## Print system information

`pytest --pyargs lenlab -m sys_info --log-cli-level INFO`

# Build

`uv build`

It builds a source distribution first and from that a wheel. To put the firmware binary into the wheel,
it is part of the source distribution as well.

It includes files, that are not excluded in .gitignore. But it only reads .gitignore from the project root,
so all ignores are there.

The build system behind `uv build` is hatchling https://hatch.pypa.io/1.10/config/build/
