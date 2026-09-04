import pytest

from neuro_symbolic_vln.env.verifier import GoToVerifier


def test_goto_requires_adjacent_and_facing() -> None:
    verifier = GoToVerifier(target_position=(2, 1))

    assert not verifier.is_satisfied(agent_position=(1, 1), agent_direction=1)
    assert verifier.is_satisfied(agent_position=(1, 1), agent_direction=0)


def test_invalid_direction_raises() -> None:
    verifier = GoToVerifier(target_position=(2, 1))

    with pytest.raises(ValueError):
        verifier.is_satisfied(agent_position=(1, 1), agent_direction=9)
