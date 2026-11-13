
import pytest
from models import SmartCard


def test_valid_card():
    card = SmartCard(
        card_id="C001",
        card_type="STANDARD",
        balance=500
    )

    assert card.card_id == "C001"
    assert card.balance == 500


def test_negative_balance():
    with pytest.raises(ValueError):
        SmartCard(
            card_id="C002",
            card_type="STANDARD",
            balance=-100
        )


def test_minimum_balance():
    card = SmartCard(
        card_id="C003",
        card_type="STUDENT",
        balance=100
    )

    assert card.minimum_balance() == 20
