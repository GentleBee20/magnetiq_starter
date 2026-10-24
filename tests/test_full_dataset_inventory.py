"""Tests for the read-only scientific ZIP inventory."""

import io
import zipfile

from scripts.inventory_full_dataset import inventory


def test_inventory_groups_and_nested_zip(tmp_path):
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w") as nested:
        nested.writestr("Data/Coherence/ramsey.txt", "Time [us],Contrast\n0,1\n1,0.9\n")
    archive = tmp_path / "dataset.zip"
    with zipfile.ZipFile(archive, "w") as outer:
        outer.writestr("Data/ODMR/sample.txt", "Freq [GHz],Normalized readout contrast\n2.85,0.99\n")
        outer.writestr("Data/Profile/nested.zip", inner.getvalue())
    result = inventory(archive)
    assert result["total_entries_including_nested"] == 3
    assert result["categories"]["odmr"] == 1
    assert result["categories"]["coherence"] == 1
    assert result["files"][0]["preview"]["unit_tokens"] == ["[GHz]"]
    assert result["sha256"]


def test_image_metadata_read_without_extraction(tmp_path):
    archive = tmp_path / "pictures.zip"
    header = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + (20).to_bytes(
        4, "big"
    ) + (30).to_bytes(4, "big")
    with zipfile.ZipFile(archive, "w") as outer:
        outer.writestr("Data/Scan/field.png", header)
    result = inventory(archive)
    assert result["files"][0]["png_dimensions"] == [20, 30]


def test_nul_containing_nested_text_is_reported_not_fatal(tmp_path):
    nested_bytes = io.BytesIO()
    with zipfile.ZipFile(nested_bytes, "w") as nested:
        nested.writestr("Data/Coherence/mixed.txt", b"header\x00binary\n")
    archive = tmp_path / "data.zip"
    with zipfile.ZipFile(archive, "w") as outer:
        outer.writestr("nested.zip", nested_bytes.getvalue())
    result = inventory(archive)
    suspect = next(row for row in result["files"] if row["path"].endswith("mixed.txt"))
    assert suspect["preview"]["sample"] == "binary_or_nul_containing"
    assert result["total_entries_including_nested"] == 2
