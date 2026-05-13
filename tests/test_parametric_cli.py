import subprocess
import sys


def test_parametric_cli_generates_valid_csv(tmp_path):
    output = tmp_path / "open.csv"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "wagon_fem.parametric",
            "docs/parametric_generator_v0_1_0/params.open_wagon.example.yaml",
            "--output",
            str(output),
            "--validate",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert output.exists()
    assert "SHA-256" in result.stdout
