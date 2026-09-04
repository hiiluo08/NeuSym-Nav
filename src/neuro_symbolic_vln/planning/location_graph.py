"""Topological location graph operations and PDDL connectivity generation."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from neuro_symbolic_vln.contracts import (
    GroundAtom,
    HeadingId,
    LocationGraph,
    LocationId,
)


class LocationGraphBuilder:
    """Builder to construct an immutable LocationGraph incrementally."""

    def __init__(self) -> None:
        self._nodes: set[LocationId] = set()
        self._directed_edges: set[tuple[LocationId, HeadingId, LocationId]] = set()
        self._frontier_nodes: set[LocationId] = set()

    def add_node(self, node: LocationId) -> LocationGraphBuilder:
        self._nodes.add(node)
        return self

    def add_nodes(self, nodes: Iterable[LocationId]) -> LocationGraphBuilder:
        self._nodes.update(nodes)
        return self

    def add_edge(
        self, from_loc: LocationId, heading: HeadingId, to_loc: LocationId
    ) -> LocationGraphBuilder:
        self._nodes.add(from_loc)
        self._nodes.add(to_loc)
        self._directed_edges.add((from_loc, heading, to_loc))
        return self

    def mark_frontier(self, node: LocationId) -> LocationGraphBuilder:
        self._nodes.add(node)
        self._frontier_nodes.add(node)
        return self

    def unmark_frontier(self, node: LocationId) -> LocationGraphBuilder:
        self._frontier_nodes.discard(node)
        return self

    def build(self) -> LocationGraph:
        """Returns a validated, immutable LocationGraph."""
        graph = LocationGraph(
            nodes=frozenset(self._nodes),
            directed_edges=frozenset(self._directed_edges),
            frontier_nodes=frozenset(self._frontier_nodes),
        )
        validate_location_graph(graph)
        return graph


def validate_location_graph(graph: LocationGraph) -> None:
    """Checks that all edge endpoints and frontiers exist in nodes."""
    for from_loc, _, to_loc in graph.directed_edges:
        if from_loc not in graph.nodes:
            raise ValueError(f"Edge source '{from_loc}' not in graph nodes.")
        if to_loc not in graph.nodes:
            raise ValueError(f"Edge target '{to_loc}' not in graph nodes.")

    for f_node in graph.frontier_nodes:
        if f_node not in graph.nodes:
            raise ValueError(f"Frontier node '{f_node}' not in graph nodes.")


def graph_to_front_cell_atoms(graph: LocationGraph) -> frozenset[GroundAtom]:
    """
    Converts directed edges (from_loc, heading, to_loc) into GroundAtoms:
    GroundAtom("front-cell", (from_loc, heading, to_loc)) for PDDL problem generation.
    """
    return frozenset(
        GroundAtom(predicate="front-cell", arguments=(from_loc, heading, to_loc))
        for from_loc, heading, to_loc in graph.directed_edges
    )


# Alias for backward compatibility
graph_to_next_atoms = graph_to_front_cell_atoms


def get_forward_node(
    graph: LocationGraph, current_loc: LocationId, heading: HeadingId
) -> LocationId | None:
    """Returns the location directly in front of the robot given current pose."""
    for from_loc, h, to_loc in graph.directed_edges:
        if from_loc == current_loc and h == heading:
            return to_loc

    return None


def get_neighbors(
    graph: LocationGraph, current_loc: LocationId
) -> frozenset[LocationId]:
    """Returns all reachable neighbor locations from current_loc."""
    return frozenset(
        to_loc
        for from_loc, _, to_loc in graph.directed_edges
        if from_loc == current_loc
    )


def find_shortest_path(
    graph: LocationGraph, start: LocationId, goal: LocationId
) -> tuple[LocationId, ...] | None:
    """
    Finds shortest unweighted path between start and goal on known graph using BFS.
    Returns tuple of nodes along the path (including start and goal),
    or None if disconnected.
    """
    if start not in graph.nodes or goal not in graph.nodes:
        return None
    if start == goal:
        return (start,)

    adjacency: dict[LocationId, list[LocationId]] = {n: [] for n in graph.nodes}
    for from_loc, _, to_loc in graph.directed_edges:
        adjacency[from_loc].append(to_loc)

    queue: deque[tuple[LocationId, list[LocationId]]] = deque([(start, [start])])
    visited: set[LocationId] = {start}

    while queue:
        current, path = queue.popleft()
        if current == goal:
            return tuple(path)

        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None
