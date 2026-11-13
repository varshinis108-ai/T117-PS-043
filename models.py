
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Optional


# ==========================================
# STATION MODEL
# ==========================================

@dataclass
class Station:

    station_id: str
    station_name: str
    line: str
    zone: int
    is_interchange: bool = False

    def __post_init__(self):

        if not 1 <= self.zone <= 5:
            raise ValueError(
                "Station zone must be between 1 and 5"
            )


# ==========================================
# SMART CARD MODEL
# ==========================================

@dataclass
class SmartCard:

    card_id: str
    card_type: str
    balance: Decimal

    validity: str = "ACTIVE"

    blocked_at: Optional[datetime] = None
    balance_at_block: Optional[Decimal] = None

    auto_reload_enabled: bool = False
    linked_account: Optional[str] = None

    reload_count: int = 0
    reload_date: Optional[date] = None

    active_journey: Optional["Journey"] = None

    daily_spending: dict = field(default_factory=dict)
    monthly_spending: dict = field(default_factory=dict)

    # Tourist pass details
    tourist_plan: str = "1_DAY"
    pass_start_date: Optional[date] = None
    pass_expiry: Optional[datetime] = None

    def __post_init__(self):

        allowed_types = {
            "STANDARD",
            "STUDENT",
            "SENIOR",
            "TOURIST_PASS"
        }

        if self.card_type not in allowed_types:
            raise ValueError("Invalid card type")

        self.balance = Decimal(str(self.balance))

        if self.balance < Decimal("0"):
            raise ValueError(
                "Initial balance cannot be negative"
            )

    # Minimum balance required for tap-in
    def minimum_balance(self):

        if self.card_type == "STANDARD":
            return Decimal("50")

        elif self.card_type in {"STUDENT", "SENIOR"}:
            return Decimal("20")

        return Decimal("0")

    # Activate tourist pass on first tap-in
    def activate_tourist_pass(self, timestamp):

        if self.card_type != "TOURIST_PASS":
            raise ValueError(
                "This is not a tourist pass card"
            )

        if self.pass_start_date is not None:
            return

        self.pass_start_date = timestamp.date()

        if self.tourist_plan == "1_DAY":

            last_day = self.pass_start_date

        elif self.tourist_plan == "3_DAY":

            last_day = (
                self.pass_start_date +
                timedelta(days=2)
            )

        else:
            raise ValueError("Invalid tourist pass plan")

        self.pass_expiry = datetime.combine(
            last_day,
            time(23, 59, 59)
        )

    # Check tourist pass validity
    def is_tourist_pass_valid(self, timestamp):

        if self.card_type != "TOURIST_PASS":
            return False

        if self.pass_start_date is None:
            return False

        if self.pass_expiry is None:
            return False

        return timestamp <= self.pass_expiry


# ==========================================
# JOURNEY MODEL
# ==========================================

@dataclass
class Journey:

    card_id: str
    entry_station: Station
    entry_time: datetime

    exit_station: Optional[Station] = None
    exit_time: Optional[datetime] = None

    fare: Decimal = Decimal("0")
    penalty: Decimal = Decimal("0")

    status: str = "OPEN"


# ==========================================
# METRO EVENT MODEL
# ==========================================

@dataclass
class MetroEvent:

    event_id: str
    card_id: str
    event_type: str
    station_id: str
    timestamp: datetime


# ==========================================
# TRANSACTION MODEL
# ==========================================

@dataclass
class Transaction:

    transaction_id: str
    card_id: str
    transaction_type: str

    amount: Decimal
    timestamp: datetime

    station_id: Optional[str] = None
    balance_after: Optional[Decimal] = None
