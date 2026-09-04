from pathlib import Path

from neuro_symbolic_vln.contracts import (
    CommittedPlanningState,
    GroundAtom,
    LocationGraph,
    PlanStatus,
    SymbolicAction,
)
from neuro_symbolic_vln.planning.location_graph import LocationGraphBuilder
from neuro_symbolic_vln.planning.problem_serializer import serialize_problem
from neuro_symbolic_vln.planning.pyperplan_adapter import (
    PlannerConfig,
    parse_symbolic_action,
    parse_symbolic_actions,
    plan_with_timeout,
)


def get_domain_path() -> str:
    domain_path = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "neuro_symbolic_vln"
        / "planning"
        / "domain.pddl"
    )
    return str(domain_path)


def test_symbolic_action_parse_roundtrip_exact() -> None:
    raw = "(move-forward robot loc-1 loc-2 east)"
    action = parse_symbolic_action(raw)
    assert action.name == "move-forward"
    assert action.arguments == ("robot", "loc-1", "loc-2", "east")

    plan = [
        "(turn-right robot north east)",
        "(move-forward robot loc-1 loc-2 east)",
    ]
    actions = parse_symbolic_actions(plan)
    assert len(actions) == 2
    assert actions[0] == SymbolicAction("turn-right", ("robot", "north", "east"))
    assert actions[1] == SymbolicAction(
        "move-forward", ("robot", "loc-1", "loc-2", "east")
    )


def test_turn_move_plan_found() -> None:
    builder = LocationGraphBuilder()
    builder.add_edge("loc-1", "east", "loc-2")
    graph = builder.build()

    state = CommittedPlanningState(
        version=1,
        state_hash="state-move",
        true_facts=frozenset(
            {
                GroundAtom("robot-at", ("robot", "loc-1")),
                GroundAtom("facing", ("robot", "north")),
                GroundAtom("passable", ("loc-2",)),
            }
        ),
        unresolved_required_facts=frozenset(),
        provenance_by_fact={},
        location_graph=graph,
    )

    problem_str = serialize_problem(
        state, goal_atom=GroundAtom("robot-at", ("robot", "loc-2"))
    )
    result = plan_with_timeout(state, get_domain_path(), problem_str)

    assert result.status == PlanStatus.FOUND
    assert result.problem_hash is not None
    assert len(result.actions) == 2
    assert result.actions[0].name == "turn-right"
    assert result.actions[1].name == "move-forward"


def test_goto_confirm_from_adjacent_facing_pose() -> None:
    builder = LocationGraphBuilder()
    builder.add_edge("loc-1", "east", "loc-target")
    graph = builder.build()

    state = CommittedPlanningState(
        version=1,
        state_hash="state-goto",
        true_facts=frozenset(
            {
                GroundAtom("robot-at", ("robot", "loc-1")),
                GroundAtom("facing", ("robot", "north")),
                GroundAtom("target-at", ("target-1", "loc-target")),
            }
        ),
        unresolved_required_facts=frozenset(),
        provenance_by_fact={},
        location_graph=graph,
    )

    problem_str = serialize_problem(
        state, goal_atom=GroundAtom("task-satisfied", ())
    )
    result = plan_with_timeout(state, get_domain_path(), problem_str)

    assert result.status == PlanStatus.FOUND
    assert len(result.actions) == 2
    assert result.actions[0].name == "turn-right"
    assert result.actions[1].name == "confirm-goto"
    assert result.actions[1].arguments == (
        "robot",
        "target-1",
        "loc-1",
        "loc-target",
        "east",
    )


def test_key_pickup_before_door_toggle_and_crossing() -> None:
    builder = LocationGraphBuilder()
    builder.add_edge("loc-1", "east", "loc-2")
    builder.add_edge("loc-2", "east", "loc-3")
    builder.add_edge("loc-3", "east", "loc-4")
    graph = builder.build()

    state = CommittedPlanningState(
        version=1,
        state_hash="state-key-door",
        true_facts=frozenset(
            {
                GroundAtom("robot-at", ("robot", "loc-1")),
                GroundAtom("facing", ("robot", "east")),
                GroundAtom("handempty", ("robot",)),
                GroundAtom("key-at", ("key-1", "loc-2")),
                GroundAtom("door-at", ("door-1", "loc-3")),
                GroundAtom("door-locked", ("door-1",)),
                GroundAtom("key-opens", ("key-1", "door-1")),
                GroundAtom("passable", ("loc-2",)),
                GroundAtom("passable", ("loc-4",)),
            }
        ),
        unresolved_required_facts=frozenset(),
        provenance_by_fact={},
        location_graph=graph,
    )

    problem_str = serialize_problem(
        state, goal_atom=GroundAtom("robot-at", ("robot", "loc-4"))
    )
    result = plan_with_timeout(state, get_domain_path(), problem_str)

    assert result.status == PlanStatus.FOUND
    action_names = [a.name for a in result.actions]
    assert action_names == [
        "pickup-key",
        "move-forward",
        "toggle-locked-door",
        "move-forward",
        "move-forward",
    ]


