# Heavy evaluation on Databricks (8 models)

Plan `05c9f2397fd3`: 300 stream tickets (precision) + 93 maintainer-confirmed duplicates (recall, reported separately). Prompt v2. Graded only against the Apache maintainers' own record. Strict = unlinked counted wrong; decided = only cases the record settles.

| Model | Answered | Unusable | Actions | Strict precision [95% lower] | Decided | ≥0.95 conf: strict | Confident & contradicted | Dup recall | p50 s | Tokens/task | $/1k tasks* |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5 122B | 46/307 | 0 | 24 | 42% [25%] | 71% | 64% (n=11) | 1 | 10/12 | 43.9 | 4916 | 9.251 |
| gpt-oss 120B | 518/523 | 26 | 291 | 33% [29%] | 72% | 40% (n=60) | 18 | 50/91 | 4.1 | 1448 | 0.512 |
| gpt-oss 20B | 523/523 | 15 | 270 | 29% [25%] | 59% | 33% (n=48) | 20 | 63/93 | 5.6 | 1516 | 0.271 |
| Llama 3.3 70B | 523/523 | 0 | 285 | 29% [24%] | 57% | 17% (n=12) | 6 | 59/93 | 4.7 | 915 | 0.626 |
| Llama 4 Maverick | 521/523 | 2 | 296 | 24% [20%] | 40% | 9% (n=22) | 14 | 73/92 | 3.8 | 916 | 0.654 |
| Qwen3-Next 80B | 514/523 | 31 | 292 | 21% [17%] | 32% | 17% (n=155) | 99 | 61/89 | 4.3 | 1038 | 0.438 |
| Gemma 3 12B | 523/523 | 2 | 292 | 9% [7%] | 14% | 5% (n=198) | 149 | 51/93 | 5.4 | 1126 | 0.274 |
| Llama 3.1 8B | 521/523 | 39 | 298 | 4% [3%] | 6% | 2% (n=83) | 68 | 54/93 | 1.7 | 959 | 0.213 |

## Assay's verdict per model

| Model | Role (cheapest proven wins) | Why | Acts alone? | vs Llama 3.3 70B (same tickets) |
|---|---|---|---|---|
| gpt-oss 120B | backup | meets every rule; used when the main model is busy, its answers wait for review | no (said 95%+ sure and was contradicted 18 of 60 times) | better on 38, worse on 17 (p=0.00646) |
| gpt-oss 20B | main | cheapest model that meets every rule | no (said 95%+ sure and was contradicted 20 of 48 times) | better on 25, worse on 26 (p=1) |
| Llama 3.3 70B | backup | meets every rule; used when the main model is busy, its answers wait for review | no (said 95%+ sure and was contradicted 6 of 12 times) | – |
| Qwen3.5 122B | not used | only 46 answers so far (needs 100) | no (right on only 10 of 14 answers the record can check) | better on 4, worse on 0 (p=0.125) |
| Llama 4 Maverick | not used | 40% right vs 57% for Llama 70B; worse on the same tickets (50 vs 7) | no (right on only 70 of 176 answers the record can check; said 95%+ sure and was contradicted 14 of 22 times) | better on 7, worse on 50 (p=4.24e-09) |
| Qwen3-Next 80B | not used | 6% unreadable answers (limit 5%); 32% right vs 57% for Llama 70B; worse on the same tickets (75 vs 6) | no (right on only 62 of 193 answers the record can check; 31 of 523 answers unreadable; said 95%+ sure and was contradicted 99 of 155 times) | better on 6, worse on 75 (p=2.91e-16) |
| Gemma 3 12B | not used | 14% right vs 57% for Llama 70B; worse on the same tickets (104 vs 3) | no (right on only 27 of 193 answers the record can check; said 95%+ sure and was contradicted 149 of 198 times) | better on 3, worse on 104 (p=2.52e-27) |
| Llama 3.1 8B | not used | 7% unreadable answers (limit 5%); 6% right vs 57% for Llama 70B; worse on the same tickets (158 vs 9) | no (right on only 13 of 228 answers the record can check; 39 of 523 answers unreadable; said 95%+ sure and was contradicted 68 of 83 times) | better on 9, worse on 158 (p=2.53e-36) |

## Coverage: does every claim reach a verdict?

