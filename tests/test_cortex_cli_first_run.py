import sys
import unittest
from subprocess import CompletedProcess
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cortex_cli import main


class FirstRunSelectionTests(unittest.TestCase):
    def test_meta_skills_are_hidden_from_guided_options(self) -> None:
        records = [
            {"skill_id": "meta/index", "domain": "meta", "summary": "Generated map."},
            {"skill_id": "sql/injection", "domain": "sql", "summary": "Use parameters."},
            {"skill_id": "writing/humanizer", "domain": "writing", "summary": "Clean prose."},
        ]

        domains, skill_options, selectable_records = main.guided_selectable_skills(records)

        self.assertEqual(domains, ["sql", "writing"])
        self.assertEqual(
            skill_options,
            [
                "sql/injection - Use parameters.",
                "writing/humanizer - Clean prose.",
            ],
        )
        self.assertEqual(
            [record["skill_id"] for record in selectable_records],
            ["sql/injection", "writing/humanizer"],
        )

    def test_individual_only_selection_omits_categories(self) -> None:
        values = main.guided_selection_values(
            categories=[],
            selected_skill_ids=["sql/injection"],
            agents=["codex"],
            scope="global",
            mode="wrapper",
            project="",
        )

        self.assertNotIn("categories", values)
        self.assertEqual(values["skills"], "sql/injection")
        self.assertEqual(values["agents"], "codex")

    def test_status_args_can_hide_missing(self) -> None:
        args = main.installer_args(
            "status",
            None,
            "all",
            "codex",
            "global",
            None,
            None,
            False,
            True,
            hide_missing=True,
        )

        self.assertIn("--hide-missing", args)

    def test_agent_flags_build_status_filter(self) -> None:
        self.assertEqual(main.apply_agent_flags(None, codex=True), "codex")
        self.assertEqual(main.apply_agent_flags("claude", codex=True), "claude,codex")
        self.assertEqual(main.apply_agent_flags("codex", codex=True), "codex")

    def test_multi_select_rows_use_stable_ascii_markers(self) -> None:
        self.assertEqual(main.format_multi_select_row("all", active=True, selected=True), "> * all")
        self.assertEqual(main.format_multi_select_row("sql", active=False, selected=False), "    sql")
        self.assertEqual(main.format_multi_select_row("codex", active=False, selected=True), "  * codex")

    @patch("cortex_cli.main.subprocess.run")
    # Confirm order: save local profile?, save shared profile?, run now?, apply same selection?
    @patch("cortex_cli.main.Confirm.ask", side_effect=[False, False, True, True])
    @patch("cortex_cli.main.Prompt.ask", return_value="")
    @patch("cortex_cli.main.guided_values")
    def test_first_run_dry_run_can_apply_same_selection(
        self,
        guided_values,
        _prompt,
        _confirm,
        run,
    ) -> None:
        guided_values.return_value = {
            "categories": "all",
            "agents": "codex",
            "scope": "global",
            "mode": "wrapper",
        }
        run.return_value = CompletedProcess(args=[], returncode=0)

        main.first_run(action="install", save_profile=None, save_profile_file=None, dry_run=True, yes=False)

        self.assertEqual(run.call_count, 2)
        first_args = run.call_args_list[0].args[0]
        second_args = run.call_args_list[1].args[0]
        self.assertIn("--dry-run", first_args)
        self.assertNotIn("--dry-run", second_args)

    @patch("cortex_cli.main.subprocess.run")
    @patch("cortex_cli.main.write_profile")
    # Save local profile? yes. Save shared profile? no. Run now? yes. Apply same selection? no.
    @patch("cortex_cli.main.Confirm.ask", side_effect=[True, False, True, False])
    # Empty profile-name entry must fall back to the shown default, not save a blank/"y" name.
    @patch("cortex_cli.main.Prompt.ask", return_value="")
    @patch("cortex_cli.main.guided_values")
    def test_first_run_blank_profile_name_uses_default(
        self,
        guided_values,
        _prompt,
        _confirm,
        write_profile,
        run,
    ) -> None:
        guided_values.return_value = {
            "categories": "all",
            "agents": "codex",
            "scope": "global",
            "mode": "wrapper",
        }
        run.return_value = CompletedProcess(args=[], returncode=0)

        main.first_run(action="install", save_profile=None, save_profile_file=None, dry_run=True, yes=False)

        write_profile.assert_called_once()
        self.assertEqual(write_profile.call_args.args[0], main.DEFAULT_PROFILE_NAME)


if __name__ == "__main__":
    unittest.main()
