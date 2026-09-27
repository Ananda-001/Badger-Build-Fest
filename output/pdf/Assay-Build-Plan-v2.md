# Assay: event build plan v2 (Sat 26 Sep, 17:00 → Sun 27 Sep, 10:45)

**Status:** proposed. It replaces the build order in `Assay-Full-Staged-Plan.md` for the event. The PRD
(`Assay-Product-Requirements.md`) is still the long-term product spec, and Stages 5–7 there are post-event.
**Reviewer (GPT Astra):** check this plan against the code *before* building. Section 8 lists what to verify
and where to push back.

---

## 0. Why v2 exists (one paragraph)
The staged plan is right about evidence quality but builds in the wrong order for 18 hours. Its Stage 1 spends
4–6 h on a 7-state action ledger, SQLite, reconciliation and rollback before any of the three questions produces a
real verdict. It also leaves the long, slow part (the model runs) until after that. v2 keeps the plan's honesty rules
and builds the three verdicts on real data first. Plumbing gets only what the demo needs. The runs start as early as
their code allows.

**The product in one line:** Assay decides, with evidence, how much freedom an AI agent gets. The Apache Jira
triage agent is the test case.

## 1. Ground truth about the code (checked on `main` @ 8fefe93, 15:42)
These are facts from reading the repo, not assumptions. Astra: re-verify after `git pull`.

| # | Finding | File | Consequence |
|---|---|---|---|
| F1 | Resume key is `(key, model)`. A v2 prompt run would silently skip every ticket already judged with v1. | `scripts/judge_eval.py` `done = {...}` | Must fix before any gate run |
| F2 | The sample is stratified 15/15/15/15, and the true target is **injected** into the shortlist when retrieval missed it (`injected` flag) | `judge_eval.py plan()` | Precision from this sample is inflated. It can't grant a permission. |
| F3 | Permission evidence is pair-level. Up to 5+ pairs from **one** ticket, judged in **one** call, count as separate evidence | `assay_engine/bands.py _actions`, `app_data.evidence` | Overstates n. Needs one decision per ticket. |
| F4 | The app filters by model, but there is no prompt/config version, so v1 and v2 evidence would mix | `app/app.py main()` | Permission isn't scoped to what's actually deployed |
| F5 | "Handled automatically today" counts judgments that fall in the auto band. Nothing was actually executed. | `app_data.auto_handled`, `page_queue` | A misleading number on the first screen |
| F6 | If the engine raises, `_auto_cutoff` silently falls back to a built-in walk, and `_lower_bound` falls back to Wilson | `app_data.py` | Doesn't fail closed |
| F7 | Accept/Reject writes `feedback.jsonl`, but no link is ever "written". The agent never acts. | `app.py _record` | There's no "act" to govern. Needs a tiny sandbox action log. |
| F8 | Reviewers see "`NN% sure`" on the card, and accepted reviews count as correct evidence | `app.py card()`, `app_data.evidence` | Reviews aren't blind, so evidence can be biased |
| F9 | App target defaults to 0.95. The docs discuss 0.90. | `app_data.AUTO_TARGET` | Pick one before the runs (section 3) |
| F10 | On Databricks Apps, local disk is ephemeral. Feedback is mirrored to the UC volume. | `app_data._mirror_to_volume` | Any new state file must use the same mirror. SQLite on App disk would be lost. |

## 2. Hard rules (from the team's CLAUDE.md, restated for Astra)
1. Work only in a fresh `git pull` of **github.com/Ananda-001/Badger-Build-Fest**. Never copy code from the
   pre-event `assay` repo / `mixed` branch / overnight lab. The organizers check repo history, and copied code means disqualification.
2. **No paid or usage-burning call** without the human running it. Show the command and cost estimate first; `--dry-run` always exists.
3. Commit after **every** ticket below (small commits; organizers want to see "early and often"). The human approves
   each one. Stage files by name, no `git add -A`, `git pull --rebase` before push, no force-push. Secret scan
   `git diff --cached | grep -E 'sk-ant-|sk-proj-|dapi[0-9a-f]{20}'` must print nothing, and no staged file may be over 5 MB.
4. Every number in README/video/Devpost comes from a file in `results/` plus the command that made it. Synthetic/sample
   data is always labeled.
5. No direction change. Renaming the app pages into "Live Analysis / Decision Orchestrator" is **out** unless krish agrees.
6. Stay in the owned files listed per ticket (merge-conflict control across 3 people).

