
import os
from datetime import datetime, date
from decimal import Decimal

from loader import (
    load_lines,
    load_stations,
    load_cards,
    load_holidays,
    load_fare_matrix,
    load_commands
)

from models import MetroEvent
from event_processor import EventProcessor
from card_service import CardService

from reports import (
    generate_journey_report,
    generate_balance_report,
    generate_revenue_report,
    generate_sample_journeys_report,
    generate_sample_card_history,
    generate_sample_station_revenue
)


SAMPLE_FOLDER = "sample_data"
OUTPUT_FOLDER = "output"


# ==========================================
# PARSE DATE AND TIME
# ==========================================

def parse_timestamp(value):
    return datetime.fromisoformat(value.strip())


def parse_date(value):
    return date.fromisoformat(value.strip())


# ==========================================
# PROCESS ONE COMMAND
# ==========================================

def process_command(
    command_data,
    cards,
    stations,
    processor,
    card_service
):

    command = command_data["command"].upper()
    args = command_data["args"]
    line_number = command_data["line_number"]

    try:

        # --------------------------------------
        # TAP IN / TAP OUT
        # --------------------------------------

        if command in {"TAP_IN", "TAP_OUT"}:

            if len(args) < 3:
                raise ValueError(
                    f"{command} requires card_id, timestamp and station_id"
                )

            card_id = args[0].strip()
            timestamp = parse_timestamp(args[1])
            station_id = args[2].strip()

            event = MetroEvent(
                event_id=f"CMD-{line_number}",
                card_id=card_id,
                event_type=command,
                station_id=station_id,
                timestamp=timestamp
            )

            processor.process_event(event)

        # --------------------------------------
        # TOP UP
        # --------------------------------------

        elif command == "TOPUP":

            if len(args) < 3:
                raise ValueError(
                    "TOPUP requires card_id, timestamp and amount"
                )

            card_id = args[0].strip()
            timestamp = parse_timestamp(args[1])
            amount = Decimal(args[2].strip())

            card = cards.get(card_id)

            if card is None:
                raise ValueError(f"Card not found: {card_id}")

            card_service.top_up(
                card,
                amount,
                timestamp
            )

        # --------------------------------------
        # BLOCK CARD
        # --------------------------------------

        elif command == "BLOCK":

            if len(args) < 2:
                raise ValueError(
                    "BLOCK requires card_id and timestamp"
                )

            card_id = args[0].strip()
            timestamp = parse_timestamp(args[1])

            card = cards.get(card_id)

            if card is None:
                raise ValueError(f"Card not found: {card_id}")

            card_service.block_card(
                card,
                timestamp
            )

        # --------------------------------------
        # SURRENDER CARD
        # --------------------------------------

        elif command == "SURRENDER":

            if len(args) < 2:
                raise ValueError(
                    "SURRENDER requires card_id and timestamp"
                )

            card_id = args[0].strip()
            timestamp = parse_timestamp(args[1])

            card = cards.get(card_id)

            if card is None:
                raise ValueError(f"Card not found: {card_id}")

            card_service.refund_card(
                card,
                timestamp
            )

        # --------------------------------------
        # PRINT CARD HISTORY
        # --------------------------------------

        elif command == "PRINT_HISTORY":

            if len(args) < 1:
                raise ValueError(
                    "PRINT_HISTORY requires card_id"
                )

            card_id = args[0].strip()

            if card_id not in cards:
                raise ValueError(f"Card not found: {card_id}")

            generate_sample_card_history(
                processor.journeys,
                card_id,
                os.path.join(
                    OUTPUT_FOLDER,
                    "card_history.csv"
                )
            )

            print(f"History generated for {card_id}")

        # --------------------------------------
        # PRINT DAILY REVENUE
        # --------------------------------------

        elif command == "PRINT_REVENUE":

            if len(args) < 1:
                raise ValueError(
                    "PRINT_REVENUE requires a date"
                )

            report_date = parse_date(args[0])

            generate_sample_station_revenue(
                processor.transactions,
                report_date,
                os.path.join(
                    OUTPUT_FOLDER,
                    "station_revenue.csv"
                ),
                stations,
                processor.journeys
            )

            print(
                f"Revenue report generated for {report_date}"
            )

        else:
            raise ValueError(
                f"Unknown command: {command}"
            )

    except (ValueError, TypeError, KeyError) as error:

        print(
            f"COMMAND ERROR at line {line_number}: {error}"
        )


