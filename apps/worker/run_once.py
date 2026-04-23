from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
WORKER_ROOT = ROOT / "apps" / "worker"

for path in (API_ROOT, WORKER_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from worker.main import main  # noqa: E402


if __name__ == "__main__":
    main(["--mode", "once"])
