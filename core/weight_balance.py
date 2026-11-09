"""Упрощённый учебный расчёт продольного CG."""
import pandas as pd

def calculate_cg(assignments: pd.DataFrame, demo_empty_mass_kg: float = 42000.0,
                 demo_empty_arm_m: float = 16.0) -> dict:
    if assignments.empty:
        return {"total_mass_kg": demo_empty_mass_kg, "cg_m": demo_empty_arm_m,
                "passenger_mass_kg": 0.0}
    pax_mass = float(assignments["weight_kg"].sum())
    pax_moment = float((assignments["weight_kg"] * assignments["arm_m"]).sum())
    total_mass = demo_empty_mass_kg + pax_mass
    total_moment = demo_empty_mass_kg * demo_empty_arm_m + pax_moment
    return {
        "total_mass_kg": total_mass,
        "cg_m": total_moment / total_mass,
        "passenger_mass_kg": pax_mass
    }

def zone_mass(assignments: pd.DataFrame) -> dict:
    if assignments.empty:
        return {"Front": 0.0, "Middle": 0.0, "Rear": 0.0}
    return {
        "Front": float(assignments.loc[assignments.zone == "Front", "weight_kg"].sum()),
        "Middle": float(assignments.loc[assignments.zone == "Middle", "weight_kg"].sum()),
        "Rear": float(assignments.loc[assignments.zone == "Rear", "weight_kg"].sum())
    }
