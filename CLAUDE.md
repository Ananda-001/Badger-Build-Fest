# CLAUDE.md: Assay at Badger BuildFest 2026

Every Claude session (and every teammate) reads this first. It holds the rules, a map of the code, the commands,
and the build + commit plan from **Sat Sep 26, 15:00** to the **Devpost deadline, Sun Sep 27, 11:00**.
Details of the idea: `docs/TEAM_BRIEF.md`. Data contract: `docs/SCHEMA.md`.

---

## 0. Hard rules (read before touching anything)

1. **No `git commit` and no `git push` without the user's explicit OK, every time.** Claude prepares the commit
   (see §5), shows it, and waits. "Looks good, commit" means commit only. Pushing needs its own "push".
   Subagents are never allowed to run git write commands (commit, push, merge, rebase, reset, checkout -- .).
   On a teammate's machine, "the user" means the human at that keyboard, but **nothing merges into `main` until
   krish has reviewed it.** Work goes on branches. The current handoff steps are in `docs/NEXT_STEPS.md`.
2. **Never:** force-push, amend or rebase commits that are already pushed, backdate commits (`--date`,
   `GIT_COMMITTER_DATE`), skip hooks (`--no-verify`), or rewrite history on `main`.
3. **All code is written at the event.** Organizers check the repo creation date and commit history, and
   *disqualify recycled code*. Nothing is copied from the old `C:\Users\krish\assay` repo or the overnight lab.
   Ideas and lessons carry over; code doesn't. Results from before the event are labeled "pre-event exploration".
4. **Secrets:** API keys live in a git-ignored `.env` and nowhere else. Never print, echo, log or commit them.
   Never zip `.env`. Run the secret scan in §5 before every commit.
5. **Money:** Claude never starts a run that costs money. Claude prepares the command, states the estimated cost,
   and the user runs it with `! <command>`. Running `claude -p` on the subscription is free but burns the usage
   window, so ask before any run of more than about 20 calls.
6. **No Docker** on this laptop (it hangs the machine).
7. **Every number in the README, video or Devpost comes from a file in `results/`** with the command that made it.
   Say what we could not prove. No simulated numbers, and no "~95%" without an interval.
8. **Talk before building anything big.** The user wants discussion first, brutal honesty, and no sudden pivots.
   The direction is locked (§1); change it only if the user asks.

---

## 1. What we are building (locked: "Path B")

**Assay is a proof engine that decides, with evidence, when an AI agent can be given more freedom.**

| # | Question | Verdicts | Engine function |
|---|---|---|---|
| 1 | Can the agent **act alone**? | auto / suggest / quiet | `auto_threshold`, `precision_bands` |
| 2 | Can it **run cheaper**? (the original idea) | CERTIFY / REJECT / INSUFFICIENT | `compare_models` |
| 3 | Did it **really learn** from a correction? | KEEP / DISCARD / UNPROVEN ("fixes N, breaks M") | `gate_change` |

**The demo agent is triage for the public Apache Jira** (SPARK, FLINK, KAFKA, HIVE). For each new ticket it decides
whether it's a `duplicate` of an earlier ticket, `part_of` an umbrella, `related`, or `none`. It runs on
**Databricks**. **We did not pivot to "a Jira project"**: Jira is the proving ground, and Assay is the product.

**Challenges:** Applied AI & Automation track, plus **Databricks Real-World Workflows (Xorbix)** and **Art of the
Break**. Declare them by Sun morning.

---

## 2. Repo map

