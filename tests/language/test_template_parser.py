from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from neuro_symbolic_vln.contracts import GroundAtom, ParseStatus
from neuro_symbolic_vln.language.template_parser import (
    TemplateInstructionParser,
    normalize_instruction,
    parse_instruction,
)


def load_fixtures() -> dict[str, Any]:
    fixture_path = Path(__file__).parent / "fixtures" / "curated_cases.yaml"
    with open(fixture_path, encoding="utf-8") as f:
        return cast(dict[str, Any], yaml.safe_load(f))


FIXTURES = load_fixtures()


def test_parse_goto_instruction() -> None:
    """Canonical test from Member B handbook Step 1."""
    result = parse_instruction("Go to the green ball.")
    assert result.status.value == "deterministic"
    assert result.goal_program is not None
    assert result.goal_program.family == "goto_type_color"
    assert result.goal_program.ordered_subgoals == (
        GroundAtom("goto-target", ("green", "ball")),
    )


def test_normalization_details() -> None:
    assert (
        normalize_instruction("   GO TO   THE   RED   BALL.!?  ")
        == "go to the red ball"
    )


@pytest.mark.parametrize("case", FIXTURES["goto_supported"], ids=lambda c: c["id"])
def test_curated_goto_supported(case: dict[str, Any]) -> None:
    result = parse_instruction(case["instruction"])
    assert result.status.value == case["expected_status"]
    assert result.goal_program is not None
    assert result.goal_program.family == case["family"]

    expected_subgoals = tuple(
        GroundAtom(predicate=item[0], arguments=tuple(item[1]))
        for item in case["subgoals"]
    )
    assert result.goal_program.ordered_subgoals == expected_subgoals
    assert result.reason is None


@pytest.mark.parametrize("case", FIXTURES["key_door_supported"], ids=lambda c: c["id"])
def test_curated_key_door_supported(case: dict[str, Any]) -> None:
    result = parse_instruction(case["instruction"])
    assert result.status.value == case["expected_status"]
    assert result.goal_program is not None
    assert result.goal_program.family == case["family"]

    expected_subgoals = tuple(
        GroundAtom(predicate=item[0], arguments=tuple(item[1]))
        for item in case["subgoals"]
    )
    assert result.goal_program.ordered_subgoals == expected_subgoals
    assert result.reason is None


@pytest.mark.parametrize("case", FIXTURES["ambiguous_cases"], ids=lambda c: c["id"])
def test_curated_ambiguous(case: dict[str, Any]) -> None:
    result = parse_instruction(case["instruction"])
    assert result.status is ParseStatus.AMBIGUOUS
    assert result.status.value == case["expected_status"]
    assert result.goal_program is None
    assert result.reason == case["expected_reason"]


@pytest.mark.parametrize("case", FIXTURES["unsupported_cases"], ids=lambda c: c["id"])
def test_curated_unsupported(case: dict[str, Any]) -> None:
    result = parse_instruction(case["instruction"])
    assert result.status is ParseStatus.UNSUPPORTED
    assert result.status.value == case["expected_status"]
    assert result.goal_program is None
    assert result.reason == case["expected_reason"]


def test_template_instruction_parser_protocol_wrapper() -> None:
    parser = TemplateInstructionParser()
    res = parser.parse("Find the blue box")
    assert res.status is ParseStatus.DETERMINISTIC
    assert res.goal_program is not None
    assert res.goal_program.ordered_subgoals == (
        GroundAtom("goto-target", ("blue", "box")),
    )
