"""Installed CLI dispatches to the packaged analysis runner."""

from __future__ import annotations

import sys
from pathlib import Path

from magnetiq import cli


def test_analyze_command_invokes_package_runner(monkeypatch, capsys) -> None:
    calls: list[tuple[Path, int, str | None]] = []

    def fake_runner(
        archive: Path,
        *,
        limit: int,
        output_dir: Path,
        run_name: str | None,
        tracking_uri: str | None,
    ) -> Path:
        calls.append((archive, limit, run_name))
        return output_dir / "test-run"

    monkeypatch.setattr(cli, "run_analysis", fake_runner)
    monkeypatch.setattr(
        sys,
        "argv",
        ["magnetiq", "analyze", "example.zip", "--limit", "2", "--run-name", "smoke"],
    )
    cli.main()
    assert calls == [(Path("example.zip"), 2, "smoke")]
    assert "measurement_report.html" in capsys.readouterr().out
