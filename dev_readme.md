# Testing

`pytest --random-order` by `pytest-random-order` plugin shuffles the test functions inside modules

`pytest-repeat` plugin repeats tests multiple times

- if marked with `@pytest.mark.repeat(1000)`
- or with `pytest --count=10` 

## Stress test

`pytest --random-order --random-order-bucket package --count=10`
