import numpy as np
import pandas as pd

REQUIRED = {"passenger_id", "weight_kg"}

def validate_passengers(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError("В CSV отсутствуют обязательные столбцы: " + ", ".join(sorted(missing)))
    out = df.copy()
    out["passenger_id"] = out["passenger_id"].astype(str)
    out["weight_kg"] = pd.to_numeric(out["weight_kg"], errors="coerce")
    if out["weight_kg"].isna().any() or (out["weight_kg"] <= 0).any():
        raise ValueError("weight_kg должен содержать положительные числа.")
    if out["passenger_id"].duplicated().any():
        raise ValueError("passenger_id должен быть уникальным.")
    for col, default in [("group_id", ""), ("preferred_zone", ""), ("needs_aisle", False)]:
        if col not in out:
            out[col] = default
    out["group_id"] = out["group_id"].fillna("").astype(str)
    out["preferred_zone"] = out["preferred_zone"].fillna("").astype(str).str.lower()
    out["needs_aisle"] = out["needs_aisle"].fillna(False).astype(str).str.lower().isin(["true", "1", "yes", "да"])
    return out.reset_index(drop=True)

def make_demo_passengers(n: int = 120, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = max(1, min(int(n), 180))
    rows = []
    i = 0
    group_num = 1
    while i < n:
        size = int(rng.choice([1, 1, 1, 2, 2, 3, 4]))
        size = min(size, n - i)
        gid = f"G{group_num:03d}" if size > 1 else ""
        for _ in range(size):
            i += 1
            rows.append({
                "passenger_id": f"P{i:03d}",
                "weight_kg": round(float(np.clip(rng.normal(78, 15), 42, 135)), 1),
                "group_id": gid,
                "needs_aisle": bool(rng.random() < 0.12),
                "preferred_zone": str(rng.choice(["front", "middle", "rear", ""]))
            })
        group_num += 1
    return pd.DataFrame(rows)
