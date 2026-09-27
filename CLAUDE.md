# CLAUDE.md: Assay at Badger BuildFest 2026

Every Claude session (and every teammate) reads this first. It holds the rules, a map of the code, the commands,
how to work with the Databricks workspace, and what is left before the **Devpost deadline, Sun Sep 27, 11:00 CDT**.
Last updated **Sat Sep 26, 23:30 CDT**.

Read next, in this order:
- `docs/ASSAY_REPORT.md` ([PDF](docs/ASSAY_REPORT.pdf)): every result, method, limit and number, with its source.
  Section 6 = Databricks, 8.8 = the manager dashboard, 11 = commands, 13 = what we do not claim.
- `docs/SUBMISSION_KIT.md`: Devpost answers, the 2-minute video script, the Break Card, the checklist before 11:00.
- `docs/NEXT_STEPS.md`: who does what between now and submission.
- `docs/DATABRICKS_SETUP.md` (top section): getting access to the workspace. `docs/SCHEMA.md`: the data contract.

---

## 0. Hard rules (read before touching anything)

1. **No `git commit` and no `git push` without the user's explicit OK, every time.** Claude prepares the commit
   (see §5), shows it, and waits. "Looks good, commit" means commit only. Pushing needs its own "push".
   Subagents are never allowed to run git write commands (commit, push, merge, rebase, reset, checkout -- .).
   On a teammate's machine, "the user" means the human at that keyboard, but **nothing merges into `main` until
   krish has reviewed it.** Work goes on branches.
2. **Never:** force-push, amend or rebase commits that are already pushed, backdate commits (`--date`,
   `GIT_COMMITTER_DATE`), skip hooks (`--no-verify`), or rewrite history on `main`.
3. **All code is written at the event.** Organizers check the repo creation date and commit history, and
   *disqualify recycled code*. Nothing is copied from the old `C:\Users\krish\assay` repo or the overnight lab.
   Ideas and lessons carry over; code doesn't. Results from before the event are labeled "pre-event exploration".
4. **Secrets:** API keys and Databricks tokens live in a git-ignored `.env` and nowhere else. Never print, echo,
   log or commit them. Never zip `.env`. Each teammate uses **their own** Databricks token. Run the secret scan in §5
   before every commit.
5. **Money and model calls:** Claude never starts a run that costs money. Model calls on Databricks Free Edition are
   $0 but rate-limited; they are off unless `ASSAY_ALLOW_MODEL_CALLS=1`, which Claude sets **only when the user asks**.
   Anything on a paid key (OpenAI, Anthropic): Claude prepares the command, states the estimated cost, and the user
   runs it with `! <command>`. Running `claude -p` on the subscription is free but burns the usage window, so ask
   before any run of more than about 20 calls.
6. **Databricks is shared.** Deploying an app replaces it for everyone, and `sync_results.py` / `precedents.py`
   rebuild shared tables. Follow §6 before any deploy or table rebuild, and ask the user first.
7. **No Docker** on krish's laptop (it hangs the machine).
8. **Every number in the README, video or Devpost comes from a file in `results/` or a Unity Catalog table**, with
   the command that made it. Say what we could not prove (`docs/ASSAY_REPORT.md` §13). No simulated numbers, and no
   "~95%" without an interval.
9. **Talk before building anything big.** The user wants discussion first, brutal honesty, and no sudden pivots.
   The direction is locked (§1); change it only if the user asks. Close to the deadline, prefer fixing and
   polishing over new features.

---

## 1. What we are building (locked)

**Assay is an AI agent manager.** It sits between the AI agents a company already uses and the people who review
their work, and it decides, **with evidence**, how much each agent may do on its own. The engine never changed:
prove before you trust.

| # | Question | Verdicts | Where |
|---|---|---|---|
| 1 | **Act alone or ask?** | AUTO (proven) / SUGGEST / QUIET | `permissions.py`, `bands.py` (receipts, 90% target) |
| 2 | **Which model answers?** | live switching; cheap model only if certified | `router.py`, `scripts/live_route.py` |
| 3 | **Did a correction really help?** | KEEP / DISCARD / UNPROVEN ("fixes N, breaks M") | `learning.py`, `gate.py` |
| 4 | **Reuse past reviewer decisions?** | only where reviewers agree enough to prove it | `precedent.py`, `scripts/precedents.py` |

**The demo agent is triage for the public Apache Jira** (SPARK, FLINK, KAFKA, HIVE). For each new ticket it decides
whether it's a `duplicate` of an earlier ticket, `part_of` an umbrella, `related`, or `none`. It runs on
**Databricks Free Edition**. Jira is the proving ground; Assay is the product.

**The demo is the manager dashboard**, a Databricks App: https://assay-manager-7474649367590010.aws.databricksapps.com
(Databricks login; add `#tour` for the guided tour). Report §8.8 describes every panel.

