from datetime import datetime, time, date
from decimal import Decimal, ROUND_HALF_UP


# Fare based on the number of zones crossed.
ZONE_FARES = {
    0: Decimal("10"),
    1: Decimal("20"),
    2: Decimal("30"),
    3: Decimal("40"),
    4: Decimal("50"),
}

CITY_SUPPLEMENT = Decimal("5")
SMART_CARD_DISCOUNT = Decimal("0.10")


def round_rupee(amount):
    """Round fare to the nearest whole rupee."""
    return Decimal(amount).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )


def zones_crossed(entry_zone, exit_zone):
    """Calculate the number of zones crossed."""
    return abs(int(entry_zone) - int(exit_zone))


def calculate_base_fare(entry_zone, exit_zone):
    """Return base fare according to zone distance."""
    distance = zones_crossed(entry_zone, exit_zone)

    if distance not in ZONE_FARES:
        raise ValueError("Invalid zone distance")

    return ZONE_FARES[distance]


def calculate_city_supplement(entry_zone, exit_zone):
    """Add ₹5 if the journey touches Zone 1."""
    if int(entry_zone) == 1 or int(exit_zone) == 1:
        return CITY_SUPPLEMENT

    return Decimal("0")


def _holiday_dates(holidays):
    """Convert holiday values into date objects."""
    result = set()

    for holiday in holidays or []:
        if isinstance(holiday, datetime):
            result.add(holiday.date())

        elif isinstance(holiday, date):
            result.add(holiday)

        else:
            result.add(date.fromisoformat(str(holiday)))

    return result


def is_special_off_peak(timestamp, holidays):
    """Check whether the date is Sunday or a listed holiday."""
    return (
        timestamp.weekday() == 6
        or timestamp.date() in _holiday_dates(holidays)
    )


def is_peak(timestamp, holidays):
    """
    Peak hours:
    Morning: 08:00 inclusive to 10:00 exclusive.
    Evening: 17:00 inclusive to 20:00 exclusive.

    Sundays and listed holidays are always off-peak.
    """
    if is_special_off_peak(timestamp, holidays):
        return False

    current = timestamp.time()

    morning = time(8, 0) <= current < time(10, 0)
    evening = time(17, 0) <= current < time(20, 0)

    return morning or evening


def calculate_journey_fare(
    entry_zone,
    exit_zone,
    card_type,
    timestamp,
    holidays=None
):
    """
    Calculate journey fare.

    Calculation order:
    1. Base fare.
    2. Card-type discount.
    3. Smart-card discount.
    4. Peak uplift or off-peak reduction.
    5. Zone 1 supplement.
    """

    card_type = str(card_type).upper()

    # Tourist pass journeys have no normal journey fare.
    if card_type == "TOURIST_PASS":
        return Decimal("0")

    base = calculate_base_fare(
        entry_zone,
        exit_zone
    )

    peak = is_peak(timestamp, holidays)

    # 1. Card-type discount
    if card_type == "STUDENT":
        if not peak:
            base *= Decimal("0.50")

    elif card_type == "SENIOR":
        base *= Decimal("0.70")

    # 2. Smart-card discount
    base *= (
        Decimal("1") - SMART_CARD_DISCOUNT
    )

    # 3. Peak uplift or off-peak reduction
    if peak:
        base *= Decimal("1.20")
    else:
        base *= Decimal("0.90")

    # 4. Zone 1 supplement is added after discounts.
    supplement = calculate_city_supplement(
        entry_zone,
        exit_zone
    )

    total = base + supplement

    return round_rupee(total)


def calculate_penalty(
    entry_zone,
    exit_zone,
    entry_time,
    exit_time
):
    """Calculate ₹50 overstay penalty when journey exceeds limit."""

    duration = exit_time - entry_time

    distance = zones_crossed(
        entry_zone,
        exit_zone
    )

    maximum_minutes = (
        90 if distance <= 2 else 120
    )

    if duration.total_seconds() > maximum_minutes * 60:
        return Decimal("50")

    return Decimal("0")
