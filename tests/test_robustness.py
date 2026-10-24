"""Phase 2 synthetic distortion families retain clean paired ground truth."""

import numpy as np

from scripts.benchmark_robustness import KINDS, generate_cases


def test_robustness_generator_has_all_families_and_reproducibility() -> None:
    first = generate_cases(20271025, 2, shifted=False)
    second = generate_cases(20271025, 2, shifted=False)
    assert len(first) == 2 * len(KINDS)
    assert {case[1] for case in first} == set(KINDS)
    for a, b in zip(first, second, strict=True):
        assert a[:4] == b[:4]
        np.testing.assert_array_equal(a[5], b[5])


def test_shifted_noise_and_distortion_differ_from_development() -> None:
    baseline = generate_cases(20271025, 1, shifted=False)
    shifted = generate_cases(20271025, 1, shifted=True)
    assert baseline[0][1] == shifted[0][1] == "clean"
    assert not np.array_equal(baseline[0][5], shifted[0][5])
    assert all(np.all(np.isfinite(case[5])) for case in shifted)
