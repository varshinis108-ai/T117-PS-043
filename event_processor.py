from datetime import date
from decimal import Decimal

from models import Journey, Transaction
from fareengine import (
    calculate_journey_fare,
    calculate_penalty
)


MAXIMUM_FARE = Decimal("55")
AUTO_RELOAD_AMOUNT = Decimal("500")
AUTO_RELOAD_FEE = Decimal("5")


class EventProcessor:

    def __init__(self, cards, stations, holidays=None):

        self.cards = cards
        self.stations = stations
        self.holidays = holidays or set()

        self.journeys = []
        self.transactions = []
        self.rejected_events = []

    # Reject invalid events
    def reject(self, event, reason):

        self.rejected_events.append({
            "event_id": event.event_id,
            "card_id": event.card_id,
            "reason": reason
        })

        print(f"Event rejected: {reason}")

    # Record transactions
    def charge(
        self,
        card,
        amount,
        timestamp,
        station_id=None,
        transaction_type="FARE"
    ):

        amount = Decimal(str(amount))
        card.balance -= amount

        transaction = Transaction(
            transaction_id=f"TXN{len(self.transactions)+1:05d}",
            card_id=card.card_id,
            transaction_type=transaction_type,
            amount=amount,
            timestamp=timestamp,
            station_id=station_id,
            balance_after=card.balance
        )

        self.transactions.append(transaction)

    # STEP 14: TAP IN
    def process_tap_in(self, event):

        card = self.cards.get(event.card_id)
        station = self.stations.get(event.station_id)

        if card is None:
            self.reject(event, "CARD_NOT_FOUND")
            return

        if station is None:
            self.reject(event, "STATION_NOT_FOUND")
            return

        if card.validity != "ACTIVE":
            self.reject(event, "CARD_INVALID")
            return

        if card.blocked_at is not None:
            if event.timestamp >= card.blocked_at:
                self.reject(event, "CARD_BLOCKED")
                return

        # Close previous unclosed journey
        if card.active_journey is not None:

            old = card.active_journey

            if event.timestamp < old.entry_time:
                self.reject(event, "INVALID_TIMESTAMP")
                return

            old.exit_time = event.timestamp
            old.status = "MISMATCH_CLOSED"
            old.penalty = MAXIMUM_FARE

            self.charge(
                card,
                MAXIMUM_FARE,
                event.timestamp,
                old.entry_station.station_id,
                "MISMATCH_PENALTY"
            )

            self.journeys.append(old)
            card.active_journey = None

        # Minimum balance check
        if card.card_type != "TOURIST_PASS":

            if card.balance <= 0:
                self.reject(event, "NEGATIVE_BALANCE")
                return

            if card.balance < card.minimum_balance():
                self.reject(event, "LOW_BALANCE")
                return

        # Create new journey
        journey = Journey(
            card_id=card.card_id,
            entry_station=station,
            entry_time=event.timestamp
        )

        card.active_journey = journey

        print(
            f"TAP IN SUCCESS: {card.card_id} at {station.station_name}"
        )

    # STEP 15: TAP OUT
    def process_tap_out(self, event):

        card = self.cards.get(event.card_id)
        station = self.stations.get(event.station_id)

        if card is None:
            self.reject(event, "CARD_NOT_FOUND")
            return

        if station is None:
            self.reject(event, "STATION_NOT_FOUND")
            return

        if card.validity != "ACTIVE":
            self.reject(event, "CARD_INVALID")
            return

        if card.blocked_at is not None:
            if event.timestamp >= card.blocked_at:
                self.reject(event, "CARD_BLOCKED")
                return

        journey = card.active_journey

        # TAP OUT without TAP IN
        if journey is None:

            self.charge(
                card,
                MAXIMUM_FARE,
                event.timestamp,
                station.station_id,
                "MISMATCH_PENALTY"
            )

            print("MISMATCH PENALTY: Rs 55")

            self.process_auto_reload(card, event.timestamp)
            return

        entry = journey.entry_station
        entry_time = journey.entry_time

        if event.timestamp < entry_time:
            self.reject(event, "INVALID_TIMESTAMP")
            return

        journey.exit_station = station
        journey.exit_time = event.timestamp

        # Same station
        if entry.station_id == station.station_id:

            duration = event.timestamp - entry_time

            if duration.total_seconds() <= 900:
                fare = Decimal("0")
            else:
                fare = Decimal("20")

            penalty = Decimal("0")

        else:

            fare = calculate_journey_fare(
                entry.zone,
                station.zone,
                card.card_type,
                entry_time,
                self.holidays
            )

            penalty = calculate_penalty(
                entry.zone,
                station.zone,
                entry_time,
                event.timestamp
            )

        # Daily cap for STANDARD cards
        charge_date = event.timestamp.date()

        if card.card_type == "STANDARD":

            spent = card.daily_spending.get(
                charge_date,
                Decimal("0")
            )

            remaining = max(
                Decimal("0"),
                Decimal("150") - spent
            )

            fare = min(fare, remaining)

            card.daily_spending[charge_date] = spent + fare

        # Save journey
        journey.fare = fare
        journey.penalty = penalty
        journey.status = "CLOSED"

        # Deduct fare
        if fare > 0:

            self.charge(
                card,
                fare,
                event.timestamp,
                station.station_id,
                "FARE"
            )

        # Deduct penalty separately
        if penalty > 0:

            self.charge(
                card,
                penalty,
                event.timestamp,
                station.station_id,
                "OVERSTAY_PENALTY"
            )

        self.journeys.append(journey)
        card.active_journey = None

        print(f"TAP OUT SUCCESS: {card.card_id}")
        print(f"Fare: Rs {fare}")
        print(f"Penalty: Rs {penalty}")
        print(f"Balance: Rs {card.balance}")

        # Auto reload
        self.process_auto_reload(card, event.timestamp)

    # STEP 16: AUTO RELOAD
    def process_auto_reload(self, card, timestamp):

        if not card.auto_reload_enabled:
            return

        if card.balance >= Decimal("100"):
            return

        today = timestamp.date()

        if card.reload_date != today:

            card.reload_date = today
            card.reload_count = 0

        if card.reload_count >= 2:
            print("AUTO RELOAD LIMIT REACHED")
            return

        # Add Rs 500
        card.balance += AUTO_RELOAD_AMOUNT

        self.transactions.append(
            Transaction(
                transaction_id=f"TXN{len(self.transactions)+1:05d}",
                card_id=card.card_id,
                transaction_type="AUTO_RELOAD",
                amount=AUTO_RELOAD_AMOUNT,
                timestamp=timestamp,
                balance_after=card.balance
            )
        )

        # Deduct Rs 5 fee
        card.balance -= AUTO_RELOAD_FEE

        self.transactions.append(
            Transaction(
                transaction_id=f"TXN{len(self.transactions)+1:05d}",
                card_id=card.card_id,
                transaction_type="RELOAD_FEE",
                amount=AUTO_RELOAD_FEE,
                timestamp=timestamp,
                balance_after=card.balance
            )
        )

        card.reload_count += 1
        card.reload_date = today

        print("AUTO RELOAD SUCCESS")
        print(f"New balance: Rs {card.balance}")

    # Process events
    def process_event(self, event):

        if event.event_type == "TAP_IN":
            self.process_tap_in(event)

        elif event.event_type == "TAP_OUT":
            self.process_tap_out(event)

        else:
            self.reject(event, "INVALID_EVENT_TYPE")
