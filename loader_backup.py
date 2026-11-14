
import csv
from datetime import datetime, date
from models import Station, SmartCard, MetroEvent


def load_stations(filename):
    stations = {}

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            station = Station(
                station_id=row["station_id"].strip(),
                station_name=row["station_name"].strip(),
                line=row["line"].strip(),
                zone=int(row["zone"]),
                is_interchange=row["is_interchange"].strip().lower() == "true"
            )
            stations[station.station_id] = station

    return stations


def load_cards(filename):
    cards = {}

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            card = SmartCard(
                card_id=row["card_id"].strip(),
                card_type=row["card_type"].strip().upper(),
                balance=row["balance"].strip(),
                validity=row["validity"].strip().upper()
            )
            cards[card.card_id] = card

    return cards


def load_holidays(filename):
    holidays = set()

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            holidays.add(date.fromisoformat(row["date"].strip()))

    return holidays


def load_events(filename):
    events = []

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            event = MetroEvent(
                event_id=row["event_id"].strip(),
                card_id=row["card_id"].strip(),
                event_type=row["event_type"].strip().upper(),
                station_id=row["station_id"].strip(),
                timestamp=datetime.fromisoformat(row["timestamp"].strip())
            )
            events.append(event)

    events.sort(key=lambda event: (event.timestamp, event.event_id))
    return events
