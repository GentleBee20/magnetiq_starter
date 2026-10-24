"""Parser and dataset audit regression tests."""

from zipfile import ZipFile

import pytest

from magnetiq.data.audit import audit_odmr, write_audit
from magnetiq.data.odmr import parse_odmr

HEADER = "Freq [GHz],Normalized readout contrast\n"


def test_parse_valid_measurement():
    spectrum = parse_odmr(HEADER + "2.85,1.01\n2.8501,0.99\n")
    assert spectrum.count == 2
    assert spectrum.frequency_ghz == (2.85, 2.8501)
    assert spectrum.normalized_contrast == (1.01, 0.99)


@pytest.mark.parametrize(
    "content,diagnostic",
    [
        ("wrong,header\n2.85,1\n", "unexpected ODMR header"),
        (HEADER + "2.85,1\n", "at least two"),
        (HEADER + "2.85,1\n2.85,2\n", "strictly increasing"),
        (HEADER + "2.85,nan\n2.86,1\n", "nonfinite"),
        (HEADER + "2.85,abc\n2.86,1\n", "nonnumeric"),
        (HEADER + "2.85,1,3\n2.86,1\n", "expected two columns"),
    ],
)
def test_invalid_measurements(content, diagnostic):
    with pytest.raises(ValueError, match=diagnostic):
        parse_odmr(content)


def test_audit_records_failures_without_stopping(tmp_path):
    source = tmp_path / "dataset.zip"
    with ZipFile(source, "w") as archive:
        archive.writestr("Data/ODMR/Hole2/ok.txt", HEADER + "2.85,1\n2.8501,0.9\n")
        archive.writestr("Data/ODMR/Hole2/bad.txt", "not,csv\n")
        archive.writestr("Data/Profile/other.txt", "ignored")
    records = audit_odmr(source)
    assert [record.status for record in records] == ["INVALID", "VALID"]
    assert records[1].median_step_mhz == pytest.approx(0.1)
    output = tmp_path / "audit.csv"
    write_audit(records, output)
    assert output.is_file()