| Claim | Evidence | 95% interval | Status |
|---|---|---|---|
| Gemma 3 12B may act alone on "same problem" (when 95%+ sure) | 0/38 | 0–10% | disproven |
| Gemma 3 12B may act alone on "part of a bigger project" (when 95%+ sure) | 7/152 | 2–10% | disproven |
| Gemma 3 12B may act alone on "connected" (when 95%+ sure) | 3/8 | 7–78% | disproven |
| gpt-oss 120B may act alone on "same problem" (when 95%+ sure) | 0/13 | 0–27% | disproven |
| gpt-oss 120B may act alone on "part of a bigger project" (when 95%+ sure) | 11/24 | 24–69% | disproven |
| gpt-oss 120B may act alone on "connected" (when 95%+ sure) | 13/23 | 33–78% | disproven |
| gpt-oss 20B may act alone on "same problem" (when 95%+ sure) | 0/17 | 0–21% | disproven |
| gpt-oss 20B may act alone on "part of a bigger project" (when 95%+ sure) | 9/21 | 20–68% | disproven |
| gpt-oss 20B may act alone on "connected" (when 95%+ sure) | 7/10 | 32–94% | undecided |
| Llama 3.1 8B may act alone on "same problem" (when 95%+ sure) | 1/51 | 0–11% | disproven |
| Llama 3.1 8B may act alone on "part of a bigger project" (when 95%+ sure) | 1/30 | 0–18% | disproven |
| Llama 3.1 8B may act alone on "connected" (when 95%+ sure) | 0/2 | 0–87% | disproven |
| Llama 3.3 70B may act alone on "same problem" (when 95%+ sure) | 0/9 | 0–37% | disproven |
| Llama 3.3 70B may act alone on "part of a bigger project" (when 95%+ sure) | 2/3 | 8–99% | undecided |
| Llama 3.3 70B may act alone on "connected" (when 95%+ sure) | 0/0 | 0–100% | undecided |
| Llama 4 Maverick may act alone on "same problem" (when 95%+ sure) | 0/8 | 0–40% | disproven |
| Llama 4 Maverick may act alone on "part of a bigger project" (when 95%+ sure) | 2/14 | 1–45% | disproven |
| Llama 4 Maverick may act alone on "connected" (when 95%+ sure) | 0/0 | 0–100% | undecided |
| Qwen3-Next 80B may act alone on "same problem" (when 95%+ sure) | 1/62 | 0–9% | disproven |
| Qwen3-Next 80B may act alone on "part of a bigger project" (when 95%+ sure) | 10/75 | 6–24% | disproven |
| Qwen3-Next 80B may act alone on "connected" (when 95%+ sure) | 15/18 | 57–97% | undecided |
| Qwen3.5 122B may act alone on "same problem" (when 95%+ sure) | 0/1 | 0–98% | undecided |
| Qwen3.5 122B may act alone on "part of a bigger project" (when 95%+ sure) | 2/3 | 8–99% | undecided |
| Qwen3.5 122B may act alone on "connected" (when 95%+ sure) | 5/7 | 26–97% | undecided |
| Past answers can be reused: "connected" for a version upgrade vs an earlier upgrade of the same library to a different version (answer: Yes) | 30/34 | 75–96% | undecided |
| Past answers can be reused: "same problem" for two tickets with the same title (answer: Yes) | 20/32 | 46–77% | disproven |
| Past answers can be reused: "connected" for two failing or flaky test reports (answer: Yes) | 6/6 | 61–100% | undecided (≈23 more) |
| Past answers can be reused: "same problem" for two failing or flaky test reports (answer: No) | 30/35 | 72–94% | undecided |
| Past answers can be reused: "same problem" for a version upgrade vs an earlier upgrade of the same library to a different version (answer: No) | 115/116 | 96–100% | proven |
| Past answers can be reused: "same problem" for two upgrades of the same library to the same version (answer: Yes) | 10/18 | 34–76% | disproven |
| Past answers can be reused: "part of a bigger project" for a version upgrade vs an earlier upgrade of the same library to a different version (answer: No) | 86/86 | 97–100% | proven |
| Past answers can be reused: "part of a bigger project" for two tickets with the same title (answer: No) | 3/3 | 37–100% | undecided (≈26 more) |
| Past answers can be reused: "part of a bigger project" for two failing or flaky test reports (answer: No) | 3/3 | 37–100% | undecided (≈26 more) |
| Past answers can be reused: "part of a bigger project" for two upgrades of the same library to the same version (answer: No) | 9/9 | 72–100% | undecided (≈20 more) |
| Past answers can be reused: "connected" for two upgrades of the same library to the same version (answer: Yes) | 1/1 | 5–100% | undecided (≈28 more) |
| "part of a bigger project" suggestions are right (all models, all kinds of case) | 90/726 | 10–15% | disproven |
| "connected" suggestions are right (all models, all kinds of case, unlinked counted as not shown) | 456/1533 | 28–32% | disproven |
| "same problem" suggestions are right (all models, all kinds of case) | 425/1013 | 39–45% | disproven |
| "connected" suggestions are right, for tickets with no special pattern | 59/698 | 7–10% | disproven |
| "same problem" suggestions are right, for tickets with no special pattern | 230/485 | 44–51% | disproven |
| "connected" suggestions are right, for a version upgrade vs an earlier upgrade of the same library to a different version | 33/237 | 10–18% | disproven |
| "connected" suggestions are right, for two failing or flaky test reports | 11/214 | 3–8% | disproven |
| "same problem" suggestions are right, for two tickets with the same title | 115/150 | 70–82% | disproven |
| "same problem" suggestions are right, for a version upgrade vs an earlier upgrade of the same library to a different version | 3/136 | 1–6% | disproven |
| "same problem" suggestions are right, for two failing or flaky test reports | 20/92 | 15–30% | disproven |
| "same problem" suggestions are right, for two upgrades of the same library to the same version | 54/74 | 63–81% | disproven |
| "connected" suggestions are right, for two upgrades of the same library to the same version | 1/22 | 0–20% | disproven |
| "connected" suggestions are right, for two tickets with the same title | 0/10 | 0–26% | disproven |
| "any link" suggestions are right, for tickets in different Apache projects | 0/46 | 0–6% | disproven |

