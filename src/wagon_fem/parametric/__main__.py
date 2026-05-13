from __future__ import annotations

import argparse
from pathlib import Path

from .covered_wagon import build_covered_wagon
from .export import export_model_csv
from .open_wagon import build_open_wagon
from .schemas import load_params
from .validation import assert_valid_generated_frame, topology_summary, write_validation_report


def _build(params_path: str | Path):
    params = load_params(params_path)
    if params.wagon_type == "covered_wagon":
        return build_covered_wagon(params)
    return build_open_wagon(params)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a parametric wagon FEM CSV model.")
    parser.add_argument("params", type=str, help="Path to YAML or JSON parameter file.")
    parser.add_argument("--output", "-o", type=str, required=True, help="Output combined CSV path.")
    parser.add_argument("--validate", action="store_true", help="Run generator validation before writing.")
    parser.add_argument("--report", type=str, default=None, help="Optional Markdown validation report path.")
    args = parser.parse_args()

    frame = _build(args.params)
    if args.validate:
        assert_valid_generated_frame(frame)
    output = export_model_csv(frame.nodes_df, frame.edges_df, args.output)
    summary = topology_summary(frame)
    if args.report:
        write_validation_report(frame, args.report)
    print(f"Generated {output}")
    print(f"Nodes: {summary['node_count']}")
    print(f"Members: {summary['edge_count']}")
    print(f"SHA-256: {summary['sha256']}")


if __name__ == "__main__":
    main()
