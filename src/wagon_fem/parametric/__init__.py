"""Parametric wagon frame generator."""

from .covered_wagon import build_covered_wagon
from .export import export_model_csv, normalized_csv_hash
from .open_wagon import build_open_wagon
from .passenger_double_deck import build_passenger_double_deck
from .passenger_single_deck import build_passenger_single_deck
from .schemas import GeneratedFrame, WagonParams, load_params
from .tank_wagon import build_tank_wagon
from .validation import ValidationIssue, validate_generated_frame

__all__ = [
    "GeneratedFrame",
    "ValidationIssue",
    "WagonParams",
    "build_covered_wagon",
    "build_open_wagon",
    "build_passenger_double_deck",
    "build_passenger_single_deck",
    "build_tank_wagon",
    "export_model_csv",
    "load_params",
    "normalized_csv_hash",
    "validate_generated_frame",
]