def test_already_satisfied_goal() -> None:
    state = CommittedPlanningState(
        version=1,
        state_hash="state-satisfied",
        true_facts=frozenset({GroundAtom("robot-at", ("robot", "loc-1"))}),
        unresolved_required_facts=frozenset(),
        provenance_by_fact={},
        location_graph=LocationGraph(
            nodes=frozenset({"loc-1"}),
            directed_edges=frozenset(),
            frontier_nodes=frozenset(),
        ),
    )
    problem_str = serialize_problem(
        state, goal_atom=GroundAtom("robot-at", ("robot", "loc-1"))
    )
    result = plan_with_timeout(state, get_domain_path(), problem_str)

    assert result.status == PlanStatus.ALREADY_SATISFIED
    assert result.actions == ()


def test_no_plan_in_known_space() -> None:
    state = CommittedPlanningState(
        version=1,
        state_hash="state-no-plan",
        true_facts=frozenset({GroundAtom("robot-at", ("robot", "loc-1"))}),
        unresolved_required_facts=frozenset(),
        provenance_by_fact={},
        location_graph=LocationGraph(
            nodes=frozenset({"loc-1", "loc-2"}),
            directed_edges=frozenset(),  # No edge connecting loc-1 to loc-2
            frontier_nodes=frozenset(),
        ),
    )
    problem_str = serialize_problem(
        state, goal_atom=GroundAtom("robot-at", ("robot", "loc-2"))
    )
    result = plan_with_timeout(state, get_domain_path(), problem_str)

    assert result.status == PlanStatus.NO_PLAN_KNOWN_SPACE
    assert result.actions == ()


def test_bounded_worker_timeout_does_not_hang() -> None:
    builder = LocationGraphBuilder()
    for i in range(10):
        builder.add_edge(f"loc-{i}", "east", f"loc-{i+1}")
    graph = builder.build()

    state = CommittedPlanningState(
        version=1,
        state_hash="state-timeout",
        true_facts=frozenset(
            {
                GroundAtom("robot-at", ("robot", "loc-0")),
                GroundAtom("facing", ("robot", "north")),
            }
        ),
        unresolved_required_facts=frozenset(),
        provenance_by_fact={},
        location_graph=graph,
    )
    problem_str = serialize_problem(
        state, goal_atom=GroundAtom("robot-at", ("robot", "loc-10"))
    )
    # Extremely small timeout to guarantee timeout trigger
    config = PlannerConfig(timeout_seconds=0.0001)
    result = plan_with_timeout(state, get_domain_path(), problem_str, config)

    assert result.status == PlanStatus.TIMEOUT
    assert result.actions == ()
    assert "timeout" in (result.reason or "").lower()


def test_planner_error_on_invalid_pddl() -> None:
    state = CommittedPlanningState(
        version=1,
        state_hash="state-error",
        true_facts=frozenset(),
        unresolved_required_facts=frozenset(),
        provenance_by_fact={},
        location_graph=LocationGraph(frozenset(), frozenset(), frozenset()),
    )
    invalid_problem = "(define (invalid-problem syntax error))"
    result = plan_with_timeout(state, get_domain_path(), invalid_problem)

    assert result.status == PlanStatus.PLANNER_ERROR
    assert result.actions == ()


def test_planning_package_has_no_minigrid_import() -> None:
    import ast

    planning_dir = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "neuro_symbolic_vln"
        / "planning"
    )
    for py_file in planning_dir.glob("*.py"):
        with open(py_file, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "minigrid" not in alias.name.lower(), (
                        f"{py_file.name} imports MiniGrid: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert "minigrid" not in module.lower(), (
                    f"{py_file.name} imports from MiniGrid: {module}"
                )

