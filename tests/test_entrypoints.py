import importlib
import subprocess
import sys


def test_ui_module_imports():
    module = importlib.import_module("wagon_fem.ui")

    assert getattr(module, "demo", None) is not None
    assert not hasattr(module, "node_props_table")
    assert not hasattr(module, "show_deformed")


def test_main_module_imports():
    module = importlib.import_module("wagon_fem.__main__")

    assert hasattr(module, "main")


def test_python_m_wagon_fem_runs_on_csv():
    result = subprocess.run(
        [sys.executable, "-m", "wagon_fem", "data/wagon_frame.csv"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Максимальный момент" in result.stdout


def test_python_m_wagon_fem_runs_with_default_csv():
    result = subprocess.run(
        [sys.executable, "-m", "wagon_fem"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Максимальный момент" in result.stdout
