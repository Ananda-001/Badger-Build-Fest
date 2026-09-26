"""FAKE sample data so the app can be built and screenshotted before the real pipeline finishes.

Every ticket key starts with FAKE-, the project is FAKE, and summaries are prefixed with "[sample]".
Files go to data/sample/ only, never next to the real data.

    python app/sample_data.py            # writes data/sample/*.jsonl and model_compare.json
"""
from __future__ import annotations

import datetime as dt
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app_data import SAMPLE_DIR, compare_from_judgments  # noqa: E402

MODELS = ("sample-small-model", "sample-large-model")
COMPONENTS = ["SQL", "Core", "Structured Streaming", "Connect", "PySpark", "Kafka Connect", "Web UI", "Build"]
TOPICS = [
    ("NullPointerException in {c} when {x} is empty", "Running a job where {x} is empty throws an NPE inside {c}. "
     "Stack trace points at the planner. Happens on 3.5 and master."),
    ("Upgrade {x} dependency to the latest release", "The current {x} version has known CVEs. Bump it and re-run "
     "the {c} test suite."),
    ("Flaky test: {x}Suite times out on CI", "The {x}Suite in {c} intermittently times out on the CI runners. "
     "Seen three times this week."),
    ("Support {x} option in {c} writer", "Users want to pass a {x} option through the {c} writer API, "
     "matching what the reader already supports."),
    ("Wrong results when joining on {x} columns", "A join on {x} columns returns duplicate rows in {c}. "
     "Minimal repro attached; the plan shows a missing exchange."),
    ("Improve error message for invalid {x}", "When {x} is invalid, {c} raises a generic error. "
     "The message should name the offending value."),
]
THINGS = ["decimal", "timestamp_ntz", "map", "partition", "checkpoint", "watermark", "schema", "offset",
          "compression", "collation", "variant", "array", "struct", "shuffle", "broadcast"]
UMBRELLAS = ["[Umbrella] {c} 4.0 migration work", "[Umbrella] Improve {c} observability",
             "[Umbrella] Harden {c} against malformed input"]
REASONS = {
    "duplicate": ["Same failure and stack trace in {c}.", "Both report the same bug with the same repro steps."],
    "part_of": ["Sub-task of the {c} umbrella; matches its checklist.", "Listed as a work item under this umbrella."],
    "related": ["Both touch the same {c} code; different symptoms.", "Same code path, different bug."],
    "none": ["Similar words, unrelated work.", "Different component and problem."],
}
# how often the model is right at a given confidence, per relation (FAKE calibration, chosen for a useful demo)
SKILL = {"part_of": 0.05, "duplicate": 0.6, "related": 1.5}
CONF = {"part_of": (14, 1.6), "duplicate": (6, 2), "related": (4, 2.5), "none": (5, 2)}  # beta(a, b) per relation


def _iso(d: dt.datetime) -> str:
    return d.replace(microsecond=0).isoformat()


