"""Coherence diagnostic and reporting regression tests."""

from __future__ import annotations

import zipfile

import numpy as np
import pytest

from magnetiq.coherence import analyze, iter_coherence, read_measurement
from scripts.analyze_coherence import run


def _measurement(n: int = 30) -> bytes:
    lines = ["tau [ns],Data,Fit,Envelope"]
    for i in range(n):
        time = i * 10
        fit = 1000.0 + 80.0 * np.exp(-i / 12)
        data = fit + 2 * np.sin(i)
        lines.append(f"{time},{data},{fit},{fit}")
    return ("\n".join(lines) + "\n").encode()


def test_loader_and_scale_invariance():
    values = read_measurement(_measurement())
    first = analyze("Data/Spin coherence/Hole Region/NV 1/Ramsey.txt", values)
    transformed = values.copy()
    transformed[:, 1:] *= 10000
    second = analyze("Data/Spin coherence/Hole Region/NV 1/Ramsey.txt", transformed)
    assert first.experiment == "ramsey"
    assert first.region == "hole"
    assert first.n_points == 30
    assert first.normalized_rmse == pytest.approx(second.normalized_rmse)


def test_reject_malformed():
    with pytest.raises(ValueError, match="expected columns"):
        read_measurement(b"time,y\n0,1\n")
    with pytest.raises(ValueError, match="strictly increasing"):
        read_measurement(
            b"tau [ns],Data,Fit,Envelope\n0,1,1,1\n1,2,2,2\n2,3,3,3\n2,4,4,4\n4,5,5,5\n"
        )


def test_archive_reporting(tmp_path):
    archive = tmp_path / "sample.zip"
    nested_path = (
        "Data/Spin coherence/Hole Region/NV 1/10-24-2022 19-04_Ramsey_2.7527_GHz_0_dBm_NV1.txt"
    )
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr(nested_path, _measurement())
        stream.writestr("Data/ODMR/test.txt", "irrelevant")
    entries = list(iter_coherence(archive))
    assert len(entries) == 1
    assert entries[0][0] == nested_path
    output = tmp_path / "out"
    assert run(archive, output) == 1
    assert (output / "coherence_diagnostics.csv").exists()
    assert (output / "coherence_report.html").exists()
    assert len(list((output / "plots").glob("*.png"))) == 1
    assert "not ground truth" in (output / "coherence_report.html").read_text()


def test_constant_signal_scale_is_undefined():
    x = np.array([[i, 5, 4, 4] for i in range(6)], dtype=float)
    result = analyze("SpinEcho.txt", x)
    assert "undefined_signal_scale" in result.warnings
    assert np.isnan(result.normalized_rmse)