## Past-decision patterns (753 decisions: {'ai': 77, 'human': 18, 'maintainer': 658})

| Relation | Kind of case | Answer | Agree | Lower | Handled automatically? |
|---|---|---|---|---|---|
| duplicate | no recognised pattern | reject | 144/197 | 0.67 | no |
| part_of | no recognised pattern | reject | 141/145 | 0.94 | no |
| duplicate | a version upgrade vs an earlier upgrade of the same library to a different version | reject | 115/116 | 0.96 | yes |
| part_of | a version upgrade vs an earlier upgrade of the same library to a different version | reject | 86/86 | 0.97 | yes |
| related | no recognised pattern | accept | 41/45 | 0.81 | no |
| duplicate | two failing or flaky test reports | reject | 30/35 | 0.72 | no |
| related | a version upgrade vs an earlier upgrade of the same library to a different version | accept | 30/34 | 0.75 | no |
| duplicate | two tickets with the same title | accept | 20/32 | 0.46 | no |
| duplicate | two upgrades of the same library to the same version | accept | 10/18 | 0.34 | no |
| related | two sub-tasks of the same parent | accept | 8/9 | 0.57 | no |
| part_of | two upgrades of the same library to the same version | reject | 9/9 | 0.72 | no (≈20 more) |
| part_of | two sub-tasks of the same parent | reject | 5/7 | 0.34 | no |
| related | two failing or flaky test reports | accept | 6/6 | 0.61 | no (≈23 more) |
| duplicate | two sub-tasks of the same parent | reject | 4/5 | 0.34 | no |
| part_of | two tickets with the same title | reject | 3/3 | 0.37 | no (≈26 more) |
| part_of | two failing or flaky test reports | reject | 3/3 | 0.37 | no (≈26 more) |
| part_of | the earlier ticket is already the new ticket's parent | accept | 2/2 | 0.22 | no (≈27 more) |
| related | two upgrades of the same library to the same version | accept | 1/1 | 0.05 | no (≈28 more) |

Leave-one-out: auto-resolved 202 of 753, right 201 (lower bound 0.98)

*List price: DBU per 1M tokens from databricks.com (fetched 2026-09-27) × an ASSUMED $0.07/DBU. Our actual cost on Free Edition: $0.

## Live router (normal = alone; stress = alongside 32 evaluation calls)