**Challenges:** Applied AI & Automation track, plus **Databricks Real-World Workflows (Xorbix)** and **The Art of
the Break**. Declare them on Devpost.

---

## 2. Repo map

```
assay_triage/          the demo agent
  ingest.py            Apache Jira REST → data/tickets.jsonl + data/truth.jsonl (cache: data/raw/)
  retrieve.py          time-honest TF-IDF + "sibling vote" → data/candidates.jsonl
  judge.py             LLM judge, one call per ticket; backends cli | anthropic | openai | databricks;
                       prompt versions v1 | v2 | bad (poisoned, for the stress test)
  plans.py             frozen, hash-checked evaluation plans
  identity.py          config ids
  dbx.py               Databricks client, SQL through the warehouse, volume uploads (reads .env)
assay_engine/          the product: the statistics behind the verdicts
  bounds.py            Clopper-Pearson / Wilson one-sided bounds
  bands.py             precision bands, auto threshold (fixed-sequence walk-down), extra_needed
  permissions.py       permission receipts, can_act, needs_more
  policy.py            one action per ticket, label keys, maintainer pre-fill
  learning.py, gate.py task-level learning gate, exact sign test
  compare.py           paired bootstrap (known bug with identical outcomes; its verdict is not used anywhere)
  router.py            live model switching
  precedent.py         reuse past reviewer decisions, proven by leave-one-out
  report.py            plain-English sentences for each verdict
  local_store.py       review store (SQLite)   ·   delta_store.py: review store (Delta)
app/
  manager/             THE DEMO: manager dashboard. server.py (FastAPI API) + static/index.html (page + tour).
                       Deployed as the Databricks App "assay-manager" by scripts/deploy_manager.py
  workbench.py         review workbench (technical view), Databricks App "assay", scripts/databricks_deploy.py
  label_app.py         blind labelling page
  app.py               first Streamlit dashboard (superseded)
scripts/               judge_eval · prepare_eval · prepare_stream · run_frozen_eval · run_stage23_databricks.sh
                       · label_actions · ai_label · quick_label · spot_check · build_permissions
                       · evaluate_correction · live_route · precedents · databricks_setup · databricks_deploy
                       · sync_results (results → tables) · deploy_manager · fetch_data (data files ↔ volume)
tests/                 test_engine · test_app · test_manager · test_stage_one · test_stage_two_three: 63 tests
results/               every number we quote: hardness test, Stage 2/3 plans/runs/labels/receipts,
                       VERDICTS.md, routing policy + log, precedents
docs/                  ASSAY_REPORT (.md + .pdf) · SUBMISSION_KIT · NEXT_STEPS · DATABRICKS_SETUP · SCHEMA
                       · STAGE_ONE · STAGE_TWO_THREE · REVISED_EVENT_PLAN_V3 · thinking/ (briefs v1-v3)
```

**Not in git:** `.env`, `.venv/`, `data/raw/`, `data/tickets.jsonl`, `data/candidates.jsonl`,
`data/judgments.jsonl`, `local-state/`, `results/frozen-plan*.json`, `app/_bundle/`, `app/manager/_bundle/`.
Get the data files with `python scripts/fetch_data.py` (from the Unity Catalog volume), or rebuild them from public
Jira with `ingest` + `retrieve --all`. **In git:** code, tests, docs, `data/sample/` (fake), `data/truth.jsonl`,
`results/`.

---

## 3. Commands

`python` below means the repo's virtualenv: `.venv\Scripts\python.exe` on Windows PowerShell,
`source .venv/Scripts/activate` in Git Bash, `source .venv/bin/activate` on Linux/WSL.

```bash
pip install -r requirements.txt
python -m pytest -q                                   # must print "63 passed" (or more) before any commit
python scripts/fetch_data.py                          # data/*.jsonl from the volume (needs .env)

# the manager dashboard (the demo)
uvicorn app.manager.server:app --port 8000            # locally, against the same live tables → http://localhost:8000
python scripts/deploy_manager.py                      # deploy / redeploy the app. Read §6 first.

# Databricks results and live runs (read §6 first)
python scripts/sync_results.py                        # results/ → Unity Catalog tables (no model calls)
python scripts/precedents.py --clicks --delta         # recompute the precedent table
ASSAY_ALLOW_MODEL_CALLS=1 python scripts/live_route.py --n 12 --delta   # live routing run ($0, rate-limited)

# data and evaluation (already run; see results/)
python -m assay_triage.ingest && python -m assay_triage.retrieve --all
python scripts/judge_eval.py --summary
bash scripts/run_stage23_databricks.sh                # the honest Stage 2/3 runs
```

