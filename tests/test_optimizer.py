import pandas as pd
from core.aircraft import AircraftConfig
from core.optimizer import optimize_seating
from core.passengers import validate_passengers

def test_optimizer_assigns_unique_seats():
    config = AircraftConfig()
    passengers = validate_passengers(pd.DataFrame({
        "passenger_id": ["A", "B", "C"],
        "weight_kg": [70, 80, 65],
        "group_id": ["G1", "G1", ""]
    }))
    result, _ = optimize_seating(passengers, config)
    assert len(result) == 3
    assert result["seat"].nunique() == 3
    assert set(result["passenger_id"]) == {"A", "B", "C"}
