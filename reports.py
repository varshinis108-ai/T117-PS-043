
import csv


def generate_journey_report(journeys, filename):

    with open(filename, "w", newline="", encoding="utf-8") as file:

        fields = [
            "card_id",
            "entry_station",
            "exit_station",
            "entry_time",
            "exit_time",
            "fare",
            "penalty",
            "status"
        ]

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
                "entry_time": journey.entry_time.isoformat(),
                "exit_time": (
                    journey.exit_time.isoformat()
                    if journey.exit_time else ""
                ),
                "fare": journey.fare,
                "penalty": journey.penalty,
                "status": journey.status
            })


def generate_balance_report(cards, filename):

    with open(filename, "w", newline="", encoding="utf-8") as file:

        fields = ["card_id", "card_type", "balance", "validity"]

        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for card in cards.values():

            writer.writerow({
                "card_id": card.card_id,
                "card_type": card.card_type,
                "balance": card.balance,
                "validity": card.validity
            })


def generate_revenue_report(transactions, filename):

    revenue = {}

    for transaction in transactions:

        station = transaction.station_id or "UNASSIGNED"

        if station not in revenue:
            revenue[station] = {
                "fare_revenue": 0,
                "penalty_revenue": 0,
                "other_revenue": 0
            }

        if transaction.transaction_type == "FARE":
            revenue[station]["fare_revenue"] += transaction.amount

        elif transaction.transaction_type in {
            "MISMATCH_PENALTY",
            "OVERSTAY_PENALTY"
        }:
            revenue[station]["penalty_revenue"] += transaction.amount

        else:
            revenue[station]["other_revenue"] += transaction.amount
    with open(filename, "w", newline="", encoding="utf-8") as file:

        fields = [
            "station_id",
            "fare_revenue",
            "penalty_revenue",
            "other_revenue",
            "total_revenue"
        ]

        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for station, amounts in revenue.items():

            total = sum(amounts.values())

            writer.writerow({
                "station_id": station,
                "fare_revenue": amounts["fare_revenue"],
                "penalty_revenue": amounts["penalty_revenue"],
                "other_revenue": amounts["other_revenue"],
                "total_revenue": total
            })
