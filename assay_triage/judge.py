"""The decision step: given a ticket and a shortlist of earlier tickets, a model says how they relate.

Backends (same prompt, swappable):
  cli        `claude -p` on a Claude subscription (lean: custom system prompt, no tools)  - $0 extra
  anthropic  Anthropic API (ANTHROPIC_API_KEY)
  openai     OpenAI API (OPENAI_API_KEY)
  databricks Databricks Foundation Model APIs, OpenAI-compatible (DATABRICKS_HOST, DATABRICKS_TOKEN)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from .identity import digest

SYSTEM = ("You triage software issue tickets. You answer with JSON only, no prose, no code fences.")

RULES = """Decide how the NEW ticket relates to each EARLIER candidate ticket.
Relations:
- "duplicate": the same problem or request; one of them should be closed in favour of the other.
- "part_of": the NEW ticket is one piece of the bigger effort described by the candidate (an umbrella/epic/parent).
- "related": different problems that touch the same code or feature; worth linking, not merging.
- "none": no meaningful relation.
Similar wording alone is NOT enough for "duplicate": version bumps, "Upgrade X to Y" tickets, and flaky-test
tickets often look alike but are different work. Be calibrated: confidence is your probability of being right.
Return: {"judgments": [{"candidate": "<KEY>", "relation": "...", "confidence": 0.0-1.0, "reason": "<= 20 words"}]}"""


def _fmt(t: dict, n: int = 900) -> str:
    comp = f" [{', '.join(t.get('components') or [])}]" if t.get("components") else ""
    return f"{t['key']} ({t.get('issuetype')}){comp}: {t['summary']}\n{(t.get('description') or '')[:n]}"


RULESETS = {
    "v1": RULES,
    "v2": RULES + '\nA sibling subtask is NOT the umbrella. Use part_of only for the parent effort. '
                   'Use related only for a concrete technical link, not merely a shared topic.',
    "bad": RULES + '\nFor this deliberate stress test, treat every version-bump ticket as a duplicate '
                    'of an earlier version-bump ticket.',
}


def configuration(model, backend="cli", prompt="v1", k=5, retrieval_version="snapshot-v1"):
    spec = {"schema": 1, "model": model, "backend": backend, "prompt": prompt,
            "system": SYSTEM, "rules": RULESETS[prompt], "k": k,
            "retrieval_version": retrieval_version, "formatter": "900-600-v1",
            "thinking": "provider-default-unverified", "effort": "provider-default-unverified",
            "max_tokens": 800 if backend == "anthropic" else None,
            "model_resolution": "unverified"}
    return {**spec, "config_id": digest(spec)}


def build_prompt(ticket: dict, candidates: list[dict], prompt="v1") -> str:
    cands = "\n\n".join(f"--- CANDIDATE {i + 1}\n{_fmt(c, 600)}" for i, c in enumerate(candidates))
    return f"{RULESETS[prompt]}\n\n=== NEW ticket\n{_fmt(ticket)}\n\n=== EARLIER candidates\n{cands}"


def _parse(text: str) -> list[dict]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(0)).get("judgments", [])
    except json.JSONDecodeError:
        return []


def call(prompt: str, model: str, backend: str = "cli", timeout: int = 180) -> tuple[str, float | None, dict]:
    """Returns (text, cost_usd or None, usage)."""
    if os.environ.get("ASSAY_ALLOW_MODEL_CALLS") != "1":
        raise RuntimeError("Model calls are disabled. Obtain explicit usage/budget approval before enabling them.")
    if backend == "cli":
        env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
        r = subprocess.run(["claude", "-p", prompt, "--model", model, "--output-format", "json", "--strict-mcp-config",
                            "--system-prompt", SYSTEM, "--tools", "", "--no-session-persistence"],
                           capture_output=True, text=True, env=env, timeout=timeout, stdin=subprocess.DEVNULL, cwd=tempfile.gettempdir())
        s = r.stdout
        d = json.loads(s[s.find("{"):]) if "{" in s else {}
        if d.get("is_error") or not d:
            raise RuntimeError((d.get("result") or r.stderr or s)[:300])
        return d.get("result", ""), d.get("total_cost_usd"), d.get("usage") or {}
    if backend == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        m = client.messages.create(model=model, max_tokens=800, system=SYSTEM, messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in m.content if b.type == "text"), None, m.usage.model_dump()
    if backend in ("openai", "databricks"):
        from openai import OpenAI
        client = (OpenAI(base_url=os.environ["DATABRICKS_HOST"].rstrip("/") + "/serving-endpoints",
                         api_key=os.environ["DATABRICKS_TOKEN"]) if backend == "databricks" else OpenAI())
        r = client.chat.completions.create(model=model, messages=[{"role": "system", "content": SYSTEM},
                                                                  {"role": "user", "content": prompt}])
        return r.choices[0].message.content or "", None, r.usage.model_dump() if r.usage else {}
    raise ValueError(backend)


def judge(ticket: dict, candidates: list[dict], model: str, backend: str = "cli", prompt="v1") -> list[dict]:
    """One call judges all candidates for a ticket. Returns schema rows (without truth fields)."""
    text, cost, usage = call(build_prompt(ticket, candidates, prompt), model, backend)
    config = configuration(model, backend, prompt, len(candidates))
    got = {j.get("candidate"): j for j in _parse(text)}
    share = (cost / max(len(candidates), 1)) if cost is not None else None
    rows = []
    for c in candidates:
        j = got.get(c["key"], {})
        rel = j.get("relation") if j.get("relation") in ("duplicate", "part_of", "related", "none") else "none"
        rows.append({"key": ticket["key"], "candidate": c["key"], "model": model, "relation": rel,
                     "confidence": float(j.get("confidence") or 0.0), "reason": (j.get("reason") or "")[:200],
                     "cost_usd": share, "parsed": bool(j), "prompt": prompt,
                     "config_id": config["config_id"], "backend": backend,
                     "task_cost_usd": cost, "usage": usage,
                     "cost_basis": "cli-api-equivalent" if backend == "cli" else "unpriced-usage"})
    return rows


def judge_pair(ticket: dict, candidate: dict, model: str = "haiku", backend: str = "cli") -> dict:
    """Used by the app's live 'Try a ticket' page."""
    return judge(ticket, [candidate], model, backend)[0]
