
from datetime import datetime, timedelta
from decimal import Decimal

from fareengine import (
    calculate_journey_fare,
    calculate_penalty,
    is_peak,
    calculate_city_supplement,
)


def test_base_fare():
    # Zone 1 to Zone 2: base Rs 30.
    # Off-peak standard: 30 * 0.90 * 0.90 + 5 = 29.3
    fare = calculate_journey_fare(
        1, 2, "STANDARD",
        datetime(2026, 11, 12, 12, 0),
        set()
    )
    assert fare == Decimal("21")

def test_peak_hour_detection():
    timestamp = datetime(2026, 11, 12, 8, 30)
    assert is_peak(timestamp, set()) is True


def test_off_peak_hour_detection():
    timestamp = datetime(2026, 11, 12, 12, 0)
    assert is_peak(timestamp, set()) is False


def test_sunday_is_off_peak():
    timestamp = datetime(2026, 11, 15, 8, 30)
    assert is_peak(timestamp, set()) is False


def test_holiday_is_off_peak():
    holiday = datetime(2026, 11, 12).date()
    timestamp = datetime(2026, 11, 12, 8, 30)
    assert is_peak(timestamp, {holiday}) is False


def test_student_discount_off_peak():
    fare = calculate_journey_fare(
        2, 3, "STUDENT",
        datetime(2026, 11, 12, 12, 0),
        set()
    )
    # 40 * 0.50 * 0.90 * 0.90 = 16.2
    assert fare == Decimal("8")

def test_senior_discount():
    fare = calculate_journey_fare(
        2, 3, "SENIOR",
        datetime(2026, 11, 12, 12, 0),
        set()
    )
    # 40 * 0.70 * 0.90 * 0.90 = 22.68
    assert fare == Decimal("11")


def test_city_supplement():
    assert calculate_city_supplement(1, 2) == Decimal("5")
    assert calculate_city_supplement(2, 3) == Decimal("0")


def test_no_overstay_penalty():
    entry_time = datetime(2026, 11, 12, 10, 0)
    exit_time = entry_time + timedelta(minutes=30)

    penalty = calculate_penalty(
        1, 2, entry_time, exit_time
    )

    assert penalty == Decimal("0")


def test_overstay_penalty():
    entry_time = datetime(2026, 11, 12, 10, 0)
    exit_time = entry_time + timedelta(minutes=100)

    penalty = calculate_penalty(
        1, 2, entry_time, exit_time
    )

    assert penalty == Decimal("50")


def test_long_distance_penalty_threshold():
    entry_time = datetime(2026, 11, 12, 10, 0)

    # Distance of 3 zones: 120 minutes is allowed.
    exit_time = entry_time + timedelta(minutes=120)

    penalty = calculate_penalty(
        1, 4, entry_time, exit_time
    )

    assert penalty == Decimal("0")


def test_long_distance_overstay_penalty():
    entry_time = datetime(2026, 11, 12, 10, 0)
    exit_time = entry_time + timedelta(minutes=121)

    penalty = calculate_penalty(
        1, 4, entry_time, exit_time
    )

    assert penalty == Decimal("50")
