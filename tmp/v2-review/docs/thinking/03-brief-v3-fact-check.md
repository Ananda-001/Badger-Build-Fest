# Assay: team brief v3 (Sat Sep 26, 15:40)

*v2 (friend's Databricks research) fact-checked against the Databricks docs, the opening deck and our own data.
What changed from v2 is marked **(v3)**. Sources are at the bottom.*

## 0. Do these first (v3)
1. **Check that the team declaration was filed.** The deck says "11:30 Declare team, track & challenges", and the
   form (with the repo link) was "due by noon today" (slides 5 and 18). Whoever filled it: confirm the track
   (Applied AI) and the challenges (Databricks/Xorbix + Art of the Break). If it wasn't filed, tell an organizer now.
2. **Get code into the team repo.** Slide 18 says "Commit early and often." As of 15:25 the repo has only the README +
   LICENSE. Push the reviewed Phase 0 commits to a `wip` branch today and keep committing every few hours.
3. **Rotate the Anthropic key that was pasted in chat, now**, and put a spending cap on the key we use for the big run.

## 1. The idea in one paragraph
**Assay is a proof engine for AI agents.** Databricks already lets you run, trace, grade, label and restrict an agent.
But every decision about **how far to trust it** is still a human guess: an admin's policy, a threshold picked by eye,
a score with no error bar. **Assay decides from evidence**: which actions the agent may take alone, whether a change
really helped, whether a cheaper setup is safe. Or it says "not proven yet, needs N more."

**Pitch line:** *Databricks collects the evidence and enforces the rules. Assay decides what the rules should be.*

**(v3) How it fits Xorbix:** their challenge is "an agent on Databricks that reads, decides, acts and improves when a
human corrects it", with *organizational knowledge capture* as a suggested direction. Our agent recovers lost
knowledge (48% of duplicate closures never link to the original), and Assay governs how far it may act.

## 2. The three questions, in priority order
| # | Question | Verdicts | Status |
|---|---|---|---|
| 1 | **Can the agent act alone?** (the lead) | AUTO above t / SUGGEST / QUIET / needs N more | See the evidence sizes below |
| 2 | **Can it run cheaper?** | certify / reject / needs N more | Re-run Haiku with thinking off before claiming anything |
| 3 | **Did the change really help?** | keep / discard / unproven | 1 hour. Fresh tickets only |

**(v3) How much evidence a proof takes** (one-sided 95%, exact Clopper-Pearson; checked by computing it):

| Target | Single walk (as quoted in v2) | Our engine's default (two walks, alpha split) |
|---|---|---|
| 90% | 29/29, or 46 with 1 mistake | 36/36, 54 with 1, 85 with 3 |
| 95% | 59/59, or 93 with 1 | 72/72, 110 with 1 |

v2's 29/46 are right for a single walk. The engine's default is more robust to one early mistake, but needs more
data. **Decision: demo at 90% with the engine default, and quote 36/54.**

## 3. The demo agent
For each new **Apache Jira** ticket (Spark, Flink, Kafka, Hive), the agent decides: **duplicate**, **part of** an
umbrella, **related**, or **new**. Humans accept or reject in a review app, and every click becomes evidence.
- Atlassian's Rovo already suggests duplicate Jira items. **The agent is our test case, not the product.**
- We don't write to Apache's Jira. "Acts" writes links to our own table; in production it would call the Jira API.

## 4. Two traps in how we measure (v3; these must be fixed before the scale run)
**Trap 1: an enriched sample inflates precision.** v2 says "scale to ~300 tickets, weighted toward duplicates."
Precision depends on how common duplicates are. On a sample that's 1/3 duplicates, the "duplicate" calls look far
more precise than they will be on the real stream, where only about 1% of tickets have a duplicate. A zone proven on
the enriched sample **would not be a real proof**.
**Fix:** define the stream honestly. The agent only considers tickets whose best search match is above a similarity
cut-off *s*, decided **before** judging. Then sample *at random* from that stream. This enriches duplicates
naturally, and the proof holds for exactly the stream the agent runs on. (The other option, stratum weights,
needs weighted intervals: more engine work.)

**Trap 2: we don't have many duplicates.** The 2025+ evaluation set has **142 duplicate tickets** (vs 6,810 part_of,
503 related). Retrieval finds ~72%, so there are about 100 usable duplicates. Proving 90% needs the model to be
nearly perfect on 36–54 of them. The best we've seen so far is 86% on 7. So:
- **Plan for a proven zone on part_of (lots of data) after the prompt fix, and "needs N more" on duplicates.**
  Both are honest results, and "needs N more" is a verdict, not a failure.
- To get more duplicates for free, add projects to the ingest (e.g. HADOOP, HBASE, CASSANDRA, BEAM, AIRFLOW) and/or
  start the evaluation window at 2024-07. Ingest costs $0; it only takes time.

**Also keep from v2:**
- **Count clusters, not pairs.** Siblings under one umbrella, and several candidates of one ticket, aren't independent.
  Count one decision per ticket (its top call), and one cluster per umbrella.