# ==========================================
# RESET SAMPLE REPORTS
# ==========================================

def reset_sample_reports():

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    files_to_reset = [
        "card_history.csv",
        "station_revenue.csv"
    ]

    for filename in files_to_reset:

        path = os.path.join(
            OUTPUT_FOLDER,
            filename
        )

        if os.path.exists(path):
            os.remove(path)


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():

    print("=" * 55)
    print("METRO FARE AND SMART CARD ENGINE")
    print("=" * 55)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Start each sample run with fresh sample reports.
    reset_sample_reports()

    # --------------------------------------
    # LOAD INPUT FILES
    # --------------------------------------

    print("\nLoading sample data...")

    lines_file = os.path.join(
        SAMPLE_FOLDER,
        "lines.csv"
    )

    stations_file = os.path.join(
        SAMPLE_FOLDER,
        "stations.csv"
    )

    cards_file = os.path.join(
        SAMPLE_FOLDER,
        "cards.csv"
    )

    holidays_file = os.path.join(
        SAMPLE_FOLDER,
        "holidays.csv"
    )

    fare_matrix_file = os.path.join(
        SAMPLE_FOLDER,
        "fare_matrix.csv"
    )

    commands_file = os.path.join(
        SAMPLE_FOLDER,
        "commands.txt"
    )

    lines = load_lines(lines_file)

    stations = load_stations(
        stations_file,
        lines
    )

    cards = load_cards(cards_file)

    holidays = load_holidays(holidays_file)

    # Load fare matrix for validation and reference.
    fare_matrix = load_fare_matrix(
        fare_matrix_file
    )

    commands = load_commands(
        commands_file
    )

    print(f"Lines loaded: {len(lines)}")
    print(f"Stations loaded: {len(stations)}")
    print(f"Cards loaded: {len(cards)}")
    print(f"Holidays loaded: {len(holidays)}")
    print(f"Fare matrix entries loaded: {len(fare_matrix)}")
    print(f"Commands loaded: {len(commands)}")

    # --------------------------------------
    # INITIALIZE SERVICES
    # --------------------------------------

    processor = EventProcessor(
        cards,
        stations,
        holidays
    )

    card_service = CardService()

    # Keep both services' transactions in one list.
    # This ensures top-ups and other card-service
    # transactions are included in the final report.
    card_service.transactions = processor.transactions

    # --------------------------------------
    # PROCESS COMMANDS IN FILE ORDER
    # --------------------------------------

    print("\nProcessing commands...\n")

    for command_data in commands:

        process_command(
            command_data,
            cards,
            stations,
            processor,
            card_service
        )

    # --------------------------------------
    # GENERATE FINAL REPORTS
    # --------------------------------------

    print("\nGenerating final reports...")

    generate_journey_report(
        processor.journeys,
        os.path.join(
            OUTPUT_FOLDER,
            "journey_history.csv"
        )
    )

    generate_balance_report(
        cards,
        os.path.join(
            OUTPUT_FOLDER,
            "card_balances.csv"
        )
    )

    generate_revenue_report(
        processor.transactions,
        os.path.join(
            OUTPUT_FOLDER,
            "revenue.csv"
        )
    )

    generate_sample_journeys_report(
        processor.event_results,
        os.path.join(
            OUTPUT_FOLDER,
            "journeys.csv"
        )
    )

    # --------------------------------------
    # DISPLAY SUMMARY
    # --------------------------------------

    completed_journeys = sum(
        1 for journey in processor.journeys
        if journey.exit_time is not None
    )

    print("\n" + "=" * 55)
    print("PROCESSING COMPLETED")
    print("=" * 55)

    print(
        f"Journey events: {len(processor.event_results)}"
    )

    print(
        f"Completed journeys: {completed_journeys}"
    )

    print(
        f"Rejected events: {len(processor.rejected_events)}"
    )

    print(
        f"Transactions: {len(processor.transactions)}"
    )

    print("\nReports saved in the output folder:")
    print("- output/journey_history.csv")
    print("- output/card_balances.csv")
    print("- output/revenue.csv")
    print("- output/journeys.csv")
    print("- output/card_history.csv")
    print("- output/station_revenue.csv")


# ==========================================
# PROGRAM ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()
