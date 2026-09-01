from neuro_symbolic_vln import __version__
from neuro_symbolic_vln.cli import build_parser

def test_package_version_and_cli_parser() -> None:
    assert __version__ == "0.1.0"
    parser = build_parser()
    assert parser.prog == "ns-vln"