## 3. Decisions locked at kickoff (17:00–17:30, whole team, 30 min max)
Write these into `docs/DECISIONS.md` and commit **before** any run. Changing them after seeing results is not allowed.

| ID | Decision | Proposed default |
|---|---|---|
| D1 | Scope | This plan |
| D2a | Permission target | **Precision ≥ 0.90, one-sided 95% Clopper-Pearson**, engine's fixed-sequence walk (`auto_threshold`, default `tolerate=(0,3)`). 0.95 is shown as information only and never grants AUTO. |
| D2b | Unit of evidence | **One decision per ticket** = its highest-confidence non-`none` call. For part_of, keep at most one ticket per predicted umbrella (the earliest-created one, so the choice never depends on the outcome). |
| D2c | Permission sample | Uniform random from the **honest stream**: 2025+ tickets whose top retrieval score ≥ `s`. Pick `s` from the score distribution only, before any judging. **No injected targets.** |
| D2d | Gate rule | Sign test (`gate_change`, α=0.05, margin 0) on **ticket-level** correctness (section 5, T2). One look at the confirmation set. |
| D2e | Families | 3 relations × 1 model config for permissions. Report it as it is; no alpha split across relations beyond the engine's walk split (disclose this in the README limits). |
| D4 | Budget | Gate run: 180 Sonnet calls on `cli` ($0, usage window). Scale run: ~300 tickets × 2 configs ≈ 600 calls, **cap $10** on the API key, or `cli`/Databricks if free. The human runs each command. |
| D5 | Break Card failure | Primary: Haiku through Claude Code burned ~1,700 hidden thinking tokens/call (+90.5% cost), **already observed**. Secondary: the poisoned correction is blocked by the gate *if* the run shows it. |
| — | Owners | Engine = Mohit + Astra; App = ?; Platform (Databricks) = ?; Story = ?. Names in the team chat. |

Also at kickoff: confirm the team/challenge declaration was filed (it was due Sat noon), and check that the Anthropic key
pasted in chat earlier gets rotated.

**Expected honest outcome (say it now so nobody is surprised later):** at 0.90, a proven AUTO zone is plausible for
part_of *after* v2 and unlikely for duplicates (~142 duplicate tickets in the 2025+ stream). Duplicates will probably say
"needs ~N more reviews". related stays QUIET (~8% precision). That's a good demo, and we never lower the bar to get an AUTO.

---

## 4. Timeline

| When | Engine (Mohit + Astra) | App | Platform | Story |
|---|---|---|---|---|
| 17:00–17:30 | Kickoff decisions (section 3), `git pull`, run tests and record the actual count | same | same | same |
| 17:30–19:00 | **T1** prompt versions + config id + resume fix + fresh + slice | **T3** fail-closed + version scoping | **P1** workspace, UC tables, endpoint smoke | **S1** mentor visits (x3), Devpost skeleton |
| ~19:00 | ▶ **RUN A: gate run** (human, $0) | | | |
| 19:00–21:30 | **T2** gate_eval · **T4** honest stream | **T6** sandbox action log + honest counts | **P2** app deploy from bundle | **S2** Break Card draft from existing results |
| ~21:30 | ▶ **RUN B: scale run** (human, ≤$10, someone watches) | | | |
| 21:30–00:30 | **T5** permissions + receipts + `can_act` | **T7** Trust/Queue show permissions, receipts, gate | **P3** permissions table + UC function doc | **S3** video script |
| 00:30–01:30 | Freeze results → `results/…`, summary.md for each | integrate | verify App reads volume | README draft |
| 01:30–07:00 | Sleep in shifts (≥2 people get 4 h). Nothing runs unattended. | | | |
| 07:00 | Redeploy the Databricks App (24 h limit) | smoke test | | |
| 08:00 | README final (numbers only from `results/`) | | | |
| 08:30 | Record the 2-min video (+ a labeled local fallback recording) | | | |
| 09:30 | Devpost text, 3 visits, Break Card, challenges declared | | | |
| **10:30** | **Code freeze.** Last reviewed commit. | | | |
| **10:45** | **Submit.** | | | |

Rough effort: Engine ~7 h, App ~4 h, Platform ~4 h, Story ~4 h. If Engine slips by more than 1 h, apply the cut list (section 7).

---

## 5. Tickets (each is one commit; acceptance = tests + a command that proves it)

