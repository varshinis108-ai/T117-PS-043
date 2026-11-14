
from datetime import datetime
from decimal import Decimal

from models import Station, SmartCard, MetroEvent
from event_processor import EventProcessor


def create_tourist_setup(plan="1_DAY"):

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
        )
    }

    card = SmartCard(
        card_id="C004",
        card_type="TOURIST_PASS",
        balance=Decimal("0"),
        tourist_plan=plan
    )

    processor = EventProcessor(
        cards={"C004": card},
        stations=stations,
        holidays=set()
    )

    return card, processor


def send_event(processor, event_id, event_type, station_id, timestamp):

    event = MetroEvent(
        event_id=event_id,
        card_id="C004",
        event_type=event_type,
        station_id=station_id,
        timestamp=timestamp
    )

    processor.process_event(event)


def test_one_day_pass_activates_on_first_tap_in():

    card, processor = create_tourist_setup("1_DAY")

    start = datetime(2026, 11, 13, 9, 0)

    send_event(
        processor,
        "E001",
        "TAP_IN",
        "S001",
        start
    )

    assert card.pass_start_date == start.date()
    assert card.pass_expiry == datetime(2026, 11, 13, 23, 59, 59)
    assert card.active_journey is not None


def test_tourist_pass_allows_free_travel():

    card, processor = create_tourist_setup("1_DAY")

    send_event(
        processor,
        "E001",
        "TAP_IN",
        "S001",
        datetime(2026, 11, 13, 9, 0)
    )

    send_event(
        processor,
        "E002",
        "TAP_OUT",
        "S002",
        datetime(2026, 11, 13, 9, 30)
    )

    assert len(processor.journeys) == 1
    assert processor.journeys[0].fare == Decimal("0")
    assert card.balance == Decimal("0")
    assert card.active_journey is None


def test_one_day_pass_expires_next_day():

    card, processor = create_tourist_setup("1_DAY")

    send_event(
        processor,
        "E001",
        "TAP_IN",
        "S001",
        datetime(2026, 11, 13, 9, 0)
    )

    send_event(
        processor,
        "E002",
        "TAP_OUT",
        "S002",
        datetime(2026, 11, 13, 9, 30)
    )

    send_event(
        processor,
        "E003",
        "TAP_IN",
        "S001",
        datetime(2026, 11, 14, 9, 0)
    )

    assert card.active_journey is None
    assert len(processor.rejected_events) == 1
    assert processor.rejected_events[0]["reason"] == "TOURIST_PASS_EXPIRED"


def test_three_day_pass_remains_valid_for_three_days():

    card, processor = create_tourist_setup("3_DAY")

    send_event(
        processor,
        "E001",
        "TAP_IN",
        "S001",
        datetime(2026, 11, 13, 9, 0)
    )

    send_event(
        processor,
        "E002",
        "TAP_OUT",
        "S002",
        datetime(2026, 11, 13, 9, 30)
    )

    send_event(
        processor,
        "E003",
        "TAP_IN",
        "S001",
        datetime(2026, 11, 15, 10, 0)
    )

    assert card.active_journey is not None
    assert card.is_tourist_pass_valid(
        datetime(2026, 11, 15, 10, 0)
    )


def test_three_day_pass_expires_after_third_day():

    card, processor = create_tourist_setup("3_DAY")

    send_event(
        processor,
        "E001",
        "TAP_IN",
        "S001",
        datetime(2026, 11, 13, 9, 0)
    )

    send_event(
        processor,
        "E002",
        "TAP_OUT",
        "S002",
        datetime(2026, 11, 13, 9, 30)
    )

    send_event(
        processor,
        "E003",
        "TAP_IN",
        "S001",
        datetime(2026, 11, 16, 9, 0)
    )

    assert card.active_journey is None
    assert len(processor.rejected_events) == 1
    assert processor.rejected_events[0]["reason"] == "TOURIST_PASS_EXPIRED"
