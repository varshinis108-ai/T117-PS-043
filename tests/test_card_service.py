
from models import SmartCard, Station, Journey
from card_service import CardService
from datetime import datetime
from decimal import Decimal

import pytest


# ==========================================
# TOP-UP TEST
# ==========================================

def test_top_up():

    card = SmartCard(
        card_id="C001",
        card_type="STANDARD",
        balance=500
    )

    service = CardService()

    service.top_up(
        card,
        200,
        datetime(2026, 11, 12, 10, 0)
    )

    assert card.balance == 700


# ==========================================
# BLOCK CARD TEST
# ==========================================

def test_block_card():

    card = SmartCard(
        card_id="C002",
        card_type="STANDARD",
        balance=500
    )

    service = CardService()

    service.block_card(
        card,
        datetime(2026, 11, 12, 10, 0)
    )

    assert card.validity == "BLOCKED"
    assert card.balance_at_block == 500


# ==========================================
# TOURIST PASS PURCHASE TESTS
# ==========================================

def create_tourist_card(balance):

    return SmartCard(
        card_id="T001",
        card_type="TOURIST_PASS",
        balance=balance
    )


def test_purchase_one_day_tourist_pass():

    card = create_tourist_card(500)
    service = CardService()

    service.purchase_tourist_pass(
        card,
        "1_DAY",
        datetime(2026, 11, 14, 10, 0)
    )

    assert card.balance == Decimal("200")
    assert card.tourist_plan == "1_DAY"
    assert service.transactions[-1].transaction_type == "PASS_PURCHASE"
    assert service.transactions[-1].amount == Decimal("300")


def test_purchase_three_day_tourist_pass():

    card = create_tourist_card(1000)
    service = CardService()

    service.purchase_tourist_pass(
        card,
        "3_DAY",
        datetime(2026, 11, 14, 10, 0)
    )

    assert card.balance == Decimal("300")
    assert card.tourist_plan == "3_DAY"
    assert service.transactions[-1].amount == Decimal("700")


def test_tourist_pass_insufficient_balance():

    card = create_tourist_card(200)
    service = CardService()

    with pytest.raises(ValueError, match="Insufficient balance"):

        service.purchase_tourist_pass(
            card,
            "1_DAY",
            datetime(2026, 11, 14, 10, 0)
        )

    assert card.balance == Decimal("200")
    assert card.tourist_plan is None


def test_tourist_pass_invalid_plan():

    card = create_tourist_card(1000)
    service = CardService()

    with pytest.raises(ValueError, match="Choose 1_DAY or 3_DAY"):

        service.purchase_tourist_pass(
            card,
            "7_DAY",
            datetime(2026, 11, 14, 10, 0)
        )

    assert card.balance == Decimal("1000")


def test_tourist_pass_duplicate_purchase():

    card = create_tourist_card(1000)
    service = CardService()

    service.purchase_tourist_pass(
        card,
        "1_DAY",
        datetime(2026, 11, 14, 10, 0)
    )

    with pytest.raises(
        ValueError,
        match="already purchased or activated"
    ):

        service.purchase_tourist_pass(
            card,
            "3_DAY",
            datetime(2026, 11, 14, 11, 0)
        )

    assert card.balance == Decimal("700")
    assert card.tourist_plan == "1_DAY"
    assert len(service.transactions) == 1


# ==========================================
# CARD REFUND TESTS
# ==========================================

def test_normal_card_refund():

    card = SmartCard(
        card_id="C010",
        card_type="STANDARD",
        balance=500
    )

    service = CardService()

    refund = service.refund_card(
        card,
        datetime(2026, 11, 14, 12, 0)
    )

    assert refund == Decimal("450")
    assert card.balance == Decimal("0")
    assert card.validity == "SURRENDERED"
    assert service.transactions[-1].transaction_type == "REFUND"


def test_blocked_card_refund():

    card = SmartCard(
        card_id="C011",
        card_type="STANDARD",
        balance=500
    )

    service = CardService()

    service.block_card(
        card,
        datetime(2026, 11, 14, 10, 0)
    )

    # Changes after blocking must not affect refund
    card.balance = Decimal("100")

    refund = service.refund_card(
        card,
        datetime(2026, 11, 14, 12, 0)
    )

    assert refund == Decimal("500")
    assert card.balance == Decimal("0")
    assert card.validity == "SURRENDERED"


def test_duplicate_refund_rejected():

    card = SmartCard(
        card_id="C012",
        card_type="STANDARD",
        balance=500
    )

    service = CardService()

    service.refund_card(
        card,
        datetime(2026, 11, 14, 12, 0)
    )

    with pytest.raises(
        ValueError,
        match="already been surrendered"
    ):

        service.refund_card(
            card,
            datetime(2026, 11, 14, 13, 0)
        )


def test_refund_rejected_during_active_journey():

    card = SmartCard(
        card_id="C013",
        card_type="STANDARD",
        balance=500
    )

    station = Station(
        station_id="S001",
        station_name="Central",
        line="RED",
        zone=1
    )

    card.active_journey = Journey(
        card_id=card.card_id,
        entry_station=station,
        entry_time=datetime(2026, 11, 14, 10, 0)
    )

    service = CardService()

    with pytest.raises(
        ValueError,
        match="active journey"
    ):

        service.refund_card(
            card,
            datetime(2026, 11, 14, 12, 0)
        )
