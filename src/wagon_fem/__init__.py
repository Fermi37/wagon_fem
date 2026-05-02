"""Top-level package for wagon_fem."""

from .model import WagonModel
from .loader import load_edges_from_csv, Edge
from .solver import solve_and_get_moments, print_results

__all__ = ["WagonModel", "load_edges_from_csv", "Edge", "solve_and_get_moments", "print_results"]

__version__ = "0.1.0"


def main() -> None:
    """Simple entrypoint for the package."""
    print("Hello from wagon-fem package!")
