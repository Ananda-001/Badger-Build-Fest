"""Data layer for the Assay Triage app: loading, trust bands, review queue, feedback.

No Streamlit imports here, so everything is unit-testable. The shared contract is docs/SCHEMA.md.
Engine functions (assay_engine.precision_bands / auto_threshold / report) are used when present and
their output is recognisable; otherwise a small built-in fallback computes the same thing.
"""
from __future__ import annotations

import datetime as dt
import gzip
import importlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent


def _find_root() -> Path:
    # Local checkout: app/ lives inside the repo. Databricks bundle: everything sits next to app.py.
    for cand in (APP_DIR, APP_DIR.parent):
        if (cand / "assay_engine").exists() or (cand / "assay_triage").exists() or (cand / "data").exists():
            return cand
    return APP_DIR.parent


ROOT = _find_root()
if str(ROOT) not in sys.path:  # so assay_engine / assay_triage import from a script or `streamlit run`
    sys.path.insert(0, str(ROOT))
REAL_DIR = Path(os.environ.get("ASSAY_DATA_DIR") or (ROOT / "data"))
SAMPLE_DIR = REAL_DIR / "sample"

RELATIONS = ("duplicate", "part_of", "related")
ALL_RELATIONS = RELATIONS + ("none",)
LABEL = {"duplicate": "Duplicate of", "part_of": "Part of umbrella", "related": "Related to", "none": "No relation"}
PLURAL = {"duplicate": "duplicates", "part_of": "umbrella links", "related": "related links"}
DECISIONS = ("accept", "reject", "change")

AUTO_TARGET = float(os.environ.get("ASSAY_AUTO_PRECISION", "0.95"))  # proven (lower-bound) precision to act alone
SUGGEST_FLOOR = float(os.environ.get("ASSAY_SUGGEST_PRECISION", "0.50"))  # below this a suggestion wastes a human's time
ALPHA = 0.05
MIN_BAND_N = 5
TOP_CONF = 0.9  # "high-confidence" slice used for the unlock estimate
JIRA = "https://issues.apache.org/jira/browse/"


# ---------------------------------------------------------------- io

def data_dir(sample: bool) -> Path:
    return SAMPLE_DIR if sample else REAL_DIR


def _jsonl_sources(path: Path) -> list[Path]:
    """The file itself, else its gzipped form or gzipped shards (the Databricks bundle caps files at 10 MB)."""
    if path.exists():
        return [path]
    gz = path.with_name(path.name + ".gz")
    if gz.exists():
        return [gz]
    return sorted(path.parent.glob(path.stem + ".part*.jsonl.gz"))


def has_data(dir_: Path, name: str) -> bool:
    return bool(_jsonl_sources(Path(dir_) / name))


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for src in _jsonl_sources(Path(path)):
        rows.extend(_read_jsonl(src))
    return rows


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a half-written line from a concurrent writer: skip, don't crash the app
    return rows


