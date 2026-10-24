from pathlib import Path
from zipfile import ZipFile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from inspect_archive import inspect


def test_inventory(tmp_path):
    sample = tmp_path / "test.zip"
    with ZipFile(sample, "w") as archive:
        archive.writestr("ODMR/sample.txt", "1,2\n3,4\n")
        archive.writestr("Scan images/scan.dat", b"abc")
    result = inspect(sample, tmp_path / "reports")
    assert result["n_files"] == 2
    assert result["extensions"][".txt"] == 1
    assert (tmp_path / "reports" / "archive_inventory.csv").is_file()
