# Submission kit: Devpost answers, 2-minute video script, Break Card

Draft for Sun Sep 27 (Devpost closes 11:00 CDT). Every number comes from `results/` or the Unity Catalog tables;
the source is in brackets. Edit the wording freely, but don't change a number without changing its source.

---

## 1. Devpost answers

**Title:** Assay: an AI agent manager that makes agents earn their freedom

**Tagline (≤ 200 chars):** Your AI agents want to act alone, run cheaper, and learn from corrections. Assay decides
with evidence when each is safe, and shows a manager exactly why, live on Databricks.

**Track / challenges:** Applied AI & Automation · Databricks Real-World Workflows (Xorbix) · The Art of the Break

### Inspiration
Companies either trust an AI agent completely and clean up after it, or check everything it does and lose the
point of having it. Nobody decides *with evidence* where the line is. And when the agent says "95% sure", that is
not evidence: in our tests a model that said 95%+ was right 4 times out of 19 [8B permission receipt].

### What it does
Assay sits between a company's AI agents and its human reviewers, and answers four questions with evidence:
1. **Act alone or ask?** An agent acts without a person only where its checked track record proves it (90% target,
   with a margin for luck). Otherwise it asks, and says how many more checks it needs.
2. **Which model answers?** Live model switching on Databricks: the cheaper model only if certified; a backup when a
   model is busy or returns junk, with the backup's answer held for review.
3. **Did a correction really help?** Every new rule or prompt is tested on fresh cases before it's switched on:
   "fixes N, breaks M".
4. **Reuse past reviewer decisions**, but only for kinds of cases where reviewers' answers are consistent enough to
   prove it.

A manager sees all of it in a plain-words dashboard on Databricks with a guided tour: what the agent did, what needs
their OK, what it has earned, and what was held back for safety.

The demo agent tidies up the public Apache Jira (Spark, Kafka, Flink, Hive): it spots tickets that are the same
problem or belong under a bigger project. 37,853 real tickets; 48% of tickets closed as duplicates were never linked
to their original [ASSAY_REPORT §4].

### How we built it
- **Databricks Free Edition end to end:** tickets and results in Unity Catalog (Delta), models through Foundation
  Model APIs (Llama 3.3 70B, Llama 3.1 8B, Qwen3-Next 80B, gpt-oss 120B), and the dashboard as a Databricks App
  (FastAPI + one page) whose service principal reads the tables, writes every Yes/No to a Delta table, and runs the
  agent live. 360 evaluation calls + live runs at $0.
- **Statistics:** one-sided Clopper-Pearson lower bounds, exact sign tests on before/after pairs, Bonferroni across
  relations, frozen hash-checked samples drawn from an honest stream (defined before any judging).
- **Labels:** maintainer links where they exist; an AI labeller (gpt-oss 120B) audited by a human spot check.
- **Python**, about 6,000 lines written at the event, 65 tests.

### Challenges we ran into
- Our first sample was balanced and had answers inserted: it would have faked precision. A teammate's review caught
  it; we rebuilt on an honest stream.
- Labels are hard: human-AI agreement was 11/20 overall, 8/9 on duplicates, 2/7 on "related". So we only make
  claims about duplicates.
- Free Edition has no Claude models, no readable gateway usage tables, and fallback routing only for external
  models, so we wrote our own live router. Its rate limits (HTTP 429) gave us a real live switch.
- Apps stop 24 h after a deploy; everything redeploys with one script.

### Accomplishments we're proud of
- Assay **blocked a plausible bad rule** ("version upgrades are duplicates") before use: fixed 0, broke 16,
  p = 1.5×10⁻⁵ [gate-v1-to-bad receipt].
- It **refused an over-confident cheap model**: 4 of 19 right at "95% sure", and 10 of 90 answers unreadable.
- A manager dashboard where every click is saved to Delta and feeds the proof, with a hands-on tour.
- We say what we could not prove: no model has earned the right to act alone yet.

### What we learned
A model's confidence is not evidence. "Needs 8 more checks" is a more useful answer than a made-up 95%. And the
hardest part of evaluating an agent is defining the stream and the labels honestly, not the model call.

### What's next for Assay
An API endpoint any agent can call (proposal in, "act / ask / hold" out); scheduled agent runs as a Databricks job;
more human reviews so patterns can be proven; more agents than Jira triage.