```
assay_triage/          the demo agent
  ingest.py            Apache Jira REST → data/tickets.jsonl + data/truth.jsonl (cache: data/raw/)
  retrieve.py          time-honest TF-IDF + "sibling vote" → data/candidates.jsonl; prints recall@k
  judge.py             LLM judge. One call judges all candidates of one ticket.
                       Backends: cli (claude -p, lean) | anthropic | openai | databricks
assay_engine/          the product: the statistics behind the verdicts
  bounds.py            Wilson / Clopper-Pearson one-sided bounds
  bands.py             precision_bands(_by_relation), auto_threshold(_by_relation) (sequential walk-down), extra_needed
  compare.py           compare_models: paired bootstrap, margin 0.02, alpha 0.05, min_n 30
  gate.py              gate_change: exact sign test (McNemar) on before/after, per item
  report.py            plain-English sentences for each verdict
scripts/judge_eval.py  hardness test: stratified sample → judge → grade → data/judgments.jsonl (resumable)
app/                   Streamlit review app, deployable as a Databricks App
  app.py               pages: Review queue · Trust · Try a ticket · Model check
  app_data.py          loads data (local files or a Unity Catalog volume), writes feedback.jsonl
  sample_data.py       generates FAKE "[sample]" data in data/sample/ for UI work
  make_bundle.py       builds app/_bundle/ (gzip/shard for the 10 MB-per-file Apps limit)
tests/                 test_engine.py (30) + test_app.py (10). All 40 must pass before any commit.
docs/                  SCHEMA.md (data contract), TEAM_BRIEF.md, DATABRICKS_SETUP.md
results/               (to create) every number we quote, plus the exact command that produced it
```

**Not in git:** `.env`, `data/raw/` (131 MB cache), `data/tickets.jsonl` (41 MB), `data/candidates.jsonl` (8.7 MB),
`app/_bundle/`. Teammates get the data by running `ingest` + `retrieve`, or from `Downloads\Assay\event-workbench-*.zip`.
**In git:** code, tests, docs, `data/sample/` (fake, 1.4 MB), `data/truth.jsonl` (1.3 MB), and `results/`.

---

## 3. Commands

```bash
# Python lives in ~/.venvs/assay (Python 3, numpy, scipy, scikit-learn, streamlit, openai, databricks-sdk)
PY=~/.venvs/assay/bin/python

$PY -m assay_triage.ingest                       # --projects SPARK,FLINK,KAFKA,HIVE --since 2023-01-01 (cached)
$PY -m assay_triage.retrieve --k 10              # --since 2025-01-01 = the evaluation window
$PY scripts/judge_eval.py --models haiku,sonnet --n 60 --k 5 --workers 4    # --backend cli|anthropic|openai|databricks
$PY scripts/judge_eval.py --dry-run ...          # shows the sample and the call count; spends nothing
$PY scripts/judge_eval.py --summary              # per-model, per-relation precision/recall
$PY -m pytest -q tests                           # must print "40 passed" (or more)
~/.venvs/assay/bin/streamlit run app/app.py      # local app; has a sample-data toggle
$PY app/make_bundle.py                           # Databricks App bundle → app/_bundle/
```

## 4. Conventions

- Plain Python 3 with stdlib + numpy / scipy / scikit-learn. No new frameworks without asking.
- Data is JSONL and follows `docs/SCHEMA.md`. If a field changes, update SCHEMA.md in the same commit.
- **Time-honest evaluation:** we evaluate on tickets created **≥ 2025-01-01**. Retrieval only looks at tickets
  created *earlier* than the one being judged. Never let a later ticket leak into a candidate list.
- **No peeking:** any prompt/rule change is designed on one sample and evaluated on a **different seed**
  (`--seed 1`, `--seed 2` …). Record which seed was used for what in `results/`.
- Engine defaults: alpha 0.05, precision target 0.95 (demo also shows 0.90), compare margin 0.02, min_n 30.
- Scripts append results and are resumable. Never delete `data/judgments.jsonl`; copy to `results/` to freeze.
- Keep comments short, like the surrounding code. Tests for engine logic; the app gets smoke tests.

---

## 5. How a commit happens (the user approves each one)

**Where we work from now on:** clone the team repo to `C:\Users\krish\Badger-Build-Fest`
(`/mnt/c/Users/krish/Badger-Build-Fest`) and work there. The old workbench `assay-triage` becomes a read-only
archive. Its local commit `4021d65` is **not** pushed; the files are copied over instead.

