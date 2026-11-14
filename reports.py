
import csv
import os
from collections import defaultdict
from decimal import Decimal


def _ensure_folder(filename):
    folder = os.path.dirname(str(filename))
    if folder:
        os.makedirs(folder, exist_ok=True)


def _write_header_if_needed(filename, fields):
    _ensure_folder(filename)

    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()


def _timestamp_string(value):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def generate_journey_report(journeys, filename):
    fields = [
        "card_id",
        "entry_station",
        "exit_station",
        "entry_time",
        "exit_time",
        "fare",
        "penalty",
        "status",
    ]

    _ensure_folder(filename)

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for journey in journeys:
            writer.writerow({
                "card_id": journey.card_id,
                "entry_station": journey.entry_station.station_name,
                "exit_station": (
                    journey.exit_station.station_name
                    if journey.exit_station else ""
                ),
                "entry_time": _timestamp_string(journey.entry_time),
                "exit_time": (
                    _timestamp_string(journey.exit_time)
                    if journey.exit_time else ""
                ),
                "fare": str(journey.fare),
                "penalty": str(journey.penalty),
                "status": journey.status,
            })


def generate_balance_report(cards, filename):
    fields = [
        "card_id",
        "card_type",
        "balance",
        "validity",
    ]

    _ensure_folder(filename)

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for card in cards.values():
            writer.writerow({
                "card_id": card.card_id,
                "card_type": card.card_type,
                "balance": str(card.balance),
                "validity": card.validity,
            })


def generate_revenue_report(transactions, filename):
    revenue = defaultdict(lambda: {
        "fare_revenue": Decimal("0"),
        "penalty_revenue": Decimal("0"),
        "other_revenue": Decimal("0"),
    })

    for transaction in transactions:
        station_id = getattr(transaction, "station_id", None)
        amount = Decimal(str(transaction.amount))
        transaction_type = transaction.transaction_type

        # Include transactions without a station under UNASSIGNED.
        if station_id is None:
            station_id = "UNASSIGNED"
            revenue[station_id]["other_revenue"] += amount
            continue

        if transaction_type == "FARE":
            revenue[station_id]["fare_revenue"] += amount

        elif transaction_type in (
            "OVERSTAY_PENALTY",
            "MISMATCH_PENALTY",
        ):
            revenue[station_id]["penalty_revenue"] += amount

        elif transaction_type not in ("TOP_UP", "REFUND"):
            revenue[station_id]["other_revenue"] += amount

    fields = [
        "station_id",
        "fare_revenue",
        "penalty_revenue",
        "other_revenue",
        "total_revenue",
    ]

    _ensure_folder(filename)

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for station_id in sorted(revenue):
            fare = revenue[station_id]["fare_revenue"]
            penalty = revenue[station_id]["penalty_revenue"]
            other = revenue[station_id]["other_revenue"]

            writer.writerow({
                "station_id": station_id,
                "fare_revenue": str(fare),
                "penalty_revenue": str(penalty),
                "other_revenue": str(other),
                "total_revenue": str(fare + penalty + other),
            })


def generate_sample_journeys_report(event_results, filename):
    fields = [
        "card_id",
        "ts",
        "event",
        "station_id",
        "entry_station_id",
        "zones_crossed",
        "fare_before_cap",
        "fare_charged",
        "penalty",
        "auto_reload_amount",
        "balance_after",
        "result",
        "rule_ids",
    ]

    _ensure_folder(filename)

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="ignore",
        )
        writer.writeheader()

        for result in event_results:
            writer.writerow({
                "card_id": result["card_id"],
                "ts": _timestamp_string(result["ts"]),
                "event": result["event"],
                "station_id": result["station_id"],
                "entry_station_id": result["entry_station_id"],
                "zones_crossed": result["zones_crossed"],
                "fare_before_cap": result["fare_before_cap"],
                "fare_charged": result["fare_charged"],
                "penalty": result["penalty"],
                "auto_reload_amount": result["auto_reload_amount"],
                "balance_after": result["balance_after"],
                "result": result["result"],
                "rule_ids": result["rule_ids"],
            })


def generate_sample_card_history(journeys, card_id, filename):
    fields = [
        "card_id",
        "journey_no",
        "tap_in_ts",
        "tap_in_station",
        "tap_out_ts",
        "tap_out_station",
        "fare",
        "penalty",
        "balance_after",
    ]

    _write_header_if_needed(filename, fields)

    card_journeys = [
        journey
        for journey in journeys
        if (
            journey.card_id == card_id
            and journey.exit_time is not None
            and journey.status in ("CLOSED", "MISMATCH_CLOSED")
        )
    ]

    with open(filename, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)

        for journey_no, journey in enumerate(card_journeys, start=1):
            writer.writerow({
                "card_id": journey.card_id,
                "journey_no": journey_no,
                "tap_in_ts": _timestamp_string(journey.entry_time),
                "tap_in_station": journey.entry_station.station_id,
                "tap_out_ts": _timestamp_string(journey.exit_time),
                "tap_out_station": (
                    journey.exit_station.station_id
                    if journey.exit_station else ""
                ),
                "fare": str(journey.fare),
                "penalty": str(journey.penalty),
                "balance_after": str(
                    getattr(journey, "balance_after", "")
                ),
            })

    print(f"History generated for {card_id}")


def generate_sample_station_revenue(
    transactions,
    report_date,
    filename,
    stations=None,
    journeys=None,
):
    fields = [
        "date",
        "station_id",
        "journeys",
        "fare_revenue",
        "penalty_revenue",
        "total",
    ]

    _write_header_if_needed(filename, fields)

    fare_by_station = defaultdict(Decimal)
    penalty_by_station = defaultdict(Decimal)
    journey_count = defaultdict(int)

    for journey in journeys or []:
        if (
            journey.exit_time is not None
            and journey.exit_time.date() == report_date
            and journey.status == "CLOSED"
            and journey.exit_station is not None
        ):
            journey_count[journey.exit_station.station_id] += 1

    for transaction in transactions:
        if transaction.timestamp.date() != report_date:
            continue

        station_id = transaction.station_id

        if not station_id:
            continue

        amount = Decimal(str(transaction.amount))

        if transaction.transaction_type == "FARE":
            fare_by_station[station_id] += amount

        elif transaction.transaction_type in (
            "OVERSTAY_PENALTY",
            "MISMATCH_PENALTY",
        ):
            penalty_by_station[station_id] += amount

    station_ids = set(stations.keys()) if stations else set()
    station_ids.update(fare_by_station.keys())
    station_ids.update(penalty_by_station.keys())
    station_ids.update(journey_count.keys())

    with open(filename, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)

        for station_id in sorted(station_ids):
            fare = fare_by_station[station_id]
            penalty = penalty_by_station[station_id]

            writer.writerow({
                "date": report_date.isoformat(),
                "station_id": station_id,
                "journeys": journey_count[station_id],
                "fare_revenue": str(fare),
                "penalty_revenue": str(penalty),
                "total": str(fare + penalty),
            })

    print(f"Revenue report generated for {report_date}")
