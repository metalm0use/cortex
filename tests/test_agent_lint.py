import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "meta" / "scripts"))
import lint_skill  # noqa: E402


PROVENANCE = "<!-- learned: 2026-06 | project: test | model: thinking-model -->"


def build_vault(tmp: Path, worker_frontmatter: str, *, beside_skill: bool = True) -> Path:
    """Create a minimal vault and return the path to the worker file."""
    orch = tmp / "skills" / "test" / "orch"
    (orch / "agents").mkdir(parents=True)
    if beside_skill:
        (orch / "SKILL.md").write_text("---\nskill_id: test/orch\n---\n# Orch\n", encoding="utf-8")
    # A referenced skill that resolves by path (no index needed).
    pcap = tmp / "skills" / "forensics" / "pcap"
    pcap.mkdir(parents=True)
    (pcap / "SKILL.md").write_text("---\nskill_id: forensics/pcap\n---\n# Pcap\n", encoding="utf-8")
    worker = orch / "agents" / "researcher.md"
    worker.write_text(f"---\n{worker_frontmatter}\n---\n\n{PROVENANCE}\n\nDo the work.\n", encoding="utf-8")
    return worker


class LintAgentTests(unittest.TestCase):
    def lint(self, frontmatter: str, **kwargs) -> list[str]:
        with tempfile.TemporaryDirectory() as d:
            worker = build_vault(Path(d), frontmatter, **kwargs)
            return lint_skill.lint_agent(worker)

    def test_valid_worker_passes(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."\nmodel_tier: thinking\nskills:\n  - "forensics/pcap"'
        self.assertEqual(self.lint(fm), [])

    def test_missing_description_fails(self) -> None:
        errors = self.lint("name: researcher")
        self.assertTrue(any("missing agent frontmatter keys" in e for e in errors))

    def test_unknown_key_fails(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."\nbogus: 1'
        errors = self.lint(fm)
        self.assertTrue(any("unknown agent frontmatter keys" in e for e in errors))

    def test_name_must_match_stem(self) -> None:
        fm = 'name: wrongname\ndescription: "Cyber research worker for packet analysis."'
        self.assertTrue(any("name must match file stem" in e for e in self.lint(fm)))

    def test_bad_model_tier_fails(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."\nmodel_tier: turbo'
        self.assertTrue(any("model_tier must be one of" in e for e in self.lint(fm)))

    def test_unresolved_skill_reference_fails(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."\nskills:\n  - "does/not-exist"'
        self.assertTrue(any("referenced skill does not resolve" in e for e in self.lint(fm)))

    def test_worker_without_orchestrator_skill_fails(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."'
        self.assertTrue(any("must sit beside an orchestrator SKILL.md" in e for e in self.lint(fm, beside_skill=False)))

    def test_review_metadata_accepted(self) -> None:
        fm = (
            'name: researcher\ndescription: "Cyber research worker for packet analysis."\n'
            "review_status: reviewed\nconfidence: high\nreviewed_at: 2026-06-19\n"
            'reviewed_by:\n  - "security lead"\nexpertise_domain:\n  - "network forensics"'
        )
        self.assertEqual(self.lint(fm), [])

    def test_bad_review_status_fails(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."\nreview_status: amazing'
        self.assertTrue(any("review_status must be one of" in e for e in self.lint(fm)))

    def test_bad_confidence_fails(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."\nconfidence: certain'
        self.assertTrue(any("confidence must be one of" in e for e in self.lint(fm)))

    def test_bad_reviewed_at_fails(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."\nreviewed_at: "06-2026"'
        self.assertTrue(any("reviewed_at must use YYYY-MM-DD" in e for e in self.lint(fm)))

    def test_reviewed_by_must_be_list(self) -> None:
        fm = 'name: researcher\ndescription: "Cyber research worker for packet analysis."\nreviewed_by: "solo string"'
        self.assertTrue(any("reviewed_by' must be a list" in e for e in self.lint(fm)))


if __name__ == "__main__":
    unittest.main()
