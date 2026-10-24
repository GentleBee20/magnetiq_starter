"""Tune on one synthetic seed; evaluate once on an independent held-out seed.

This evaluates a proposed *escalation to FIT_FAILED*, never changes production QC.
Run from repository root: python scripts/validate_adequacy_policy.py
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import mlflow
import numpy as np

from magnetiq.tracking import EXPERIMENT, git_revision, new_run_location
from scripts.benchmark_ground_truth import evaluate, make_cases


def classify(row: dict[str, object], rmse_gate: float, lag_gate: float) -> str:
    """Escalate only non-OK spectra meeting both severe-mismatch gates."""
    existing = str(row["current_status"])
    if existing in ("FIT_FAILED", "FIT_OK"):
        return existing
    rmse = float(row["normalized_rmse"])
    lag = float(row["abs_lag1"])
    if math.isfinite(rmse) and math.isfinite(lag) and rmse > rmse_gate and lag > lag_gate:
        return "FIT_FAILED"
    return existing


def score(rows: list[dict[str, object]], statuses: list[str]) -> dict[str, float]:
    """Conservative policy evaluation: review is abstention, not acceptance."""
    assert len(rows) == len(statuses)
    accurate = [i for i, r in enumerate(rows) if r["centers_within_tolerance"]]
    inaccurate = [i for i, r in enumerate(rows) if not r["centers_within_tolerance"]]
    return {
        "n": float(len(rows)),
        "accurate": float(len(accurate)),
        "inaccurate": float(len(inaccurate)),
        "accepted": float(statuses.count("FIT_OK")),
        "reviewed": float(statuses.count("REVIEW_REQUIRED")),
        "failed": float(statuses.count("FIT_FAILED")),
        "false_accept_rate": (
            sum(statuses[i] == "FIT_OK" for i in inaccurate) / len(inaccurate)
            if inaccurate
            else float("nan")
        ),
        "failure_recall": (
            sum(statuses[i] == "FIT_FAILED" for i in inaccurate) / len(inaccurate)
            if inaccurate
            else float("nan")
        ),
        "false_failure_rate": (
            sum(statuses[i] == "FIT_FAILED" for i in accurate) / len(accurate)
            if accurate
            else float("nan")
        ),
    }


def select_policy(
    rows: list[dict[str, object]], max_false_failure: float
) -> tuple[float, float]:
    """Select only on training cases; constrain false failures among accurate fits."""
    candidates = [(r, l) for r in (0.04, 0.07, 0.10, 0.13, 0.16, 0.20)
                  for l in (0.70, 0.80, 0.90, 0.97, 0.985)]
    viable: list[tuple[float, float, float, float]] = []
    for rmse_gate, lag_gate in candidates:
        statuses = [classify(row, rmse_gate, lag_gate) for row in rows]
        metrics = score(rows, statuses)
        if (
            math.isfinite(metrics["false_failure_rate"])
            and metrics["false_failure_rate"] <= max_false_failure
            and math.isfinite(metrics["failure_recall"])
        ):
            viable.append((metrics["failure_recall"], -metrics["false_failure_rate"],
                           rmse_gate, lag_gate))
    if not viable:
        raise ValueError("No viable candidate; need both accurate and inaccurate training cases")
    _, _, rmse, lag = max(viable)
    return rmse, lag


def save_rows(path: Path, rows: list[dict[str, object]], statuses: list[str]) -> None:
    """Persist all observed errors alongside policy decisions."""
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*rows[0], "tuned_status"])
        writer.writeheader()
        for row, status in zip(rows, statuses, strict=True):
            writer.writerow({**row, "tuned_status": status})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-seed", type=int, default=20261024)
    parser.add_argument("--test-seed", type=int, default=20261124)
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--tolerance-mhz", type=float, default=0.5)
    parser.add_argument("--max-train-false-failure", type=float, default=0.05)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/odmr/experiments"))
    parser.add_argument("--tracking-uri", type=str, default=None)
    args = parser.parse_args()
    if args.train_seed == args.test_seed:
        parser.error("Training and holdout seeds must differ")
    if args.repeats < 1 or args.tolerance_mhz <= 0:
        parser.error("Positive repeats and tolerance required")
    if not 0 <= args.max_train_false_failure <= 1:
        parser.error("max-train-false-failure must be between 0 and 1")
    train = evaluate(make_cases(args.train_seed, args.repeats), args.tolerance_mhz)
    test = evaluate(make_cases(args.test_seed, args.repeats), args.tolerance_mhz)
    rmse_gate, lag_gate = select_policy(train, args.max_train_false_failure)
    location = new_run_location(args.output_dir, "adequacy-heldout-policy", args.tracking_uri)
    mlflow.set_tracking_uri(location.tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=location.run_name) as active:
        mlflow.set_tags({
            "project": "MagnetIQ",
            "pipeline": "synthetic-heldout-adequacy",
            "quality_labels": "synthetic-center-truth-only",
            "git_revision": git_revision(),
        })
        mlflow.log_params({
            "train_seed": args.train_seed,
            "test_seed": args.test_seed,
            "repeats": args.repeats,
            "center_tolerance_mhz": args.tolerance_mhz,
            "max_train_false_failure": args.max_train_false_failure,
            "selected_rmse_gate": rmse_gate,
            "selected_lag_gate": lag_gate,
        })
        result: dict[str, dict[str, float]] = {}
        for split, rows in (("train", train), ("holdout", test)):
            tuned = [classify(row, rmse_gate, lag_gate) for row in rows]
            save_rows(location.output_dir / f"{split}_cases.csv", rows, tuned)
            for policy, statuses in (
                ("existing", [str(row["current_status"]) for row in rows]),
                ("previous_candidate", [str(row["candidate_status"]) for row in rows]),
                ("tuned", tuned),
            ):
                metrics = score(rows, statuses)
                result[f"{split}_{policy}"] = metrics
                for key, value in metrics.items():
                    if np.isfinite(value):
                        mlflow.log_metric(f"{split}_{policy}_{key}", value)
                print(f"{split}/{policy}: {metrics}")
        (location.output_dir / "comparison.json").write_text(
            json.dumps({"thresholds": {"rmse": rmse_gate, "lag1": lag_gate},
                        "results": result, "mlflow_run_id": active.info.run_id}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        mlflow.log_artifacts(str(location.output_dir), artifact_path="benchmark")
        print(f"Selected on TRAIN only: nRMSE > {rmse_gate}, |lag1| > {lag_gate}")
        print(f"MLflow run: {active.info.run_id}")
        print(f"Reports: {location.output_dir}")
        print("Research only: no production thresholds were changed.")


if __name__ == "__main__":
    main()
