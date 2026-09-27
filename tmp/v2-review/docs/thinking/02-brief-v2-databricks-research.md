# Assay: team brief v2 (Sat Sep 26, ~17:00)

*Updates TEAM_BRIEF.md (v1, ~14:30) with this afternoon's Databricks research. Details and sources are in
**ON_TOP_OF_DATABRICKS.md**. Changes from v1 are marked **(new)**.*

## 1. The idea in one paragraph
**Assay is a proof engine for AI agents.** Databricks already lets you run, trace, grade, label and restrict an agent.
But every decision about **how far to trust it** is still a human guess: an admin's policy, a threshold picked by eye,
a score with no error bar. **Assay decides from evidence**: which actions the agent may take alone, whether a change
really helped, whether a cheaper setup is safe. Or it says "not proven yet, needs N more." The demo agent triages the
public Apache Jira and runs on **Databricks**.

**(new) Pitch line:** *Databricks collects the evidence and enforces the rules. Assay decides what the rules should be.*

## 2. The three questions, in priority order **(new order)**
| # | Question | Verdicts | Status |
|---|---|---|---|
| 1 | **Can the agent act alone?** (the lead) | AUTO above t / SUGGEST / QUIET / needs N more | Proving ≥ 90% precision takes 29 of 29 correct in the zone, or 46 with 1 mistake |
| 2 | **Can it run cheaper?** | certify / reject / needs N more | Re-run Haiku with thinking off before claiming anything |
| 3 | **Did the change really help?** | keep / discard / unproven | 1 hour. Held-out tickets only |

## 3. The demo agent (as v1, plus two honesty notes)
For each new **Apache Jira** ticket (Spark, Flink, Kafka, Hive), the agent decides: **duplicate**, **part of** an
umbrella, **related**, or **new**. It links, nests or flags the ticket. Humans accept or reject in a review app, and
every click becomes evidence for Assay.
- **(new)** Atlassian's Rovo already suggests duplicate Jira items. **The agent is our test case, not the product.**
- **(new)** We don't write to Apache's real Jira. "Acts" means writing links to our own table; in production this
  step would call the Jira API.

## 4. What Assay adds on top of Databricks **(new)**
| | What Assay adds | Databricks piece it builds on |
|---|---|---|
| A1 | **Earned autonomy:** a proven auto zone per action type, written to `assay.permissions`. The agent asks `assay.can_act()` before acting | MLflow traces, Unity Catalog function. It's the evidence an approval policy (Beta) would need |
| A2 | **Judge + a few human labels = an honest number** with an interval (prediction-powered inference), plus "label these next" | MLflow judges, Review App feedback. Databricks' judge alignment improves the judge; this corrects what's left |
| A3 | **Change gate:** fixes vs breaks on held-out tickets (sign test) | MLflow compares averages only (a feature request for significance tests was filed today) |
| A4 | **True cost per task** including thinking and cache tokens, judged together with quality | `system.ai_gateway.usage` has cache and reasoning-token columns but no dollars |
| A5 | **Re-check over time:** demote AUTO to SUGGEST when evidence drops (fixed checkpoints) | Jobs. Data Quality Monitoring flags drift but doesn't change what the agent may do |
| A6 | **Evidence receipts:** every verdict and auto-action links to the tickets that proved it | Delta and Unity Catalog. Xorbix asks to "show sources" |
| A7 | **Calibration report:** stated confidence vs actual precision | Break Card evidence |

## 5. Real results so far (as v1, with corrections)
**Overnight lab** (`overnight-lab/report.md`): 518 real Claude runs (514 ok), $33.01 of API-equivalent usage, $0 paid.
- Switching one turn from Opus to Sonnet cost **4.1×** staying on Opus.
- Subagents started in parallel **each** pay the full cold-cache cost.
- A setup used only occasionally cost **2.25×** per task (small sample).
- Cost per task vs Opus high: Opus-low **−19%**, Sonnet **−38%**, Haiku **−70%**.
- **Every model scored 100%, including on the hard question types.** The invented question world can't separate
  models, which is why we moved to real Jira data.

