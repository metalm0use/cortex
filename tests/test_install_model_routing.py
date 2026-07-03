import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass machinery can resolve the module.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


install = _load("cortex_install_skills", "scripts/install-skills.py")
sys.path.insert(0, str(ROOT / "skills" / "meta" / "scripts"))
import lint_skill  # noqa: E402


def make_skill(model_role: str, model_tier: str = "") -> "install.Skill":
    return install.Skill(
        skill_id="x/y",
        path=ROOT / "skills" / "meta" / "roles" / "SKILL.md",
        summary="Summary.",
        model_role=model_role,
        model_tier=model_tier,
        status="seed",
        aliases=("alias one", "alias two"),
        topics=("topic one",),
        install_name="y",
    )


class ResolveModelTests(unittest.TestCase):
    def test_role_maps_to_claude_model(self) -> None:
        self.assertEqual(install.resolve_model(make_skill("thinking"), "claude"), "opus")
        self.assertEqual(install.resolve_model(make_skill("execution"), "claude"), "haiku")

    def test_reference_inherits_session_model(self) -> None:
        # Domain skills must never silently downgrade; inherit means no override.
        self.assertIsNone(install.resolve_model(make_skill("reference"), "claude"))

    def test_model_tier_overrides_role(self) -> None:
        # A hard reference skill can bump itself; a light thinking skill can opt out.
        self.assertEqual(install.resolve_model(make_skill("reference", "thinking"), "claude"), "opus")
        self.assertIsNone(install.resolve_model(make_skill("thinking", "inherit"), "claude"))

    def test_non_claude_agents_inherit(self) -> None:
        self.assertIsNone(install.resolve_model(make_skill("thinking"), "codex"))
        self.assertIsNone(install.resolve_model(make_skill("thinking"), "cursor"))


class WrapperEmissionTests(unittest.TestCase):
    def _frontmatter(self, text: str) -> str:
        return text.split("---", 2)[1]

    def test_thinking_wrapper_emits_model_line(self) -> None:
        fm = self._frontmatter(install.wrapper_text(make_skill("thinking"), "claude"))
        self.assertIn("model: opus", fm)

    def test_reference_wrapper_has_no_model_line(self) -> None:
        fm = self._frontmatter(install.wrapper_text(make_skill("reference"), "claude"))
        self.assertNotIn("model:", fm)

    def test_codex_wrapper_has_no_model_line(self) -> None:
        fm = self._frontmatter(install.wrapper_text(make_skill("thinking"), "codex"))
        self.assertNotIn("model:", fm)


class ModelRoutingConfigTests(unittest.TestCase):
    def test_shipped_config_matches_builtin_default(self) -> None:
        # The committed config equals the default, so wrappers stay byte-stable.
        self.assertEqual(install.model_routing(), install.DEFAULT_MODEL_ROUTING)

    def test_partial_override_keeps_other_defaults(self) -> None:
        routing = install.build_model_routing({"claude": {"thinking": "sonnet"}})
        self.assertEqual(routing["claude"]["thinking"], "sonnet")
        self.assertEqual(routing["claude"]["execution"], "haiku")
        self.assertEqual(routing["claude"]["reference"], "inherit")

    def test_null_value_normalizes_to_inherit(self) -> None:
        routing = install.build_model_routing({"claude": {"execution": None}})
        self.assertEqual(routing["claude"]["execution"], "inherit")

    def test_invalid_model_value_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            install.build_model_routing({"claude": {"thinking": "gpt-9"}})

    def test_resolve_model_uses_injected_routing(self) -> None:
        routing = install.build_model_routing({"claude": {"thinking": "sonnet"}})
        self.assertEqual(install.resolve_model(make_skill("thinking"), "claude", routing), "sonnet")


