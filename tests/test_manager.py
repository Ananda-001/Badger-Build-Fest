"""Manager dashboard state: built from table rows, no Databricks needed."""
import importlib.util
import json
import re
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
_spec = importlib.util.spec_from_file_location(  # by path: tests/test_app.py puts a module named "app" on sys.path
    "manager_server", Path(__file__).resolve().parents[1] / "app" / "manager" / "server.py")
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)


def _pair(i, key_v, cand_v):
    return {"key_summary": f"Upgrade Netty to 4.{key_v}", "key_parent": None, "key_created": "2025-02-01",
            "cand_summary": f"Upgrade Netty to 4.{cand_v}", "cand_parent": None, "cand_created": "2025-01-01"}


def _raw(clicks):
    past = [{"id": f"p{i}", "key": f"SPARK-{100 + i}", "candidate": f"SPARK-{900 + i}", "relation": "duplicate",
             "correct": False, "source": "ai", **_pair(i, i + 1, i)} for i in range(21)]
    open_rows = [{"key": f"SPARK-{200 + i}", "candidate": f"SPARK-{800 + i}", "relation": "duplicate",
                  "confidence": 0.8, "model": "Llama 70B", "reason": "same library", "origin": "stage-2-3",
                  **_pair(i, i + 50, i + 40)} for i in range(10)]
    actions = [{"key": r["key"], "candidate": r["candidate"], "relation": "duplicate", "decision": "reject",
                "user": "manager", "ts": "2026-09-27T00:00:00Z"} for r in open_rows[:clicks]]
    verdicts = [{"name": "summary", "verdict": "", "data": json.dumps({"tickets_read": 5})}]
    return {"proposals": open_rows, "live": [], "past": past, "verdicts": verdicts, "actions": actions, "routing": []}


def test_past_pattern_waits_until_proven_then_handles_the_rest():
    s = server.build_state(_raw(clicks=0))
    bump = next(m for m in s["learning"] if m["kind"] == "bump-same-lib-diff-version")
    assert (bump["agree"], bump["n"], bump["enabled"], bump["needs_more"]) == (21, 21, False, 8)
    assert len(s["inbox"]) == 10 and not s["handled"]

    s = server.build_state(_raw(clicks=8))  # 8 more consistent "No" answers: 29/29 proves 90%
    bump = next(m for m in s["learning"] if m["kind"] == "bump-same-lib-diff-version")
    assert bump["enabled"] and s["counts"]["answered"] == 8
    assert not s["inbox"] and len(s["handled"]) == 2
    assert all(h["mode"] == "auto-reject" for h in s["handled"])


def test_click_on_other_kind_never_auto_handles():
    raw = _raw(clicks=0)
    for r in raw["proposals"] + raw["past"]:
        r["key_summary"], r["cand_summary"] = "Fix a bug", "Improve docs"
    s = server.build_state(raw)
    assert not s["handled"] and not s["learning"]


def test_last_switch_is_found_even_when_older_than_the_log_shown():
    def route(i, switched):
        return {"ts": f"2026-09-27T01:{59 - i:02d}:00Z", "ticket": f"SPARK-{i}", "first_choice": "a",
                "answered_by": "b" if switched else "a", "switched": switched, "needs_review": switched,
                "steps": json.dumps([{"model": "a", "outcome": "busy" if switched else "ok", "ms": 3000}])}
    raw = _raw(clicks=0)
    raw["routing"] = [route(i, i == 13) for i in range(15)]  # newest first; the only switch is 14th
    s = server.build_state(raw)
    assert not any(d["switched"] for d in s["routing"])  # the page's log no longer reaches it...
    assert s["last_switch"]["ticket"] == "SPARK-13"      # ...but it stays pinned
    assert (s["counts"]["switches"], s["counts"]["main_answers"], s["counts"]["typical_ms"]) == (1, 14, 3000)
    raw["routing"] = [route(i, False) for i in range(3)]
    assert server.build_state(raw)["last_switch"] is None


def test_page_wires_every_tour_step_and_element():
    html = (Path(server.__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
    steps = re.findall(r'^\s*\["(\w+)"', re.search(r"const TOUR = \[(.*?)\n\];", html, re.S).group(1), re.M)
    assert len(steps) == 12 and steps[4] == "buttons"  # the docs link #tour=5 to the hands-on step
    for key in steps:
        assert f'data-tour="{key}"' in html, key
    for el in set(re.findall(r'\$\("([\w-]+)"\)', html)):
        assert f'id="{el}"' in html, el
    assert not re.search("[\U0001F300-\U0001FAFF☀-➿]", html)  # SVG icons, never emoji
