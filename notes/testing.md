# Testing

## BSL

The test suite does not test the Bootstrap Loader or flashing, because the code can only handle
a cold BSL that wasn't connected yet, but the test suite connects to it in several tests and warms it up.

The test suite can test the Lenlab firmware in several tests, because the firmware has no cold or warm state.
