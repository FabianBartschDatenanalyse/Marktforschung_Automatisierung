from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.pilot_runner import compute_metrics, predict_decision, read_dataset, write_markdown_report
from governance.audit_log import read_audit_events
from governance.override import apply_override, load_policy


DEFAULT_POLICY = Path("governance/policy.yaml")
DEFAULT_AUDIT = Path("examples/audit_log.jsonl")


def build_gate_decision(blockers: int, warnings: int, score: int | None = None) -> dict[str, Any]:
    decision = predict_decision(blockers, warnings)
    if decision == "REJECT":
        reason = f"{blockers} BLOCKER gefunden"
    elif decision == "REVIEW":
        reason = f"{warnings} WARNING gefunden"
    else:
        reason = "Keine BLOCKER/WARNING"

    return {
        "decision": decision,
        "reason": reason,
        "counts": {
            "blockers": int(blockers),
            "warnings": int(warnings),
            "hints": 0,
        },
        "score": score if score is not None else (90 if decision == "PASS" else 75 if decision == "REVIEW" else 50),
    }


def execute_override(
    gate_report: dict[str, Any],
    user: str,
    role: str,
    reason: str,
    policy_path: Path = DEFAULT_POLICY,
    audit_path: Path = DEFAULT_AUDIT,
) -> dict[str, Any]:
    policy = load_policy(policy_path)
    return apply_override(
        gate_report=gate_report,
        user_id=user,
        role=role,
        reason=reason,
        policy=policy,
        audit_path=audit_path,
    )


def run_pilot(dataset_path: Path, json_output: Path, md_output: Path) -> dict[str, Any]:
    cases = read_dataset(dataset_path)
    metrics = compute_metrics(cases)

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown_report(metrics, md_output)

    return metrics


def get_audit_events(audit_path: Path = DEFAULT_AUDIT) -> list[dict[str, Any]]:
    return read_audit_events(audit_path)
