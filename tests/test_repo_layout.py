from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepoLayoutTest(unittest.TestCase):
    def test_legacy_archive_exists(self) -> None:
        archive_root = ROOT / "archive" / "mesitis-mvp-2026-04-09"
        self.assertTrue(archive_root.is_dir())
        self.assertTrue((archive_root / "backend").is_dir())
        self.assertTrue((archive_root / "frontend").is_dir())

    def test_rebuild_folders_exist(self) -> None:
        required_dirs = [
            ROOT / "apps" / "api",
            ROOT / "apps" / "web",
            ROOT / "apps" / "worker",
            ROOT / "packages" / "domain",
            ROOT / "packages" / "scoring",
            ROOT / "packages" / "ui",
            ROOT / "packages" / "config",
            ROOT / "docs",
            ROOT / "tests",
        ]
        for path in required_dirs:
            with self.subTest(path=path):
                self.assertTrue(path.is_dir())

    def test_source_of_truth_docs_exist(self) -> None:
        required_docs = [
            ROOT / "README.md",
            ROOT / "AGENTS.md",
            ROOT / "docs" / "ARCHITECTURE.md",
            ROOT / "docs" / "ROADMAP.md",
            ROOT / "docs" / "SPRINTS.md",
            ROOT / "docs" / "DECISIONS.md",
            ROOT / "docs" / "HANDOFF.md",
            ROOT / "docs" / "WORKFLOW_GAPS.md",
            ROOT / "docs" / "WORKFLOW_QA_PLAN.md",
            ROOT / "docs" / "MANUAL_QA_RUNBOOK.md",
            ROOT / "docs" / "MANUAL_QA_CHECKLIST.md",
            ROOT / "docs" / "MANUAL_QA_RESULTS.md",
            ROOT / "docs" / "WORKSTATION_SYNC.md",
            ROOT / "docs" / "GITHUB_BOOTSTRAP.md",
            ROOT / "docs" / "CODEBASE_REFERENCE.md",
            ROOT / "docs" / "WORKFLOW_MAP.md",
            ROOT / "docs" / "WORKFLOW_DIAGRAMS.md",
            ROOT / "docs" / "WORKSPACE_GUIDE.md",
        ]
        for path in required_docs:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())

    def test_api_and_worker_scaffolds_exist(self) -> None:
        self.assertTrue((ROOT / "apps" / "api" / "app" / "main.py").is_file())
        self.assertTrue((ROOT / "apps" / "worker" / "worker" / "main.py").is_file())
        self.assertTrue((ROOT / "run_api.py").is_file())
        self.assertTrue((ROOT / "run_web.py").is_file())
        self.assertTrue((ROOT / "bootstrap_workstation.ps1").is_file())


if __name__ == "__main__":
    unittest.main()
