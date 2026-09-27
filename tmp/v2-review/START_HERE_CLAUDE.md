# START HERE: handover to the teammate's Claude (Sat Sep 26, 16:00)

You are joining a 3-person team at **Badger BuildFest 2026** (UW-Madison) mid-hackathon. The previous Claude
session (krish's) is out of usage. This file brings you to exactly where it stopped. **Read all of it before you
touch anything.** Then read `CLAUDE.md` (rules + plan) and `docs/thinking/03-brief-v3-fact-check.md` (current
thinking). Then start at §8 ("Your first tasks").

---

## 1. The clock
- Now: Sat ~16:00. **Devpost submissions close Sun Sep 27, 11:00.** Aim to submit at 10:45; code freeze 10:30.
- Finalists demo live Sun 13:00–15:00. Challenges (ours: Databricks/Xorbix + Art of the Break) are **judged online**,
  and winners are announced Sep 30, so the **2-minute video** carries the challenge demos.
- Devpost needs: GitHub repo + short README, 2-min video, the required answers, one track + up to two challenges,
  **"your three visits"** (mentors/orgs visited + one thing learned each), and a Break Card (for Art of the Break).
- Track judges look for: problem & user insight, solution fit, **technical execution ("is it actually working?")**,
  demo & communication, innovation & differentiation, real-world potential.

## 2. Hard rules (non-negotiable)
1. **Organizer rule:** "The code should be new … using someone else's code or recycling a previous project verbatim
   = disqualified. We review repo creation date and commit history." And: "**Commit early and often.**"
   → Write all code fresh here. Never copy code from anywhere pre-event (krish has an old `assay` repo and an
   "overnight lab"; ideas from them are fine, code is not). `context/` in this package has pre-event *reports* for
   reading only. Never put them in the repo.
2. **Commits:** your human approves each commit. The team agreed commits go straight to **`main`** now (no `wip`).
   Always `git pull --rebase` before `git push`. Never force-push, amend pushed commits, or backdate. Stage files
   **by name** (no `git add -A`). Before each commit, scan: `git diff --cached | grep -E 'sk-ant-|sk-proj-|dapi[0-9a-f]{20}'`
   must print nothing, and no staged file over 5 MB.
3. **Secrets:** keys live only in a git-ignored `.env`. Never print, echo or commit them.
4. **Money:** never start a paid run on your own. State the command + estimated cost; your human runs it.
5. **Every number** in the README/video/Devpost must come from a file in `results/` with the command that made it.
   Say what we could not prove. No made-up or simulated numbers.
6. **Don't pivot.** The direction is locked (§3). The team (krish especially) hates sudden changes of direction;
   discuss before any big design change.
7. Don't use Docker on krish's laptop (it hangs). Fine on yours if you want.

## 3. What we are building (locked)
**Assay is a proof engine that decides, with evidence, when an AI agent can be given more freedom.**
Pitch: *"Databricks collects the evidence and enforces the rules. Assay decides what the rules should be."*

| # | Question | Verdicts | Code |
|---|---|---|---|
| 1 (lead) | Can the agent **act alone**? | AUTO above a proven threshold / SUGGEST / QUIET / "needs N more" | `assay_engine.auto_threshold`, `precision_bands` |
| 2 | Can it **run cheaper**? | CERTIFY / REJECT / INSUFFICIENT | `assay_engine.compare_models` |
| 3 | Did a correction **really help**? | KEEP / DISCARD / UNPROVEN ("fixes N, breaks M") | `assay_engine.gate_change` |

**The demo agent (our test case, not the product):** triage for the public Apache Jira (SPARK, FLINK, KAFKA, HIVE).
For each new ticket it decides whether it's a **duplicate** of an earlier ticket, **part_of** an umbrella ticket,
**related**, or **none**. Ground truth = links that the Apache maintainers made. We don't write to Apache's Jira:
"acting" means writing links to our own table.
**Why this fits Xorbix:** their prompt is "an agent on Databricks that reads, decides, acts and improves when a
human corrects it", with *organizational knowledge capture* as a suggested direction. 48% of tickets closed as
duplicates never link to their original, so that knowledge is lost. Our agent recovers it, and Assay governs how far
it may act.

**How we got here** (so you don't re-suggest dead ends): cost control plane → "certify cheaper models" (the original
Assay) → pre-event experiments showed every model scored 100% on clean synthetic tasks (useless for proving
anything) → Databricks already routes models automatically but doesn't prove quality → so we kept the engine
and gave it a real, messy task with real ground truth. Atlassian Rovo already suggests duplicates, which is why the
agent isn't the product.

## 4. Repo tour (`main` on GitHub = what's in this folder)
```
assay_triage/ingest.py     Apache Jira REST → data/tickets.jsonl + data/truth.jsonl (cache in data/raw/, not included)
assay_triage/retrieve.py   time-honest TF-IDF shortlist + "sibling vote" → data/candidates.jsonl; prints recall@k
assay_triage/judge.py      LLM judge; one call judges all candidates of one ticket. SYSTEM + RULES prompt.
                           call(prompt, model, backend): backends cli (claude -p, lean flags) | anthropic | openai | databricks
scripts/judge_eval.py      stratified sample → judge → grade vs truth → append data/judgments.jsonl; --summary, --dry-run
assay_engine/bounds.py     Clopper-Pearson / Wilson one-sided bounds (lower_bound, lower_bound_array)
assay_engine/bands.py      precision_bands(_by_relation), auto_threshold(_by_relation), extra_needed
assay_engine/compare.py    compare_models(pairs, margin=0.02, alpha=0.05, n_boot=2000, min_n=30)
assay_engine/gate.py       gate_change(before, after): exact sign test; returns fixed/broke items, verdict, need_n
assay_engine/report.py     plain-English sentences: describe_threshold / describe_compare / describe_gate
app/                       Streamlit review app (pages: Review queue, Trust, Try a ticket, Model check); Databricks App
                           config in app.yaml; make_bundle.py splits data under the 10 MB-per-file Apps limit
tests/                     test_engine.py (30), test_app.py (10). All 40 pass.
results/2026-09-26-hardness-60/   first real results + summary.md
docs/SCHEMA.md             the JSONL data contract; read it
docs/DATABRICKS_SETUP.md   Free Edition step-by-step (workspace, volume, tables, endpoints, App deploy)
docs/NEXT_STEPS.md         the earlier handoff (Tracks A–E); Track B is done. §8 below supersedes it where they differ
docs/thinking/             briefs v1 → v2 → v3: how the idea evolved (the judges read the history)
```
**Data files** (git-ignored, included in this package under `data/`): `tickets.jsonl` (37,853 tickets since 2023),
`candidates.jsonl` (14,910 eval tickets), `judgments.jsonl` (656 judged pairs). `truth.jsonl` (13,687 pairs) is in git.

## 5. Setup (10 min)
```bash
cd Badger-Build-Fest
python3 -m venv .venv && source .venv/bin/activate       # Python 3.11+
pip install -r requirements.txt
python -m pytest -q tests                                # expect: 40 passed
python scripts/judge_eval.py --summary                   # expect: 656 pairs, Haiku 53.4%, Sonnet 55.8%
streamlit run app/app.py                                 # try the sample toggle on and off
```
If you cloned from GitHub instead of unzipping, copy `data/tickets.jsonl`, `data/candidates.jsonl` and
`data/judgments.jsonl` from this package into `data/`, or rebuild them for free:
`python -m assay_triage.ingest` (network, some minutes), then `python -m assay_triage.retrieve --k 10`.
`.env` (never commit it) holds `ANTHROPIC_API_KEY`, `DATABRICKS_HOST=https://…` and `DATABRICKS_TOKEN`. Scripts
don't auto-load it, so run `set -a; source .env; set +a` first.
The `cli` backend runs `claude -p` on a Claude subscription ($0 but uses the usage window). It needs the `claude`
CLI logged in, and it strips `ANTHROPIC_API_KEY` from the environment so the subscription is used.

## 6. What we know (real results, Sep 26)
- **Data:** 16,919 tickets created 2025+ (the evaluation window; SPARK 9,073). Truth pairs: part_of 11,726, related
  1,500, duplicate 461. In the 2025+ eval set: **only 142 duplicate tickets**, 6,810 part_of, 503 related.
- **Retrieval recall@10 (2025+):** duplicate 72.5%, part_of 57.2% (13.6% before the sibling vote), related 49.4%.
  Caveat: the sibling vote reads a sibling's parent from today's data, which is slightly optimistic.
- **Hardness test** (60 tickets, 15 per class, 328 pairs per model, `cli` backend): see
  `results/2026-09-26-hardness-60/summary.md`.
  - Duplicate/part_of precision 50–67%; related ~8% → related stays QUIET.
  - Both models are **overconfident on part_of**, most likely mistaking a *sibling* subtask for the *umbrella*.
  - compare_models: Haiku vs Sonnet = **REJECT, +90.5% cost**. Haiku burned ~1,700 hidden thinking tokens per call
    through Claude Code, while Sonnet used 0. **This is about our setup, not the model:** on the plain API Haiku
    doesn't think unless asked. Must re-run with thinking off before claiming anything.
  - No auto zone is proven yet (n too small). The most confident duplicate calls were 86% right (n=7) for Haiku and 100% (n=5) for Sonnet.

## 7. Traps we found (don't fall in)
1. **Base-rate trap.** `retrieve.py` builds `candidates.jsonl` from *all* 2025+ tickets that have a truth link plus
   an **equal-sized random sample** of those without one. `judge_eval.py` then stratifies further (15/15/15/15). On
   the real stream, only ~0.8% of tickets (142/16,919) have a duplicate. **Precision measured on an enriched sample is
   inflated, so an auto zone "proven" on it is fake.** Fix (decided in v3 §4): define the stream as *tickets whose
   top retrieval score ≥ s* (s fixed **before** judging), and sample **uniformly at random** from that stream over
   **all** 16,919 tickets. The proof then holds for exactly the stream the agent acts on.
2. **Not enough duplicates.** Proving ≥90% precision at one-sided 95% with the engine's default (two walks, alpha
   split) takes **36/36, or 54 with 1 mistake** (29/46 for a single walk). With ~100 findable duplicates that's
   unlikely. Expect: a proven zone for **part_of** (after the prompt fix), and "needs N more" for duplicates. Both
   are honest results. For more duplicates at $0: add projects to ingest (HADOOP, HBASE, CASSANDRA, BEAM, AIRFLOW)
   and/or start the eval window at 2024-07.
