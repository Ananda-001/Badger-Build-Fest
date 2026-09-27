# Assay: a proof engine for AI agents

Badger BuildFest 2026 · Applied AI & Automation · Databricks (Xorbix) + Art of the Break

Agents keep being given more freedom: act without asking, run on cheaper models, learn from corrections.
**Assay decides, with evidence, when each of those is safe**: a verdict plus an error bar, or "not proven yet, needs N more."

| # | Question | Verdicts |
|---|---|---|
| 1 | Can the agent **act alone**? | AUTO above a proven threshold / SUGGEST / QUIET |
| 2 | Can it **run cheaper**? | CERTIFY / REJECT / INSUFFICIENT |
| 3 | Did it **really learn** from a correction? | KEEP / DISCARD / UNPROVEN ("fixes N, breaks M") |

**Demo agent:** triage for the public Apache Jira (Spark, Flink, Kafka, Hive). For each new ticket it decides
whether it's a duplicate, part of an umbrella, related, or new, and it's checked against 13,687 real maintainer links.
It runs on Databricks.

## See it
- **Manager dashboard (Databricks App):** https://assay-manager-7474649367590010.aws.databricksapps.com
  (Databricks login; add `#tour` for the guided tour). Plain-words inbox, trust bars, what was held back, which
  model answered, and a button that runs the agent live. Every Yes/No is saved to a Delta table.
- **Full report:** [`docs/ASSAY_REPORT.md`](docs/ASSAY_REPORT.md) ([PDF](docs/ASSAY_REPORT.pdf)): every result,
  method, limit and number, with its source.
- **Submission kit:** [`docs/SUBMISSION_KIT.md`](docs/SUBMISSION_KIT.md): Devpost answers, video script, Break Card.

## Layout
- `assay_triage/`: the demo agent (Jira ingest, time-honest retrieval, LLM judge)
- `assay_engine/`: the statistics behind the verdicts (precision bands, auto threshold, model compare, learning gate)
- `app/manager/`: the manager dashboard (FastAPI + one page, deployed with `scripts/deploy_manager.py`)
- `app/`: the review workbench (Streamlit, deployable as a Databricks App)
- `results/`: every number we quote, with the command that produced it
- `docs/thinking/`: how our thinking evolved during the event, step by step
- `CLAUDE.md`: our rules and build plan

## Run
```bash
pip install -r requirements.txt
python -m pytest -q tests
python -m assay_triage.ingest && python -m assay_triage.retrieve --k 10   # pulls public Jira data (~no login)
python scripts/judge_eval.py --summary
streamlit run app/app.py                                                 # has a sample-data toggle
```

Development started in a local folder at 11:00 on Sep 26 at the event and was moved into this repo at ~15:30.
License: MIT.