class WorkerGenerationTests(unittest.TestCase):
    def _worker(self, **fm):
        from pathlib import Path
        base = {"name": "researcher", "description": "Cyber research worker for packet analysis."}
        base.update(fm)
        return {"path": Path("agents/researcher.md"), "frontmatter": base, "body": "Do the research."}

    def _frontmatter(self, text: str) -> str:
        return text.split("---", 2)[1]

    def test_claude_worker_emits_model_from_class(self) -> None:
        text = install.worker_agent_text(self._worker(model_tier="thinking"), "claude")
        self.assertIn("model: opus", self._frontmatter(text))

    def test_worker_with_reference_class_omits_model(self) -> None:
        text = install.worker_agent_text(self._worker(model_role="reference"), "claude")
        self.assertNotIn("model:", self._frontmatter(text))

    def test_codex_worker_omits_model(self) -> None:
        text = install.worker_agent_text(self._worker(model_tier="thinking"), "codex")
        self.assertNotIn("model:", self._frontmatter(text))

    def test_skills_mapped_to_native_names_and_body_pointer(self) -> None:
        text = install.worker_agent_text(
            self._worker(skills=["forensics/pcap"]), "claude", skill_names={"forensics/pcap": "pcap"}
        )
        self.assertIn("  - pcap", self._frontmatter(text))
        body = text.split("---", 2)[2]
        # Body pointer names the invokable handle (/pcap) plus the source id.
        self.assertIn("/pcap", body)
        self.assertIn("forensics/pcap", body)

    def test_body_pointer_falls_back_to_skill_id_without_native_name(self) -> None:
        # When no native mapping is supplied, the pointer still names the skill.
        text = install.worker_agent_text(self._worker(skills=["forensics/pcap"]), "claude")
        self.assertIn("forensics/pcap", text.split("---", 2)[2])


