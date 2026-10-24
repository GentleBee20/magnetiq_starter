"""Coverage of the portable HTML report's plot links and escaping."""

import json

from magnetiq.processing.diagnostics import FitDiagnostics
from magnetiq.reporting.mvp_report import write_measurement_report


def test_report_links_existing_plots_and_escapes_sources(tmp_path):
    plots = tmp_path / "plots"
    plots.mkdir()
    (plots / "001_test.png").write_bytes(b"example")
    item = FitDiagnostics(
        source="input/<test>.txt",
        model="double",
        status="REVIEW_REQUIRED",
        warnings=("structured_residuals",),
        rmse=0.1,
        normalized_rmse=0.2,
        max_abs_residual=0.3,
        lag1_residual_correlation=0.8,
        delta_aicc_to_runner_up=3.0,
        center_1_ghz=None,
        center_2_ghz=None,
        separation_mhz=None,
        width_1_mhz=None,
        width_2_mhz=None,
        amplitude_1=None,
        amplitude_2=None,
    )
    write_measurement_report([item], tmp_path)
    html = (tmp_path / "measurement_report.html").read_text(encoding="utf-8")
    assert "plots/001_&lt;test&gt;.png" not in html
    assert "Plot unavailable" in html
    assert "&lt;test&gt;.txt" in html
    assert "structured_residuals" in html
    assert "summary.png" in html
    data = json.loads((tmp_path / "measurement_report.json").read_text(encoding="utf-8"))
    assert len(data["measurements"]) == 1


def test_plot_link_when_file_exists(tmp_path):
    plot_dir = tmp_path / "plots"
    plot_dir.mkdir()
    (plot_dir / "001_test.png").write_bytes(b"example")
    item = FitDiagnostics(
        source="test.txt",
        model="baseline",
        status="FIT_OK",
        warnings=(),
        rmse=0.1,
        normalized_rmse=0.1,
        max_abs_residual=0.1,
        lag1_residual_correlation=0.1,
        delta_aicc_to_runner_up=2.0,
        center_1_ghz=None,
        center_2_ghz=None,
        separation_mhz=None,
        width_1_mhz=None,
        width_2_mhz=None,
        amplitude_1=None,
        amplitude_2=None,
    )
    write_measurement_report([item], tmp_path)
    html = (tmp_path / "measurement_report.html").read_text(encoding="utf-8")
    assert 'href="plots/001_test.png"' in html