def load_json(path: Path):
    path = Path(path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def make_feedback(key: str, candidate: str, relation: str, decision: str,
                  new_relation: str | None = None, user: str = "reviewer", ts: str | None = None) -> dict:
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {DECISIONS}, got {decision!r}")
    if relation not in ALL_RELATIONS:
        raise ValueError(f"relation must be one of {ALL_RELATIONS}, got {relation!r}")
    if decision == "change":
        if new_relation not in ALL_RELATIONS or new_relation == relation:
            raise ValueError("a 'change' needs a new_relation different from the proposed one")
    else:
        new_relation = None
    return {"key": key, "candidate": candidate, "relation": relation, "decision": decision,
            "new_relation": new_relation, "user": user or "reviewer", "ts": ts or now_iso()}


def append_feedback(dir_: Path, row: dict) -> Path:
    """Append one feedback row (schema: docs/SCHEMA.md) to <dir>/feedback.jsonl."""
    dir_ = Path(dir_)
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / "feedback.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    _mirror_to_volume(path)
    return path


VOLUME_FILES = ("tickets.jsonl", "judgments.jsonl", "candidates.jsonl", "feedback.jsonl", "model_compare.json")


def _volume() -> str | None:
    """ASSAY_DATA_VOLUME, e.g. /Volumes/workspace/assay_triage/data: the app's data home on Databricks."""
    v = os.environ.get("ASSAY_DATA_VOLUME")
    return v.rstrip("/") if v else None


def sync_from_volume(dest: Path | None = None) -> list[str]:
    """Download the data files from the Unity Catalog volume into the local data dir (Databricks Apps only)."""
    vol = _volume()
    if not vol:
        return []
    dest = Path(dest or REAL_DIR)
    dest.mkdir(parents=True, exist_ok=True)
    got = []
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
    except Exception:
        return got
    for name in VOLUME_FILES:
        try:
            data = w.files.download(f"{vol}/{name}").contents.read()
        except Exception:
            continue  # missing file: that page shows its empty state
        (dest / name).write_bytes(data)
        got.append(name)
    return got


def _mirror_to_volume(path: Path) -> None:
    """On Databricks Apps the local disk is ephemeral, so write feedback back to the UC volume too."""
    vol = _volume()
    if not vol or path.parent.resolve() != REAL_DIR.resolve():  # never push sample feedback
        return
    try:
        from databricks.sdk import WorkspaceClient
        with path.open("rb") as f:
            WorkspaceClient().files.upload(f"{vol}/{path.name}", f, overwrite=True)
    except Exception:  # best effort; the local append already succeeded
        pass


def ticket_url(key: str) -> str | None:
    return None if key.startswith("FAKE-") else JIRA + key


# ---------------------------------------------------------------- engine access

def engine(name: str, module: str = "assay_engine"):
    """Return assay_engine.<name> (or <module>.<name>) if it exists, else None."""
    try:
        mod = importlib.import_module(module)
    except Exception:
        return None
    fn = getattr(mod, name, None)
    return fn if callable(fn) else None


def _lower_bound(k: float, n: float, alpha: float = ALPHA) -> float:
    if n <= 0:
        return 0.0
    try:
        from assay_engine.bounds import lower_bound
        return float(lower_bound(k, n, alpha))
    except Exception:
        # one-sided Wilson score bound (z for alpha=0.05)
        z = 1.6448536269514722
        p = k / n
        denom = 1 + z * z / n
        centre = (p + z * z / (2 * n)) / denom
        half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
        return max(0.0, centre - half)


# ---------------------------------------------------------------- evidence

def pick_model(judgments: list[dict]) -> str | None:
    c = Counter(j.get("model") for j in judgments if j.get("model"))
    return c.most_common(1)[0][0] if c else None


def evidence(judgments: list[dict], feedback: list[dict]) -> list[dict]:
    """Labelled judgments: maintainer truth (correct not null) plus human reviews from the app.

    A human review only counts for pairs that have no maintainer label, so nothing is counted twice.
    """
    rows = [j for j in judgments if j.get("correct") is not None and j.get("relation") in RELATIONS]
    labelled = {(j["key"], j["candidate"]) for j in rows}
    latest = {}
    for f in feedback:
        latest[(f.get("key"), f.get("candidate"))] = f
    for j in judgments:
        pair = (j.get("key"), j.get("candidate"))
        if j.get("relation") not in RELATIONS or pair in labelled or pair not in latest:
            continue
        f = latest[pair]
        if f.get("relation") != j.get("relation"):
            continue
        rows.append({**j, "correct": f.get("decision") == "accept", "truth_source": "review"})
        labelled.add(pair)
    return rows


# ---------------------------------------------------------------- trust bands

def _stats(rows: list[dict]) -> dict:
    n = len(rows)
    k = sum(1 for r in rows if r.get("correct"))
    return {"n": n, "k": k, "precision": (k / n) if n else None, "lower": _lower_bound(k, n) if n else None}


def _conf(r: dict) -> float:
    return float(r.get("confidence") or 0)


def _auto_cutoff(rows: list[dict], relation: str, target: float) -> tuple[float | None, str]:
    """Lowest confidence at which acting alone is proven safe. Engine first, built-in fallback."""
    fn = engine("auto_threshold")
    if fn is not None:
        try:
            res = fn(rows, target, ALPHA, relation=relation)
            return (None if res is None else float(res["threshold"])), "assay_engine"
        except Exception:
            pass
    t_auto = None  # fallback: same fixed-sequence walk, highest cutoff first, stop at the first failure
    min_n = next(n for n in range(1, 100000) if _lower_bound(n, n) >= target)
    for t in sorted({_conf(r) for r in rows}, reverse=True):
        s = _stats([r for r in rows if _conf(r) >= t])
        if s["n"] < min_n:
            continue
        if s["lower"] < target:
            break
        t_auto = t
    return t_auto, "built-in"


def _suggest_cutoff(rows: list[dict], relation: str, top: float, floor: float) -> float:
    """Walk down from the auto cutoff while each confidence band is still worth a human's look."""
    below = [r for r in rows if _conf(r) < top]
    if not below:
        return top if rows else 0.5
    fn = engine("precision_bands")
    segs = None
    if fn is not None:
        try:
            segs = [(b["lo_conf"], b["action"] != "silent")
                    for b in fn(below, AUTO_TARGET, ALPHA, relation=relation, useful_floor=floor) if b["n"]]
        except Exception:
            segs = None
    if segs is None:
        segs = []
        edge = math.floor(min(top, 1.0) * 10 - 1e-9) / 10
        hi = top
        while edge >= 0:
            s = _stats([r for r in below if edge <= _conf(r) < hi])
            if s["n"]:
                segs.append((edge, s["precision"] >= floor))
            hi, edge = edge, round(edge - 0.1, 10)
    t_sug = top
    for lo, useful in sorted(segs, key=lambda x: -x[0]):
        if not useful:
            break
        t_sug = lo
    return t_sug


def bands(ev: list[dict], relation: str, target: float = AUTO_TARGET, floor: float = SUGGEST_FLOOR) -> dict:
    """Confidence ranges where the agent acts alone (auto), asks a human (suggest), or stays quiet (silent)."""
    rows = [r for r in ev if r.get("relation") == relation and r.get("correct") is not None]
    t_auto, source = _auto_cutoff(rows, relation, target)
    top = 1.0001 if t_auto is None else t_auto
    t_sug = _suggest_cutoff(rows, relation, top, floor) if rows else 0.5
    if t_sug >= 1.0:
        t_sug = top

    def seg(band, lo, hi):
        return {"relation": relation, "band": band, "lo": lo, "hi": min(hi, 1.0),
                **_stats([r for r in rows if lo <= _conf(r) < hi])}

    segs = []
    if t_auto is not None:
        segs.append(seg("auto", t_auto, 1.0001))
    if t_sug < top:
        segs.append(seg("suggest", t_sug, top))
    if t_sug > 0:
        segs.append(seg("silent", 0.0, t_sug))
    return {"relation": relation, "auto_threshold": t_auto, "suggest_threshold": t_sug, "segments": segs,
            "n": len(rows), "source": source}


def all_bands(ev: list[dict]) -> dict:
    return {rel: bands(ev, rel) for rel in RELATIONS}


def band_of(b: dict, confidence: float) -> str:
    c = float(confidence or 0)
    if b.get("auto_threshold") is not None and c >= b["auto_threshold"]:
        return "auto"
    if c >= b.get("suggest_threshold", 1.0001):
        return "suggest"
    return "silent"


def reviews_to_unlock(ev: list[dict], relation: str, target: float = AUTO_TARGET) -> dict:
    """How many more high-confidence reviews (at today's hit rate) until auto can switch on."""
    rows = [r for r in ev if r.get("relation") == relation and r.get("correct") is not None and _conf(r) >= TOP_CONF]
    s = _stats(rows)
    if s["n"] == 0:
        return {**s, "more": None, "reachable": None}
    fn = engine("extra_needed")
    more = None
    if fn is not None:
        try:
            more = fn(s["k"], s["n"], target, ALPHA)
        except Exception:
            fn = None
    if fn is None:
        p = s["precision"]
        if s["lower"] >= target:
            more = 0
        elif p > target:
            m = 1
            while m < 1_000_000 and _lower_bound(p * (s["n"] + m), s["n"] + m) < target:
                m *= 2
            lo, hi = m // 2, m
            while hi - lo > 1:
                mid = (lo + hi) // 2
                lo, hi = (lo, mid) if _lower_bound(p * (s["n"] + mid), s["n"] + mid) >= target else (mid, hi)
            more = hi if m < 1_000_000 else None
    return {**s, "more": more, "reachable": more is not None}


def trust_sentence(ev: list[dict], relation: str, target: float = AUTO_TARGET) -> str | None:
    """Plain-English line from assay_engine.report.describe_threshold, if the engine is there."""
    thr, desc = engine("auto_threshold"), engine("describe_threshold", "assay_engine.report")
    if thr is None or desc is None:
        return None
    try:
        return desc(thr(ev, target, ALPHA, relation=relation), target)
    except Exception:
        return None

# ---------------------------------------------------------------- queue

def _day(ts) -> str:
    """YYYY-MM-DD (local) from an ISO string or a Unix epoch number; '' if unknown."""
    if isinstance(ts, (int, float)):
        try:
            return dt.datetime.fromtimestamp(ts).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return ""
    if isinstance(ts, str) and ts:
        try:
            d = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return (d.astimezone() if d.tzinfo else d).date().isoformat()
        except ValueError:
            return ts[:10]
    return ""


def queue(judgments: list[dict], feedback: list[dict], bands_by_rel: dict, model: str | None = None) -> list[dict]:
    """Suggest-band proposals not yet reviewed, most confident first; one card per (ticket, candidate)."""
    done = {(f.get("key"), f.get("candidate")) for f in feedback}
    best = {}
    for j in judgments:
        rel = j.get("relation")
        if rel not in RELATIONS or (model and j.get("model") != model):
            continue
        pair = (j.get("key"), j.get("candidate"))
        if pair in done or band_of(bands_by_rel[rel], j.get("confidence")) != "suggest":
            continue
        if pair not in best or float(j.get("confidence") or 0) > float(best[pair].get("confidence") or 0):
            best[pair] = j
    return sorted(best.values(), key=lambda j: -float(j.get("confidence") or 0))


def auto_handled(judgments: list[dict], bands_by_rel: dict, model: str | None = None,
                 today: str | None = None) -> dict:
    today = today or dt.date.today().isoformat()
    rows = [j for j in judgments if j.get("relation") in RELATIONS and (not model or j.get("model") == model)
            and band_of(bands_by_rel[j["relation"]], j.get("confidence")) == "auto"]
    proven = [s["lower"] for b in bands_by_rel.values() for s in b["segments"]
              if s["band"] == "auto" and s.get("lower") is not None]
    return {"today": sum(1 for j in rows if _day(j.get("ts")) == today), "total": len(rows),
            "proven": min(proven) if proven else None}


# ---------------------------------------------------------------- search fallback

class LocalIndex:
    """TF-IDF over tickets, used when assay_triage.retrieve is missing or sample data is on."""

    def __init__(self, tickets: list[dict]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.tickets = tickets
        docs = [" ".join([t.get("summary") or "", t.get("summary") or "", " ".join(t.get("components") or []),
                          (t.get("description") or "")[:1500]]) for t in tickets]
        self.vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), stop_words="english",
                                   min_df=1 if len(tickets) < 200 else 2)
        self.X = self.vec.fit_transform(docs)

    def search(self, text: str, k: int = 10) -> list[dict]:
        sims = (self.X @ self.vec.transform([text]).T).toarray().ravel()
        order = sims.argsort()[::-1][:k]
        return [{"key": self.tickets[i]["key"], "score": round(float(sims[i]), 4)} for i in order if sims[i] > 0]