```
{
 "normal": {
  "requests": 300,
  "switches": 179,
  "held_for_review": 226,
  "unanswered": 47,
  "answered_by": {
   "gpt-oss 20B": 74,
   "gpt-oss 120B": 90,
   "Llama 3.3 70B": 89,
   "nobody": 47
  },
  "busy_events": 402,
  "unusable_events": 7,
  "latency_ms_p50": 5001,
  "precision": {
   "n": 233,
   "confirmed": 70,
   "contradicted": 35,
   "unlinked": 128,
   "strict": 0.30042918454935624,
   "strict_lower": 0.2509973869121688,
   "decided": 0.6666666666666666,
   "optimistic": 0.8497854077253219
  },
  "precision_trusted": {
   "n": 62,
   "confirmed": 20,
   "contradicted": 11,
   "unlinked": 31,
   "strict": 0.3225806451612903,
   "strict_lower": 0.22508405786741528,
   "decided": 0.6451612903225806,
   "optimistic": 0.8225806451612904
  },
  "precision_held": {
   "n": 171,
   "confirmed": 50,
   "contradicted": 24,
   "unlinked": 97,
   "strict": 0.29239766081871343,
   "strict_lower": 0.23530935720437,
   "decided": 0.6756756756756757,
   "optimistic": 0.8596491228070176
  }
 },
 "stress": {
  "requests": 300,
  "switches": 78,
  "held_for_review": 215,
  "unanswered": 137,
  "answered_by": {
   "Llama 3.3 70B": 85,
   "Qwen3-Next 80B": 59,
   "gpt-oss 120B": 19,
   "nobody": 137
  },
  "busy_events": 501,
  "unusable_events": 7,
  "latency_ms_p50": 4557,
  "precision": {
   "n": 157,
   "confirmed": 43,
   "contradicted": 41,
   "unlinked": 73,
   "strict": 0.27388535031847133,
   "strict_lower": 0.21575946572973306,
   "decided": 0.5119047619047619,
   "optimistic": 0.7388535031847133
  },
  "precision_trusted": {
   "n": 79,
   "confirmed": 20,
   "contradicted": 17,
   "unlinked": 42,
   "strict": 0.25316455696202533,
   "strict_lower": 0.1745252603424512,
   "decided": 0.5405405405405406,
   "optimistic": 0.7848101265822784
  },
  "precision_held": {
   "n": 78,
   "confirmed": 23,
   "contradicted": 24,
   "unlinked": 31,
   "strict": 0.2948717948717949,
   "strict_lower": 0.21065508033063454,
   "decided": 0.48936170212765956,
   "optimistic": 0.6923076923076923
  }
 }
}
```

## Edge cases (stream, all models pooled)

| Relation | Kind of case | Actions | Confirmed | Contradicted | Unlinked |
|---|---|---|---|---|---|
| related | other | 698 | 59 | 0 | 639 |
| duplicate | other | 541 | 230 | 255 | 56 |
| part_of | other | 468 | 0 | 311 | 157 |
| related | siblings | 351 | 351 | 0 | 0 |
| related | bump-same-lib-diff-version | 237 | 33 | 0 | 204 |
| related | both-test-failures | 214 | 11 | 0 | 203 |
| part_of | siblings | 194 | 0 | 194 | 0 |
| duplicate | same-title | 173 | 115 | 35 | 23 |
| duplicate | bump-same-lib-diff-version | 136 | 3 | 133 | 0 |
| part_of | bump-same-lib-diff-version | 121 | 0 | 111 | 10 |
| duplicate | both-test-failures | 120 | 20 | 72 | 28 |
| part_of | candidate-is-parent | 90 | 90 | 0 | 0 |
| duplicate | bump-same-lib-same-version | 77 | 54 | 20 | 3 |
| duplicate | siblings | 72 | 3 | 69 | 0 |
| related | bump-same-lib-same-version | 22 | 1 | 0 | 21 |
| part_of | both-test-failures | 14 | 0 | 7 | 7 |
| part_of | bump-same-lib-same-version | 12 | 0 | 10 | 2 |
| related | same-title | 10 | 0 | 0 | 10 |
| part_of | same-title | 7 | 0 | 3 | 4 |
| duplicate | candidate-is-parent | 4 | 0 | 4 | 0 |
| related | candidate-is-parent | 1 | 1 | 0 | 0 |
| any | cross-project | 116 | 0 | 46 | 70 |
