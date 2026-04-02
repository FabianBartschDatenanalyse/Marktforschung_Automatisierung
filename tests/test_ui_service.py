import tempfile
import unittest
from pathlib import Path

from ui.service import build_gate_decision, execute_override, get_audit_events, run_pilot


class TestUIService(unittest.TestCase):
    def test_build_gate_decision(self):
        gate = build_gate_decision(blockers=0, warnings=2)
        self.assertEqual(gate["decision"], "REVIEW")
        self.assertEqual(gate["counts"]["warnings"], 2)

    def test_execute_override(self):
        gate = build_gate_decision(blockers=0, warnings=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            audit = Path(tmpdir) / "audit.jsonl"
            out = execute_override(
                gate_report=gate,
                user="lead_anna",
                role="lead",
                reason="Methodisch akzeptabel und freigegeben.",
                audit_path=audit,
            )
            self.assertEqual(out["decision"], "PASS")
            self.assertEqual(len(get_audit_events(audit)), 1)

    def test_run_pilot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "results.json"
            md_out = Path(tmpdir) / "results.md"
            metrics = run_pilot(Path("evaluation/pilot_dataset.jsonl"), json_out, md_out)
            self.assertIn("accuracy", metrics)
            self.assertTrue(json_out.exists())
            self.assertTrue(md_out.exists())


if __name__ == "__main__":
    unittest.main()
