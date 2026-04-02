import unittest

from evaluation.pilot_runner import PilotCase, compute_metrics, predict_decision


class TestPilotRunner(unittest.TestCase):
    def test_predict_decision(self):
        self.assertEqual(predict_decision(1, 0), "REJECT")
        self.assertEqual(predict_decision(0, 2), "REVIEW")
        self.assertEqual(predict_decision(0, 0), "PASS")

    def test_compute_metrics(self):
        cases = [
            PilotCase("A", blockers=1, warnings=0, expert_decision="REJECT"),
            PilotCase("B", blockers=0, warnings=1, expert_decision="REVIEW"),
            PilotCase("C", blockers=0, warnings=0, expert_decision="PASS"),
            PilotCase("D", blockers=0, warnings=1, expert_decision="PASS"),
        ]
        metrics = compute_metrics(cases)

        self.assertEqual(metrics["num_cases"], 4)
        self.assertAlmostEqual(metrics["accuracy"], 0.75, places=3)
        self.assertIn("macro_f1", metrics)
        self.assertEqual(metrics["confusion_matrix"]["PASS"]["REVIEW"], 1)


if __name__ == "__main__":
    unittest.main()
