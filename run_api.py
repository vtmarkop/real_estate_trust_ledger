from __future__ import annotations

from pathlib import Path
import argparse
import sys

import uvicorn


ROOT = Path(__file__).resolve().parent
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"

for path in (API_ROOT, DOMAIN_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start the Trust Ledger API from the repo root."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", dest="reload", action="store_true")
    parser.add_argument("--no-reload", dest="reload", action="store_false")
    parser.set_defaults(reload=True)
    parser.add_argument("--log-level", default="info")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    uvicorn.run(
        "app.main:app",
        app_dir=str(API_ROOT),
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=[str(API_ROOT), str(DOMAIN_ROOT)],
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
