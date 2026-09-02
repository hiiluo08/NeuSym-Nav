import pytest

from neuro_symbolic_vln.contracts import GroundAtom


def test_ground_atom_is_immuatable_and_orderable() -> None:
    atom = GroundAtom("robot-at", ("robot", "loc-1"))
    with pytest.raises(AttributeError):
        atom.predicate = "changed" # type: ignore[misc]
    assert atom < GroundAtom("wall", ("loc-1",))