Quick Databricks check: `python -c "from assay_triage import dbx; print(dbx.sql('SHOW TABLES IN workspace.assay_triage'))"`
prints 12 tables. On Windows PowerShell, put multi-line Python in a file; inline quotes get mangled.

## 4. Conventions

- Plain Python 3 with stdlib + numpy / scipy / scikit-learn; FastAPI + one static page for the dashboard. No new
  frameworks without asking.
- Data is JSONL and follows `docs/SCHEMA.md`. If a field changes, update SCHEMA.md in the same commit.
- **Time-honest evaluation:** we evaluate on tickets created **≥ 2025-01-01**. Retrieval only looks at tickets
  created *earlier* than the one being judged. Never let a later ticket leak into a candidate list.
- **Honest stream:** the stream is defined before any judging (best search score ≥ 0.4575, 4,231 tickets), and plans
  are drawn from it and frozen, hash-checked. Never enrich a sample with extra positives: it fakes precision.
- **No peeking:** any prompt/rule change is designed on one sample and evaluated on a different one.
- Engine defaults: permission target 90% (one-sided lower bound), fixed AUTO cutoff 0.95, family alpha 0.05 split
  across relations (Bonferroni). Details: `docs/STAGE_TWO_THREE.md`.
- **Claims only about duplicates:** "related" and "part of" labels are too inconsistent (human–AI 2/7 and 0/2).
- Scripts append results and are resumable. Never delete `data/judgments.jsonl`; copy to `results/` to freeze.
- UI work on the dashboard follows the checklist it was built with (ui-ux-pro-max): SVG icons instead of emoji,
  visible keyboard focus, 4.5:1 text contrast, badges never rely on colour alone, works at phone width, respects
  "reduce motion". Plain words for a manager with no background in code.
- Keep comments short, like the surrounding code. Tests for engine logic; the apps get smoke tests.

---

## 5. How a commit happens (the user approves each one)

**For every commit, Claude does steps 1 to 5 and then STOPS:**
1. Run `python -m pytest -q`. It must pass.
2. Stage only the intended files, by name (`git add path/…`, never `git add -A` / `git add .`).
3. Secret and size scan on the staged diff:
   ```bash
   git diff --cached | grep -nE 'sk-ant-|sk-proj-|sk-[A-Za-z0-9]{20,}|dapi[0-9a-f]{20,}|ANTHROPIC_API_KEY=.+|OPENAI_API_KEY=.+|DATABRICKS_TOKEN=.+' && echo "STOP: secret"
   git diff --cached --stat ; git diff --cached --name-only | xargs -r du -k | sort -n | tail -5   # nothing > 5 MB
   ```
4. Show the user: the file list, a 3–6 line summary of what changed and why, the test result, the scan result,
   and the proposed message.
5. Wait. Commit only after "commit"/"yes". Push only after "push".

**Commit message format:** `<area>: <what, imperative>`, then a blank line and a short why. Areas: `ingest`,
`retrieve`, `judge`, `engine`, `app`, `eval`, `results`, `docs`, `databricks`, `repo`. End with the trailer
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` when Claude wrote the code.

**Branches:**
- `main` must always run the demo and pass the tests.
- One short-lived branch per task: `<name>/<topic>` (e.g. `mohith/dashboard-copy`). Merge through a GitHub PR that
  krish has reviewed. Docs typo fixes may go straight to `main`.
- `git pull --rebase` before pushing. Never rebase a branch someone else has pulled.
- Commit when a unit works, not one giant dump at the end. Judges read the history.

---

## 6. Working with Databricks (shared workspace)

**Workspace:** `https://dbc-f374519f-f1e1.cloud.databricks.com`, Free Edition, SQL warehouse `6de382ea82d4b218`.
`.env` needs `DATABRICKS_HOST`, `DATABRICKS_WAREHOUSE_ID` and your own `DATABRICKS_TOKEN`. Access steps are at the
top of `docs/DATABRICKS_SETUP.md`.

**What lives where** (Unity Catalog `workspace.assay_triage`, owned by krish, `guruvayoorra@wisc.edu`):

| What | Where |
|---|---|
| Inputs | tables `tickets` (37,853), `truth`, `candidates`, `judgments`, `stream`; files in `/Volumes/workspace/assay_triage/data` |
| Results (from `sync_results.py`) | `proposals`, `past_decisions`, `verdicts`; `precedents` (from `precedents.py --delta`) |
| Live, written by the apps | `actions` (every Yes / No), `routing_log` (model switching), `live_proposals` |
| Manager dashboard (the demo) | app `assay-manager`, code `app/manager/`, deploy `scripts/deploy_manager.py` |
| Review workbench | app `assay`, code `app/workbench.py`, deploy `scripts/databricks_deploy.py` |
| Models | Foundation Model APIs: Llama 3.3 70B (main), Llama 3.1 8B (not certified), Qwen3-Next 80B and gpt-oss 120B (backups). No Claude on Free Edition. |

