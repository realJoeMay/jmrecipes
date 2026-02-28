"""Command-line interface for the jmrecipes application."""

import argparse
from jmrecipes.build import build


def main():
    """Entry point for the jmrecipes command-line interface."""

    parser = argparse.ArgumentParser(
        prog="jmrecipes", description="A static recipe website generator."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'build' command
    build_parser = subparsers.add_parser("build", help="Build the recipe site")
    build_parser.add_argument(
        "--data", type=str, help="Directory with recipe input data"
    )

    args = parser.parse_args()
    if args.command == "build":
        build(data=args.data)