**For every commit, Claude does steps 1 to 5 and then STOPS:**
1. Run `$PY -m pytest -q tests`. It must pass.
2. Stage only the intended files, by name (`git add path/…`, never `git add -A` / `git add .`).
3. Secret and size scan on the staged diff:
   ```bash
   git diff --cached | grep -nE 'sk-ant-|sk-proj-|sk-[A-Za-z0-9]{20,}|dapi[0-9a-f]{20,}|ANTHROPIC_API_KEY=.+|DATABRICKS_TOKEN=.+' && echo "STOP: secret"
   git diff --cached --stat ; git diff --cached --name-only | xargs -r du -k | sort -n | tail -5   # nothing > 5 MB
   ```
4. Show the user: the file list, a 3–6 line summary of what changed and why, the test result, the scan result,
   and the proposed message.
5. Wait. Commit only after "commit"/"yes". Push only after "push".

**Commit message format:** `<area>: <what, imperative>`, then a blank line and a short why. Areas: `ingest`,
`retrieve`, `judge`, `engine`, `app`, `eval`, `results`, `docs`, `databricks`, `repo`. End with the trailer
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` when Claude wrote the code.

**Branches (3 people, 20 hours: keep it simple):**
- `main` must always run the demo and pass the tests.
- One short-lived branch per task: `<name>/<topic>` (e.g. `krish/prompt-v2`). Merge through a GitHub PR that a
  teammate has glanced at. Docs typo fixes may go straight to `main`.
- `git pull --rebase` before pushing. Never rebase a branch someone else has pulled.
- Commit when a unit works (every 1–2 hours), not one giant dump at the end. Judges read the history.

**Honesty about history:** the workbench code was written today between 11:00 and 15:00 at the event. Committing
it now in logical chunks with the real timestamps is honest. The README says: "Development started in a local
folder at 11:00 on Sep 26 and was moved into this repo at ~15:00."

---

## 6. Build plan (Sat 15:00 → Sun 11:00)

Roles (3 people, 4 hats; assign names in the team chat): **Engine** (stats + experiments), **Data** (Jira, runs,
results), **Platform** (Databricks), **Story** (README, Break Card, video, Devpost). Someone wears two hats.

### Phase 0: Move into the team repo (Sat 15:00–16:00). Owner: user + Claude
- [ ] Clone `Ananda-001/Badger-Build-Fest` to `C:\Users\krish\Badger-Build-Fest`.
- [ ] Copy code, tests and docs from the workbench (not `.git`, `data/raw`, big data, `__pycache__`, `.pytest_cache`).
- [ ] Merge `.gitignore` (root + app), add a root `requirements.txt` from the real imports, rewrite `README.md`.
- [ ] Leave out `docs/HANDOFF.md` (personal notes about the local machine) or trim it first.
- [ ] Prepare these commits **one at a time for review** (§5):

| # | Message | Files |
|---|---|---|
| C1 | `repo: README, gitignore, requirements, data contract, CLAUDE.md` | README.md, .gitignore, requirements.txt, docs/SCHEMA.md, CLAUDE.md |
| C2 | `ingest: pull Apache Jira tickets and maintainer links` | assay_triage/__init__.py, ingest.py |
| C3 | `retrieve: time-honest TF-IDF shortlist with sibling vote` | assay_triage/retrieve.py |
| C4 | `judge: one-call LLM judge with cli/anthropic/openai/databricks backends` | assay_triage/judge.py, scripts/judge_eval.py |
| C5 | `engine: precision bands, auto threshold, model compare, learning gate` | assay_engine/, tests/test_engine.py |
| C6 | `app: review app with queue, trust, try-a-ticket, model check` | app/ (no _bundle), data/sample/, tests/test_app.py |
| C7 | `results: hardness test, 60 tickets × Haiku/Sonnet` | results/2026-09-26-hardness-60/ (judgments.jsonl, summary.md with the command + numbers) |
| C8 | `docs: team brief and Databricks setup` | docs/TEAM_BRIEF.md, docs/DATABRICKS_SETUP.md |

- [ ] Push after the user says "push". Teammates pull and run the tests.
- [ ] **Someone asks Xorbix:** which Free Edition models and embeddings are enabled, the rate limits, whether PATs
  work, the default catalog, whether notebooks/Apps can reach the internet, and whether there are credits.

**Done when:** `main` on GitHub has C1–C8, a fresh clone passes the tests, and teammates can run the app on sample data.

### Phase 1: Learning demo + the cheaper-model question (Sat 16:00–19:00)
**1a. Prompt v2 through the learning gate (Engine).** Q3 is the heart of the Xorbix challenge ("improves when corrected").
- [ ] Add `RULES_V2` in `judge.py`, selected with `--prompt v1|v2` (the default stays v1). Two corrections:
  "a sibling subtask is not the umbrella: pick the parent only if the new ticket is a piece of it", and
  "related is suggest-only; say none unless the link is concrete".
- [ ] Evaluate v1 and v2 on the **same fresh tickets** (`--seed 1`, not the 60 we studied), then run
  `gate_change(before, after)` per pair → "fixes N, breaks M → KEEP/DISCARD/UNPROVEN".
- [ ] Also run one **deliberately bad correction** (e.g. "treat every version-bump ticket as a duplicate") and show
  the gate DISCARDs it. That is Art of the Break material.
- [ ] Record the result in `results/…-gate-v2/`. Commit (after review): `judge: prompt v2…`, `results: gate v1→v2`.

**1b. Haiku with thinking off (Engine).**
- [ ] Be precise about the finding: the ~1,700 hidden thinking tokens per call were measured **through Claude Code
  (`claude -p`)**. On the plain API, Haiku 4.5 doesn't think unless asked. Rerun both ways:
  CLI with thinking disabled (verify that `usage` shows no thinking tokens; `MAX_THINKING_TOKENS=0` is a guess
  until verified) and the `anthropic` backend.
- [ ] `compare_models`: Haiku (no thinking) vs Sonnet → CERTIFY / REJECT / INSUFFICIENT, with cost per task.
- [ ] The honest story either way: "the cheap model is only cheap if you control how it runs; Assay caught it."

**1c. Databricks workspace (Platform), in parallel.** Follow `docs/DATABRICKS_SETUP.md`.
- [ ] Workspace up, a PAT in `.env`, `tickets` / `truth` / `candidates` / `judgments` loaded as Unity Catalog tables,
  and a volume `/Volumes/workspace/assay_triage/data`.
- [ ] Smoke test: `judge_eval.py --backend databricks --models databricks-claude-haiku-4-5 --n 4` (or gpt-oss if Claude isn't enabled).

**Done when:** a gate verdict on fresh tickets, a compare verdict with thinking off, and a Databricks endpoint answering.

### Phase 2: Evidence at scale (Sat 19:00–Sun 01:00)
- [ ] **~300 fresh tickets** stratified duplicate / part_of / none (use all the 2025+ duplicates there are),
  `--k 5`, with Sonnet + Haiku-no-think, prompt v2. That's about 600 calls. List-price estimate: about
  $0.011/ticket for Sonnet, i.e. **~$3–8 in total**. The user runs it with `!` on the API key (or Databricks, if the
  free tier allows). Do `--dry-run` first.
- [ ] Run `auto_threshold_by_relation` at 0.95 and 0.90 → is there a **proven** auto zone for duplicates? If not,
  say how many more labels (`extra_needed`) it would take. Both answers are fine; making one up is not.
- [ ] `compare_models` on the big sample. Freeze everything in `results/…-scale-300/`.
- [ ] **Databricks App (Platform):** `make_bundle.py`, deploy, point it at the volume, and check that feedback clicks
  land in `feedback.jsonl` in the volume. Apps last 24 h on Free Edition, so **redeploy on Sun morning** before the demo.

**Done when:** the Trust page shows real bands with intervals, and the app runs on Databricks with the real data.

### Phase 3: Demo content + Break Card (Sun 01:00–07:00, in shifts, and sleep)
- [ ] **Open backlog (Data):** ingest *open* SPARK tickets, run the agent, and take the 10 most confident
  "duplicate" suggestions. **Humans hand-check all 10** and record how many were right, in `results/…-open-backlog/`.
  This is the "it found real lost knowledge" moment. Report it honestly even if it's 4/10.
- [ ] **Break Card (Story + Engine):** one page, each item with its number and file.
  - part_of overconfidence (siblings mistaken for the umbrella), and what v2 fixed
  - the "cheap" model costing +90% because of hidden thinking
  - look-alike traps: version bumps, flaky tests, backports, clones
  - the poisoned correction that the gate discarded
  - "related" precision ~8% → why it stays quiet
  - known limits: the sibling's parent is read from today's data (slightly optimistic), n per band, 4 projects only
- [ ] Sleep plan: at least 2 people get 4 h of sleep. Nothing is run overnight without someone watching the cost.

### Phase 4: Ship it (Sun 07:00–10:45)
- [ ] 07:00 Redeploy the Databricks App, and check the Try-a-ticket page live.
- [ ] 08:00 Final README: problem → the 3 questions → results table (from `results/`) → how to run → Databricks →
  Break Card link → limits → team.
- [ ] 08:30 Record the **2-minute video**: 20 s problem, 60 s app (queue → accept/reject → trust band moves →
  model check → gate verdict), 25 s break card, 15 s ask/close. Screen capture plus voice; do one take and fix it after.
- [ ] 09:30 Devpost: title, tagline, what it does, how we built it, challenges, what we learned, what's next,
  repo link, video link, and declare **Databricks (Xorbix) + Art of the Break**.
- [ ] **10:30 code freeze.** Last commit (reviewed), tag `v1.0-submission` (only with the user's OK).
- [ ] **10:45 submit.** Don't wait for 11:00.

### Finalists (Sun 13:00–15:00)
- [ ] A 3-minute live script, with the sample-data toggle and screenshots as a fallback if the Wi-Fi or the App dies.
- [ ] Have three numbers ready: a proven precision (or "N more labels needed"), the cheap-model verdict, and
  "fixes N, breaks M".

### What to cut if we fall behind (in this order)
1. The third model arm → keep the Haiku-vs-Sonnet result we already have.
2. The open-backlog hand-check → use held-out 2025 tickets only.
3. Deploying the Databricks App → run the app locally, and show Databricks tables + the endpoint in a notebook.
4. **Never cut:** the gate demo (Q3), the honest intervals, the tests passing, the video.

---

## 7. Known facts and numbers (source: runs on Sep 26)

- Data: 37,853 tickets since 2023; 13,687 truth pairs (part_of 11,726, related 1,500, duplicate 461);
  14,910 eval tickets from 2025 onward. 48% of tickets closed as duplicates never link to their original.
- Retrieval recall@10 (2025+): duplicate 72.5%, part_of 57.2% (13.6% before the sibling vote), related 49.4%.
- Hardness test (60 tickets, 328 pairs per model, cli):

  | Model | Pair accuracy | Duplicate P/R | Part_of P/R | Related P |
  |---|---|---|---|---|
  | Haiku | 53.4% | 67/67 | 58/69 | 8.4% |
  | Sonnet | 55.8% | 61/73 | 50/75 | 7.0% |

  - compare_models: Haiku **REJECTED** (+90.5% cost, quality −2.4 pp [−5.8, +0.9]).
  - No auto zone is proven yet: n is too small.
- Databricks Free Edition: 3 Apps, each alive 24 h; serverless; max 10 MB per App file; model availability is unconfirmed.
- Pre-event exploration (label it as such if quoted): switching models mid-conversation cost 4.1×; parallel
  subagents each start cold.

## 8. Open questions (owner in brackets)
- [Platform] Xorbix's answers (§6, Phase 0).
- [User] Whose API key and what cap for Phase 2? The key pasted in chat earlier must be **rotated after the event**.
- [Team] Names for the four roles, and who declares the challenges on Devpost.
