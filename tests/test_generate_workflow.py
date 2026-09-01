from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "generate-daily.yml"
PAGES = ROOT / ".github" / "workflows" / "deploy-pages.yml"


class GenerateWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.pages = PAGES.read_text(encoding="utf-8")

    def test_manual_dispatch_and_singapore_cron_are_present(self) -> None:
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn('cron: "0 0 * * *"', self.workflow)
        self.assertIn("TZ=Asia/Singapore date +%F", self.workflow)

    def test_cron_is_gated_until_real_manual_acceptance(self) -> None:
        self.assertIn("vars.MARKET_DAILY_CRON_ENABLED == 'true'", self.workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", self.workflow)

    def test_concurrency_serializes_generation(self) -> None:
        self.assertIn("group: market-daily-generation", self.workflow)
        self.assertIn("cancel-in-progress: false", self.workflow)

    def test_secret_is_only_referenced_as_github_secret(self) -> None:
        self.assertIn("OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}", self.workflow)
        self.assertNotIn("set -x", self.workflow)
        self.assertNotRegex(self.workflow, r"sk-[A-Za-z0-9]")

    def test_existing_archive_skips_second_generation(self) -> None:
        existing = self.workflow.index("Check for an existing formal report")
        generate = self.workflow.index("Generate one researched Markdown draft")
        self.assertLess(existing, generate)
        self.assertIn("steps.existing.outputs.present == 'false'", self.workflow)
        self.assertIn("idempotently skipped", self.workflow)

    def test_generation_and_publication_stages_are_ordered(self) -> None:
        labels = [
            "Generate one researched Markdown draft",
            "Validate generated draft",
            "Import validated draft deterministically",
            "Build MkDocs strictly",
            "Commit deterministic archive changes",
            "Push and verify remote SHA",
            "Dispatch and wait for Pages deployment",
            "Verify final daily page",
        ]
        positions = [self.workflow.index(label) for label in labels]
        self.assertEqual(positions, sorted(positions))
        for layer in ("Generate", "Validate", "Import", "Build", "Commit", "Push", "Deploy", "Verify"):
            self.assertIn(f"CURRENT_LAYER={layer}", self.workflow)

    def test_generate_workflow_cannot_recursively_trigger_on_push(self) -> None:
        on_block = self.workflow.split("permissions:", 1)[0]
        self.assertNotRegex(on_block, r"(?m)^\s+push:")
        self.assertRegex(self.pages, r"(?m)^\s+push:")
        self.assertIn("branches:\n      - main", self.pages)

    def test_pages_is_explicitly_dispatched_for_github_token_push(self) -> None:
        self.assertIn("actions: write", self.workflow)
        self.assertIn("gh workflow run deploy-pages.yml --ref main", self.workflow)
        self.assertIn("gh run watch", self.workflow)

    def test_strict_build_and_final_content_verification_are_required(self) -> None:
        self.assertIn("mkdocs build --strict", self.workflow)
        self.assertIn("scripts/verify_daily_page.py", self.workflow)
        self.assertIn("if: failure()", self.workflow)
        self.assertIn("Blocked layer: $CURRENT_LAYER", self.workflow)


if __name__ == "__main__":
    unittest.main()
