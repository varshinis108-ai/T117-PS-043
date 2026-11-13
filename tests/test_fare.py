
from datetime import datetime, timedelta
from fareengine import calculate_journey_fare, calculate_penalty


def test_base_fare():
    fare = calculate_journey_fare(
        1,
        2,
        "STANDARD",
        datetime(2026, 11, 12, 12, 0),
        set()
    )

    assert fare >= 0


def test_no_overstay_penalty():
    entry_time = datetime(2026, 11, 12, 10, 0)
    exit_time = entry_time + timedelta(minutes=30)

    penalty = calculate_penalty(
        1,
        2,
        entry_time,
        exit_time
    )

    assert penalty == 0


def test_overstay_penalty():
    entry_time = datetime(2026, 11, 12, 10, 0)
    exit_time = entry_time + timedelta(minutes=100)

    penalty = calculate_penalty(
        1,
        2,
        entry_time,
        exit_time
    )

    assert penalty == 50
