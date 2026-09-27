"""Assay manager dashboard: a Databricks App (FastAPI + one static page) for people who are not engineers.

    uvicorn app.manager.server:app --port 8000          # locally (uses .env: DATABRICKS_HOST/TOKEN/WAREHOUSE_ID)
    python scripts/deploy_manager.py                    # on Databricks

Everything shown is read live from Unity Catalog (<catalog>.<schema>):
  proposals, live_proposals   what the agent suggested and nobody has answered yet
  past_decisions, actions     what reviewers decided (actions = clicks in this dashboard and the workbench)
  verdicts                    Assay's verdicts on models and corrections, plus headline counts
  routing_log, stream         live model switching log; fresh tickets for "Check new tickets"
Past decisions are reused (assay_engine.precedent) only where the record proves reuse would have been right.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE if (HERE / "assay_engine").exists() else HERE.parent.parent  # bundle root on Databricks, repo locally
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402

from assay_engine import precedent as P  # noqa: E402
from assay_engine import router  # noqa: E402
from assay_engine.policy import select_action  # noqa: E402
from assay_triage import dbx  # noqa: E402

dbx.load_env()
app = FastAPI(title="Assay manager dashboard")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

RELATIONS = ("duplicate", "part_of", "related")
_cache: dict = {"at": 0.0, "state": None}
_lock = threading.Lock()
_run_lock = threading.Lock()
TTL = 20


def rows(sql: str, params: list[dict] | None = None) -> list[dict]:
    """SELECT ... as dicts: every row comes back as one JSON string from the warehouse."""
    return [json.loads(r[0]) for r in dbx.sql(sql, params=params)]


def table(name: str) -> str:
    return dbx.table(name)


def load_all() -> dict:
    q = {
        "proposals": f"SELECT to_json(struct(*)) FROM {table('proposals')}",
        "live": f"SELECT to_json(struct(*)) FROM {table('live_proposals')} ORDER BY ts DESC",
        "past": f"SELECT to_json(struct(*)) FROM {table('past_decisions')}",
        "verdicts": f"SELECT to_json(struct(*)) FROM {table('verdicts')}",
        "actions": f"SELECT to_json(struct(id, key, candidate, relation, decision, user, ts, payload)) "
                   f"FROM {table('actions')} ORDER BY ts DESC",
        "routing": f"SELECT to_json(struct(*)) FROM {table('routing_log')} ORDER BY ts DESC",
    }
    with ThreadPoolExecutor(len(q)) as ex:
        futs = {k: ex.submit(rows, s) for k, s in q.items()}
        return {k: f.result() for k, f in futs.items()}


def click_id(key: str, cand: str, relation: str) -> str:
    return "manager:" + hashlib.sha256(f"{key}|{cand}|{relation}".encode()).hexdigest()[:40]


def build_state(raw: dict) -> dict:
    verdicts = {v["name"]: {"verdict": v["verdict"], **json.loads(v["data"])} for v in raw["verdicts"]}
    tickets: dict[str, dict] = {}
    for r in raw["past"] + raw["proposals"] + raw["live"]:
        tickets.setdefault(r["key"], {"key": r["key"], "summary": r.get("key_summary"), "parent": r.get("key_parent")})
        tickets.setdefault(r["candidate"], {"key": r["candidate"], "summary": r.get("cand_summary"),
                                            "parent": r.get("cand_parent")})

    # decisions: past reviews, then clicks (a click is a human answer and wins over anything earlier)
    decisions = {f"{d['key']}|{d['candidate']}|{d['relation']}": {**d} for d in raw["past"]}
    clicked = {}
    for a in raw["actions"]:
        if a.get("decision") not in ("accept", "reject") or a.get("relation") not in RELATIONS:
            continue
        k = f"{a['key']}|{a['candidate']}|{a['relation']}"
        if k in clicked:  # newest first: keep the latest answer
            continue
        clicked[k] = a
        decisions[k] = {"id": k, "key": a["key"], "candidate": a["candidate"], "relation": a["relation"],
                        "correct": a["decision"] == "accept", "source": "human"}
    memory = P.build_memory(list(decisions.values()), tickets)

    open_items, handled = [], []
    seen = set()
    for r in raw["live"] + raw["proposals"]:
        k = f"{r['key']}|{r['candidate']}|{r['relation']}"
        if k in seen or r["relation"] not in RELATIONS:
            continue
        seen.add(k)
        item = {"id": k, "key": r["key"], "candidate": r["candidate"], "relation": r["relation"],
                "confidence": r.get("confidence"), "model": r.get("model"), "reason": r.get("reason"),
                "new": r.get("origin") == "live", "ts": r.get("ts"),
                "a": {"key": r["key"], "title": r.get("key_summary"), "date": r.get("key_created")},
                "b": {"key": r["candidate"], "title": r.get("cand_summary"), "date": r.get("cand_created")}}
        if k in clicked:
            continue
        res = P.resolve(tickets[r["key"]], tickets[r["candidate"]], r["relation"], memory)
        item["kind"], item["kind_text"] = res["kind"], P.KINDS[res["kind"]]
        item["precedent"] = res.get("precedent") and {x: res["precedent"][x] for x in
                                                      ("n", "agree", "answer", "needs_more", "enabled")}
        item["precedent_reason"] = res["reason"]
        (handled if res["mode"].startswith("auto-") else open_items).append({**item, "mode": res["mode"]})

    def priority(it):  # newest live first; then answers that teach it the most; then most confident
        p = it.get("precedent") or {}
        teach = p.get("needs_more") if p.get("needs_more") is not None and p["agree"] == p["n"] else 999
        return (not it["new"], teach, -(it.get("confidence") or 0))
    open_items.sort(key=priority)

    learning = []
    for m in memory.values():
        if m["kind"] == "other":
            continue
        learning.append({"relation": m["relation"], "kind": m["kind"], "kind_text": m["kind_text"], "n": m["n"],
                         "agree": m["agree"], "answer": m["answer"], "enabled": m["enabled"],
                         "needs_more": m["needs_more"], "lower": m["lower"], "target": m["target"],
                         "open": sum(1 for it in open_items if it["relation"] == m["relation"] and it["kind"] == m["kind"]),
                         "clicks": sum(1 for c in clicked.values() if c["relation"] == m["relation"]
                                       and c["key"] in tickets and c["candidate"] in tickets
                                       and P.case_kind(tickets[c["key"]], tickets[c["candidate"]]) == m["kind"])})
    learning.sort(key=lambda m: (not m["enabled"], m["agree"] != m["n"], -m["n"]))

    routing = raw["routing"]
    for d in routing:
        d["answered_name"] = router.name(d.get("answered_by"))
        d["first_name"] = router.name(d.get("first_choice"))
        d["steps"] = json.loads(d["steps"]) if isinstance(d.get("steps"), str) else d.get("steps") or []
    main = [d for d in routing if d.get("answered_by") and d["answered_by"] == d.get("first_choice")]
    main_ms = sorted(sum(s.get("ms") or 0 for s in d["steps"]) for d in main)
    summary = verdicts.get("summary", {})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog": f"{dbx.CATALOG}.{dbx.SCHEMA}",
        "counts": {
            "tickets_read": summary.get("tickets_read", 0) + len({r["key"] for r in raw["live"]}),
            "suggestions": summary.get("suggestions", 0) + len(raw["live"]),
            "auto_handled": len(handled), "waiting": len(open_items),
            "answered": len(clicked), "past_decisions": len(decisions),
            "model_requests": summary.get("model_requests", 0) + len(routing),
            "wrong_prevented": summary.get("wrong_prevented", 0),
            "switches": sum(1 for d in routing if d.get("switched")),
            "live_runs": len(routing), "main_answers": len(main),
            "typical_ms": main_ms[len(main_ms) // 2] if main_ms else None,
        },
        "inbox": open_items,
        "handled": handled,
        "learning": learning,
        "permission": verdicts.get("main-permission", {}),
        "held": {k: verdicts.get(k, {}) for k in ("cheap-model", "bad-rule", "new-instructions")},
        "policy": verdicts.get("routing-policy", {}),
        "routing": routing[:12],
        "last_switch": next((d for d in routing if d.get("switched")), None),  # the whole log: it can be older than 12
        "recent_clicks": [{"key": c["key"], "candidate": c["candidate"], "relation": c["relation"],
                           "decision": c["decision"], "user": c.get("user"), "ts": c.get("ts")}
                          for c in list(clicked.values())[:8]],
        "can_run": os.environ.get("ASSAY_ALLOW_MODEL_CALLS") == "1",
    }


def state(fresh: bool = False) -> dict:
    with _lock:
        if fresh or not _cache["state"] or time.time() - _cache["at"] > TTL:
            _cache["state"], _cache["at"] = build_state(load_all()), time.time()
        return _cache["state"]


def who(request: Request) -> str:
    return (request.headers.get("x-forwarded-email") or request.headers.get("x-forwarded-preferred-username")
            or os.environ.get("ASSAY_REVIEWER") or "local-reviewer")


@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/state")
def api_state(fresh: int = 0):
    try:
        return state(bool(fresh))
    except Exception as e:  # noqa: BLE001  (show the page with a readable error instead of a blank screen)
        return JSONResponse({"error": str(e)[:400]}, status_code=503)


MERGE = f"""MERGE INTO {table('actions')} t USING (SELECT :id AS id) s ON t.id = s.id
WHEN MATCHED THEN UPDATE SET decision = :decision, user = :user, ts = current_timestamp(), payload = :payload,
  link_created = :link_created
