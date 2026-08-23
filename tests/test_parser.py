"""Golden tests: real dictation transcripts and the pre-comma baseline.

Fixtures are frozen snapshots — refresh tests/fixtures/transcripts.txt and
transcripts_expected.json deliberately when the live dictations change.

Known limitations intentionally NOT asserted:
- T1 LVPW_E swallows КДР's value («задняя стенка 8,12» followed by «КДР 50»
  is ambiguous for a count=3 group).
"""

import json
from pathlib import Path

import pytest

from parser import parse

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_transcripts() -> tuple[list[str], dict]:
    lines = [
        line.replace("\r", "")
        for line in FIXTURES.joinpath("transcripts.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    expected = json.loads(
        FIXTURES.joinpath("transcripts_expected.json").read_text(encoding="utf-8")
    )
    return lines, expected


def test_unrecognized_transcript_raises(config):
    with pytest.raises(ValueError, match="не удалось распознать"):
        parse("", config)


def test_comma_decimals_parse_end_to_end(config):
    findings = parse("диаметр выходного тракта 21,2", config)
    assert findings == {"LVOT": 21.2}


def test_branch_integers_take_first_value(config):
    findings = parse("ветви 12,13", config)
    assert findings == {"PA_BRANCH": 12.0}


def test_three_part_group_stays_separate(config):
    findings = parse("задняя стенка 9,12,8", config)
    assert findings == {"LVPW_d": 9.0, "LVPW_s": 12.0, "LVPW_E": 8.0}


@pytest.mark.parametrize("index", ["1", "2"])
def test_real_transcripts_match_golden(config, index):
    lines, expected = _load_transcripts()
    findings = parse(lines[int(index) - 1], config)

    missing = [key for key in expected[index] if key not in findings]
    wrong = {
        key: (value, findings.get(key))
        for key, value in expected[index].items()
        if key in findings and findings[key] != value
    }
    assert not missing, f"fields absent from output: {missing}"
    assert not wrong, f"field mismatches (expected, got): {wrong}"


def test_pre_comma_baseline_unchanged(config):
    data = json.loads(FIXTURES.joinpath("baseline.json").read_text(encoding="utf-8"))
    for sample, expected in zip(data["samples"], data["outputs"]):
        assert parse(sample, config) == expected
