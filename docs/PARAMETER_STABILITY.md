# Parameter-stability research milestone

This experiment probes two different properties of a *fixed* selected
double-Lorentzian fit:

- **IID residual bootstrap:** resample residuals around the fitted signal,
  refit the model, and report the wider of the two center percentile 95%
  intervals, in MHz.
- **Multi-start stability:** jitter the fitted center positions, widths and
  amplitudes and refit with bounded least squares; report the largest range
  of either center across successful restarts, in MHz.

Neither statistic is a calibrated statement about absolute resonance-center
accuracy. In particular, structured residuals invalidate simple IID noise
assumptions and can make bootstrap intervals falsely narrow. Multistart
agreement is not proof of a correct physical model. The resampling keeps
the number of resonances fixed (no repeated AICc selection), so model-choice
uncertainty remains out of scope.

## Run

```powershell
python -m scripts.benchmark_stability --seed 20261124 --repeats 3 --bootstrap 20 --starts 8
```

The experiment selects clean and oscillatory examples from the held-out
synthetic generator, saves a new non-overwriting CSV and logs it as an MLflow
artifact under the existing experiment. Begin with this small sample because
each case requires multiple nonlinear optimizations.

## Interpretation

Compare the true maximum center error (an artificial 0.5 MHz tolerance)
with bootstrap interval width and multistart range. Evaluate whether either
indicator separates accurate-but-oscillatory cases from inaccurately fitted
cases. Do not change production FIT_OK/REVIEW_REQUIRED/FIT_FAILED rules.
Next steps: multiple held-out seeds, block bootstrap accounting for correlated
errors, coverage tests, model-selection stability and shifted distortion regimes.