# ---------------------------------------------------------------- model check

def compare_pairs(judgments: list[dict], ref: str, cand: str) -> list[dict]:
    """Pair two models' labelled judgments on the same (ticket, candidate) for compare_models."""
    by = {}
    for j in judgments:
        if j.get("correct") is None or j.get("model") not in (ref, cand):
            continue
        by.setdefault((j["key"], j["candidate"]), {})[j["model"]] = j
    out = []
    for item, d in by.items():
        if ref in d and cand in d:
            out.append({"item": f"{item[0]}|{item[1]}", "correct_a": bool(d[ref]["correct"]),
                        "correct_b": bool(d[cand]["correct"]),
                        "cost_a": d[ref].get("cost_usd"), "cost_b": d[cand].get("cost_usd")})
    return out


def compare_from_judgments(judgments: list[dict], ref: str, cand: str, step: str = "the triage decision"):
    fn = engine("compare_models")
    if fn is None:
        return None
    pairs = compare_pairs(judgments, ref, cand)
    if not pairs:
        return None
    res = dict(fn(pairs))
    res.update(reference=ref, candidate=cand, step=step)
    return res


def normalise_compare(data) -> list[dict]:
    """data/model_compare.json -> list of compare_models-style dicts.

    Accepts one compare_models result, a list of them, or {"comparisons": [...]}; model names may be given as
    reference/candidate, name_a/name_b or model_a/model_b.
    """
    if data is None:
        return []
    if isinstance(data, dict) and isinstance(data.get("comparisons"), list):
        items = data["comparisons"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    out = []
    for d in items:
        if not isinstance(d, dict) or "verdict" not in d:
            continue
        out.append({**d,
                    "reference": d.get("reference") or d.get("name_a") or d.get("model_a") or "the reference model",
                    "candidate": d.get("candidate") or d.get("name_b") or d.get("model_b") or "the cheaper model",
                    "step": d.get("step") or "this step"})
    return out


def _signed(x: float, unit: str = "", digits: int = 1) -> str:
    return f"{'−' if x < 0 else '+'}{abs(x):.{digits}f}{unit}"


def compare_headline(c: dict) -> str:
    """e.g. 'Haiku can replace Sonnet for this step: CERTIFIED, −70% cost, quality −0.4 pts [−1.9, +1.1]'."""
    v = str(c.get("verdict")).upper()
    a, b, step = c["reference"], c["candidate"], c["step"]
    head = {"CERTIFY": f"{b} can replace {a} for {step}: CERTIFIED",
            "REJECT": f"{b} cannot replace {a} for {step}: REJECTED"}.get(v, f"Can {b} replace {a} for {step}? NOT PROVEN YET")
    parts = [head]
    if c.get("cost_rel") is not None:
        parts.append(f"{_signed(100 * c['cost_rel'], '%', 0)} cost")
    if c.get("quality_pp") is not None:
        q = f"quality {_signed(c['quality_pp'], ' pts')}"
        if c.get("quality_lo_pp") is not None and c.get("quality_hi_pp") is not None:
            q += f" [{_signed(c['quality_lo_pp'])}, {_signed(c['quality_hi_pp'])}]"
        parts.append(q)
    return ", ".join(parts)
