
from loader import (
    load_stations,
    load_cards,
    load_events,
    load_holidays
)

from event_processor import EventProcessor

from reports import (
    generate_journey_report,
    generate_balance_report,
    generate_revenue_report
)


def main():

    print("=" * 45)
    print("       METRO FARE ENGINE")
    print("=" * 45)

    # 1. Load input data
    print("\nLoading stations...")
    stations = load_stations("data/stations.csv")

    print("Loading cards...")
    cards = load_cards("data/cards.csv")

    print("Loading holidays...")
    holidays = load_holidays("data/holidays.csv")

    print("Loading events...")
    events = load_events("data/events.csv")

    print("\nInput data loaded successfully.")

    print("Stations:", len(stations))
    print("Cards:", len(cards))
    print("Events:", len(events))

    # 2. Create event processor
    processor = EventProcessor(
        cards,
        stations,
        holidays
    )

    # 3. Process events
    print("\nProcessing metro events...")

    for event in events:
        processor.process_event(event)

    # 4. Generate reports
    print("\nGenerating reports...")

    generate_journey_report(
        processor.journeys,
        "output/journey_history.csv"
    )

    generate_balance_report(
        cards,
        "output/card_balances.csv"
    )

    generate_revenue_report(
        processor.transactions,
        "output/revenue.csv"
    )

    print("\nProcessing completed.")
    print("Journey report generated.")
    print("Balance report generated.")
    print("Revenue report generated.")

    print("\nRejected events:", len(processor.rejected_events))


if __name__ == "__main__":
    main()
