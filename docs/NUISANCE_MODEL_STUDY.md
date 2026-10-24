# Sinusoidal nuisance-model stress experiment

**Status:** Research only. Production model selection and
`FIT_OK` / `REVIEW_REQUIRED` / `FIT_FAILED` are unchanged.

## Hypothesis

Coherent background oscillations in synthetic ODMR spectra can shift
Lorentzian resonance center estimates. Adding a sine/cosine nuisance
component may reduce those errors when its assumed period family is
appropriate. A smaller RSS **does not** prove more accurate centers.

Compare a fixed two-dip Lorentzian baseline with a two-dip model plus
`a*sin(2π(f-f_min)/P)+b*cos(2π(f-f_min)/P)`. Candidate periods are
fixed at 4, 5, 6, 7, 8, 9 MHz. The nuisance fit jointly refits both
resonances at each period, reporting the best AICc. This AICc **does not
correct for searching across periods** and can favor a nuisance model
on clean noise: treat the selection flag as exploratory.

## Evaluation

Independent development and held-out random seeds create clean,
low-amplitude and high-amplitude oscillation cases. The held-out
generator also shifts the underlying oscillation periods (5.1, 7.2,
8.6 MHz) and phases relative to the development regime.

The benchmark records model RSS/RMSE, per-case *true* maximum center
error, illustrative center-accuracy classification at 0.5 MHz, nuisance
amplitude/period, and AICc-based selection. Outputs are immutable local
MLflow run artifacts.

Run a pilot:

```powershell
python -m scripts.benchmark_nuisance --train-seed 20261024 --test-seed 20261124 --repeats 3
```

Then increase to `--repeats 12` to cover all three held-out
period/phase conditions several times.

**Limitations:** The simulated oscillations are in the same functional
family as the nuisance model, so this is a test of model recovery,
not evidence of general hardware robustness. Both splits vary one
generator rather than representing measured devices. Future controls
must include chirped waves, non-sinusoidal artifacts, shifted
backgrounds, and comparisons to no nuisance on genuine clean data.
