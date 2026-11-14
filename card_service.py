
from datetime import datetime
from decimal import Decimal

from models import Transaction


class CardService:

    def __init__(self):
        self.transactions = []

    # ==========================================
    # RECORD TRANSACTION
    # ==========================================

    def record_transaction(
        self,
        card,
        transaction_type,
        amount,
        timestamp
    ):

        transaction = Transaction(
            transaction_id=f"TXN{len(self.transactions)+1:05d}",
            card_id=card.card_id,
            transaction_type=transaction_type,
            amount=Decimal(str(amount)),
            timestamp=timestamp,
            balance_after=card.balance
        )

        self.transactions.append(transaction)

    # ==========================================
    # TOP-UP
    # ==========================================

    def top_up(self, card, amount, timestamp):

        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError(
                "Top-up amount must be greater than zero"
            )

        if card.validity != "ACTIVE":
            raise ValueError(
                "Cannot top up a blocked or surrendered card"
            )

        card.balance += amount

        self.record_transaction(
            card,
            "TOP_UP",
            amount,
            timestamp
        )

        print("TOP-UP SUCCESSFUL")
        print(f"Amount added: Rs {amount}")
        print(f"New balance: Rs {card.balance}")

        return card.balance

    # ==========================================
    # AUTO RELOAD SETTINGS
    # ==========================================

    def enable_auto_reload(self, card, linked_account):

        if card.validity != "ACTIVE":
            raise ValueError("Card is not active")

        if not linked_account:
            raise ValueError(
                "Linked account is required"
            )

        card.auto_reload_enabled = True
        card.linked_account = linked_account

        return True

    def disable_auto_reload(self, card):

        card.auto_reload_enabled = False
        card.linked_account = None

        return True

    # ==========================================
    # TOURIST PASS PURCHASE
    # ==========================================

    def purchase_tourist_pass(
        self,
        card,
        plan,
        timestamp
    ):

        prices = {
            "1_DAY": Decimal("300"),
            "3_DAY": Decimal("700")
        }

        if card.card_type != "TOURIST_PASS":
            raise ValueError(
                "This is not a tourist pass card"
            )

        if card.validity != "ACTIVE":
            raise ValueError("Card is not active")

        if plan not in prices:
            raise ValueError(
                "Choose 1_DAY or 3_DAY"
            )

        # Prevent duplicate purchases before activation
        if (
            card.pass_start_date is not None
            or card.tourist_plan is not None
        ):
            raise ValueError(
                "Tourist pass already purchased or activated"
            )

        if card.balance < prices[plan]:
            raise ValueError(
                "Insufficient balance to purchase pass"
            )

        amount = prices[plan]

        card.balance -= amount
        card.tourist_plan = plan

        self.record_transaction(
            card,
            "PASS_PURCHASE",
            amount,
            timestamp
        )

        print("TOURIST PASS PURCHASE SUCCESSFUL")
        print(f"Plan: {plan}")
        print(f"Price: Rs {amount}")
        print(f"Remaining balance: Rs {card.balance}")

        return card.balance

    # ==========================================
    # BLOCK LOST CARD
    # ==========================================

    def block_card(self, card, block_time):

        if card.validity != "ACTIVE":
            raise ValueError(
                "Card is already blocked or surrendered"
            )

        # Save balance at exact block time
        card.balance_at_block = card.balance

        card.blocked_at = block_time
        card.validity = "BLOCKED"

        # Stop future auto reloads
        card.auto_reload_enabled = False

        print("CARD BLOCKED SUCCESSFULLY")
        print(f"Card ID: {card.card_id}")
        print(
            f"Balance at block time: Rs {card.balance_at_block}"
        )

        return card.balance_at_block

    # ==========================================
    # REFUND ON CARD SURRENDER
    # ==========================================

    def refund_card(self, card, timestamp):

        if card.validity == "SURRENDERED":
            raise ValueError(
                "Card has already been surrendered"
            )

        if card.active_journey is not None:
            raise ValueError(
                "Close or reconcile the active journey first"
            )

        # Lost card refund
        if card.validity == "BLOCKED":

            if card.balance_at_block is None:
                raise ValueError(
                    "Balance at block time is unavailable"
                )

            refund = card.balance_at_block

        # Normal surrender refund
        elif card.validity == "ACTIVE":

            refund = max(
                Decimal("0"),
                card.balance - Decimal("50")
            )

        else:
            raise ValueError("Invalid card status")

        # Clear card balance
        card.balance = Decimal("0")
        card.validity = "SURRENDERED"
        card.auto_reload_enabled = False

        self.record_transaction(
            card,
            "REFUND",
            refund,
            timestamp
        )

        print("CARD REFUND SUCCESSFUL")
        print(f"Card ID: {card.card_id}")
        print(f"Refund amount: Rs {refund}")

        return refund
