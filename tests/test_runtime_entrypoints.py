from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RuntimeEntrypointTests(unittest.TestCase):
    def test_root_api_launcher_bootstraps_app_dir_and_reload_dirs(self) -> None:
        source = (ROOT / "run_api.py").read_text(encoding="utf-8")
        self.assertIn('app.main:app', source)
        self.assertIn('app_dir=str(API_ROOT)', source)
        self.assertIn('reload_dirs=[str(API_ROOT), str(DOMAIN_ROOT)]', source)
        self.assertIn('parser.set_defaults(reload=True)', source)

    def test_local_run_doc_points_to_root_api_launcher(self) -> None:
        local_run = (ROOT / "docs" / "LOCAL_RUN.md").read_text(encoding="utf-8")
        self.assertIn('.\\.venv\\Scripts\\python run_api.py', local_run)
        self.assertIn('avoids import-path issues', local_run)

    def test_root_web_launcher_runs_vite_from_web_root(self) -> None:
        source = (ROOT / "run_web.py").read_text(encoding="utf-8")
        self.assertIn('cwd=WEB_ROOT', source)
        self.assertIn('"run",', source)
        self.assertIn('"dev",', source)
        self.assertIn('resolve_npm_command()', source)
        self.assertIn('"--host"', source)
        self.assertIn('"--port"', source)

    def test_local_run_doc_points_to_root_web_launcher(self) -> None:
        local_run = (ROOT / "docs" / "LOCAL_RUN.md").read_text(encoding="utf-8")
        self.assertIn('.\\.venv\\Scripts\\python run_web.py', local_run)
        self.assertIn('avoids needing to change into `apps\\web` first', local_run)


if __name__ == "__main__":
    unittest.main()
