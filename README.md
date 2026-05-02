# wagon-fem

Small example project scaffolded with a modern PyPA-compatible structure.

Quickstart
---------

Install dev dependencies and run tests:

```bash
python -m pip install --upgrade pip
pip install -e .[dev]
pytest -q
```

Run package entrypoint:

```bash
python -m wagon_fem
# or if installed: wagon-fem
```

Project layout
--------------

- `src/` — package sources (`src/wagon_fem`)
- `tests/` — pytest tests
- `pyproject.toml` — PEP 621 metadata + tool config
- `.github/workflows/ci.yml` — CI for tests and lint
- `.pre-commit-config.yaml` — pre-commit hooks
