from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StagingDeliveryFilesTests(unittest.TestCase):
    def test_staging_delivery_files_exist(self) -> None:
        expected_files = [
            ROOT / "apps" / "api" / "Dockerfile",
            ROOT / "apps" / "worker" / "Dockerfile",
            ROOT / "apps" / "web" / "Dockerfile",
            ROOT / "apps" / "web" / "nginx.conf",
            ROOT / "deploy" / "staging" / "docker-compose.yml",
            ROOT / "deploy" / "staging" / ".env.example",
            ROOT / "docs" / "STAGING_RUN.md",
            ROOT / "docs" / "BACKUP_RESTORE.md",
        ]
        for file_path in expected_files:
            self.assertTrue(file_path.exists(), f"Missing expected staging file: {file_path}")

    def test_requirements_and_compose_cover_postgres_and_redis_runtime(self) -> None:
        requirements = (ROOT / "apps" / "api" / "requirements.txt").read_text(encoding="utf-8")
        compose = (ROOT / "deploy" / "staging" / "docker-compose.yml").read_text(encoding="utf-8")
        env_example = (ROOT / "deploy" / "staging" / ".env.example").read_text(encoding="utf-8")
        self.assertIn("psycopg[binary]", requirements)
        self.assertIn("postgres:", compose)
        self.assertIn("redis:", compose)
        self.assertIn("/health/ready", compose)
        self.assertIn("TRUST_LEDGER_DATABASE_URL=postgresql+psycopg://", env_example)
        self.assertIn("TRUST_LEDGER_REDIS_URL=redis://redis:6379/0", env_example)
        self.assertIn("VITE_TRUST_LEDGER_API_BASE_URL=", env_example)

    def test_docs_cover_staging_run_and_backup_restore(self) -> None:
        staging_run = (ROOT / "docs" / "STAGING_RUN.md").read_text(encoding="utf-8")
        backup_restore = (ROOT / "docs" / "BACKUP_RESTORE.md").read_text(encoding="utf-8")
        self.assertIn("docker compose up --build -d", staging_run)
        self.assertIn("/health/ready", staging_run)
        self.assertIn("pg_dump", backup_restore)
        self.assertIn("pg_restore", backup_restore)
        self.assertIn("restore verification checklist", backup_restore.lower())


if __name__ == "__main__":
    unittest.main()
