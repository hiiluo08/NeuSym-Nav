from argparse import ArgumentParser


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="ns-vln")
    parser.add_argument("--version", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    parser.parse_args()
    return 0
