#!/usr/bin/env python3
"""Role router for the Shorts Suite plugin."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROLE_SCRIPTS = {
    "guided": "guided.py",
    "configure-typecast": "configure_typecast.py",
    "discover": "discover.py",
    "package": "research_package.py",
    "animal": "animal.py",
    "healing": "healing.py",
    "romance": "romance.py",
    "globalize": "globalize.py",
    "whiteboard": "whiteboard.py",
    "senior": "senior.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Route a Shorts task to the guided five-stage workflow or a legacy-compatible role."
    )
    parser.add_argument("role", choices=tuple(ROLE_SCRIPTS))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    script = Path(__file__).resolve().parent / ROLE_SCRIPTS[args.role]
    result = subprocess.run([sys.executable, str(script), *args.arguments], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