WHEN NOT MATCHED THEN INSERT (id, key, candidate, relation, config_id, decision, correction, user, reason, ts,
  link_created, payload)
VALUES (:id, :key, :candidate, :relation, 'manager-dashboard', :decision, NULL, :user, :reason, current_timestamp(),
  :link_created, :payload)"""


def _sql_retry(statement: str, params: list[dict]):
    for attempt in range(6):
        try:
            return dbx.sql(statement, params=params)
        except RuntimeError as e:  # concurrent writes to one Delta table can conflict; retry sees the winner
            if "concurrent" not in str(e).lower() or attempt == 5:
                raise
            time.sleep(0.5 * (attempt + 1))


@app.post("/api/answer")
async def api_answer(request: Request):
    body = await request.json()
    key, cand, rel, decision = body.get("key"), body.get("candidate"), body.get("relation"), body.get("decision")
    if rel not in RELATIONS or decision not in ("accept", "reject") or not key or not cand:
        raise HTTPException(400, "key, candidate, relation and decision (accept|reject) are required")
    user = who(request)
    cid = click_id(key, cand, rel)
    payload = {"id": cid, "key": key, "candidate": cand, "relation": rel, "decision": decision, "user": user,
               "source": "manager-dashboard", "overrode": body.get("overrode"),
               "ts": datetime.now(timezone.utc).isoformat()}
    p = lambda n, v, t=None: {"name": n, "value": None if v is None else str(v), "type": t}  # noqa: E731
    await run_in_threadpool(_sql_retry, MERGE, [p("id", cid), p("key", key), p("candidate", cand), p("relation", rel), p("decision", decision),
                       p("user", user), p("reason", body.get("overrode") or ""), p("payload", json.dumps(payload)),
                       p("link_created", "true" if decision == "accept" else "false", "BOOLEAN")])
    return {"ok": True, "id": cid, "state": await run_in_threadpool(state, True)}


@app.post("/api/undo")
async def api_undo(request: Request):
    body = await request.json()
    cid = click_id(body.get("key", ""), body.get("candidate", ""), body.get("relation", ""))
    await run_in_threadpool(_sql_retry, f"DELETE FROM {table('actions')} WHERE id = :id", [{"name": "id", "value": cid}])
    return {"ok": True, "state": await run_in_threadpool(state, True)}


@app.post("/api/run")
async def api_run(request: Request):
    """Run the agent live on a few fresh tickets: the router picks the model, switches on busy/bad output."""
    if os.environ.get("ASSAY_ALLOW_MODEL_CALLS") != "1":
        raise HTTPException(403, "Live runs are switched off for this app (ASSAY_ALLOW_MODEL_CALLS).")
    if not _run_lock.acquire(blocking=False):
        raise HTTPException(409, "A check is already running. Give it a few seconds.")
    try:
        n = max(1, min(int((await request.json()).get("n", 3)), 5))
        return await run_in_threadpool(run_live, n)  # 10-40 s of model calls: keep the server responsive
    finally:
        _run_lock.release()


def run_live(n: int) -> dict:
    done = {r["ticket"] for r in rows(f"SELECT to_json(struct(ticket)) FROM {table('routing_log')}")}
    stream = rows(f"SELECT to_json(struct(*)) FROM {table('stream')}")
    pick = random.Random().sample([s for s in stream if s["key"] not in done], n)
    keys = sorted({s["key"] for s in pick} | {c for s in pick for c in json.loads(s["candidates"])})
    params = [{"name": f"k{i}", "value": k} for i, k in enumerate(keys)]
    tickets = {t["key"]: t for t in rows(
        f"SELECT to_json(struct(*)) FROM {table('tickets')} WHERE key IN ({', '.join(f':k{i}' for i in range(len(keys)))})",
        params)}
    policy = state()["policy"] or router.load_policy()

    def one(s):
        cands = [tickets[c] for c in json.loads(s["candidates"]) if c in tickets]
        return router.route(tickets[s["key"]], cands, policy, prompt="v2")

    with ThreadPoolExecutor(n) as ex:
        results = list(ex.map(one, pick))
    decisions = [d for _, d in results]
    router.log_delta(decisions)
    new_rows = []
    for (judged, d) in results:
        if not judged:
            continue
        a = select_action([{**j, "task_status": "complete"} for j in judged])
        if a.get("relation") not in RELATIONS or a.get("candidate") not in tickets:
            continue
        src = next((j for j in judged if j["candidate"] == a["candidate"]), {})
        t, c = tickets[a["key"]], tickets[a["candidate"]]
        new_rows.append({"id": f"{a['key']}|{a['candidate']}|{a['relation']}", "key": a["key"], "candidate": a["candidate"],
                         "relation": a["relation"], "confidence": a.get("confidence"),
                         "model": router.name(d["answered_by"]), "reason": src.get("reason"), "runs": "live",
                         "origin": "live", "key_summary": t.get("summary"), "key_created": (t.get("created") or "")[:10],
                         "key_parent": t.get("parent"), "cand_summary": c.get("summary"),
                         "cand_created": (c.get("created") or "")[:10], "cand_parent": c.get("parent"),
                         "kind": P.case_kind(t, c), "ts": d["ts"], "answered_by": d["answered_by"],
                         "switched": d["switched"], "trusted": d["trusted"], "route_reason": d["reason"]})
    if new_rows:
        cols = list(new_rows[0])
        types = {"confidence": "DOUBLE", "ts": "TIMESTAMP", "switched": "BOOLEAN", "trusted": "BOOLEAN"}
        params, vals = [], []
        for i, r in enumerate(new_rows):
            for c in cols:
                v = r[c]
                params.append({"name": f"{c}{i}", "value": None if v is None else (str(v).lower() if isinstance(v, bool)
                                                                                   else str(v)), "type": types.get(c)})
            vals.append("(" + ", ".join(f":{c}{i}" for c in cols) + ")")
        _sql_retry(f"INSERT INTO {table('live_proposals')} ({', '.join(cols)}) VALUES {', '.join(vals)}", params)
    return {"ok": True, "tickets": [d["ticket"] for d in decisions], "suggestions": len(new_rows),
            "decisions": [{"ticket": d["ticket"], "answered_by": router.name(d["answered_by"]), "switched": d["switched"],
                           "needs_review": d["needs_review"], "reason": d["reason"]} for d in decisions],
            "state": state(fresh=True)}
