"""Две прозрачные эвристики для учебного сравнения."""
import time
import numpy as np
import pandas as pd
from core.weight_balance import calculate_cg, zone_mass

LETTERS = list("ABCDEF")

def _zone(row: int, total_rows: int) -> str:
    fraction = (row - 1) / max(total_rows - 1, 1)
    return "Front" if fraction < 1/3 else ("Middle" if fraction < 2/3 else "Rear")

def _seat_table(config):
    seats = pd.DataFrame(config.seats())
    seats["zone"] = seats["row"].apply(lambda r: _zone(r, config.rows))
    return seats

def _grouped_passengers(passengers):
    groups = []
    used = set()
    for _, p in passengers.iterrows():
        pid = p["passenger_id"]
        if pid in used:
            continue
        gid = str(p.get("group_id", "") or "")
        if gid:
            group = passengers[passengers.group_id.astype(str) == gid]
        else:
            group = passengers[passengers.passenger_id == pid]
        groups.append(group.to_dict("records"))
        used.update(group.passenger_id.tolist())
    return groups

def sequential_baseline(passengers, config):
    seats = _seat_table(config)
    ordered = passengers.sort_values("passenger_id").to_dict("records")
    rows = []
    for p, (_, s) in zip(ordered, seats.iterrows()):
        rows.append({**p, **s.to_dict()})
    result = pd.DataFrame(rows)
    return result

def optimize_seating(passengers, config, seed=1):
    start = time.perf_counter()
    seats = _seat_table(config)
    available = seats.to_dict("records")
    groups = _grouped_passengers(passengers)
    # Крупные группы сначала: повышает шанс разместить их на соседних креслах.
    groups.sort(key=lambda g: (-len(g), -sum(float(p["weight_kg"]) for p in g)))
    rng = np.random.default_rng(seed)
    assigned = []

    for group in groups:
        candidates = []
        # Ищем непрерывный блок в одном ряду. Для одиночек блок из одного места.
        for row in range(1, config.rows + 1):
            row_seats = [s for s in available if s["row"] == row]
            for side_letters in [list("ABC"), list("DEF")]:
                side = [s for s in row_seats if s["letter"] in side_letters]
                side.sort(key=lambda s: side_letters.index(s["letter"]))
                if len(side) >= len(group):
                    for start_idx in range(len(side) - len(group) + 1):
                        block = side[start_idx:start_idx + len(group)]
                        aisle_penalty = sum(1 for p, s in zip(group, block)
                                            if p.get("needs_aisle", False) and not s["aisle"])
                        pref_penalty = 0
                        for p, s in zip(group, block):
                            pref = str(p.get("preferred_zone", "")).lower()
                            if pref in ("front", "middle", "rear") and pref != s["zone"].lower():
                                pref_penalty += 1
                        # Балансируем массу в трёх зонах; мягко штрафуем отклонение.
                        current = sum(float(a["weight_kg"]) for a in assigned if a["zone"] == _zone(row, config.rows))
                        group_mass = sum(float(p["weight_kg"]) for p in group)
                        zone_penalty = (current + group_mass) ** 2
                        center_penalty = abs(np.mean([s["arm_m"] for s in block]) - config.seat_arm((config.rows+1)/2))
                        candidates.append((aisle_penalty * 1000 + pref_penalty * 30 +
                                           zone_penalty * 0.002 + center_penalty * 0.1 +
                                           rng.random() * 0.001, block))
        if not candidates:
            # Fallback: любые первые свободные места; это может разорвать группу.
            block = available[:len(group)]
        else:
            block = min(candidates, key=lambda x: x[0])[1]
        for p, s in zip(group, block):
            assigned.append({**p, **s})
            available.remove(s)

    result = pd.DataFrame(assigned)
    elapsed = time.perf_counter() - start
    return result, elapsed

def metrics(assignments):
    masses = zone_mass(assignments)
    vals = list(masses.values())
    cg = calculate_cg(assignments)
    return {
        "passengers": len(assignments),
        "zone_mass_kg": masses,
        "zone_mass_spread_kg": max(vals) - min(vals) if vals else 0,
        "cg_m": cg["cg_m"],
        "total_mass_kg": cg["total_mass_kg"]
    }
