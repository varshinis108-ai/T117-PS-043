
from models import SmartCard
from card_service import CardService
from datetime import datetime


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
