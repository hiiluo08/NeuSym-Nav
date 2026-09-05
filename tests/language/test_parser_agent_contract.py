from neuro_symbolic_vln.contracts import (
    EpisodeOutcome,
    ParseResult,
    ParseStatus,
)
from neuro_symbolic_vln.language.template_parser import parse_instruction


def decide_agent_lifecycle(
    parse_result: ParseResult,
) -> tuple[EpisodeOutcome | None, tuple[str, ...]]:
    """
    Simulates agent top-level dispatch contract based on parse result.
    If parse fails, no environment actions may be emitted.
    """
    if parse_result.status is ParseStatus.UNSUPPORTED:
        # Agent terminates immediately without issuing any primitive actions
        return EpisodeOutcome.UNSUPPORTED_INSTRUCTION, ()

    if parse_result.status is ParseStatus.AMBIGUOUS:
        # Agent terminates immediately or requests clarification without action
        return EpisodeOutcome.AMBIGUOUS_GROUNDING, ()

    assert parse_result.status is ParseStatus.DETERMINISTIC
    assert parse_result.goal_program is not None
    # For deterministic instructions, execution proceeds to perception/planning
    return None, ("execute",)


def test_unsupported_instruction_emits_no_action() -> None:
    unsupported_instructions = [
        "Go to the object left of the yellow box.",
        "If you see a blue door, use it; otherwise use the red door.",
        "Put the green ball next to the box.",
        "dance around the room",
        "",
    ]
    for instruction in unsupported_instructions:
        result = parse_instruction(instruction)
        assert result.status is ParseStatus.UNSUPPORTED
        assert result.goal_program is None
        assert result.reason is not None and len(result.reason) > 0

        outcome, actions = decide_agent_lifecycle(result)
        assert outcome is EpisodeOutcome.UNSUPPORTED_INSTRUCTION
        assert actions == (), "Agent must emit zero actions on unsupported instruction!"


def test_ambiguous_instruction_emits_no_action() -> None:
    ambiguous_instructions = [
        "Go to the key",
        "Open the red door then open the blue door",
        "Pick up the red key and the blue key",
        "open the door",
    ]
    for instruction in ambiguous_instructions:
        result = parse_instruction(instruction)
        assert result.status is ParseStatus.AMBIGUOUS
        assert result.goal_program is None
        assert result.reason is not None and len(result.reason) > 0

        outcome, actions = decide_agent_lifecycle(result)
        assert outcome is EpisodeOutcome.AMBIGUOUS_GROUNDING
        assert actions == (), "Agent must emit zero actions on ambiguous instruction!"


def test_deterministic_instruction_proceeds_to_execution() -> None:
    valid_instructions = [
        "Go to the green ball.",
        "pick up the yellow key, open the yellow door, then go to the goal",
    ]
    for instruction in valid_instructions:
        result = parse_instruction(instruction)
        assert result.status is ParseStatus.DETERMINISTIC
        assert result.goal_program is not None
        assert len(result.goal_program.ordered_subgoals) >= 1
        assert result.reason is None

        outcome, actions = decide_agent_lifecycle(result)
        assert outcome is None
        assert len(actions) > 0
