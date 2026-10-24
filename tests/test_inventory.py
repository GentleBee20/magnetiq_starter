"""Tests for archive inspection and persistence."""

import json
from zipfile import ZipFile

import pytest

from magnetiq.data.archive import inspect, inspect_archive


def test_inventory(tmp_path):
    sample = tmp_path / "test.zip"
    with ZipFile(sample, "w") as archive:
        archive.writestr("ODMR/sample.txt", "1,2\n3,4\n")
        archive.writestr("Scan images/scan.dat", b"abc")
        archive.writestr("empty_folder/", "")

    out_dir = tmp_path / "reports"
    result = inspect(sample, out_dir)

    assert result["n_files"] == 2
    assert result["extensions"] == {".dat": 1, ".txt": 1}
    assert result["files"][0]["name"] == "ODMR/sample.txt"
    assert (out_dir / "archive_inventory.csv").is_file()
    assert json.loads((out_dir / "archive_inventory.json").read_text(encoding="utf-8")) == result


def test_missing_archive(tmp_path):
    with pytest.raises(FileNotFoundError, match="Archive not found"):
        inspect_archive(tmp_path / "missing.zip")


def test_invalid_archive(tmp_path):
    invalid = tmp_path / "invalid.zip"
    invalid.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="Not a valid ZIP"):
        inspect_archive(invalid)


def test_empty_archive(tmp_path):
    archive = tmp_path / "empty.zip"
    with ZipFile(archive, "w"):
        pass
    inventory = inspect_archive(archive)
    assert inventory["n_files"] == 0
    assert inventory["extensions"] == {}
