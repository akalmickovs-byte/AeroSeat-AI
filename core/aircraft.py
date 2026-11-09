"""Учебная геометрия салона. Не является схемой сертифицированного борта."""
from dataclasses import dataclass

@dataclass(frozen=True)
class AircraftConfig:
    name: str = "Airbus A320 (учебная модель)"
    rows: int = 30
    seats_per_side: int = 3
    # Условное расстояние между рядами, метры
    row_pitch_m: float = 0.79
    # Условное положение начала ряда относительно datum, метры
    first_row_arm_m: float = 8.0

    @property
    def seat_count(self) -> int:
        return self.rows * self.seats_per_side * 2

    def seat_arm(self, row: int) -> float:
        return self.first_row_arm_m + (row - 1) * self.row_pitch_m

    def seats(self):
        # Буквы A,B,C — левая сторона; D,E,F — правая сторона.
        return [
            {"seat": f"{row}{letter}", "row": row, "letter": letter,
             "side": "left" if letter in "ABC" else "right",
             "arm_m": self.seat_arm(row),
             "aisle": letter in ("C", "D")}
            for row in range(1, self.rows + 1)
            for letter in "ABCDEF"
        ]
