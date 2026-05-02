"""Модуль для работы с конструкцией вагона и расчетом методом конечных элементов."""

from .model import WagonModel
from .loader import load_edges_from_csv
from .solver import solve_and_get_moments

__all__ = ["WagonModel", "load_edges_from_csv", "solve_and_get_moments"]
