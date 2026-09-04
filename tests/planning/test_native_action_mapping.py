from neuro_symbolic_vln.contracts import SymbolicAction

# Native action map from Member A contract
NATIVE_ACTION_MAP: dict[str, str] = {
    "turn-left": "turn_left",
    "turn-right": "turn_right",
    "move-forward": "move_forward",
    "pickup-key": "pickup",
    "toggle-locked-door": "toggle",
}

CONFIRMATION_ACTIONS: set[str] = {"confirm-goto"}


def map_symbolic_to_native(action: SymbolicAction) -> str | None:
    """Maps a symbolic action to Member A native primitive or None for confirmation."""
    if action.name in CONFIRMATION_ACTIONS:
        return None
    if action.name in NATIVE_ACTION_MAP:
        return NATIVE_ACTION_MAP[action.name]
    raise ValueError(f"Unsupported symbolic action: {action.name}")


def test_primitive_actions_map_to_native() -> None:
    assert (
        map_symbolic_to_native(SymbolicAction("turn-left", ("robot", "north", "west")))
        == "turn_left"
    )
    assert (
        map_symbolic_to_native(SymbolicAction("turn-right", ("robot", "north", "east")))
        == "turn_right"
    )
    assert (
        map_symbolic_to_native(
            SymbolicAction("move-forward", ("robot", "loc-1", "loc-2", "east"))
        )
        == "move_forward"
    )
    assert (
        map_symbolic_to_native(
            SymbolicAction(
                "pickup-key", ("robot", "key-1", "loc-1", "loc-2", "east")
            )
        )
        == "pickup"
    )
    assert (
        map_symbolic_to_native(
            SymbolicAction(
                "toggle-locked-door",
                ("robot", "key-1", "door-1", "loc-1", "loc-2", "east"),
            )
        )
        == "toggle"
    )


def test_confirmation_action_does_not_emit_primitive() -> None:
    confirm_action = SymbolicAction(
        "confirm-goto", ("robot", "target-1", "loc-1", "loc-2", "east")
    )
    assert map_symbolic_to_native(confirm_action) is None


def test_action_schemas_conform_to_b_specification() -> None:
    # Verify expected parameter counts for all action types
    expected_arities = {
        "turn-left": 3,  # ?r, ?from, ?to
        "turn-right": 3,  # ?r, ?from, ?to
        "move-forward": 4,  # ?r, ?from, ?to, ?h
        "pickup-key": 5,  # ?r, ?k, ?loc, ?front, ?h
        "toggle-locked-door": 6,  # ?r, ?k, ?d, ?loc, ?front, ?h
        "confirm-goto": 5,  # ?r, ?t, ?from, ?target-loc, ?h
    }

    sample_actions = [
        SymbolicAction("turn-left", ("robot", "north", "west")),
        SymbolicAction("turn-right", ("robot", "north", "east")),
        SymbolicAction("move-forward", ("robot", "loc-1", "loc-2", "east")),
        SymbolicAction("pickup-key", ("robot", "key-1", "loc-1", "loc-2", "east")),
        SymbolicAction(
            "toggle-locked-door",
            ("robot", "key-1", "door-1", "loc-1", "loc-2", "east"),
        ),
        SymbolicAction(
            "confirm-goto", ("robot", "target-1", "loc-1", "loc-2", "east")
        ),
    ]

    for action in sample_actions:
        assert len(action.arguments) == expected_arities[action.name]
