import pytest

from neuro_symbolic_vln.contracts import LocationGraph
from neuro_symbolic_vln.planning.location_graph import (
    LocationGraphBuilder,
    find_shortest_path,
    get_forward_node,
    get_neighbors,
    graph_to_front_cell_atoms,
    validate_location_graph,
)


def test_builder_and_validation() -> None:
    builder = LocationGraphBuilder()
    builder.add_edge("loc-1", "east", "loc-2")
    builder.mark_frontier("loc-2")
    graph = builder.build()

    assert "loc-1" in graph.nodes
    assert "loc-2" in graph.nodes
    assert ("loc-1", "east", "loc-2") in graph.directed_edges
    assert "loc-2" in graph.frontier_nodes


def test_invalid_edge_raises_error() -> None:
    invalid_graph = LocationGraph(
        nodes=frozenset({"loc-1"}),
        directed_edges=frozenset({("loc-1", "north", "loc-dangling")}),
        frontier_nodes=frozenset(),
    )
    with pytest.raises(
        ValueError, match="Edge target 'loc-dangling' not in graph nodes"
    ):
        validate_location_graph(invalid_graph)


def test_graph_to_atoms_and_navigation() -> None:
    builder = LocationGraphBuilder()
    builder.add_edge("loc-1", "east", "loc-2")
    builder.add_edge("loc-2", "south", "loc-3")
    graph = builder.build()

    atoms = graph_to_front_cell_atoms(graph)
    assert any(
        a.predicate == "front-cell"
        and a.arguments == ("loc-1", "east", "loc-2")
        for a in atoms
    )

    assert get_forward_node(graph, "loc-1", "east") == "loc-2"
    assert get_forward_node(graph, "loc-1", "north") is None
    assert get_neighbors(graph, "loc-1") == frozenset({"loc-2"})

    path = find_shortest_path(graph, "loc-1", "loc-3")
    assert path == ("loc-1", "loc-2", "loc-3")

    disconnected_path = find_shortest_path(graph, "loc-3", "loc-1")
    assert disconnected_path is None
