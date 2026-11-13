
import csv
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from reports import (
    generate_journey_report,
    generate_balance_report,
    generate_revenue_report,
)


def test_generate_journey_report(tmp_path):
    entry_station = SimpleNamespace(station_name="Central")
    exit_station = SimpleNamespace(station_name="City_Market")

    journey = SimpleNamespace(
        card_id="C001",
        entry_station=entry_station,
        exit_station=exit_station,
        entry_time=datetime(2026, 11, 12, 8, 30),
        exit_time=datetime(2026, 11, 12, 9, 0),
        fare=Decimal("27"),
        penalty=Decimal("0"),
        status="CLOSED",
    )

    filename = tmp_path / "journeys.csv"
    generate_journey_report([journey], filename)

    with open(filename, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["card_id"] == "C001"
    assert rows[0]["entry_station"] == "Central"
    assert rows[0]["exit_station"] == "City_Market"
    assert rows[0]["fare"] == "27"
    assert rows[0]["status"] == "CLOSED"


def test_generate_balance_report(tmp_path):
    card = SimpleNamespace(
        card_id="C001",
        card_type="STANDARD",
        balance=Decimal("473"),
        validity="ACTIVE",
    )

    filename = tmp_path / "balances.csv"
    generate_balance_report({"C001": card}, filename)

    with open(filename, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["card_id"] == "C001"
    assert rows[0]["card_type"] == "STANDARD"
    assert rows[0]["balance"] == "473"
    assert rows[0]["validity"] == "ACTIVE"


def test_generate_revenue_report(tmp_path):
    transactions = [
        SimpleNamespace(
            transaction_type="FARE",
            amount=Decimal("27"),
            station_id="S002",
        ),
        SimpleNamespace(
            transaction_type="MISMATCH_PENALTY",
            amount=Decimal("50"),
            station_id="S002",
        ),
        SimpleNamespace(
            transaction_type="TOP_UP",
            amount=Decimal("100"),
            station_id=None,
        ),
    ]

    filename = tmp_path / "revenue.csv"
    generate_revenue_report(transactions, filename)

    with open(filename, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    revenue = {row["station_id"]: row for row in rows}

    assert revenue["S002"]["fare_revenue"] == "27"
    assert revenue["S002"]["penalty_revenue"] == "50"
    assert revenue["S002"]["other_revenue"] == "0"
    assert revenue["S002"]["total_revenue"] == "77"

    assert revenue["UNASSIGNED"]["other_revenue"] == "100"
