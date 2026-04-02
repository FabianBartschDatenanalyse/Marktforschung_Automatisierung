#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .audit_log import DEFAULT_AUDIT_PATH, append_audit_event, utc_now_iso


def load_policy(path: Path) -> dict[str, Any]:
    """Minimal YAML reader for the current policy shape."""
    data: dict[str, Any] = {
        "roles": {
            "editor": {"can_override": False},
            "lead": {"can_override": True},
        },
        "override": {
            "reason_min_chars": 12,
            "allowed_from_decisions": ["REVIEW", "REJECT"],
        },
    }

    current_section = None
    current_sub = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.strip().startswith("#"):
            continue

        if not line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1]
            current_sub = None
            continue

        if line.startswith("  ") and line.endswith(":") and current_section:
            current_sub = line.strip()[:-1]
            continue

        if ":" in line and current_section:
            key, value = [x.strip() for x in line.split(":", 1)]
            value = value.strip()
            if value.lower() in {"true", "false"}:
                parsed: Any = value.lower() == "true"
            elif value.isdigit():
                parsed = int(value)
            elif value:
                parsed = value
            else:
                continue

            if current_sub:
                data.setdefault(current_section, {}).setdefault(current_sub, {})[key] = parsed
            else:
                data.setdefault(current_section, {})[key] = parsed

        if line.strip().startswith("-") and current_section == "override":
            item = line.strip().lstrip("-").strip()
            data.setdefault("override", {}).setdefault("allowed_from_decisions", []).append(item)

    return data


def apply_override(
    gate_report: dict[str, Any],
    user_id: str,
    role: str,
    reason: str,
    policy: dict[str, Any],
    audit_path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    current_decision = gate_report.get("decision", "UNKNOWN")
    reason_min_chars = int(policy.get("override", {}).get("reason_min_chars", 12))
    allowed_decisions = policy.get("override", {}).get("allowed_from_decisions", ["REVIEW", "REJECT"])
    can_override = bool(policy.get("roles", {}).get(role, {}).get("can_override", False))

    if not can_override:
        raise PermissionError(f"Rolle '{role}' darf keine Overrides durchführen")

    if current_decision not in allowed_decisions:
        raise ValueError(f"Override für Entscheidung '{current_decision}' laut Policy nicht erlaubt")

    if len(reason.strip()) < reason_min_chars:
        raise ValueError(f"Override-Begründung zu kurz (min. {reason_min_chars} Zeichen)")

    overridden = {
        **gate_report,
        "decision": "PASS",
        "override": {
            "by": user_id,
            "role": role,
            "reason": reason,
            "timestamp": utc_now_iso(),
            "original_decision": current_decision,
        },
    }

    audit_event = {
        "event_type": "gate_override",
        "timestamp": overridden["override"]["timestamp"],
        "user": user_id,
        "role": role,
        "reason": reason,
        "before": gate_report,
        "after": overridden,
    }
    append_audit_event(audit_event, path=audit_path)

    return overridden


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply governed override to gate decision")
    parser.add_argument("gate_report", type=Path, help="Path to gate decision JSON")
    parser.add_argument("--user", required=True, help="Actor identifier")
    parser.add_argument("--role", required=True, help="Role (editor|lead)")
    parser.add_argument("--reason", required=True, help="Mandatory override reason")
    parser.add_argument("--policy", type=Path, default=Path("governance/policy.yaml"))
    parser.add_argument("--audit-log", type=Path, default=DEFAULT_AUDIT_PATH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    gate_report = json.loads(args.gate_report.read_text(encoding="utf-8"))
    policy = load_policy(args.policy)

    result = apply_override(
        gate_report,
        args.user,
        args.role,
        args.reason,
        policy,
        audit_path=args.audit_log,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
