"""Top-level package for wagon_fem."""

from .core import add

__all__ = ["add"]

__version__ = "0.1.0"


def main() -> None:
    """Simple entrypoint for the package."""
    print("Hello from wagon-fem package!")
