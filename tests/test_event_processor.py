
from datetime import datetime
from decimal import Decimal

from models import Station, SmartCard, MetroEvent
from event_processor import EventProcessor


def create_test_setup():
    stations = {
        "S001": Station(
            station_id="S001",
            station_name="Central",
            line="RED",
            zone=1
        ),
        "S002": Station(
            station_id="S002",
            station_name="City_Market",
            line="RED",
            zone=2
        ),
        "S003": Station(
            station_id="S003",
            station_name="Park_Street",
            line="BLUE",
            zone=3
        ),
    }

    card = SmartCard(
        card_id="C001",
        card_type="STANDARD",
        balance=1000
    )

    processor = EventProcessor(
        cards={"C001": card},
        stations=stations,
        holidays=set()
    )

    return card, processor


def make_event(event_id, event_type, station_id, timestamp):
    return MetroEvent(
        event_id=event_id,
        card_id="C001",
        event_type=event_type,
        station_id=station_id,
        timestamp=timestamp
    )


def complete_journey(processor, entry_id, exit_id, start_time, end_time):
    processor.process_event(
        make_event(
            f"{entry_id}_IN",
            "TAP_IN",
            entry_id,
            start_time
        )
    )

    processor.process_event(
        make_event(
            f"{exit_id}_OUT",
            "TAP_OUT",
            exit_id,
            end_time
        )
    )


# ==========================================
# NORMAL JOURNEY AND DAILY CAP TESTS
# ==========================================

def test_normal_tap_in_and_tap_out():
    card, processor = create_test_setup()

    complete_journey(
        processor,
        "S001",
        "S002",
        datetime(2026, 11, 12, 10, 0),
        datetime(2026, 11, 12, 10, 30)
    )

    assert card.active_journey is None
    assert card.balance < 1000
    assert len(processor.journeys) == 1
    assert processor.journeys[0].status == "CLOSED"


def test_daily_cap_reached():
    card, processor = create_test_setup()

    card.daily_spending[datetime(2026, 11, 12).date()] = Decimal("150")

    complete_journey(
        processor,
        "S001",
        "S002",
        datetime(2026, 11, 12, 12, 0),
        datetime(2026, 11, 12, 12, 30)
    )

    assert processor.journeys[0].fare == Decimal("0")
    assert card.daily_spending[datetime(2026, 11, 12).date()] == Decimal("150")


def test_daily_cap_limits_fare():
    card, processor = create_test_setup()

    card.daily_spending[datetime(2026, 11, 12).date()] = Decimal("145")

    complete_journey(
        processor,
        "S001",
        "S002",
        datetime(2026, 11, 12, 12, 0),
        datetime(2026, 11, 12, 12, 30)
    )

    assert processor.journeys[0].fare == Decimal("5")
    assert card.daily_spending[datetime(2026, 11, 12).date()] == Decimal("150")


def test_daily_cap_resets_next_day():
    card, processor = create_test_setup()

    card.daily_spending[datetime(2026, 11, 12).date()] = Decimal("150")

    complete_journey(
        processor,
        "S001",
        "S002",
        datetime(2026, 11, 13, 12, 0),
        datetime(2026, 11, 13, 12, 30)
    )

    next_day = datetime(2026, 11, 13).date()

    assert processor.journeys[0].fare > 0
    assert card.daily_spending[next_day] == processor.journeys[0].fare


# ==========================================
# AUTOMATIC RELOAD TESTS
# ==========================================

def test_auto_reload_success():
    card, processor = create_test_setup()

    card.balance = Decimal("50")
    card.auto_reload_enabled = True

    timestamp = datetime(2026, 11, 12, 12, 0)

    processor.process_auto_reload(card, timestamp)

    assert card.balance == Decimal("545")
    assert card.reload_count == 1
    assert card.reload_date == timestamp.date()
    assert len(processor.transactions) == 2

    assert processor.transactions[0].transaction_type == "AUTO_RELOAD"
    assert processor.transactions[0].amount == Decimal("500")

    assert processor.transactions[1].transaction_type == "RELOAD_FEE"
    assert processor.transactions[1].amount == Decimal("5")


def test_auto_reload_disabled():
    card, processor = create_test_setup()

    card.balance = Decimal("50")
    card.auto_reload_enabled = False

    processor.process_auto_reload(
        card,
        datetime(2026, 11, 12, 12, 0)
    )

    assert card.balance == Decimal("50")
    assert len(processor.transactions) == 0


def test_auto_reload_daily_limit():
    card, processor = create_test_setup()

    card.balance = Decimal("50")
    card.auto_reload_enabled = True

    timestamp = datetime(2026, 11, 12, 12, 0)

    # First reload
    processor.process_auto_reload(card, timestamp)

    # Simulate balance becoming low again
    card.balance = Decimal("50")

    # Second reload
    processor.process_auto_reload(card, timestamp)

    # Simulate balance becoming low a third time
    card.balance = Decimal("50")

    # Third reload should be rejected
    processor.process_auto_reload(card, timestamp)

    assert card.reload_count == 2
    assert card.balance == Decimal("50")
    assert len(processor.transactions) == 4


def test_auto_reload_resets_next_day():
    card, processor = create_test_setup()

    card.balance = Decimal("50")
    card.auto_reload_enabled = True

    card.reload_count = 2
    card.reload_date = datetime(2026, 11, 12).date()

    next_day = datetime(2026, 11, 13, 12, 0)

    processor.process_auto_reload(card, next_day)

    assert card.balance == Decimal("545")
    assert card.reload_count == 1
    assert card.reload_date == next_day.date()


# ==========================================
# JOURNEY PENALTY TESTS
# ==========================================

def test_overstay_penalty_is_charged():
    card, processor = create_test_setup()

    complete_journey(
        processor,
        "S001",
        "S002",
        datetime(2026, 11, 12, 12, 0),
        datetime(2026, 11, 12, 13, 31)
    )

    journey = processor.journeys[0]

    assert journey.status == "CLOSED"
    assert journey.penalty == Decimal("50")

    penalty_transactions = [
        transaction
        for transaction in processor.transactions
        if transaction.transaction_type == "OVERSTAY_PENALTY"
    ]

    assert len(penalty_transactions) == 1
    assert penalty_transactions[0].amount == Decimal("50")


def test_mismatch_tap_in_penalty_is_charged():
    card, processor = create_test_setup()

    # First tap-in
    processor.process_event(
        make_event(
            "E001",
            "TAP_IN",
            "S001",
            datetime(2026, 11, 12, 12, 0)
        )
    )

    # Second tap-in without tapping out
    processor.process_event(
        make_event(
            "E002",
            "TAP_IN",
            "S002",
            datetime(2026, 11, 12, 12, 10)
        )
    )

    assert len(processor.journeys) == 1
    assert processor.journeys[0].status == "MISMATCH_CLOSED"
    assert processor.journeys[0].penalty == Decimal("55")

    mismatch_transactions = [
        transaction
        for transaction in processor.transactions
        if transaction.transaction_type == "MISMATCH_PENALTY"
    ]

    assert len(mismatch_transactions) == 1
    assert mismatch_transactions[0].amount == Decimal("55")
    assert card.active_journey is not None