- **Maintainer links are a floor:** they miss real duplicates, so measured precision understates the agent. When
  humans "rescue" a wrong-looking call, they must review **blind** (without seeing the model's confidence), or the
  rescue inflates the numbers.

## 5. What Assay adds on top of Databricks (v3: tiered, 19 hours left)
| | What Assay adds | Databricks piece | Tier |
|---|---|---|---|
| A1 | **Earned autonomy:** a proven zone per action → `assay.permissions` table; the agent calls `assay.can_act()` before acting | Unity Catalog function; Contextual Service Policies (Beta) are **SQL UC functions**, so in production a policy could read our table | **Must** |
| A6 | **Evidence receipts:** every verdict/auto-action links to the tickets that proved it | Delta + Unity Catalog; Xorbix asks to "show sources" | **Must** (cheap once A1 exists) |
| A3 | **Change gate:** fixes vs breaks on fresh tickets (sign test) | MLflow compares means only; there's an open request (mlflow#26193) for paired tests | **Must** (built; needs the run) |
| A7 | **Calibration:** stated confidence vs actual precision | Break Card evidence | **Must** (1 small function, data exists) |
| A4 | **True cost per task** incl. thinking + cache tokens, judged together with quality | `system.ai_gateway.usage.token_details` has `cache_read_input_tokens`, `cache_creation_input_tokens`, `output_reasoning_tokens`; **no dollar column** | Should |
| A2 | Judge + a few human labels = honest number with interval (prediction-powered inference) | MLflow judges + judge alignment | Could (stretch) |
| A5 | Re-check over time: demote AUTO → SUGGEST when evidence drops | Jobs; Data Quality Monitoring flags drift only | Could: one slide + a function; no live monitoring |

## 6. Databricks facts (v3: each checked against the docs)
- ✅ Free Edition: **Knowledge Assistant unsupported**; **up to 3 Apps, which run up to 24 h after start/update/redeploy**;
  **one AI Search endpoint (one unit)**; Foundation Model APIs with "certain models not available", no provisioned
  throughput; serverless notebooks with limited size.
- ✅ Outbound internet is "restricted to a limited set of trusted domains". **(v3) After LinkedIn verification the
  account gets outbound internet.** Worth doing: then a notebook can pull Jira directly. Otherwise upload from a laptop.
- ✅ Challenges are judged **online**, winners Sep 30 → **the video + screenshots carry the demo**; the app will be down.
- ✅ Contextual Service Policies (Beta, announced at Data + AI Summit, June 2026) can allow / deny / **require approval**,
  written as SQL UC functions. ❓ Whether Free Edition has them: ask Xorbix.
- ✅ Usage table columns (above). ❓ Whether Free Edition exposes `system.ai_gateway.usage`: ask Xorbix.
- ✅ MLflow 3 `mlflow.log_feedback()` stores human feedback on traces; the Review App exists. ❓ Free Edition support: ask.

## 7. Next steps (v3 order) and owners
1. **Now:** confirm the declaration; Phase 0 commits to `wip`; rotate the key. *(krish + friend)*
2. **Prompt v2 + Haiku with thinking off** on fresh tickets → gate verdict + compare verdict. *(Engine)*
3. **Fix the measurement** (§4): pre-filter stream + random sample, count per ticket/cluster; optionally more projects. *(Data)*
4. **Scale run** on that stream (~300 tickets; ~$3–8; the user runs it with `!`). *(Data)*
5. **A1 + A6 + A7:** permissions table, `can_act`, receipts, calibration table. *(Engine)*
6. **Databricks:** workspace, volume + tables, model endpoint, app deployed; review clicks → feedback table (MLflow if available). *(Platform)*
7. **Break Card** (part_of overconfidence, the "cheap model" trap, the poisoned correction, calibration). *(Story)*
8. **Video while the app is up**, Devpost answers, **the three mentor/org visits** (Devpost asks which, plus one thing
   learned each). *(Everyone)*

## 8. Open questions
**For Xorbix:** which models work on Free Edition and their rate limits · whether the usage system table exists ·
whether the Review App / MLflow feedback works · whether service policies (Beta) are available · whether the video is
enough for online judging · "Can Databricks set an auto-action threshold with a precision guarantee today?" (this
also counts as a mentor-visit insight).
**For the team:** the budget and cap for step 4 · confirm the declaration (§0).

## 9. Rules we follow
- **All code is new at the event** (organizers review repo history). Ideas carry over; code doesn't.
- Commit early and often to `wip` (reviewed by krish); merge to `main` only after team review. No backdating.
- API keys stay in `.env` only.
- Every number in the video or README comes from a real run. We say what we couldn't prove.

## Sources
- Opening deck: `Downloads\+BuildFest-2026-Opening-Ceremony.pptx.pdf`, slides 5, 8, 13, 15–18.
- Free Edition limits: https://docs.databricks.com/aws/en/getting-started/free-edition-limitations
- Usage table: https://docs.databricks.com/aws/en/ai-gateway/usage-tracking
- Service policies: https://www.databricks.com/blog/ai-governance-data-ai-summit-2026-whats-new-unity-ai-gateway
- MLflow feedback: https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/
- MLflow paired-comparison request: https://github.com/mlflow/mlflow/issues/26193
- Evidence sizes and the 142-duplicate count: computed from `assay_engine` and `data/` on Sep 26.
