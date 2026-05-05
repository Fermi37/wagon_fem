"""Compatibility exports for the current wagon_fem FEM surface."""

from .model import create_simple_wagon_model, create_simply_supported_beam, load_model_from_csv
from .services import AnalysisOptions, analyze_model, prepare_ui_tables
from .solver import get_3d_figure, get_displacements_table, get_moments_table, run_analysis

__all__ = [
    "AnalysisOptions",
    "analyze_model",
    "create_simple_wagon_model",
    "create_simply_supported_beam",
    "get_3d_figure",
    "get_displacements_table",
    "get_moments_table",
    "load_model_from_csv",
    "prepare_ui_tables",
    "run_analysis",
]
