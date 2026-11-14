
from decimal import Decimal

from models import Journey, Transaction
from fareengine import (
    calculate_journey_fare,
    calculate_penalty,
    zones_crossed,
)

MAXIMUM_FARE = Decimal("55")
AUTO_RELOAD_AMOUNT = Decimal("500")
AUTO_RELOAD_FEE = Decimal("5")
DAILY_STANDARD_CAP = Decimal("150")


class EventProcessor:

    def __init__(self, cards, stations, holidays=None):
        self.cards = cards
        self.stations = stations
        self.holidays = holidays or []

        self.journeys = []
        self.transactions = []
        self.rejected_events = []
        self.event_results = []

    def record_result(
        self,
        event,
        result,
        entry_station_id="",
        zones=0,
        fare_before_cap=Decimal("0"),
        fare_charged=Decimal("0"),
        penalty=Decimal("0"),
        reload_amount=Decimal("0"),
        rule_ids="",
    ):
        card = self.cards.get(event.card_id)
        balance = card.balance if card else Decimal("0")

        self.event_results.append({
            "card_id": event.card_id,
            "ts": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event.event_type,
            "station_id": event.station_id,
            "entry_station_id": entry_station_id,
            "zones_crossed": zones,
            "fare_before_cap": str(fare_before_cap),
            "fare_charged": str(fare_charged),
            "penalty": str(penalty),
            "auto_reload_amount": str(reload_amount),
            "balance_after": str(balance),
            "result": result,
            "rule_ids": rule_ids,
        })

    def reject(self, event, reason, rule_ids=""):
        self.rejected_events.append({
            "card_id": event.card_id,
            "event_type": event.event_type,
            "reason": reason,
        })

        result = reason

        if reason in ("LOW_BALANCE", "NEGATIVE_BALANCE"):
            result = "REFUSED_LOW_BALANCE"

        elif reason in (
            "CARD_BLOCKED",
            "REJECTED_BLOCKED",
            "CARD_INVALID",
            "TOURIST_PASS_EXPIRED",
            "TOURIST_PASS_NOT_PURCHASED",
        ):
            result = "REJECTED_BLOCKED"

        self.record_result(
            event,
            result,
            rule_ids=rule_ids,
        )

        print(f"Rejected {event.event_type}: {reason}")

    def charge(
        self,
        card,
        amount,
        timestamp,
        station_id=None,
        transaction_type="FARE",
    ):
        amount = Decimal(str(amount))
        card.balance -= amount

        transaction = Transaction(
            transaction_id=f"TXN{len(self.transactions) + 1:05d}",
            card_id=card.card_id,
            transaction_type=transaction_type,
            amount=amount,
            timestamp=timestamp,
            station_id=station_id,
            balance_after=card.balance,
        )

        self.transactions.append(transaction)

    def process_auto_reload(self, card, timestamp):
        if not card.auto_reload_enabled:
            return Decimal("0")

        if card.balance >= Decimal("100"):
            return Decimal("0")

        current_date = timestamp.date()

        if card.reload_date != current_date:
            card.reload_date = current_date
            card.reload_count = 0

        if card.reload_count >= 2:
            return Decimal("0")

        card.balance += AUTO_RELOAD_AMOUNT

        self.transactions.append(
            Transaction(
                transaction_id=f"TXN{len(self.transactions) + 1:05d}",
                card_id=card.card_id,
                transaction_type="AUTO_RELOAD",
                amount=AUTO_RELOAD_AMOUNT,
                timestamp=timestamp,
                balance_after=card.balance,
            )
        )

        self.charge(
            card,
            AUTO_RELOAD_FEE,
            timestamp,
            transaction_type="RELOAD_FEE",
        )

        card.reload_count += 1

        return AUTO_RELOAD_AMOUNT

    def process_tap_in(self, event):
        card = self.cards.get(event.card_id)
        station = self.stations.get(event.station_id)

        if card is None:
            self.reject(event, "CARD_INVALID", "BR-CARD")
            return

        if station is None:
            self.reject(event, "INVALID_STATION", "BR-STATION")
            return

        if card.validity != "ACTIVE":
            self.reject(event, "CARD_BLOCKED", "BR-BLOCK")
            return

        if card.blocked_at and event.timestamp >= card.blocked_at:
            self.reject(event, "CARD_BLOCKED", "BR-BLOCK")
            return

        if card.balance < Decimal("0"):
            self.reject(event, "NEGATIVE_BALANCE", "BR-BALANCE")
            return

        mismatch_rule = "BR-TAP-IN"

        # A new TAP_IN while another journey is open.
        if card.active_journey is not None:
            old_journey = card.active_journey

            if event.timestamp < old_journey.entry_time:
                self.reject(event, "INVALID_TIMESTAMP", "BR-TIME")
                return

            old_journey.exit_time = event.timestamp
            old_journey.status = "MISMATCH_CLOSED"
            old_journey.penalty = MAXIMUM_FARE
            old_journey.exit_station = None

            self.charge(
                card,
                MAXIMUM_FARE,
                event.timestamp,
                station.station_id,
                "MISMATCH_PENALTY",
            )

            old_journey.balance_after = card.balance
            self.journeys.append(old_journey)
            card.active_journey = None

            mismatch_rule = "BR-MISMATCH,BR-TAP-IN"

        # Tourist-pass validation.
        if card.card_type == "TOURIST_PASS":

            if card.tourist_plan is None:
                self.reject(
                    event,
                    "TOURIST_PASS_NOT_PURCHASED",
                    "BR-TOURIST",
                )
                return

            if card.pass_start_date is None:
                card.activate_tourist_pass(event.timestamp)

            if not card.is_tourist_pass_valid(event.timestamp):
                self.reject(
                    event,
                    "TOURIST_PASS_EXPIRED",
                    "BR-TOURIST",
                )
                return

        else:
            # minimum_balance is a method in models.py.
            if card.balance < card.minimum_balance():
                self.reject(event, "LOW_BALANCE", "BR-BALANCE")
                return

        journey = Journey(
            card_id=card.card_id,
            entry_station=station,
            entry_time=event.timestamp,
        )

        card.active_journey = journey

        result = (
            "PASS"
            if card.card_type == "TOURIST_PASS"
            else "OK"
        )

        self.record_result(
            event,
            result,
            entry_station_id=station.station_id,
            rule_ids=mismatch_rule,
        )

        print(
            f"TAP_IN: {card.card_id} at "
            f"{station.station_name}"
        )

    def process_tap_out(self, event):
        card = self.cards.get(event.card_id)
        station = self.stations.get(event.station_id)

        if card is None:
            self.reject(event, "CARD_INVALID", "BR-CARD")
            return

        if station is None:
            self.reject(event, "INVALID_STATION", "BR-STATION")
            return

        if card.blocked_at and event.timestamp >= card.blocked_at:
            self.reject(event, "CARD_BLOCKED", "BR-BLOCK")
            return

        if card.validity != "ACTIVE":
            self.reject(event, "CARD_BLOCKED", "BR-BLOCK")
            return

        journey = card.active_journey

        # TAP_OUT without a matching TAP_IN.
        # The mismatch penalty applies to every card type.
        if journey is None:
            self.charge(
                card,
                MAXIMUM_FARE,
                event.timestamp,
                station.station_id,
                "MISMATCH_PENALTY",
            )

            reload_amount = self.process_auto_reload(
                card,
                event.timestamp,
            )

            self.record_result(
                event,
                "PENALTY",
                fare_before_cap=MAXIMUM_FARE,
                penalty=MAXIMUM_FARE,
                reload_amount=reload_amount,
                rule_ids="BR-MISMATCH",
            )

            print("MISMATCH PENALTY: Rs 55")
            return

        if event.timestamp < journey.entry_time:
            self.reject(event, "INVALID_TIMESTAMP", "BR-TIME")
            return

        entry_station = journey.entry_station
        entry_time = journey.entry_time

        distance = zones_crossed(
            entry_station.zone,
            station.zone,
        )

        fare = Decimal("0")
        penalty = Decimal("0")
        result = "OK"

        # Tourist-pass journey.
        if card.card_type == "TOURIST_PASS":

            if not card.is_tourist_pass_valid(event.timestamp):
                journey.exit_station = station
                journey.exit_time = event.timestamp
                journey.status = "REJECTED_EXPIRED_PASS"
                journey.fare = Decimal("0")
                journey.penalty = Decimal("0")

                card.active_journey = None
                self.journeys.append(journey)

                self.reject(
                    event,
                    "TOURIST_PASS_EXPIRED",
                    "BR-TOURIST",
                )
                return

            fare = Decimal("0")
            penalty = Decimal("0")
            result = "PASS"

        else:
            # Same-station journey.
            if station.station_id == entry_station.station_id:

                duration = (
                    event.timestamp - entry_time
                ).total_seconds()

                if duration <= 15 * 60:
                    fare = Decimal("0")
                else:
                    fare = Decimal("20")

            else:
                fare = calculate_journey_fare(
                    entry_station.zone,
                    station.zone,
                    card.card_type,
                    entry_time,
                    self.holidays,
                )

                penalty = calculate_penalty(
                    entry_station.zone,
                    station.zone,
                    entry_time,
                    event.timestamp,
                )

        fare_before_cap = fare

        # Daily STANDARD fare cap.
        # Use the dictionary structure from models.py.
        if card.card_type == "STANDARD":

            current_date = event.timestamp.date()

            spent_today = card.daily_spending.get(
                current_date,
                Decimal("0"),
            )

            remaining_cap = max(
                Decimal("0"),
                DAILY_STANDARD_CAP - spent_today,
            )

            fare = min(fare, remaining_cap)

            card.daily_spending[current_date] = spent_today + fare

        # Record journey details.
        journey.exit_station = station
        journey.exit_time = event.timestamp
        journey.fare = fare
        journey.penalty = penalty
        journey.status = "CLOSED"

        # Charge fare.
        if fare > Decimal("0"):
            self.charge(
                card,
                fare,
                event.timestamp,
                station.station_id,
                "FARE",
            )

        # Penalties are outside the daily fare cap.
        if penalty > Decimal("0"):
            self.charge(
                card,
                penalty,
                event.timestamp,
                station.station_id,
                "OVERSTAY_PENALTY",
            )

        journey.balance_after = card.balance

        self.journeys.append(journey)
        card.active_journey = None

        reload_amount = self.process_auto_reload(
            card,
            event.timestamp,
        )

        rule_ids = "BR-TAP-OUT"

        if penalty > Decimal("0"):
            rule_ids += ",BR-OVERSTAY"

        if card.card_type == "STANDARD":
            rule_ids += ",BR-DAILY-CAP"

        self.record_result(
            event,
            result,
            entry_station_id=entry_station.station_id,
            zones=distance,
            fare_before_cap=fare_before_cap,
            fare_charged=fare,
            penalty=penalty,
            reload_amount=reload_amount,
            rule_ids=rule_ids,
        )

        print(
            f"TAP_OUT: {card.card_id} | "
            f"Fare: Rs {fare} | "
            f"Penalty: Rs {penalty}"
        )

    def process_event(self, event):
        event_type = event.event_type.upper()

        if event_type == "TAP_IN":
            self.process_tap_in(event)

        elif event_type == "TAP_OUT":
            self.process_tap_out(event)

        else:
            self.reject(
                event,
                "INVALID_EVENT",
                "BR-EVENT",
            )
