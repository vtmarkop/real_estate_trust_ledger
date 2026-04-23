from __future__ import annotations

from pathlib import Path
import argparse
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "apps" / "web"


def resolve_npm_command() -> str:
    if os.name == "nt":
        return "npm.cmd"

    return "npm"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start the Trust Ledger web app from the repo root."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5173)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    command = [
        resolve_npm_command(),
        "run",
        "dev",
        "--",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    completed = subprocess.run(command, cwd=WEB_ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