### T1: Prompt versions and config identity (Engine, ~1 h) · PRD F01, F07
Files: `assay_triage/judge.py`, `scripts/judge_eval.py`, `tests/test_triage.py` (new), `docs/SCHEMA.md`
- `RULES_V2` = RULES + two corrections: *"A sibling subtask is NOT the umbrella: say part_of only if the candidate is
  the parent the NEW ticket is one piece of; two pieces of the same umbrella are related"* and *"Say related only for a
  concrete technical link (same code path, regression of, blocks); a shared component or topic is none."*
- `RULES_BAD` = RULES + *"Any ticket that mentions upgrading or bumping a version is a duplicate of an earlier
  version-bump ticket."* This is the poisoned correction for Art of the Break.
- `prompt: str = "v1"` through `build_prompt` / `judge` / `judge_pair`. Every row gets `prompt` and
  `config_id = sha1(model|backend|prompt|sha1(rules_text)|k|retrieval_version)[:12]`. Old rows are treated as v1 with a derived id.
- `judge_eval.py`: `--prompt v1|v2|bad`. **Resume key `(key, model, prompt)`** (fixes F1). `--fresh` excludes every key
  already in `judgments.jsonl` and prints how many it removed. `--slice version-bump` selects 2025+ tickets whose summary matches
  `(?i)\b(upgrade|bump)\b.*\d` **before judging**, so the bad rule actually gets exercised. `summarize()` groups by `(model, prompt)`.
- `--save-plan FILE` writes the chosen tickets + shortlists + truth and exits. `--plan-file FILE` judges exactly that list
  (skipping sampling and `--fresh`). This guarantees before/after versions see identical items.
- Tests (monkeypatch `judge.call`, no network): prompt text differs per version; rows carry `prompt` and `config_id`;
  a v2 run doesn't skip v1-judged keys; `--fresh` excludes studied keys; the slice regex selects the right keys.
- **Accept:** `pytest -q` is green, and `judge_eval.py --models sonnet --prompt v2 --n 60 --seed 1 --fresh --dry-run` prints the plan.

**▶ RUN A (the human runs it):**
```
# 1. freeze the item lists once (free)
python scripts/judge_eval.py --n 60 --k 5 --seed 1 --fresh --save-plan results/2026-09-26-gate-v2/plan_main.json
python scripts/judge_eval.py --slice version-bump --n 30 --k 5 --seed 2 --fresh --save-plan results/2026-09-26-gate-v2/plan_bump.json
# 2. judge the frozen lists (human runs, cli = $0 usage window, 180 calls total)
python scripts/judge_eval.py --models sonnet --prompt v1  --plan-file results/2026-09-26-gate-v2/plan_main.json --workers 3
python scripts/judge_eval.py --models sonnet --prompt v2  --plan-file results/2026-09-26-gate-v2/plan_main.json --workers 3
python scripts/judge_eval.py --models sonnet --prompt v1  --plan-file results/2026-09-26-gate-v2/plan_bump.json
python scripts/judge_eval.py --models sonnet --prompt bad --plan-file results/2026-09-26-gate-v2/plan_bump.json
```
(Why the plan files: `--fresh` excludes keys already in `judgments.jsonl`, so running it again after v1 would drop
exactly the v1 tickets from the v2 run. Freezing the list first removes that trap.)

### T2: Learning gate, ticket-level (Engine, ~1 h) · PRD F09
Files: `scripts/gate_eval.py` (new), `assay_engine/tickets.py` (new), `tests/test_engine.py`
- `ticket_outcomes(rows) -> {key: correct}`: per ticket and config, take the top non-`none` call. It's **correct** iff that
  relation equals the truth for that candidate. With no action, it's correct iff no shortlisted candidate has a non-`none` truth.
- `gate_eval.py --model sonnet --before v1 --after v2 [--slice …] [--json out.json]` → `gate_change` on the ticket
  outcomes (primary), plus pair-level fixed/broken lists and per-relation precision before/after (detail only).
- Tests: synthetic "fixes 12, breaks 0" → KEEP; "0 / 12" → DISCARD; "3 / 2" → UNPROVEN; ticket reduction with mixed pairs.
- **Accept:** after RUN A, `results/2026-09-26-gate-v2/` has `summary.md` (commands, verdicts, fixed/broke keys) and
  `gate.json`. If `bad` comes out UNPROVEN rather than DISCARD, report it as is.

### T3: Fail closed and scope to the deployed version (App, ~1 h) · PRD F06, N01 · fixes F4, F6, F9
Files: `app/app_data.py`, `app/app.py`, `tests/test_app.py`
- Remove the silent fallbacks in `_auto_cutoff` / `_lower_bound`. If the engine is missing or raises → **no AUTO for that relation**,
  plus a visible error chip ("Trust engine failed: auto is off").
