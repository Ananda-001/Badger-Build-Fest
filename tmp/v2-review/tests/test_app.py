"""Smoke tests for the Streamlit app (app/). Run: ~/.venvs/assay/bin/python -m pytest tests/test_app.py -q"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

import app_data as D  # noqa: E402
import sample_data  # noqa: E402

TICKET_KEYS = {"key", "project", "created", "updated", "summary", "description", "issuetype", "status",
               "resolution", "components", "labels", "parent", "subtasks", "links"}
JUDGMENT_KEYS = {"key", "candidate", "model", "relation", "confidence", "reason", "truth", "correct", "cost_usd", "ts"}
FEEDBACK_KEYS = {"key", "candidate", "relation", "decision", "new_relation", "user", "ts"}


def _import_app():
    spec = importlib.util.spec_from_file_location("assay_app_under_test", APP_DIR / "app.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_app_module_imports_without_running_ui():
    mod = _import_app()
    assert callable(mod.main)
    assert mod.PAGES[0] == "Review queue"
    assert mod.clean("{code}x = 1{code} h2. Title " + "word " * 200, 50).endswith("…")


@pytest.fixture()
def sample_dir(tmp_path):
    out = tmp_path / "sample"
    stats = sample_data.generate(out, n_tickets=200)
    assert stats["judgments"] > 0
    return out


def test_sample_rows_follow_the_schema(sample_dir):
    tickets = D.load_jsonl(sample_dir / "tickets.jsonl")
    keys = {t["key"] for t in tickets}
    for t in tickets:
        assert set(t) == TICKET_KEYS
        assert t["key"].startswith("FAKE-") and t["project"] == "FAKE"  # clearly fake
        assert isinstance(t["components"], list) and isinstance(t["links"], list)
        assert len(t["description"]) <= 4000
        for link in t["links"]:
            assert link["direction"] in ("outward", "inward") and link["key"] in keys
    by = {t["key"]: t for t in tickets}
    for r in D.load_jsonl(sample_dir / "truth.jsonl"):
        assert set(r) == {"src", "dst", "relation", "evidence"}
        assert r["relation"] in D.RELATIONS
        assert by[r["src"]]["created"] > by[r["dst"]]["created"]  # src is the newer ticket
    for r in D.load_jsonl(sample_dir / "candidates.jsonl"):
        assert set(r) == {"key", "candidates"}
        for c in r["candidates"]:
            assert by[c["key"]]["created"] < by[r["key"]]["created"]  # only earlier tickets
    judgments = D.load_jsonl(sample_dir / "judgments.jsonl")
    for j in judgments:
        assert set(j) == JUDGMENT_KEYS
        assert j["relation"] in D.ALL_RELATIONS and 0 <= j["confidence"] <= 1
        assert j["correct"] in (True, False, None)
        assert (j["truth"] is None) == (j["correct"] is None)
        if j["correct"] is not None:
            assert j["correct"] == (j["relation"] == j["truth"])
    assert any(j["correct"] is None for j in judgments)  # something left for the review queue
    assert D.normalise_compare(D.load_json(sample_dir / "model_compare.json"))


def test_feedback_append_writes_valid_json(tmp_path):
    D.append_feedback(tmp_path, D.make_feedback("SPARK-1", "SPARK-0", "duplicate", "accept", user="t"))
    D.append_feedback(tmp_path, D.make_feedback("SPARK-2", "SPARK-0", "duplicate", "change", "related", user="t"))
    rows = [json.loads(line) for line in (tmp_path / "feedback.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    for r in rows:
        assert set(r) == FEEDBACK_KEYS and r["decision"] in D.DECISIONS
    assert rows[0]["new_relation"] is None and rows[1]["new_relation"] == "related"
    with pytest.raises(ValueError):
        D.make_feedback("A-1", "A-0", "duplicate", "maybe")
    with pytest.raises(ValueError):
        D.make_feedback("A-1", "A-0", "duplicate", "change", "duplicate")


def test_bands_queue_and_feedback_loop(sample_dir):
    J = D.load_jsonl(sample_dir / "judgments.jsonl")
    model = D.pick_model(J)
    J = [j for j in J if j["model"] == model]
    ev = D.evidence(J, [])
    bands = D.all_bands(ev)
    for rel, b in bands.items():
        segs = sorted(b["segments"], key=lambda s: s["lo"])
        assert segs and segs[0]["lo"] == 0.0 and segs[-1]["hi"] == 1.0  # ranges cover [0, 1]
        for a, c in zip(segs, segs[1:]):
            assert a["hi"] == pytest.approx(c["lo"])
    q = D.queue(J, [], bands, model)
    assert q and all(D.band_of(bands[j["relation"]], j["confidence"]) == "suggest" for j in q)
    # a review removes the card and (for an unlabelled pair) becomes evidence
    unl = next(j for j in q if j["correct"] is None)
    fb = [D.make_feedback(unl["key"], unl["candidate"], unl["relation"], "accept")]
    assert len(D.queue(J, fb, bands, model)) == len(q) - 1
    assert len(D.evidence(J, fb)) == len(ev) + 1


def test_empty_data_is_graceful():
    bands = D.all_bands([])
    assert all(b["auto_threshold"] is None for b in bands.values())
    assert D.queue([], [], bands) == []
    assert D.reviews_to_unlock([], "duplicate")["more"] is None
    assert D.normalise_compare(None) == []


def test_compare_headline_matches_the_pitch():
    c = D.normalise_compare({"verdict": "CERTIFY", "quality_pp": -0.4, "quality_lo_pp": -1.9, "quality_hi_pp": 1.1,
                             "cost_rel": -0.70, "reference": "Sonnet", "candidate": "Haiku", "step": "this step"})[0]
    assert D.compare_headline(c) == "Haiku can replace Sonnet for this step: CERTIFIED, −70% cost, quality −0.4 pts [−1.9, +1.1]"


def test_home_page_runs_on_sample_data(tmp_path, monkeypatch):
    testing = pytest.importorskip("streamlit.testing.v1")
    real = tmp_path / "data"  # no real data here, so the app defaults to sample data (in tmp, not the repo)
    monkeypatch.setattr(D, "REAL_DIR", real)
    monkeypatch.setattr(D, "SAMPLE_DIR", real / "sample")
    sample_data.generate(real / "sample", n_tickets=200)
    at = testing.AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60).run()
    assert not at.exception, at.exception
    assert at.title[0].value == "Review queue"
    assert at.sidebar.toggle[0].value is True
    assert any("SAMPLE DATA" in m.value for m in at.markdown)
    assert any("Handled automatically today" in m.value for m in at.markdown)
    accept = next(b for b in at.button if b.label == "Accept")
    accept.click().run()
    assert not at.exception, at.exception
    rows = D.load_jsonl(real / "sample" / "feedback.jsonl")
    assert len(rows) == 1 and rows[0]["decision"] == "accept"
    assert not (real / "feedback.jsonl").exists()  # never mixed into real data
    for page in ("Trust", "Try a ticket", "Model check"):
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, (page, at.exception)
        assert at.title[0].value == page


def test_bundle_splits_big_files_and_loader_reads_them(tmp_path, monkeypatch):
    import make_bundle
    src = tmp_path / "judgments.jsonl"
    import hashlib  # hex digests barely compress, so gzip alone cannot get under the limit
    rows = [{"key": f"X-{i}", "reason": hashlib.sha256(str(i).encode()).hexdigest() * 3} for i in range(3000)]
    src.write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = tmp_path / "out"
    out.mkdir()
    monkeypatch.setattr(make_bundle, "LIMIT", 20_000)  # force gzip + shards
    names = make_bundle._copy_data(src, out)
    assert len(names) > 1 and all(n.startswith("judgments.part") for n in names)
    assert D.has_data(out, "judgments.jsonl")
    assert D.load_jsonl(out / "judgments.jsonl") == rows


def test_try_a_ticket_search_runs(tmp_path, monkeypatch):
    testing = pytest.importorskip("streamlit.testing.v1")
    real = tmp_path / "data"
    monkeypatch.setattr(D, "REAL_DIR", real)
    monkeypatch.setattr(D, "SAMPLE_DIR", real / "sample")
    sample_data.generate(real / "sample", n_tickets=200)
    at = testing.AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60).run()
    at.sidebar.radio[0].set_value("Try a ticket").run()
    at.text_input[0].input("NullPointerException in SQL when decimal is empty")
    at.text_area[0].input("Running a job where decimal is empty throws an NPE.")
    at.button[0].click().run()  # the form's submit button
    assert not at.exception, at.exception
    assert at.session_state["try_state"]["hits"], "search returned nothing"


def test_timestamps_can_be_iso_or_epoch():
    import time
    today = __import__("datetime").date.today().isoformat()
    assert D._day(time.time()) == today
    assert D._day(D.now_iso()) == today
    assert D._day(None) == "" and D._day("garbage") == "garbage"[:10]
    b = {"duplicate": {"auto_threshold": 0.5, "suggest_threshold": 0.2, "segments": [
        {"band": "auto", "lower": 0.96}]}, "part_of": {"segments": []}, "related": {"segments": []}}
    rows = [{"relation": "duplicate", "confidence": 0.9, "ts": time.time()},
            {"relation": "duplicate", "confidence": 0.9, "ts": D.now_iso()}]
    assert D.auto_handled(rows, b)["today"] == 2