**Permissions a teammate needs:** `USE CATALOG` on `workspace`; `USE SCHEMA, SELECT, MODIFY, CREATE TABLE,
READ VOLUME, WRITE VOLUME` on the schema; `CAN_USE` on the warehouse; `CAN_MANAGE` on both apps. **Also `MANAGE` on
the schema** for anyone who deploys or rebuilds tables: `deploy_manager.py` runs `GRANT`s for the app's service
principal, and `sync_results.py` / `precedents.py` use `CREATE OR REPLACE TABLE` on tables krish owns. Without it
they fail partway (deploy uploads the files, then stops at the `GRANT`). Grant `MANAGE` explicitly by name.

**Before any deploy (`deploy_manager.py` or `databricks_deploy.py`), Claude:**
1. Pulls `origin/main` and makes sure the local branch has everything that is live.
2. Compares the local `app/manager/server.py` and `static/index.html` with the live app's active deployment
   (`w.apps.get("assay-manager").active_deployment.source_code_path`, then download those two files). If the live
   copy has changes the local copy doesn't, **stop and tell the user**: deploying would erase a teammate's work.
3. Runs the tests, tells the user who deployed last and when, and deploys only after the user says so.

Why: `deploy_manager.py` uploads the deployer's own local files to `/Workspace/Users/<their email>/assay-manager-app`
and redeploys from there, replacing the whole app. **Whoever deploys last wins.** Deploying does not touch GitHub,
and pushing to GitHub does not update Databricks. Agree in the team chat who deploys.

**Free Edition limits we hit:** apps stop **24 h after a deploy** (redeploy Sunday morning before the demo); HTTP 429
on Llama 70B when 5–16 requests run at once; the gateway usage tables can't be read (we log token counts ourselves);
fallback routing exists only for external models (our router does it in code).

---

## 7. Known facts and numbers (source: `docs/ASSAY_REPORT.md`, Appendix B and §8)

| | |
|---|---|
| Real tickets (since 2023) | 37,853; 13,687 maintainer links as truth (part_of 11,726, related 1,500, duplicate 461) |
| Duplicate closures never linked to the original | 48% |
| Duplicate tickets in the 2025+ window | 142 (≈0.8% of the stream) |
| Model calls on Databricks | 360 evaluation + 105 labelling + 42 routed; $0 (Free Edition) |
| Cheap model (Llama 8B) "95% sure" duplicates that were right | 4 of 19 (21%) → QUIET; 10 of 90 answers unusable |
| Llama 70B | SUGGEST: 2 actions at the cutoff (1 right); part_of needs ~38 more |
| Poisoned correction ("version upgrades are duplicates") | fixed 0, broke 16 → DISCARD (p = 1.5×10⁻⁵) |
| Prompt v2 | fixed 3, broke 3 → UNPROVEN |
| Human–AI label agreement | 11/20 overall; duplicates 8/9 |
| Checks needed with Assay vs checking everything | 105 vs 360 (−71%) |
| Live switches observed | 1 (Llama 70B busy → Qwen 80B, held for review) |
| Strongest precedent | 21 of 21 rejections (version-upgrade look-alikes); ≈8 reviews from proven at 90% |
| First hardness test (Claude CLI, diagnostic only) | Haiku REJECTED: +90.5% cost from hidden thinking tokens |
| Tests | 63 passing |

Verdicts in one page: `results/stage-2-3-runs/VERDICTS.md`. Pre-event exploration (label it as such if quoted):
switching models mid-conversation cost 4.1×; parallel subagents each start cold.

**What we do not claim** (report §13): no model has earned the right to act alone; cost certification is not
claimed; "related"/"part of" labels are unreliable; precedent reuse is not proven at 90% ("Handled for you" is empty);
the agent loop runs from a laptop, not yet as a Databricks job; four Apache projects only.

---

## 8. What's left before 11:00 Sunday

The detailed checklist is `docs/SUBMISSION_KIT.md` §4; the handoff is `docs/NEXT_STEPS.md`.
- [ ] Teammates click through the dashboard (tour, a few answers, one "Check new tickets now") and report confusion.
- [ ] Redeploy the dashboard Sunday morning (§6), open it once to wake the warehouse.
- [ ] Record the 2-minute video (script in the submission kit).
- [ ] Devpost: paste the kit's answers, add repo + video links, declare Xorbix + Art of the Break.
- [ ] Three mentor visits logged; Break Card attached.
- [ ] **10:30 code freeze**; tag `v1.0-submission` only with the user's OK. **10:45 submit.**
- [ ] Rotate every API key that was pasted into a chat.

Not before the deadline (report §14): the scheduled Databricks job, the live precedent switch-on demo.
