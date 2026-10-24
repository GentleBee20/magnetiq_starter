"""Transparent, model-free preliminary ODMR signal metrics.

These statistics are exploratory. A local minimum is NOT a validated resonance.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from magnetiq.data.odmr import OdmrSpectrum


@dataclass(frozen=True)
class SpectrumSummary:
    """Basic characteristics of one measured ODMR spectrum."""

    source: str
    samples: int
    frequency_start_ghz: float
    frequency_stop_ghz: float
    contrast_min: float
    contrast_max: float
    contrast_median: float
    minimum_frequency_ghz: float
    contrast_range: float
    median_absolute_difference: float


def summarize_spectrum(spectrum: OdmrSpectrum) -> SpectrumSummary:
    """Summarize observed data without fitting or changing measured values."""
    contrast = spectrum.normalized_contrast
    midpoint = statistics.median(contrast)
    differences = [abs(later - earlier) for earlier, later in zip(contrast, contrast[1:], strict=False)]
    minimum_index = min(range(len(contrast)), key=contrast.__getitem__)
    return SpectrumSummary(
        source=spectrum.source,
        samples=spectrum.count,
        frequency_start_ghz=spectrum.frequency_ghz[0],
        frequency_stop_ghz=spectrum.frequency_ghz[-1],
        contrast_min=min(contrast),
        contrast_max=max(contrast),
        contrast_median=midpoint,
        minimum_frequency_ghz=spectrum.frequency_ghz[minimum_index],
        contrast_range=max(contrast) - min(contrast),
        median_absolute_difference=statistics.median(differences),
    )
