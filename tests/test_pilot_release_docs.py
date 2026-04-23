from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PilotReleaseDocsTests(unittest.TestCase):
    def test_pilot_runbooks_exist(self) -> None:
        expected_files = [
            ROOT / "docs" / "UAT.md",
            ROOT / "docs" / "SECURITY_REVIEW.md",
            ROOT / "docs" / "RELEASE_CANDIDATE.md",
        ]
        for file_path in expected_files:
            self.assertTrue(file_path.exists(), f"Missing expected pilot doc: {file_path}")

    def test_pilot_runbooks_cover_release_readiness_and_signoff(self) -> None:
        uat = (ROOT / "docs" / "UAT.md").read_text(encoding="utf-8")
        security_review = (ROOT / "docs" / "SECURITY_REVIEW.md").read_text(encoding="utf-8")
        release_candidate = (ROOT / "docs" / "RELEASE_CANDIDATE.md").read_text(encoding="utf-8")

        self.assertIn("release-readiness", uat.lower())
        self.assertIn("secure", security_review.lower())
        self.assertIn("/api/v1/internal/release-readiness", security_review)
        self.assertIn("go / no-go", release_candidate.lower())
        self.assertIn("rollback", release_candidate.lower())


if __name__ == "__main__":
    unittest.main()
