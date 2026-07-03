import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "prompting" / "patterns" / "scripts" / "intent_router.py"


def _load():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("intent_router", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["intent_router"] = module
    spec.loader.exec_module(module)
    return module


intent_router = _load()


class DetectIntentTests(unittest.TestCase):
    def test_create_intent(self) -> None:
        self.assertEqual(intent_router.detect_intent("Write a prompt that generates release notes.")["intent"], "create")

    def test_transform_intent(self) -> None:
        self.assertEqual(intent_router.detect_intent("Rewrite and improve this prompt.")["intent"], "transform")

    def test_reason_intent(self) -> None:
        self.assertEqual(intent_router.detect_intent("Solve this step by step and derive the answer.")["intent"], "reason")

    def test_critique_intent(self) -> None:
        self.assertEqual(intent_router.detect_intent("Red-team this prompt and find flaws.")["intent"], "critique")

    def test_recover_intent(self) -> None:
        self.assertEqual(intent_router.detect_intent("Reconstruct the prompt from this output.")["intent"], "recover")

    def test_empty_defaults_to_create_low_confidence(self) -> None:
        result = intent_router.detect_intent("")
        self.assertEqual(result["intent"], "create")
        self.assertEqual(result["confidence"], "low")

    def test_frameworks_returned_for_intent(self) -> None:
        result = intent_router.detect_intent("Rewrite and improve and revise this.")
        self.assertTrue(result["frameworks"])
        self.assertIn("Self-Refine", result["frameworks"][0])


if __name__ == "__main__":
    unittest.main()
