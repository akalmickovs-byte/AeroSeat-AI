import pandas as pd

def seat_grid(assignments, rows=30):
    if assignments.empty:
        return pd.DataFrame()
    pivot = assignments.pivot(index="row", columns="letter", values="passenger_id")
    return pivot.reindex(index=range(1, rows + 1), columns=list("ABCDEF"))
