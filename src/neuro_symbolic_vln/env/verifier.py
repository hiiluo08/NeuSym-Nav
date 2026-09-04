"""Explicit task verifiers over local actuator state."""

from dataclasses import dataclass

_DIRECTION_TO_DELTA = {
    0: (1, 0),
    1: (0, 1),
    2: (-1, 0),
    3: (0, -1),
}


@dataclass(frozen=True)
class GoToVerifier:
    target_position: tuple[int, int]

    def is_satisfied(
        self, agent_position: tuple[int, int], agent_direction: int
    ) -> bool:
        try:
            dx, dy = _DIRECTION_TO_DELTA[agent_direction]
        except KeyError as error:
            raise ValueError(
                f"invalid MiniGrid direction: {agent_direction}"
            ) from error
        return (
            agent_position[0] + dx,
            agent_position[1] + dy,
        ) == self.target_position