---

## 2. Two-minute video script (screen capture + voice)

| Time | Screen | Voice |
|---|---|---|
| 0:00–0:15 | Title card, then Apache Jira | "AI agents want more freedom: to act alone, to run on cheaper models, to learn from corrections. Most teams decide on gut feel. Assay decides with evidence." |
| 0:15–0:30 | Dashboard, top of page: the numbers, then the "What Assay decided" row | "This is Assay on Databricks. Our demo agent tidies the public Apache Jira. It read [N] tickets and suggested [M] tidy-ups (read them off the screen; they grow with every live run). It did zero on its own, because it hasn't earned that yet." |
| 0:30–0:55 | Earning your trust: under the version-upgrade bar, click "1 is in your list: show it"; point at "Seen before" on that card, answer No; the message says what moved (22 of 29) | "Every suggestion is in plain words, with the agent's reason and what reviewers said on similar cases. My answer is saved to a Delta table. Version-upgrade look-alikes: reviewers said No 21 of 21 times. About 8 more and Assay handles that kind for me." |
| 0:55–1:20 | Held back for your safety | "Here is what it was stopped from doing. A cheaper model said it was 95% sure about 19 merges; only 4 were right. Someone proposed a rule; tested first, it broke 16 decisions and fixed none. Blocked before it touched anything." |
| 1:20–1:40 | Press "Check new tickets now" (a summary card appears); then Which AI answered: the pinned "Latest switch" | "Now live: the agent reads three new tickets on Databricks. The main model answers; when it's busy, Assay switches to a backup on the spot and holds that answer for review." |
| 1:40–1:55 | What it saved you | "All at zero AI cost on Databricks Free Edition, 31 wrong changes prevented, and every number is counted, not estimated." |
| 1:55–2:00 | Logo + repo link | "Assay: agents earn their freedom." |

Tip: open the dashboard with `#tour` for a clean first frame; record in one take and trim.

Before recording: only one version-upgrade case is open. If someone answers it before the take, "show it" disappears;
then point at the bar ("22 so far · 29 prove it") instead. Don't answer cards at random while rehearsing: each
answer is real evidence. The colour switch in the top bar picks light or dark for the recording.

---

## 3. Break Card (The Art of the Break)

**What broke, how we found it, what we changed.**

| # | What broke | Number | How we found it | What we changed |
|---|---|---|---|---|
| 1 | "95% sure" is not 95% right | 4 of 19 right (8B) | permission receipt on audited labels | Autonomy is gated on checked outcomes, never on the model's own confidence |
| 2 | A plausible correction was poison | fixed 0, broke 16, p = 1.5×10⁻⁵ | learning gate on 30 fresh tickets | Every correction is tested before it's switched on |
| 3 | The cheap model's output was unusable | 10 of 90 tasks (11%) | format failures counted as failures | Cost comparisons include failures |
| 4 | The big model over-links | 60 of 90 tickets "related" | Stage 2 run | "Related" stays suggest-only |
| 5 | New instructions: no proof they're better | fixed 3, broke 3 | learning gate | Old instructions stay (UNPROVEN) |
| 6 | Our own sample was rigged | balanced classes + inserted answers | teammate code review | Honest stream defined before judging; frozen hash-checked plans |
| 7 | Labellers disagree | 11/20 overall; 2/7 on "related" | two human spot-check rounds | Claims only where labels agree (duplicates 8/9) |
| 8 | Models get busy under load | 1 live switch in a 16-way burst | routing log | Backups answer, but uncertified answers are held for review |
| 9 | The "cheap" model was the expensive one | +90.5% cost | first hardness test (Claude CLI) | Control how a model runs before comparing costs |

Sources: `results/stage-2-3-runs/VERDICTS.md`, `receipts-ai/`, `results/routing-log.jsonl`, `docs/ASSAY_REPORT.md` §9.

---

## 4. Checklist before 11:00

- [ ] Redeploy the dashboard (`python scripts/deploy_manager.py`) on Sunday morning; open it once to wake the warehouse.
- [ ] README: link the dashboard, the report and this kit.
- [ ] Record and upload the video (≤ 2 min).
- [ ] Devpost: paste section 1, add repo + video links, declare Xorbix + Art of the Break.
- [ ] Three mentor visits logged; Break Card attached.
- [ ] Rotate the API key that was pasted in chat.
