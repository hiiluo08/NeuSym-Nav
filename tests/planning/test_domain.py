from pathlib import Path

from pyperplan.pddl.parser import Parser


def get_domain_path() -> Path:
    domain_path = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "neuro_symbolic_vln"
        / "planning"
        / "domain.pddl"
    )
    assert domain_path.exists(), f"Domain file not found at {domain_path}"
    return domain_path


def test_domain_parses_with_strips_and_typing() -> None:
    domain_path = get_domain_path()
    parser = Parser(str(domain_path))
    domain = parser.parse_domain()

    assert domain.name == "vln-minigrid"

    # Domain text inspection for requirements
    with open(domain_path, encoding="utf-8") as f:
        content = f.read()

    assert "(:requirements :strips :typing)" in content
    assert ":equality" not in content
    assert ":negative-preconditions" not in content
    assert ":disjunctive-preconditions" not in content


def test_domain_declares_all_required_predicates() -> None:
    domain_path = get_domain_path()
    parser = Parser(str(domain_path))
    domain = parser.parse_domain()

    predicate_names = set(domain.predicates.keys())
    required_predicates = {
        "robot-at",
        "facing",
        "turn-right-of",
        "turn-left-of",
        "front-cell",
        "passable",
        "key-at",
        "door-at",
        "handempty",
        "holding",
        "door-locked",
        "door-open",
        "key-opens",
        "target-at",
        "task-satisfied",
    }

    assert required_predicates.issubset(predicate_names)


def test_domain_declares_all_required_actions() -> None:
    domain_path = get_domain_path()
    parser = Parser(str(domain_path))
    domain = parser.parse_domain()

    action_names = set(domain.actions.keys())
    required_actions = {
        "turn-left",
        "turn-right",
        "move-forward",
        "pickup-key",
        "toggle-locked-door",
        "confirm-goto",
    }

    assert required_actions.issubset(action_names)