3. **Non-independence.** Count one decision per ticket (its top call), and one cluster per umbrella; siblings under
   the same umbrella aren't independent evidence.
4. **Maintainer links are a floor** (they miss real duplicates). If humans "rescue" wrong-looking calls, they review
   blind (without seeing the model's confidence).
5. **No peeking.** Prompt changes were designed on the seed-0 sample, so evaluate them on **fresh tickets**
   (`--seed 1`, excluding keys that are already judged).
6. **Resume-key bug to fix:** `judge_eval.py` skips `(key, model)` pairs that are already done, so a run with a new
   prompt version would silently skip everything. The key must include the prompt version.
7. The hardness test used the `cli` backend. Its `cost_usd` comes from Claude Code (1-hour cache writes at 2×, hidden
   thinking), so it's not API list price. Keep that separate when quoting costs.

## 8. Your first tasks (in order; ask your human before anything that costs money)
**Suggested split** (confirm with krish): **you = engine + eval (items 1–4)**. krish/others = Databricks, app, story.
Work only in your files to avoid merge conflicts, and commit after each item.

1. **Prompt v2 + the learning gate** (question 3, the heart of the Xorbix challenge). Spec in `docs/NEXT_STEPS.md`
   Track D, plus the resume-key fix (§7.6).
   - `RULES_V2`: a sibling isn't the umbrella; related only for a concrete technical link.
   - `RULES_BAD`: a poisoned correction ("anything mentioning a version bump is a duplicate"), used for Art of the Break.
   - `--prompt v1|v2|bad`; a `prompt` field on each row; resume key `(key, model, prompt)`; `--fresh` excludes studied keys.
   - A new `scripts/gate_eval.py` (before/after → `gate_change` + `report.describe_gate` + per-relation precision).
   - Tests with a monkeypatched `judge.call`; update `docs/SCHEMA.md`.
   - Then *propose* the run (your human runs it): Sonnet × {v1, v2, bad} × 60 fresh tickets = 180 calls.
2. **Honest sampling** (§7.1–7.3).
   - `retrieve.py --all`: candidates for every 2025+ ticket (16,919; TF-IDF only, free). Keep the current mode as the default.
   - `judge_eval.py --stream-min-score s --n N`: a uniform random sample from tickets whose top candidate score ≥ s.
     Print the stream size and the class mix.
   - In the engine, a helper that keeps one decision per ticket (the highest-confidence non-none call) and clusters
     siblings by umbrella. Add tests.
3. **A7 calibration table:** for each relation, bins of stated confidence vs actual precision (with CP intervals).
   A new function in `assay_engine/` + tests. It feeds the Break Card and the Trust page.
4. **A1 "earned autonomy":** `assay_engine/permissions.py` turns `auto_threshold_by_relation` results into rows
   `{relation, mode: auto|suggest|quiet, threshold, n, k, lower, target, alpha, evidence_keys, computed_at}` →
   `results/permissions.json` (later a Unity Catalog table `assay.permissions`).
   - `can_act(relation, confidence) → (mode, reason)`.
   - **Receipts (A6):** each row lists the ticket keys that proved it.
   - Also a short SQL template in `docs/` for a Unity Catalog function that reads the table. Contextual Service
     Policies (Databricks Beta) are SQL UC functions, which is our production story.
5. **Then the scale run** (your human runs it; ~$3–8): ~300 tickets from the honest stream, Sonnet + Haiku-with-thinking-off
   (via `--backend anthropic`, where Haiku doesn't think by default), prompt v2 → auto_threshold, compare_models,
   permissions. Freeze everything in `results/<date>-scale/` with a summary.md.

**Tiering if time runs short:** Must = 1, 3, 4 (+ the gate run). Should = 2 + the scale run. Could = PPI (judge + human
labels with an interval) and a re-check over time. **Never cut:** the gate demo, honest intervals, passing tests, the video.

## 9. Databricks facts (checked against the docs today)
- Free Edition: up to 3 Apps, **each stops 24 h after start/redeploy** (redeploy Sun morning before recording).
  Knowledge Assistant is unsupported. One AI Search endpoint. Foundation Model APIs exist, but "certain models" aren't
  available. Outbound internet is limited to trusted domains, and **LinkedIn verification unlocks it**.
- Expected endpoint names (unconfirmed on Free Edition): `databricks-claude-haiku-4-5`, `databricks-claude-sonnet-*`,
  `databricks-gpt-oss-20b/120b`, `databricks-gte-large-en`. The `databricks` backend = OpenAI-compatible
  `DATABRICKS_HOST/serving-endpoints`.
- `system.ai_gateway.usage.token_details` has `cache_read_input_tokens`, `cache_creation_input_tokens` and
  `output_reasoning_tokens`, but **no dollar column** (useful for question 2 on Databricks).
- Unity AI Gateway can route Claude Code (`ug claude --provider <catalog>.<schema>.<name> --workspace https://<host>`)
  and Gemini CLI (`GEMINI_MODEL=system.ai.gemini-2-5-flash`, `GOOGLE_GEMINI_BASE_URL=https://<host>/ai-gateway/gemini`,
  bearer = PAT). This is untested. Gemini could become a third model family, *if* it answers through `/serving-endpoints`.
- MLflow 3 `mlflow.log_feedback()` stores human feedback on traces (Free Edition support unknown). There's an open
  request, mlflow#26193, for paired significance tests in eval comparison: MLflow compares means only, and Assay
  fills that gap.

## 10. Open items (not yours unless your human says so)
- Was the team/track/challenge declaration filed? It was due Sat noon. Someone must confirm with the organizers.
- Questions for Xorbix: Free Edition models + rate limits, the usage table, Review App/MLflow feedback, service policies, whether the video is enough.
- The Anthropic key krish pasted in chat earlier must be rotated.
- The Break Card, the video, the Devpost answers and the three mentor visits: story owner.

## 11. How krish likes to work (so you match the team)
Discuss before building anything big. Brutal honesty, no hype. Plain language in docs, since teammates read them.
Small, reviewable commits. Save progress often (usage limits hit without warning). When you finish an item,
append a line to the **Log** at the bottom of `docs/NEXT_STEPS.md`: time, who, what, where the result is.
