"""Deterministic MiniGrid probe environment for native semantics tests."""

from minigrid.core.grid import Grid
from minigrid.core.mission import MissionSpace
from minigrid.core.world_object import Door, Key
from minigrid.minigrid_env import MiniGridEnv


class LockedDoorProbeEnv(MiniGridEnv):
    """A key of `key_color` in front of the agent and a locked red door."""

    def __init__(self, key_color: str = "red") -> None:
        self._key_color = key_color
        super().__init__(
            mission_space=MissionSpace(mission_func=lambda: "probe"),
            width=6,
            height=5,
            max_steps=32,
        )

    def _gen_grid(self, width: int, height: int) -> None:
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)
        self.agent_pos = (1, 1)
        self.agent_dir = 0
        self.put_obj(Key(self._key_color), 2, 1)
        self.put_obj(Door("red", is_locked=True), 3, 1)
        self.mission = "probe"


def make_locked_door_probe_env(key_color: str = "red") -> LockedDoorProbeEnv:
    return LockedDoorProbeEnv(key_color)
