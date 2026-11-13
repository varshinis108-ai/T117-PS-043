
import pytest
from models import Station


def test_valid_station():
    station = Station(
        station_id="S001",
        station_name="Central",
        line="RED",
        zone=1
    )

    assert station.station_id == "S001"
    assert station.station_name == "Central"
    assert station.zone == 1


def test_invalid_station_zone():
    with pytest.raises(ValueError):
        Station(
            station_id="S002",
            station_name="Airport",
            line="BLUE",
            zone=6
        )
