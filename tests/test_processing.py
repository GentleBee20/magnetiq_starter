"""Scientific summaries are calculated without smoothing or model fitting."""

import csv

import pytest

from magnetiq.data.odmr import OdmrSpectrum
from magnetiq.processing.summary import summarize_spectrum
from magnetiq.reporting.spectra import write_summaries


def test_summary_metrics_preserve_values():
    spectrum = OdmrSpectrum(
        "example", (2.85, 2.8501, 2.8502), (1.0, 0.8, 1.1)
    )
    result = summarize_spectrum(spectrum)
    assert result.samples == 3
    assert result.minimum_frequency_ghz == pytest.approx(2.8501)
    assert result.contrast_range == pytest.approx(0.3)
    assert result.median_absolute_difference == pytest.approx(0.25)
    assert spectrum.normalized_contrast == (1.0, 0.8, 1.1)


def test_write_summary_csv(tmp_path):
    spectrum = OdmrSpectrum("example", (2.85, 2.86), (1.0, 0.95))
    output = tmp_path / "results.csv"
    write_summaries([summarize_spectrum(spectrum)], output)
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["source"] == "example"


def test_no_empty_report(tmp_path):
    with pytest.raises(ValueError, match="No summaries"):
        write_summaries([], tmp_path / "empty.csv")
