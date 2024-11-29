from lenlab.app.voltmeter import VoltmeterChart


def test_batch_size_seconds():
    # chart draws between 120 and 7200 points
    for last_time in range(120, 15_000, 20):
        n_points = last_time
        n = VoltmeterChart.get_batch_size(last_time, interval=1000)
        assert 120 <= n_points / n <= 7200


def test_batch_size_20_ms():
    # chart draws between 120 and 7200 points
    for last_time in range(120, 15_000, 20):
        n_points = last_time * 50
        n = VoltmeterChart.get_batch_size(last_time, interval=20)
        assert 120 <= n_points / n <= 7200
