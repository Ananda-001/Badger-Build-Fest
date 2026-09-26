# NEXT_STEPS: exact steps to pick up right now (written Sat Sep 26, 15:05)

**For the teammate's Claude:** read `CLAUDE.md` first (the rules and the plan), then this file, then do the tracks
below **in order**. krish is out of usage until about **16:00** and will then work in parallel with you.
Every step says what "done" looks like. If a step fails, write down what happened in the **Log** section at the
bottom of this file, and continue with the next track instead of getting stuck.

**Commit rule for this handoff:** you prepare commits exactly as `CLAUDE.md` §5 says, and **your human approves
each one**. Everything goes on the branch **`import/phase0`** (and feature branches after it). **Nothing is merged
into `main` until krish has reviewed it at ~16:00.** No force-push, no backdating, and no `git add -A`.

> **Update 15:45 (krish's Claude):** Track B is DONE except for the commits themselves. The team repo is set up on
> branch **`wip`** with every file in place (see `READ_FIRST.md` in the package for the 9 commit commands). The big
> data files are in the package under `data/` (git-ignored). **Read `docs/thinking/03-brief-v3-fact-check.md`
> before the scale run:** it changes how we sample (§4: an enriched sample fakes the precision proof).

---

## Track A: Get it running on your machine (15 min)

1. Unzip `assay-workbench-1505.zip` (from krish) into a folder, e.g. `~/assay-workbench`. It contains the code,
   tests, docs, fake sample data and the real data (`data/tickets.jsonl`, `truth.jsonl`, `candidates.jsonl`,
   `judgments.jsonl`). It has **no** `.env` and no `data/raw/` cache.
2. Make a Python environment (3.11+):
   ```bash
   cd ~/assay-workbench
   python3 -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install numpy scipy scikit-learn streamlit openai anthropic databricks-sdk pytest
   ```
3. Run the tests: `python -m pytest -q tests` → **done when it prints `40 passed`**.
4. Print the existing results: `python scripts/judge_eval.py --summary` → it should show 656 judged pairs, Haiku 53.4%,
   Sonnet 55.8%.
5. Run the app: `streamlit run app/app.py`. Tick "sample data" and click through all 4 pages; then untick it
   (real data). **Done when the Review queue and Trust pages render with both settings.** Screenshot anything broken
   into the Log.

## Track B: Move the code into the team repo on a branch (30–40 min)

1. `git clone https://github.com/Ananda-001/Badger-Build-Fest ~/Badger-Build-Fest && cd ~/Badger-Build-Fest`
   `git checkout -b import/phase0`
2. Copy from the workbench: `assay_triage/`, `assay_engine/`, `scripts/`, `tests/`, `app/` (without `_bundle/`),
   `data/sample/`, `data/truth.jsonl`, `docs/SCHEMA.md`, `docs/TEAM_BRIEF.md`, `docs/DATABRICKS_SETUP.md`,
   `docs/NEXT_STEPS.md`, `CLAUDE.md`. **Do not copy** `docs/HANDOFF.md`, `.env*` (except `.env.example` if you make
   one), `__pycache__/`, `.pytest_cache/`, `data/raw/`, `data/tickets.jsonl`, `data/candidates.jsonl`.
3. Write the root `.gitignore`:
   ```
   .env
   .env.*
   !.env.example
   __pycache__/
   *.pyc
   .pytest_cache/
   .venv/
   data/raw/
   data/tickets.jsonl
   data/candidates.jsonl
   data/judgments.jsonl
   data/feedback.jsonl
   app/_bundle/
   *.parquet
   ```
   (`data/judgments.jsonl` is a live working file; frozen copies go into `results/`.)
4. Write `requirements.txt`: `numpy`, `scipy`, `scikit-learn`, `streamlit>=1.45`, `openai`, `anthropic`,
   `databricks-sdk`, `pytest`.
5. Write `.env.example` (names only, **no values**): `ANTHROPIC_API_KEY=`, `DATABRICKS_HOST=https://…`, `DATABRICKS_TOKEN=`.
6. Rewrite `README.md` (keep it short for now): the one-paragraph idea from `docs/TEAM_BRIEF.md` §1, the three
   questions table, "How to run" (the commands from `CLAUDE.md` §3), and the line: *"Development started in a local
   folder at 11:00 on Sep 26 at the event and was moved into this repo at ~15:00."* Keep the existing MIT `LICENSE`.
7. Create `results/2026-09-26-hardness-60/`: copy the workbench's `data/judgments.jsonl` there as `judgments.jsonl`,
   and write `summary.md` with the command
   (`scripts/judge_eval.py --models haiku,sonnet --n 60 --k 5 --workers 4 --backend cli`, seed 0), the output of
   `--summary`, and the notes from `CLAUDE.md` §7 (compare_models REJECT, +90.5% cost, thinking tokens measured
   through Claude Code only).
8. Run the tests in the new repo. Then prepare the commits **C1 to C8** from `CLAUDE.md` §6 (Phase 0 table), one at a
   time: stage the files by name → run the secret/size scan → show your human → commit on "yes".
9. With your human's OK: `git push -u origin import/phase0`. **Don't open a merge into main; krish reviews at 16:00.**

**Done when:** the branch `import/phase0` on GitHub has C1–C8, and a fresh clone of that branch passes the tests.

## Track C: Databricks up and a model answering (30–45 min; can run alongside B)

Follow `docs/DATABRICKS_SETUP.md` §1–§4. Short version:
1. Log in to the workspace. User settings → Developer → Access tokens → make a PAT.
   Put it in **`.env`** in the workbench (never in chat, code or git):
   `DATABRICKS_HOST=https://<workspace-host>` (must start with `https://`) and `DATABRICKS_TOKEN=<pat>`.
2. List the model endpoints we can actually use:
   ```bash
   set -a; source .env; set +a
   python -c "from databricks.sdk import WorkspaceClient; w=WorkspaceClient(); [print(e.name) for e in w.serving_endpoints.list()]"
   ```
   Write the list into the Log. We hope for `databricks-claude-haiku-4-5`, `databricks-claude-sonnet-*`,
   `databricks-gpt-oss-120b`, `databricks-gte-large-en`.
3. Smoke test the judge on 4 tickets (4 calls per model, cents at most). **Ask your human before running it:**
   ```bash
   python scripts/judge_eval.py --backend databricks --models databricks-claude-haiku-4-5 --n 4 --k 5 --dry-run
   python scripts/judge_eval.py --backend databricks --models databricks-claude-haiku-4-5 --n 4 --k 5 --workers 2
   ```
   Use whichever chat model the list shows if Claude isn't there (e.g. `databricks-gpt-oss-120b`).
   **Done when** new rows with that model name appear in `data/judgments.jsonl` with `parsed: true`.
   If the output isn't valid JSON, note it in the Log. `judge._parse` may need to strip a reasoning preamble.
4. **Optional, only after 3 works: the AI Gateway (from the Databricks info we were sent).**
   - Gemini through the gateway (`GEMINI_MODEL=system.ai.gemini-2-5-flash`, base URL
     `https://<host>/ai-gateway/gemini`, bearer = the PAT) would give a **third model family** for `compare_models`.
     Our judge speaks the OpenAI-compatible API, and the gateway URL above is Gemini-native. So first check whether
     `system.ai.gemini-2-5-flash` also answers through `/serving-endpoints` with our `databricks` backend. If it
     doesn't, write that down and stop. Don't build a new backend without krish.
   - `ug claude --provider <catalog>.<schema>.<name> --workspace https://<host>` runs Claude Code through the gateway
     (governance, tracing, rate limits). **Good story for the Databricks challenge** ("every agent call is traced in
     Unity Catalog"), but it's unverified whether `claude -p` works through it. Try one `ug claude` session by hand
     and record what you see. Don't route the eval through it yet.
5. Upload the data to Unity Catalog (`DATABRICKS_SETUP.md` §2): schema `workspace.assay_triage`, volume `data`, the
   four JSONL files → tables. **Done when** `SELECT count(*) FROM workspace.assay_triage.tickets` = 37,853.

## Track D: Prompt v2 + the learning gate: code only, no paid runs (45–60 min)

This is question 3 ("did it really learn?"), the core of the Xorbix challenge. Write the code and the tests; the
real run happens when krish is back (it costs money or usage).

1. **`assay_triage/judge.py`**: add `RULES_V2` next to `RULES`: the same text plus two corrections:
   - "A sibling subtask is NOT the umbrella. Say part_of only if the candidate is the parent/umbrella that the NEW
     ticket is one piece of. Two tickets that are both pieces of the same umbrella are related, not part_of."
   - "Say related only for a concrete technical link (the same code path, a regression of, blocks). Sharing a
     component or a topic is none."
   Add a `prompt: str = "v1"` parameter through `build_prompt`, `judge` and `judge_pair`, which picks
   `RULES`/`RULES_V2`. Put `"prompt": prompt` into every row that `judge()` returns.
2. **`scripts/judge_eval.py`**:
   - add `--prompt v1|v2` (default `v1`) and pass it to `judge`.
   - **Fix the resume key**: `done` must be `(key, model, prompt)`, treating rows without a `prompt` field as `"v1"`.
     Otherwise a v2 run skips every ticket that was already judged with v1.
   - add `--fresh`: remove from the sample any ticket key already in `data/judgments.jsonl` (so v2 is judged on
     tickets we did **not** study when writing the rules = no peeking). Print how many were excluded.
   - `summarize()`: group by `(model, prompt)` instead of `model`.
3. **New `scripts/gate_eval.py`**: loads `data/judgments.jsonl`, takes `--model`, `--before v1 --after v2`, builds
   `{f"{key}|{candidate}": correct}` for each prompt version, runs `assay_engine.gate_change(before, after)`, and
   prints `report.describe_gate(...)` plus the fixed and broken pairs (key, candidate, truth, before→after
   relation). `--json out.json` writes the whole result. Also add per-relation precision before/after, since v2 is
   expected to trade some recall for precision on part_of/related.
4. **Poisoned correction** (Art of the Break): add `RULES_BAD` = RULES + "Any ticket that mentions upgrading or
   bumping a version is a duplicate of an earlier version-bump ticket." Selectable as `--prompt bad`. The gate should
   DISCARD it; that's the demo that the gate protects against bad feedback.
5. **Tests** in `tests/test_triage.py` (no model calls; monkeypatch `judge.call`): the prompt text differs per
   version; rows carry `prompt`; the resume key respects prompt; `--fresh` excludes studied keys; `gate_eval` gives
   KEEP on a synthetic "fixes 12, breaks 0" and DISCARD on "fixes 0, breaks 12".
6. Update `docs/SCHEMA.md`: `judgments.jsonl` gains `prompt` (v1 | v2 | bad; missing = v1).
7. Branch `feat/prompt-v2` off `import/phase0`, and commit after your human's OK:
   `judge: prompt v2 and poisoned-rule variants`, then `eval: learning-gate script and fresh-sample flag`.

**The run for when krish is back** (not now; the dry run is free):
```bash
python scripts/judge_eval.py --models sonnet --prompt v1 --n 60 --k 5 --seed 1 --fresh --dry-run
# then the same without --dry-run for v1, v2 and bad (3 × 60 calls), then:
python scripts/gate_eval.py --model sonnet --before v1 --after v2
python scripts/gate_eval.py --model sonnet --before v1 --after bad
```

## Track E: Only if A–D are done
- Draft the Break Card (`docs/BREAK_CARD.md`) from `CLAUDE.md` §6 Phase 3; every claim needs a number + file.
- Draft the Devpost text in `docs/DEVPOST.md` (the sections are listed in `CLAUDE.md` Phase 4).

---

## When krish is back (~16:00): what they do
1. Review the branch `import/phase0` (and `feat/prompt-v2`); approve the merge into `main`.
2. Run the paid or usage-burning jobs with `!`: the v1/v2/bad gate run, then Haiku with thinking off, then Phase 2 scale.
3. Declare the challenges; the Xorbix questions.

## Log (append: time, who, what happened)
- 15:05 krish's Claude: wrote CLAUDE.md + this file; the workbench zip `assay-workbench-1505.zip` is in `Downloads\Assay`.
