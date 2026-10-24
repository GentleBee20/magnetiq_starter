"""Unit tests for non-destructive ODMR previews."""

from zipfile import ZipFile

import pytest

from magnetiq.data.preview import preview_odmr


def test_preview_odmr(tmp_path):
    archive_path = tmp_path / "sample.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("Data/ODMR/Hole2/a.txt", b"Frequency,Signal\r\n1,2\r\n")
        archive.writestr("Data/ODMR/Hole3/b.txt", b"3;4\n")
        archive.writestr("Data/Profile/image.txt", b"unrelated\n")
    result = preview_odmr(archive_path, sample_count=2, line_count=2)
    assert result.number_of_files == 2
    assert result.groups == {"Hole2": 1, "Hole3": 1}
    assert result.samples[0].lines == ("b'Frequency,Signal'", "b'1,2'")
    assert result.samples[1].member_name == "Data/ODMR/Hole3/b.txt"


def test_preview_rejects_missing_archive(tmp_path):
    with pytest.raises(FileNotFoundError):
        preview_odmr(tmp_path / "missing.zip")


@pytest.mark.parametrize("samples,lines", [(0, 10), (2, 0), (-1, 1)])
def test_preview_rejects_invalid_limits(tmp_path, samples, lines):
    with pytest.raises(ValueError, match="must be positive"):
        preview_odmr(tmp_path / "missing.zip", sample_count=samples, line_count=lines)
