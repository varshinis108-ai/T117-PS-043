
from datetime import datetime

from models import Station, SmartCard, MetroEvent
from event_processor import EventProcessor


def test_normal_tap_in_and_tap_out():
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
        card_id="C001",
        card_type="STANDARD",
        balance=500
    )

    cards = {"C001": card}

    processor = EventProcessor(
        cards=cards,
        stations=stations,
        holidays=set()
    )

    tap_in = MetroEvent(
        event_id="E001",
        card_id="C001",
        event_type="TAP_IN",
        station_id="S001",
        timestamp=datetime(2026, 11, 12, 10, 0)
    )

    tap_out = MetroEvent(
        event_id="E002",
        card_id="C001",
        event_type="TAP_OUT",
        station_id="S002",
        timestamp=datetime(2026, 11, 12, 10, 30)
    )

    processor.process_event(tap_in)
    processor.process_event(tap_out)

    assert card.active_journey is None
    assert card.balance < 500
    assert len(processor.journeys) == 1
    assert processor.journeys[0].status == "CLOSED"
