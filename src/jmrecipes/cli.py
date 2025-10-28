# src/jmrecipes/cli.py
import argparse
from jmrecipes.build import build


def main():
    parser = argparse.ArgumentParser(
        prog="jmrecipes", description="A simple static recipe site generator demo"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'build' command
    build_parser = subparsers.add_parser("build", help="Build the recipe site")
    build_parser.add_argument(
        "--output", default="builds/latest", help="Directory to place built site"
    )

    args = parser.parse_args()

    if args.command == "build":
        build()
