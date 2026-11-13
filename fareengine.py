
from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP


ZONE_FARES = {
    0: Decimal("10"),
    1: Decimal("20"),
    2: Decimal("30"),
    3: Decimal("40"),
    4: Decimal("50")
}

CITY_SUPPLEMENT = Decimal("5")
SMART_CARD_DISCOUNT = Decimal("0.10")


def round_rupee(amount):
    return amount.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )


def zones_crossed(entry_zone, exit_zone):
    return abs(entry_zone - exit_zone)


def calculate_base_fare(entry_zone, exit_zone):
    distance = zones_crossed(entry_zone, exit_zone)

    if distance not in ZONE_FARES:
        raise ValueError("Invalid zone distance")

    return ZONE_FARES[distance]


def calculate_city_supplement(entry_zone, exit_zone):
    if entry_zone == 1 or exit_zone == 1:
        return CITY_SUPPLEMENT

    return Decimal("0")


def is_peak(timestamp, holidays):
    if timestamp.date() in holidays:
        return False

    if timestamp.weekday() == 6:
        return False

    current = timestamp.time()

    morning = time(8, 0) <= current <= time(10, 0)
    evening = time(17, 0) <= current <= time(20, 0)

    return morning or evening


def calculate_journey_fare(
    entry_zone,
    exit_zone,
    card_type,
    timestamp,
    holidays
):
    base = calculate_base_fare(entry_zone, exit_zone)

    # 1. Card-type discount
    if card_type == "STUDENT":
        if not is_peak(timestamp, holidays):
            base *= Decimal("0.50")

    elif card_type == "SENIOR":
        base *= Decimal("0.70")

    # 2. Smart card discount
    if card_type != "TOURIST_PASS":
        base *= Decimal("0.90")

    # 3. Peak uplift or off-peak reduction
    if is_peak(timestamp, holidays):
        base *= Decimal("1.20")
    else:
        base *= Decimal("0.90")

    # Supplement is added after discounts.
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
    duration = exit_time - entry_time
    distance = zones_crossed(entry_zone, exit_zone)

    maximum_minutes = 90 if distance <= 2 else 120

    if duration.total_seconds() > maximum_minutes * 60:
        return Decimal("50")

    return Decimal("0")