class WorkerWiringTests(unittest.TestCase):
    """Step 3b-3d: worker files land in the agents home, drift, and uninstall."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        skill_dir = self.project / "skills" / "security" / "review"
        (skill_dir / "agents").mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nskill_id: security/review\n---\n\nBody.\n", encoding="utf-8")
        (skill_dir / "agents" / "researcher.md").write_text(
            "---\n"
            "name: researcher\n"
            'description: "Cyber research worker for packet-capture analysis."\n'
            "model_tier: thinking\n"
            "skills:\n  - forensics/pcap\n"
            "---\n\n"
            "Do the research.\n",
            encoding="utf-8",
        )
        self.skill = install.Skill(
            skill_id="security/review",
            path=skill_dir / "SKILL.md",
            summary="Security review orchestrator.",
            model_role="thinking",
            model_tier="",
            status="seed",
            aliases=("security-review",),
            topics=("security",),
            install_name="security-review",
        )
        self.home = install.agents_home("claude", "project", self.project)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_worker_filename_is_namespaced(self) -> None:
        workers = install.generated_workers(self.skill, "claude", {})
        self.assertEqual(workers[0][0], "security-review__researcher.md")

    def test_agents_home_only_for_claude(self) -> None:
        self.assertIsNone(install.agents_home("codex", "project", self.project))
        self.assertEqual(self.home, self.project / ".cortex" / "claude" / "agents")

    def test_sync_writes_worker_file(self) -> None:
        manifest = install.sync_worker_agents(
            self.skill, "claude", "project", self.project, {"forensics/pcap": "pcap"}, None, False
        )
        target = Path(manifest[0]["path"])
        self.assertTrue(target.is_file())
        text = target.read_text(encoding="utf-8")
        self.assertIn("model: opus", text)
        self.assertIn("  - pcap", text)

    def test_sync_prunes_removed_worker(self) -> None:
        prior = [{"name": "ghost", "path": str(self.home / "security-review__ghost.md"), "sha256": "x"}]
        (self.home).mkdir(parents=True)
        (self.home / "security-review__ghost.md").write_text("stale", encoding="utf-8")
        install.sync_worker_agents(self.skill, "claude", "project", self.project, {}, prior, False)
        self.assertFalse((self.home / "security-review__ghost.md").exists())

    def test_sync_skips_foreign_file(self) -> None:
        self.home.mkdir(parents=True)
        foreign = self.home / "security-review__researcher.md"
        foreign.write_text("user-owned", encoding="utf-8")
        install.sync_worker_agents(self.skill, "claude", "project", self.project, {}, None, False)
        self.assertEqual(foreign.read_text(encoding="utf-8"), "user-owned")

    def test_workers_current_detects_edits(self) -> None:
        manifest = install.sync_worker_agents(self.skill, "claude", "project", self.project, {}, None, False)
        data = {"worker_agents": manifest}
        self.assertTrue(install.workers_current(self.skill, "claude", "project", self.project, {}, data))
        Path(manifest[0]["path"]).write_text("tampered", encoding="utf-8")
        self.assertFalse(install.workers_current(self.skill, "claude", "project", self.project, {}, data))

    def test_workers_current_detects_missing(self) -> None:
        manifest = install.sync_worker_agents(self.skill, "claude", "project", self.project, {}, None, False)
        data = {"worker_agents": manifest}
        Path(manifest[0]["path"]).unlink()
        self.assertFalse(install.workers_current(self.skill, "claude", "project", self.project, {}, data))

    def test_remove_worker_agents_deletes_files(self) -> None:
        manifest = install.sync_worker_agents(self.skill, "claude", "project", self.project, {}, None, False)
        install.remove_worker_agents("claude", self.skill, {"worker_agents": manifest}, False)
        self.assertFalse(Path(manifest[0]["path"]).exists())


class ReferenceDeepSkillTests(unittest.TestCase):
    """The security/review reference skill is the live worker-emission fixture."""

    def setUp(self) -> None:
        skills = install.load_skills()
        self.by_id = {skill.skill_id: skill for skill in skills}
        self.skill_names = {skill.skill_id: skill.install_name for skill in skills}
        self.skill = self.by_id.get("security/review")

    def test_reference_skill_exists(self) -> None:
        self.assertIsNotNone(self.skill, "security/review reference skill is missing")

    def test_workers_route_to_distinct_models(self) -> None:
        workers = {name: text for _, text, name in
                   install.generated_workers(self.skill, "claude", self.skill_names)}
        self.assertIn("model: opus", workers["researcher"].split("---", 2)[1])
        self.assertIn("model: haiku", workers["reporter"].split("---", 2)[1])

    def test_workers_reference_real_skills_by_native_name(self) -> None:
        workers = {name: text for _, text, name in
                   install.generated_workers(self.skill, "claude", self.skill_names)}
        self.assertIn("/pcap (forensics/pcap)", workers["researcher"])
        self.assertIn("/ja4 (forensics/ja4)", workers["researcher"])
        self.assertIn("/article-writing (writing/article-writing)", workers["reporter"])


class PromptOptimizerDeepSkillTests(unittest.TestCase):
    """The prompting/optimize deep skill: critic/evaluator opus, rewriter haiku."""

    def setUp(self) -> None:
        skills = install.load_skills()
        self.by_id = {skill.skill_id: skill for skill in skills}
        self.skill_names = {skill.skill_id: skill.install_name for skill in skills}
        self.skill = self.by_id.get("prompting/optimize")

    def _workers(self) -> dict:
        return {name: text for _, text, name in
                install.generated_workers(self.skill, "claude", self.skill_names)}

    def test_reference_skill_exists(self) -> None:
        self.assertIsNotNone(self.skill, "prompting/optimize deep skill is missing")

    def test_critic_and_evaluator_route_to_opus(self) -> None:
        workers = self._workers()
        self.assertIn("model: opus", workers["critic"].split("---", 2)[1])
        self.assertIn("model: opus", workers["evaluator"].split("---", 2)[1])

    def test_rewriter_routes_to_haiku(self) -> None:
        self.assertIn("model: haiku", self._workers()["rewriter"].split("---", 2)[1])

    def test_workers_reference_patterns_by_native_name(self) -> None:
        workers = self._workers()
        self.assertIn("/prompt-engineering (prompting/patterns)", workers["critic"])
        self.assertIn("/article-writing (writing/article-writing)", workers["rewriter"])


class LintModelTierTests(unittest.TestCase):
    def test_valid_tier_is_accepted(self) -> None:
        self.assertIn("inherit", lint_skill.VALID_MODEL_TIERS)
        self.assertIn("thinking", lint_skill.VALID_MODEL_TIERS)

    def test_invalid_tier_is_rejected_when_present(self) -> None:
        self.assertNotIn("bogus", lint_skill.VALID_MODEL_TIERS)


if __name__ == "__main__":
    unittest.main()
