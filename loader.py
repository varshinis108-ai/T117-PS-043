
import csv
from datetime import datetime, date
from decimal import Decimal

from models import Station, SmartCard, MetroEvent


def _get_value(row, *names, default=""):
    """Return the first available non-empty CSV column."""
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return default


def _to_bool(value):
    """Convert CSV text into a Boolean value."""
    return str(value).strip().lower() in {
        "true", "1", "yes", "y"
    }


# ==========================================
# LOAD METRO LINES
# ==========================================

def load_lines(filename):
    """Load line IDs and their display names."""
    lines = {}

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            line_id = _get_value(row, "line_id")
            line_name = _get_value(
                row, "line_name", "name", default=line_id
            )

            if line_id:
                lines[line_id] = line_name

    return lines


# ==========================================
# LOAD STATIONS
# ==========================================

def load_stations(filename, lines=None):
    """Load original and sample-pack station formats."""
    stations = {}
    lines = lines or {}

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            line_id = _get_value(row, "line", "line_id")
            line_name = lines.get(line_id, line_id)

            station = Station(
                station_id=_get_value(row, "station_id"),
                station_name=_get_value(row, "station_name"),
                line=line_name,
                zone=int(_get_value(row, "zone")),
                is_interchange=_to_bool(
                    _get_value(row, "is_interchange", "interchange")
                ),
                line_id=line_id or None,
                interchange_line_id=(
                    _get_value(row, "interchange_line_id") or None
                )
            )

            stations[station.station_id] = station

    return stations


# ==========================================
# LOAD SMART CARDS
# ==========================================

def load_cards(filename):
    """Load original and sample-pack card formats."""
    cards = {}

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            card_type = _get_value(row, "card_type").upper()

            status = _get_value(
                row, "validity", "status", default="ACTIVE"
            ).upper()

            auto_reload = _to_bool(
                _get_value(row, "auto_reload", default="false")
            )

            pass_days_value = _get_value(row, "pass_days")

            pass_days = (
                int(pass_days_value) if pass_days_value else None
            )

            tourist_plan = None

            if card_type == "TOURIST_PASS" and pass_days:
                tourist_plan = f"{pass_days}_DAY"

            issued_date_value = _get_value(row, "issued_date")

            issued_date = (
                date.fromisoformat(issued_date_value)
                if issued_date_value else None
            )

            card = SmartCard(
                card_id=_get_value(row, "card_id"),
                card_type=card_type,
                balance=Decimal(
                    _get_value(row, "balance", default="0")
                ),
                validity=status,
                auto_reload_enabled=auto_reload,
                linked_account=(
                    _get_value(row, "linked_account") or None
                ),
                tourist_plan=tourist_plan,
                issued_date=issued_date,
                pass_days=pass_days
            )

            cards[card.card_id] = card

    return cards


# ==========================================
# LOAD HOLIDAYS
# ==========================================

def load_holidays(filename):
    """Load holiday dates."""
    holidays = set()

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            holiday_value = _get_value(
                row, "date", "holiday_date"
            )

            if holiday_value:
                holidays.add(date.fromisoformat(holiday_value))

    return holidays


# ==========================================
# LOAD FARE MATRIX
# ==========================================

def load_fare_matrix(filename):
    """Load fares based on the number of zones crossed."""
    fare_matrix = {}

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            zones_crossed = int(
                _get_value(row, "zones_crossed")
            )

            fare = Decimal(
                _get_value(row, "fare")
            )

            fare_matrix[zones_crossed] = fare

    return fare_matrix


# ==========================================
# LOAD ORIGINAL EVENTS CSV
# ==========================================

def load_events(filename):
    """Load the original event CSV format."""
    events = []

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            event = MetroEvent(
                event_id=_get_value(row, "event_id"),
                card_id=_get_value(row, "card_id"),
                event_type=_get_value(
                    row, "event_type"
                ).upper(),
                station_id=_get_value(row, "station_id"),
                timestamp=datetime.fromisoformat(
                    _get_value(row, "timestamp")
                )
            )

            events.append(event)

    # Preserve the existing events.csv workflow.
    events.sort(
        key=lambda event: (
            event.timestamp,
            event.event_id
        )
    )

    return events


# ==========================================
# LOAD COMMANDS TXT
# ==========================================

def load_commands(filename):
    """
    Load commands.txt in original file order.

    Supported command names include:
    TAP_IN, TAP_OUT, TOPUP, BLOCK, SURRENDER,
    PRINT_HISTORY and PRINT_REVENUE.
    """

    commands = []

    with open(filename, "r", encoding="utf-8-sig") as file:

        for line_number, line in enumerate(file, start=1):

            line = line.strip()

            # Ignore blank lines and comments.
            if not line or line.startswith("#"):
                continue

            parts = [
                part.strip()
                for part in line.split("|")
            ]

            commands.append({
                "command": parts[0].upper(),
                "args": parts[1:],
                "line_number": line_number
            })

    return commands