**Real Apache Jira** (37,853 tickets since 2023): as in v1.
- 48% of duplicate closures never link to the original.
- Top-10 search recall: duplicate 72.5%, part-of 57.2%, related 49.4%.
- Precision on 60 tickets: 50–67% for duplicate and part-of; about 8% for related.

**(new) Two corrections before anything goes in the video:**
- **Haiku +90% is a result about our setup (thinking on), not about the model.** It contradicts the lab's −70%.
  Re-run with thinking off, then tell it as "Assay caught that our cheap setup was the expensive one."
- **Maintainer links miss true duplicates.** So precision measured against them is a **floor**. That's safe for
  proving the auto zone, but it understates the agent. Human review of the "wrong" ones rescues the true finds.

## 6. Databricks facts that change the plan **(new)**
- **Free Edition has no Agent Bricks** (Knowledge Assistant is listed as unsupported). Don't build on it.
- **Apps stop 24 hours after they start**, and the challenges are judged online until Sep 30.
  **The video and screenshots have to carry the demo.**
- **Outbound internet is limited to "trusted domains."** Download Jira on a laptop and upload it to a volume.
- One AI Search endpoint. Foundation Model APIs are available, but "certain models unavailable": check which.
- The usage table records cache and thinking tokens, so Q2 can run natively on Databricks.
- Contextual Service Policies (Beta) can "require approval" for actions, but admins set them by hand.
  Assay's permissions table is what should set them.

## 7. Next steps (revised order) and suggested owners
1. **Re-run Haiku with thinking off, and apply the prompt fix** (siblings aren't the umbrella; "related" is suggest-only). *(Engine)*
2. **Scale to ~300 tickets, weighted toward duplicates**, so one zone can reach the 29–46 examples a proof needs.
   Count siblings under one umbrella as one cluster. *(Data)*
3. **A1:** permissions table, `assay.can_act`, receipts (A6). Check that the threshold scan is fixed-sequence,
   not "pick the best." *(Engine)*
4. **Databricks:** workspace, volume and tables, model endpoint, app deployed, review clicks saved as MLflow feedback. *(Platform)*
5. **A7 calibration table, then the Break Card** (part-of overconfidence). *(Story)*
6. If time allows: A2 on the open backlog, A3 on held-out tickets, A4 joint cost verdict. *(Engine + Data)*
7. **Demo video while the app is running**, Devpost answers, the three mentor visits. *(Everyone)*

## 8. Open questions
**For Xorbix:**
- Which models work on Free Edition, and what are the rate limits?
- Is the usage system table available?
- Does the Review App work?
- Can a notebook reach issues.apache.org?
- Can we use the Beta approval policies?
- Is a video enough for online judging, given that apps stop after 24 hours?
- "Can Databricks set an auto-action threshold with a precision guarantee today?" This also counts as a mentor-visit insight.

**For the team:**
- Budget for step 2: whose API key, and what's the cap?
- Challenges: the opening deck said team, track and challenges were declared by **noon Saturday** via QR. Confirm the
  Devpost selection counts, and that Databricks (Xorbix) + Art of the Break are on it.

## 9. Rules we follow
- **All code is new at the event** (the organizers review repo history). Ideas carry over; code doesn't.
- Nothing merges to `main` in `Ananda-001/Badger-Build-Fest` until the team has reviewed it.
  **(new, proposed)** Commit to a `wip` branch every few hours anyway. The organizers expect steady commits, and one
  big commit near the deadline looks imported.
- API keys stay in `.env` only. **(new, proposed)** Rotate the key that was pasted in chat **now**, not after the event,
  and put a spending cap on the key used for step 2.
- Every number in the video or README has to come from a real run. We say what we couldn't prove.
