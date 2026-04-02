#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

Decision = str


@dataclass(frozen=True)
class PilotCase:
    questionnaire_id: str
    blockers: int
    warnings: int
    expert_decision: Decision


def predict_decision(blockers: int, warnings: int) -> Decision:
    if blockers > 0:
        return "REJECT"
    if warnings > 0:
        return "REVIEW"
    return "PASS"


def read_dataset(path: Path) -> list[PilotCase]:
    cases: list[PilotCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        cases.append(
            PilotCase(
                questionnaire_id=raw["questionnaire_id"],
                blockers=int(raw.get("blockers", 0)),
                warnings=int(raw.get("warnings", 0)),
                expert_decision=raw["expert_decision"],
            )
        )
    return cases


def _safe_div(num: int, den: int) -> float:
    return num / den if den else 0.0


def compute_metrics(cases: list[PilotCase]) -> dict[str, Any]:
    labels = ["PASS", "REVIEW", "REJECT"]
    confusion = {truth: {pred: 0 for pred in labels} for truth in labels}

    for case in cases:
        pred = predict_decision(case.blockers, case.warnings)
        confusion[case.expert_decision][pred] += 1

    per_label: dict[str, dict[str, float]] = {}
    total_correct = 0
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[t][label] for t in labels if t != label)
        fn = sum(confusion[label][p] for p in labels if p != label)

        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall) if precision + recall else 0.0

        per_label[label] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": sum(confusion[label].values()),
        }
        total_correct += tp

    accuracy = _safe_div(total_correct, len(cases))
    macro_f1 = _safe_div(sum(v["f1"] for v in per_label.values()), len(labels))

    return {
        "num_cases": len(cases),
        "accuracy": round(accuracy, 3),
        "macro_f1": round(macro_f1, 3),
        "confusion_matrix": confusion,
        "per_label": per_label,
    }


def write_markdown_report(metrics: dict[str, Any], output: Path) -> None:
    lines = [
        "# Pilot-Ergebnisse (Schritt 8)",
        "",
        f"- Fälle: **{metrics['num_cases']}**",
        f"- Accuracy: **{metrics['accuracy']:.3f}**",
        f"- Macro-F1: **{metrics['macro_f1']:.3f}**",
        "",
        "## Per Label",
        "",
        "| Label | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]

    for label, vals in metrics["per_label"].items():
        lines.append(
            f"| {label} | {vals['precision']:.3f} | {vals['recall']:.3f} | {vals['f1']:.3f} | {vals['support']} |"
        )

    lines.extend([
        "",
        "## Confusion Matrix (Truth x Pred)",
        "",
        "| Truth \\ Pred | PASS | REVIEW | REJECT |",
        "|---|---:|---:|---:|",
    ])

    for truth, row in metrics["confusion_matrix"].items():
        lines.append(f"| {truth} | {row['PASS']} | {row['REVIEW']} | {row['REJECT']} |")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pilot calibration against expert decisions")
    parser.add_argument("dataset", type=Path, help="JSONL dataset with blockers/warnings + expert_decision")
    parser.add_argument("--json-output", type=Path, default=Path("evaluation/results.json"))
    parser.add_argument("--md-output", type=Path, default=Path("evaluation/results.md"))
    args = parser.parse_args()

    cases = read_dataset(args.dataset)
    metrics = compute_metrics(cases)

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown_report(metrics, args.md_output)


if __name__ == "__main__":
    main()
