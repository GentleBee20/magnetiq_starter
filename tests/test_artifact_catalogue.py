"""Artifact catalogue must explain existing warnings without diagnosing physics."""

from magnetiq.reporting.artifact_catalogue import CATALOGUE, describe_warnings


def test_known_reason_codes_have_investigation_guidance() -> None:
    notes = describe_warnings(("structured_residuals", "center_near_edge"))
    assert len(notes) == 2
    assert all(note["next_check"] for note in notes)
    assert notes[0]["investigation_stage"] == "signal_evaluation"


def test_unknown_reasons_are_not_invented() -> None:
    entry = describe_warnings(("future_code",))[0]
    assert entry["category"] == "unclassified"
    assert entry["investigation_stage"] == "undetermined"


def test_all_known_codes_have_nonempty_explanations() -> None:
    assert all(item.interpretation and item.next_check for item in CATALOGUE.values())
