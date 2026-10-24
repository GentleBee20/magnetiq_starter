"""Reproducible ODMR plotting and metrics exports."""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from magnetiq.data.odmr import OdmrSpectrum
    from magnetiq.processing.summary import SpectrumSummary


def write_summaries(summaries: list[SpectrumSummary], destination: Path) -> None:
    """Export descriptive statistics as CSV."""
    if not summaries:
        raise ValueError("No summaries supplied")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(summaries[0])))
        writer.writeheader()
        writer.writerows(asdict(summary) for summary in summaries)


def plot_spectra(spectra: list[OdmrSpectrum], destination: Path) -> None:
    """Save a comparison of measured ODMR spectra; does not display a GUI."""
    if not spectra:
        raise ValueError("No spectra supplied")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(
        len(spectra), 1, figsize=(10, 2.6 * len(spectra)), squeeze=False
    )
    for axis, spectrum in zip(axes[:, 0], spectra):
        axis.plot(spectrum.frequency_ghz, spectrum.normalized_contrast, linewidth=0.9)
        axis.set_title(spectrum.source.rsplit("/", 1)[-1], fontsize=8)
        axis.set_ylabel("Normalized contrast")
        axis.grid(alpha=0.2)
    axes[-1, 0].set_xlabel("Microwave frequency (GHz)")
    figure.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        figure.savefig(destination, dpi=160)
    finally:
        plt.close(figure)