def generate(out: Path = SAMPLE_DIR, seed: int = 7, n_tickets: int = 600) -> dict:
    rng = random.Random(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    start = dt.datetime(2024, 1, 3, 9, 0, tzinfo=dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    tickets = []
    for i in range(n_tickets):
        key = f"FAKE-{1000 + i}"
        c, x = rng.choice(COMPONENTS), rng.choice(THINGS)
        created = start + dt.timedelta(days=i * 1.1, hours=rng.randint(0, 20))
        if i % 20 == 0:
            summary, desc, itype = rng.choice(UMBRELLAS).format(c=c), f"Umbrella to track the {c} effort. " \
                "Sub-tasks are linked below.", "Umbrella"
        else:
            s, d = rng.choice(TOPICS)
            summary, desc, itype = s.format(c=c, x=x), d.format(c=c, x=x), rng.choice(["Bug", "Improvement", "Task"])
        tickets.append({"key": key, "project": "FAKE", "created": _iso(created), "updated": _iso(created),
                        "summary": "[sample] " + summary, "description": "FAKE SAMPLE TICKET. " + desc,
                        "issuetype": itype, "status": "Open", "resolution": None, "components": [c], "labels": ["sample"],
                        "parent": None, "subtasks": [], "links": []})

    truth, candidates, judgments = [], [], []
    for i in range(30, n_tickets):
        t = tickets[i]
        earlier = tickets[:i]
        umbrellas = [e for e in earlier if e["issuetype"] == "Umbrella"]
        pool = rng.sample(earlier, 3)
        rel = rng.choices(["duplicate", "part_of", "related", "none"], [0.3, 0.3, 0.2, 0.2])[0]
        if rel == "part_of":
            pool[0] = rng.choice(umbrellas)
        if rel == "duplicate":  # a duplicate reads like the earlier ticket
            t["summary"] = pool[0]["summary"] + " (seen again on 3.5.1)"
            t["description"] = pool[0]["description"] + " Still happens after upgrading to 3.5.1."
            t["components"] = list(pool[0]["components"])
        if rel != "none":
            truth.append({"src": t["key"], "dst": pool[0]["key"], "relation": rel,
                          "evidence": {"duplicate": "link:Duplicate", "part_of": "subtask", "related": "link:Relates"}[rel]})
            if rel == "part_of":
                t["parent"] = pool[0]["key"]
            else:
                t["links"].append({"type": "Duplicate" if rel == "duplicate" else "Relates", "direction": "outward",
                                   "key": pool[0]["key"]})
        candidates.append({"key": t["key"], "candidates": [{"key": p["key"], "score": round(0.9 - 0.2 * j - rng.random() * 0.1, 4)}
                                                            for j, p in enumerate(pool)]})
        recent = i >= n_tickets - 40  # newest tickets: no maintainer label yet, they feed the review queue
        for j, p in enumerate(pool):
            true_rel = rel if j == 0 else "none"
            for model in MODELS:
                if j == 0:
                    pred = true_rel
                    conf = rng.betavariate(*CONF[pred])
                    if pred in SKILL:  # wrong more often when less sure
                        wrong_p = SKILL[pred] * ((1 - conf) / 0.35) ** 2
                        if rng.random() < min(wrong_p, 0.9):
                            pred = rng.choice([r for r in SKILL if r != pred])
                else:  # unrelated candidates: mostly "none", sometimes a low-confidence false alarm
                    pred = rng.choices(["none", "related", "duplicate"], [0.85, 0.11, 0.04])[0]
                    conf = rng.betavariate(5, 2) if pred == "none" else rng.betavariate(2, 4)
                c, x = t["components"][0], ""
                ts = now - dt.timedelta(hours=rng.randint(0, 8)) if recent else \
                    dt.datetime.fromisoformat(t["created"]) + dt.timedelta(hours=1)
                judgments.append({
                    "key": t["key"], "candidate": p["key"], "model": model, "relation": pred,
                    "confidence": round(conf, 3), "reason": rng.choice(REASONS[pred]).format(c=c, x=x),
                    "truth": None if recent else true_rel,
                    "correct": None if recent else (pred == true_rel),
                    "cost_usd": round((0.0004 if model == MODELS[0] else 0.0013) * (1 + rng.random() * 0.3), 6),
                    "ts": _iso(ts)})

    # compare_models output shape (assay_engine.compare); computed from the fake judgments when the engine is here
    compare = compare_from_judgments(judgments, MODELS[1], MODELS[0]) or {
        "verdict": "CERTIFY", "n": 330, "margin": 0.02, "alpha": 0.05, "acc_a": 0.86, "acc_b": 0.856,
        "quality_pp": -0.4, "quality_lo_pp": -1.9, "quality_hi_pp": 1.1, "cost_rel": -0.70, "cost_lo": -0.72,
        "cost_hi": -0.68, "need_n": None, "reason": "no worse than the reference (within margin) and cheaper",
        "reference": MODELS[1], "candidate": MODELS[0], "step": "the triage decision"}
    compare["_note"] = "FAKE sample comparison"

    def dump(name, rows):
        (out / name).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    dump("tickets.jsonl", tickets)
    dump("truth.jsonl", truth)
    dump("candidates.jsonl", candidates)
    dump("judgments.jsonl", judgments)
    (out / "model_compare.json").write_text(json.dumps(compare, indent=2), encoding="utf-8")
    (out / "README.txt").write_text(
        "FAKE SAMPLE DATA generated by app/sample_data.py for developing and screenshotting the app.\n"
        "Nothing here is a real Apache Jira ticket or a real model output. Delete freely.\n", encoding="utf-8")
    return {"tickets": len(tickets), "truth": len(truth), "candidates": len(candidates), "judgments": len(judgments)}


def ensure(out: Path = SAMPLE_DIR) -> Path:
    if not (Path(out) / "judgments.jsonl").exists():
        generate(out)
    return Path(out)


if __name__ == "__main__":
    print(generate(), "->", SAMPLE_DIR)
