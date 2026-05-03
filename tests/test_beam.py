import pytest

from wagon_fem.model import create_simply_supported_beam
from wagon_fem.solver import run_analysis


def test_fixed_fixed_midspan_moment():
    # Use a clamped-clamped single-member beam
    L = 4000.0
    w = -10.0
    model = create_simply_supported_beam(
        L=L, w=w, support_type='clamped', n_segments=1)
    model = run_analysis(model)

    member = list(model.members.values())[0]
    mid = member.L() / 2.0
    mz = member.moment('Mz', mid)

    # Analytical mid-span moment for clamped-clamped uniform load: -q*L^2/24
    expected = w * L ** 2 / 24.0

    # Allow small numerical tolerance
    assert mz == pytest.approx(expected, rel=1e-6)
