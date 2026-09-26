"""Task-level action policy and independent human-label contract."""
from __future__ import annotations

from collections import defaultdict

from assay_triage.identity import digest

RELATIONS = ("duplicate", "part_of", "related")


def select_action(rows: list[dict]) -> dict:
    """Select exactly one deployed action for a task, or an explicit abstention."""
    if not rows:
        raise ValueError("A task needs at least one judgment row")
    task = rows[0].get("key")
    config_id = rows[0].get("config_id")
    if not task or not config_id:
        raise ValueError("Every row needs key and config_id")
    if any(r.get("key") != task or r.get("config_id") != config_id for r in rows):
        raise ValueError("Rows must describe one task and one configuration")
    choices = [r for r in rows if r.get("parsed") is not False and r.get("relation") in RELATIONS]
    if choices:
        chosen = sorted(choices, key=lambda r: (-float(r.get("confidence") or 0),
                                                str(r.get("candidate") or ""), r["relation"]))[0]
        action = {"key": task, "candidate": chosen["candidate"], "relation": chosen["relation"],
                  "confidence": float(chosen.get("confidence") or 0), "config_id": config_id,
                  "plan_id": chosen.get("plan_id"), "run_id": chosen.get("run_id")}
    else:
        first = rows[0]
        action = {"key": task, "candidate": None, "relation": "none", "confidence": 0.0,
                  "config_id": config_id, "plan_id": first.get("plan_id"), "run_id": first.get("run_id")}
    return {**action, "action_id": digest(action)}


def selected_actions(rows: list[dict], config_id: str) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        if row.get("config_id") == config_id and row.get("task_status", "complete") == "complete":
            grouped[row.get("key")].append(row)
    return [select_action(grouped[key]) for key in sorted(grouped)]


def label_template(rows: list[dict], config_id: str) -> list[dict]:
    return [{**action, "correct": None, "reviewer": "", "reason": "",
             "label_status": "unknown"} for action in selected_actions(rows, config_id)]


def validate_labels(labels: list[dict]) -> dict[str, dict]:
    out = {}
    for row in labels:
        action_id = row.get("action_id")
        if not action_id or action_id in out:
            raise ValueError("Labels need unique action_id values")
        correct = row.get("correct")
        if correct not in (True, False, None):
            raise ValueError("correct must be true, false, or null")
        if correct is not None and not str(row.get("reviewer") or "").strip():
            raise ValueError("Adjudicated labels need a reviewer")
        out[action_id] = row
    return out


def scored_actions(rows: list[dict], labels: list[dict], config_id: str) -> list[dict]:
    by_id = validate_labels(labels)
    return [{**action, "correct": by_id.get(action["action_id"], {}).get("correct"),
             "label_status": by_id.get(action["action_id"], {}).get("label_status", "missing")}
            for action in selected_actions(rows, config_id)]
