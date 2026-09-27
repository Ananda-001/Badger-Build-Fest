"""Pull real tickets from the public Apache Software Foundation Jira into data/tickets.jsonl and
derive maintainer-made ground truth into data/truth.jsonl (see docs/SCHEMA.md).

    python -m assay_triage.ingest [--projects SPARK,FLINK,KAFKA,HIVE] [--since 2023-01-01]

No login needed. Requests are sequential with a short pause, to be polite to Apache's servers.
Resumable: pages already saved under data/raw/ are not fetched again.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://issues.apache.org/jira/rest/api/2/search"
FIELDS = "summary,description,created,updated,issuetype,status,resolution,components,labels,parent,subtasks,issuelinks"
ROOT = Path(__file__).resolve().parent.parent / "data"
RAW = ROOT / "raw"
PAGE = 100

# Jira link type name -> our relation. "Duplicate": outward = "duplicates", inward = "is duplicated by".
LINK_RELATION = {"Duplicate": "duplicate", "Incorporates": "part_of", "Reference": "related",
                 "Related": "related", "Relates": "related", "Blocker": None, "Cloners": None}


def fetch(project: str, since: str, start: int) -> dict:
    cache = RAW / f"{project}_{since}_{start:06d}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    q = urllib.parse.urlencode({"jql": f"project={project} AND created>={since} ORDER BY created ASC",
                                "startAt": start, "maxResults": PAGE, "fields": FIELDS})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(f"{API}?{q}", timeout=60) as r:
                d = json.load(r)
            cache.write_text(json.dumps(d))
            time.sleep(0.4)
            return d
        except Exception as ex:  # noqa: BLE001 - network hiccups: back off and retry
            wait = 5 * (attempt + 1)
            print(f"  {project}@{start}: {type(ex).__name__}; retry in {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"failed to fetch {project} at {start}")


def flatten(issue: dict) -> dict:
    f = issue["fields"]
    links = []
    for l in f.get("issuelinks") or []:
        if "outwardIssue" in l:
            links.append({"type": l["type"]["name"], "direction": "outward", "key": l["outwardIssue"]["key"]})
        elif "inwardIssue" in l:
            links.append({"type": l["type"]["name"], "direction": "inward", "key": l["inwardIssue"]["key"]})
    return {
        "key": issue["key"], "project": issue["key"].split("-")[0],
        "created": f.get("created"), "updated": f.get("updated"),
        "summary": f.get("summary") or "", "description": (f.get("description") or "")[:4000],
        "issuetype": (f.get("issuetype") or {}).get("name"), "status": (f.get("status") or {}).get("name"),
        "resolution": (f.get("resolution") or {}).get("name"),
        "components": [c["name"] for c in f.get("components") or []], "labels": f.get("labels") or [],
        "parent": (f.get("parent") or {}).get("key"), "subtasks": [s["key"] for s in f.get("subtasks") or []],
        "links": links,
    }


def derive_truth(tickets: list[dict]) -> list[dict]:
    """Maintainer-made relations, oriented newer -> earlier. Only pairs where both tickets are in our data."""
    by = {t["key"]: t for t in tickets}
    out, seen = [], set()

    def add(a, b, rel, ev):
        if a not in by or b not in by or a == b:
            return
        src, dst = (a, b) if by[a]["created"] >= by[b]["created"] else (b, a)
        if rel == "part_of":  # part_of keeps its direction: the child is src, the umbrella dst
            src, dst = a, b
        k = (src, dst, rel)
        if k not in seen:
            seen.add(k)
            out.append({"src": src, "dst": dst, "relation": rel, "evidence": ev})

    for t in tickets:
        if t["parent"]:
            add(t["key"], t["parent"], "part_of", "subtask")
        for l in t["links"]:
            rel = LINK_RELATION.get(l["type"])
            if rel == "part_of":
                # "A incorporates B": the outward side is the bigger ticket
                child, parent = (l["key"], t["key"]) if l["direction"] == "outward" else (t["key"], l["key"])
                add(child, parent, "part_of", f"link:{l['type']}")
            elif rel:
                add(t["key"], l["key"], rel, f"link:{l['type']}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default="SPARK,FLINK,KAFKA,HIVE")
    ap.add_argument("--since", default="2023-01-01")
    a = ap.parse_args(argv)
    RAW.mkdir(parents=True, exist_ok=True)
    def one_project(p):
        first = fetch(p, a.since, 0)
        total = first["total"]
        print(f"{p}: {total} tickets since {a.since}", flush=True)
        issues = list(first["issues"])
        for start in range(PAGE, total, PAGE):
            issues += fetch(p, a.since, start)["issues"]
            if start % 2000 == 0:
                print(f"  {p}: {start}/{total}", flush=True)
        return [flatten(i) for i in issues]

    # one polite sequential stream per project, projects in parallel
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(len(a.projects.split(","))) as ex:
        tickets = [t for part in ex.map(one_project, a.projects.split(",")) for t in part]
    tickets.sort(key=lambda t: t["created"])
    (ROOT / "tickets.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tickets))
    truth = derive_truth(tickets)
    (ROOT / "truth.jsonl").write_text("".join(json.dumps(t) + "\n" for t in truth))
    from collections import Counter
    print(f"wrote {len(tickets)} tickets, {len(truth)} truth pairs: {dict(Counter(t['relation'] for t in truth))}")


if __name__ == "__main__":
    main()