- The sidebar selects a **config** (model + prompt), not just a model. Evidence and bands use only rows with that `config_id`.
- `AUTO_TARGET` is read from `docs/DECISIONS.md`'s value (0.90 default via env), and the page shows it.
- Tests: an engine exception gives zero auto bands; mixed v1/v2 rows are never pooled.

### T4: Honest stream sample (Engine, ~1.5 h) · PRD evidence policy · fixes F2, F3
Files: `assay_triage/retrieve.py`, `scripts/judge_eval.py`, `assay_engine/tickets.py`, tests
- `retrieve.py --all`: candidates for **every** 2025+ ticket (TF-IDF, free), written to `data/candidates_all.jsonl`, with
  the current mode left unchanged. Print the top-score distribution (deciles).
- `judge_eval.py --stream-min-score s --n N --no-inject --plan-file …`: uniform random sample of stream tickets, **no injected
  truth**. It prints stream size, class mix and s.
- `tickets.py`: `one_per_ticket(rows)` and `dedupe_umbrella(rows, tickets)` per D2b; the permission code (T5) uses only these.
- **Accept:** a dry run prints stream size / class mix. Tests cover no-inject and the dedup rules.

**▶ RUN B (the human runs it, cap $10):** ~300 stream tickets × {Sonnet v2, Haiku v2 with thinking off via `--backend anthropic`}.
Run `--dry-run` first. Freeze to `results/2026-09-27-scale-300/`. If only one config fits the budget or time: Sonnet v2.

### T5: Permissions, receipts, `can_act` (Engine, ~1.5 h) · PRD F06, F08
Files: `assay_engine/permissions.py` (new), `scripts/permissions.py` (new), `tests/test_engine.py`
- `build_permissions(rows, config_id, target, alpha) -> list[row]`, one row per relation:
  `{relation, mode: auto|suggest|quiet, threshold, n, k, precision, lower, target, alpha, config_id, method: "cp-fixed-seq",
  unit: "ticket", evidence_keys, excluded: {injected, unlabeled, dedup}, need_n, computed_at, receipt_id}`.
  `receipt_id` = hash of the content. Recomputing writes a **new** file and never overwrites (`results/permissions-<receipt_id>.json`).
- `can_act(permission_rows, relation, confidence, config_id) -> (mode, reason)`: no row, a config mismatch, an expired row,
  or an exception all return **suggest** with the reason. **This is the "change the prompt → AUTO revoked" demo.**
- Tests: config mismatch → suggest; all-correct n=10 → not auto; engine error → suggest; receipt immutability.
- **Accept:** `python scripts/permissions.py --results results/2026-09-27-scale-300 --config <id>` prints a readable table.

