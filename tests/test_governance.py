import tempfile
import unittest
from pathlib import Path

from governance.audit_log import append_audit_event, read_audit_events
from governance.override import apply_override


class TestGovernance(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "roles": {
                "editor": {"can_override": False},
                "lead": {"can_override": True},
            },
            "override": {
                "reason_min_chars": 12,
                "allowed_from_decisions": ["REVIEW", "REJECT"],
            },
        }

    def test_lead_can_override_with_reason(self):
        gate_report = {"decision": "REVIEW", "reason": "1 WARNING", "score": 87, "counts": {}}
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.jsonl"
            result = apply_override(
                gate_report,
                user_id="lead_anna",
                role="lead",
                reason="Methodisch akzeptabel nach Teamreview.",
                policy=self.policy,
                audit_path=audit_path,
            )
            self.assertEqual(result["decision"], "PASS")
            self.assertEqual(result["override"]["original_decision"], "REVIEW")
            self.assertEqual(len(read_audit_events(audit_path)), 1)

    def test_editor_cannot_override(self):
        gate_report = {"decision": "REVIEW", "reason": "1 WARNING", "score": 87, "counts": {}}
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(PermissionError):
                apply_override(
                    gate_report,
                    user_id="editor_max",
                    role="editor",
                    reason="Bitte freigeben trotz Warnung.",
                    policy=self.policy,
                    audit_path=Path(tmpdir) / "audit.jsonl",
                )

    def test_audit_log_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "audit.jsonl"
            append_audit_event({"event_type": "gate_override", "user": "u1"}, path=path)
            events = read_audit_events(path=path)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["user"], "u1")


if __name__ == "__main__":
    unittest.main()
