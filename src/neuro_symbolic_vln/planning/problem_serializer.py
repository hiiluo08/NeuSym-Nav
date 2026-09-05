"""PDDL problem serializer from committed planning state."""

from __future__ import annotations

from neuro_symbolic_vln.contracts import CommittedPlanningState, GroundAtom
from neuro_symbolic_vln.planning.location_graph import graph_to_front_cell_atoms


def serialize_problem(state: CommittedPlanningState, goal_atom: GroundAtom) -> str:
    """
    Serializes a CommittedPlanningState and goal atom into a PDDL problem string.
    Only true_facts and known location_graph topology are emitted into :init.
    Unresolved required facts (unknowns) are never emitted.
    """
    # 1. Collect objects dynamically
    locations: set[str] = set(state.location_graph.nodes)
    robots: set[str] = {"robot"}
    keys: set[str] = set()
    doors: set[str] = set()
    targets: set[str] = set()

    for atom in state.true_facts:
        if atom.predicate in ("robot-at", "at") and len(atom.arguments) >= 2:
            robots.add(atom.arguments[0])
            locations.add(atom.arguments[1])
        elif atom.predicate in ("key-at",) and len(atom.arguments) >= 2:
            keys.add(atom.arguments[0])
            locations.add(atom.arguments[1])
        elif atom.predicate in ("holding",) and len(atom.arguments) >= 2:
            robots.add(atom.arguments[0])
            keys.add(atom.arguments[1])
        elif atom.predicate in ("door-at",) and len(atom.arguments) >= 2:
            doors.add(atom.arguments[0])
            locations.add(atom.arguments[1])
        elif atom.predicate in ("door-locked", "door-open") and atom.arguments:
            doors.add(atom.arguments[0])
        elif atom.predicate in ("key-opens",) and len(atom.arguments) >= 2:
            keys.add(atom.arguments[0])
            doors.add(atom.arguments[1])
        elif atom.predicate in ("target-at",) and len(atom.arguments) >= 2:
            targets.add(atom.arguments[0])
            locations.add(atom.arguments[1])
        elif atom.predicate in ("passable", "free") and atom.arguments:
            locations.add(atom.arguments[0])

    if goal_atom.predicate in ("target-at",) and len(goal_atom.arguments) >= 2:
        targets.add(goal_atom.arguments[0])
        locations.add(goal_atom.arguments[1])
    elif goal_atom.predicate in ("robot-at", "at") and len(goal_atom.arguments) >= 2:
        robots.add(goal_atom.arguments[0])
        locations.add(goal_atom.arguments[1])

    objects_lines: list[str] = [
        "north east south west - heading",
        f"{' '.join(sorted(robots))} - robot",
    ]
    if locations:
        objects_lines.append(f"{' '.join(sorted(locations))} - location")
    if keys:
        objects_lines.append(f"{' '.join(sorted(keys))} - key")
    if doors:
        objects_lines.append(f"{' '.join(sorted(doors))} - door")
    if targets:
        objects_lines.append(f"{' '.join(sorted(targets))} - target")

    objects_block = "\n            ".join(objects_lines)

    # 2. INIT DECLARATION (Only true_facts, edges, and static rotations)
    init_facts: list[str] = []

    for atom in state.true_facts:
        if atom.arguments:
            args_str = " ".join(atom.arguments)
            init_facts.append(f"({atom.predicate} {args_str})")
        else:
            init_facts.append(f"({atom.predicate})")

    # Topological connectivity from LocationGraph
    for atom in graph_to_front_cell_atoms(state.location_graph):
        args_str = " ".join(atom.arguments)
        init_facts.append(f"({atom.predicate} {args_str})")

    # Static rotation relations
    static_rotation = [
        "(turn-left-of north west)",
        "(turn-left-of west south)",
        "(turn-left-of south east)",
        "(turn-left-of east north)",
        "(turn-right-of north east)",
        "(turn-right-of east south)",
        "(turn-right-of south west)",
        "(turn-right-of west north)",
    ]
    init_facts.extend(static_rotation)

    init_block = "\n            ".join(init_facts)

    # 3. GOAL DECLARATION
    if goal_atom.arguments:
        goal_args = " ".join(goal_atom.arguments)
        goal_predicate_str = f"({goal_atom.predicate} {goal_args})"
    else:
        goal_predicate_str = f"({goal_atom.predicate})"

    # 4. CONCATENATE INTO PDDL PROBLEM
    pddl_sequence = f"""(define (problem current-state)
    (:domain vln-minigrid)
    (:objects
        {objects_block}
    )
    (:init
        {init_block}
    )
    (:goal
        {goal_predicate_str}
    )
)
"""
    return pddl_sequence