### T6: Sandbox action log and honest counts (App, ~1.5 h) · PRD F04, F05 (slimmed) · fixes F5, F7
Files: `app/actions.py` (new), `app/app.py`, `app/app_data.py`, tests
- `actions.jsonl` (same dir + same volume mirror as feedback): `{action_id, key, candidate, relation, config_id, receipt_id|null,
  path: auto|approved, status: done|rejected, user, ts}`. `action_id = sha1(key|candidate|relation|config_id)`. **Write is skipped
  if the id exists**, so double-click/retry makes one action. States stay minimal on purpose (no UNKNOWN/reconcile: a local
  append can't have an uncertain outcome).
- Accept in the queue → `can_act` rechecked → action `approved/done`. Reject → `rejected` + reason. A script
  `scripts/act.py --config <id>` applies AUTO-mode decisions through `can_act` and logs them `path: auto`.
- The queue header shows **"Links written: N (auto a · approved b) · rejected r"** from `actions.jsonl`. Delete
  "Handled automatically today".
- Label single-user local demo mode in the sidebar ("local demo: one reviewer, no login").
- Tests: double accept → 1 action; mismatched config → no auto action; counts survive a reload.

### T7: Show it (App, ~1.5 h) · PRD dashboards (inside the existing 4 pages, no renaming)
- Trust page: the permission table per relation from the latest receipt (mode, proven ≥, n, need_n, config, receipt id,
  expandable evidence keys). Show D2a/b/c in one caption.
- Add a "Learning gate" section (Model check page or a new page, krish decides): the fixed/broke lists with both tickets'
  text, verdict and the one-sentence `describe_gate`.
- Optional (Should): blind-review toggle, default on, that hides confidence on queue cards (fixes F8).

### Platform (parallel, owner = Platform)
- **P1:** workspace, PAT in `.env`, UC tables `tickets/truth/candidates/judgments` (count = 37,853 tickets), endpoint list,
  4-ticket smoke via `--backend databricks` (human runs it). Record results in the `docs/NEXT_STEPS.md` Log.
- **P2:** `make_bundle.py` → deploy the App, check that feedback **and actions** land in the volume.
- **P3:** write the permissions receipt to a UC table `assay.permissions`, plus a short SQL UC function template in `docs/`
  (the "Databricks enforces, Assay decides" story). Only claim what actually ran there.

### Story (parallel, owner = Story)
- **S1:** three mentor visits (Xorbix questions from CLAUDE.md section 6 Phase 0), one thing learned each.
- **S2:** `docs/BREAK_CARD.md`: failure, version, expected vs observed, root cause, fix, retest, each with a number + file.
- **S3:** 2-min video script: problem 20 s → queue accept writes one link 25 s → Trust: proven zone or "needs N more"
  25 s → change the prompt, AUTO revoked 15 s → gate: fixes N, breaks M 20 s → Break Card 15 s.

---

## 6. What we deliberately do NOT build before 10:45 (and why)
| From the staged plan | Decision | Reason |
|---|---|---|
| 7-state ledger, UNKNOWN reconciliation | Cut to done/rejected + idempotent id | No external writes exist; reconciliation guards against something that can't happen here |
| SQLite store | Cut; JSONL + volume mirror | SQLite on App disk is lost on redeploy (F10). JSONL already works on both. |
| Version activation + rollback UI | Cut; `can_act` config check + README text | Permission revocation on config change shows the same idea in 15 s |
| Page renaming to Live Analysis / Decision Orchestrator | Cut unless krish agrees | Direction-change rule; merge conflicts in `app.py` |
| N05 performance, multi-user auth, adapters, Stages 5–7 | README "What's next" | Post-event |
| Q2 CERTIFY rebuild | Keep existing `compare_models`, re-run in RUN B only | Already implemented; the new data is what's missing |

## 7. Cut order if late (apply in order, announce in the team chat)
1. Haiku arm of RUN B → keep the existing REJECT result with its caveat.
2. T7 blind-review toggle and the gate page polish → show `gate_eval` output in the README.
3. P2 App deploy → run locally, show UC tables + endpoint + permissions table in a notebook. Disclose it.
4. T4 honest stream → permissions computed on the stratified sample are **labeled "diagnostic, not a permission"**, and every
   mode shows suggest.
**Never cut:** T1 + RUN A + T2 (gate verdict on fresh tickets), T3 fail-closed, T5 `can_act` with config check, passing tests, video, README limits.

---

## 8. For Astra: verify before building, and push back where it's wrong
Answer these in writing first. Build only after the human has read the answers.
1. Re-check findings F1–F10 on the latest `main`. Mark each one confirmed, changed or wrong.
2. **Test count:** run `pytest -q` and report the real number (the handover says 40; I counted 39 `def test` in the two files).
3. Does T1's `--save-plan`/`--plan-file` really give v1 and v2 identical tickets, shortlists *and* candidate order
   (`plan()` shuffles shortlists with the seeded RNG)? Point out any hole.
4. Is ticket-level correctness (T2) well-defined when the truth has two relations for one ticket? Propose a rule.
5. Does `auto_threshold`'s default `tolerate=(0,3)` walk work on one-per-ticket rows after dedup? Estimate the minimum n
   to prove 0.90 with 0 and with 1 mistake (use `assay_engine.bounds`, no guessing).
6. Given the stream threshold `s`, estimate how many predicted duplicates RUN B will produce. If it's < 30, say so now.
7. Does the `cli` backend let us turn thinking off for Haiku, verified from `usage` rather than assumed? If not, RUN B's
   Haiku arm must use `--backend anthropic` (costs money; needs D4).
8. Anything in this plan that breaks the existing tests or the Databricks bundle (`make_bundle.py` 10 MB/file limit)?
9. Where do you disagree with section 6 (cuts)? Argue with evidence from the code, not preference.

**Done for the event means:** a judge can watch an accept write exactly one link; see per-relation modes with
receipts computed on honest, one-per-ticket evidence; see AUTO revoked when the prompt changes; see "fixes N, breaks M"
on fresh tickets; and read a Break Card whose every number links to `results/`.
