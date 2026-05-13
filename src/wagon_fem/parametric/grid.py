from __future__ import annotations

import math


def rounded_key(value: float, tolerance: float = 1e-6) -> float:
    if tolerance <= 0.0:
        return value
    return round(float(value) / tolerance) * tolerance


def unique_sorted(values: list[float] | tuple[float, ...], tolerance: float = 1e-6) -> list[float]:
    keyed: dict[float, float] = {}
    for value in values:
        key = rounded_key(float(value), tolerance)
        keyed[key] = key
    return sorted(keyed.values())


def pitch_coordinates(start: float, end: float, pitch: float, tolerance: float = 1e-6) -> list[float]:
    if pitch <= 0.0:
        return unique_sorted([start, end], tolerance)
    values = [float(start), float(end)]
    count = max(0, int(math.floor((end - start) / pitch)))
    for idx in range(1, count + 1):
        value = start + idx * pitch
        if start + tolerance < value < end - tolerance:
            values.append(value)
    return unique_sorted(values, tolerance)


def floor_z_lines(width: float, count_each_side: int, tolerance: float = 1e-6) -> list[float]:
    half = width / 2.0
    values = [-half, 0.0, half]
    for idx in range(1, count_each_side + 1):
        fraction = idx / (count_each_side + 1)
        values.append(-half * fraction)
        values.append(half * fraction)
    return unique_sorted(values, tolerance)


def height_lines(floor_y: float, side_height: float, divisions: int, tolerance: float = 1e-6) -> list[float]:
    divisions = max(1, int(divisions))
    return unique_sorted(
        [floor_y + side_height * idx / divisions for idx in range(divisions + 1)],
        tolerance,
    )
