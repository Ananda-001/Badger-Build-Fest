# Heavy evaluation on Databricks (8 models)

Plan `05c9f2397fd3`: 300 stream tickets (precision) + 93 maintainer-confirmed duplicates (recall, reported separately). Prompt v2. Graded only against the Apache maintainers' own record. Strict = unlinked counted wrong; decided = only cases the record settles.

| Model | Answered | Unusable | Actions | Strict precision [95% lower] | Decided | ≥0.95 conf: strict | Confident & contradicted | Dup recall | p50 s | Tokens/task | $/1k tasks* |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.5 122B | 46/307 | 0 | 24 | 42% [25%] | 71% | 64% (n=11) | 1 | 10/12 | 43.9 | 4916 | 9.251 |
| gpt-oss 120B | 409/473 | 24 | 286 | 33% [28%] | 72% | 39% (n=59) | 18 | 27/46 | 4.4 | 1422 | 0.509 |
| gpt-oss 20B | 410/473 | 14 | 263 | 29% [25%] | 59% | 34% (n=47) | 19 | 41/56 | 6.1 | 1494 | 0.272 |
| Llama 3.3 70B | 356/425 | 0 | 281 | 29% [24%] | 58% | 18% (n=11) | 5 | 29/41 | 3.9 | 870 | 0.603 |
| Llama 4 Maverick | 521/523 | 2 | 296 | 24% [20%] | 40% | 9% (n=22) | 14 | 73/92 | 3.8 | 916 | 0.654 |
| Qwen3-Next 80B | 514/523 | 31 | 292 | 21% [17%] | 32% | 17% (n=155) | 99 | 61/89 | 4.3 | 1038 | 0.438 |
| Gemma 3 12B | 523/523 | 2 | 292 | 9% [7%] | 14% | 5% (n=198) | 149 | 51/93 | 5.4 | 1126 | 0.274 |
| Llama 3.1 8B | 521/523 | 39 | 298 | 4% [3%] | 6% | 2% (n=83) | 68 | 54/93 | 1.7 | 959 | 0.213 |

## Assay's verdict per model

| Model | Role (cheapest proven wins) | Why | Acts alone? | vs Llama 3.3 70B (same tickets) |
|---|---|---|---|---|
| gpt-oss 120B | backup | 5% unreadable answers (limit 5%). Used only when the main model is busy; its answers wait for review | no (24 of 473 answers unreadable; said 95%+ sure and was contradicted 18 of 59 times) | better on 38, worse on 17 (p=0.00646) |
| gpt-oss 20B | main | cheapest model that meets every rule | no (said 95%+ sure and was contradicted 19 of 47 times) | better on 25, worse on 25 (p=1) |
| Llama 3.3 70B | backup | meets every rule; used when the main model is busy, its answers wait for review | no (said 95%+ sure and was contradicted 5 of 11 times) | – |
| Qwen3.5 122B | not used | only 46 answers so far (needs 100) | no (right on only 10 of 14 answers the record can check) | better on 4, worse on 0 (p=0.125) |
| Llama 4 Maverick | not used | 40% right vs 58% for Llama 70B; worse on the same tickets (50 vs 7) | no (right on only 70 of 176 answers the record can check; said 95%+ sure and was contradicted 14 of 22 times) | better on 7, worse on 50 (p=4.24e-09) |
| Qwen3-Next 80B | not used | 6% unreadable answers (limit 5%); 32% right vs 58% for Llama 70B; worse on the same tickets (74 vs 6) | no (right on only 62 of 193 answers the record can check; 31 of 523 answers unreadable; said 95%+ sure and was contradicted 99 of 155 times) | better on 6, worse on 74 (p=5.4e-16) |
| Gemma 3 12B | not used | 14% right vs 58% for Llama 70B; worse on the same tickets (103 vs 3) | no (right on only 27 of 193 answers the record can check; said 95%+ sure and was contradicted 149 of 198 times) | better on 3, worse on 103 (p=4.9e-27) |
| Llama 3.1 8B | not used | 7% unreadable answers (limit 5%); 6% right vs 58% for Llama 70B; worse on the same tickets (157 vs 8) | no (right on only 13 of 228 answers the record can check; 39 of 523 answers unreadable; said 95%+ sure and was contradicted 68 of 83 times) | better on 8, worse on 157 (p=5.16e-37) |

## Coverage: does every claim reach a verdict?

| Claim | Evidence | 95% interval | Status |
|---|---|---|---|
| Gemma 3 12B may act alone on "same problem" (when 95%+ sure) | 0/38 | 0–10% | disproven |
| Gemma 3 12B may act alone on "part of a bigger project" (when 95%+ sure) | 7/152 | 2–10% | disproven |
| Gemma 3 12B may act alone on "connected" (when 95%+ sure) | 3/8 | 7–78% | disproven |
| gpt-oss 120B may act alone on "same problem" (when 95%+ sure) | 0/13 | 0–27% | disproven |
| gpt-oss 120B may act alone on "part of a bigger project" (when 95%+ sure) | 10/23 | 22–67% | disproven |
| gpt-oss 120B may act alone on "connected" (when 95%+ sure) | 13/23 | 33–78% | disproven |
| gpt-oss 20B may act alone on "same problem" (when 95%+ sure) | 0/17 | 0–21% | disproven |
| gpt-oss 20B may act alone on "part of a bigger project" (when 95%+ sure) | 9/20 | 22–70% | disproven |
| gpt-oss 20B may act alone on "connected" (when 95%+ sure) | 7/10 | 32–94% | undecided |
| Llama 3.1 8B may act alone on "same problem" (when 95%+ sure) | 1/51 | 0–11% | disproven |
| Llama 3.1 8B may act alone on "part of a bigger project" (when 95%+ sure) | 1/30 | 0–18% | disproven |
| Llama 3.1 8B may act alone on "connected" (when 95%+ sure) | 0/2 | 0–87% | disproven |
| Llama 3.3 70B may act alone on "same problem" (when 95%+ sure) | 0/8 | 0–40% | disproven |
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
| Past answers can be reused: "connected" for a version upgrade vs an earlier upgrade of the same library to a different version (answer: Yes) | 23/27 | 69–95% | undecided |
| Past answers can be reused: "same problem" for two tickets with the same title (answer: Yes) | 20/31 | 48–79% | disproven |
| Past answers can be reused: "connected" for two failing or flaky test reports (answer: Yes) | 5/5 | 55–100% | undecided (≈24 more) |
| Past answers can be reused: "same problem" for two failing or flaky test reports (answer: No) | 30/35 | 72–94% | undecided |
| Past answers can be reused: "same problem" for a version upgrade vs an earlier upgrade of the same library to a different version (answer: No) | 115/116 | 96–100% | proven |
| Past answers can be reused: "same problem" for two upgrades of the same library to the same version (answer: Yes) | 10/18 | 34–76% | disproven |
| Past answers can be reused: "part of a bigger project" for a version upgrade vs an earlier upgrade of the same library to a different version (answer: No) | 86/86 | 97–100% | proven |
| Past answers can be reused: "part of a bigger project" for two tickets with the same title (answer: No) | 3/3 | 37–100% | undecided (≈26 more) |
| Past answers can be reused: "part of a bigger project" for two failing or flaky test reports (answer: No) | 3/3 | 37–100% | undecided (≈26 more) |
| Past answers can be reused: "part of a bigger project" for two upgrades of the same library to the same version (answer: No) | 9/9 | 72–100% | undecided (≈20 more) |
| Past answers can be reused: "connected" for two upgrades of the same library to the same version (answer: Yes) | 1/1 | 5–100% | undecided (≈28 more) |
| "part of a bigger project" suggestions are right (all models, all kinds of case) | 88/709 | 10–15% | disproven |
| "connected" suggestions are right (all models, all kinds of case) | 404/404 | 99–100% | proven |
| "same problem" suggestions are right (all models, all kinds of case) | 350/907 | 36–41% | disproven |
| "connected" suggestions are right, for tickets with no special pattern | 39/39 | 93–100% | proven |
| "same problem" suggestions are right, for tickets with no special pattern | 193/435 | 40–48% | disproven |
| "connected" suggestions are right, for a version upgrade vs an earlier upgrade of the same library to a different version | 23/23 | 88–100% | undecided (≈6 more) |
| "connected" suggestions are right, for two failing or flaky test reports | 7/7 | 65–100% | undecided (≈22 more) |
| "same problem" suggestions are right, for two tickets with the same title | 89/118 | 68–82% | disproven |
| "same problem" suggestions are right, for a version upgrade vs an earlier upgrade of the same library to a different version | 3/136 | 1–6% | disproven |
| "same problem" suggestions are right, for two failing or flaky test reports | 17/80 | 14–30% | disproven |
| "same problem" suggestions are right, for two upgrades of the same library to the same version | 46/65 | 60–80% | disproven |
| "connected" suggestions are right, for two upgrades of the same library to the same version | 1/1 | 5–100% | undecided (≈28 more) |
| "connected" suggestions are right, for two tickets with the same title | 0/0 | 0–100% | undecided |
| "any link" suggestions are right, for tickets in different Apache projects | 0/45 | 0–6% | disproven |

## Past-decision patterns (732 decisions: {'ai': 77, 'human': 18, 'maintainer': 637})

| Relation | Kind of case | Answer | Agree | Lower | Handled automatically? |
|---|---|---|---|---|---|
| duplicate | no recognised pattern | reject | 142/195 | 0.67 | no |
| part_of | no recognised pattern | reject | 140/144 | 0.94 | no |
| duplicate | a version upgrade vs an earlier upgrade of the same library to a different version | reject | 115/116 | 0.96 | yes |
| part_of | a version upgrade vs an earlier upgrade of the same library to a different version | reject | 86/86 | 0.97 | yes |
| related | no recognised pattern | accept | 32/36 | 0.76 | no |
| duplicate | two failing or flaky test reports | reject | 30/35 | 0.72 | no |
| duplicate | two tickets with the same title | accept | 20/31 | 0.48 | no |
| related | a version upgrade vs an earlier upgrade of the same library to a different version | accept | 23/27 | 0.69 | no |
| duplicate | two upgrades of the same library to the same version | accept | 10/18 | 0.34 | no |
| related | two sub-tasks of the same parent | accept | 8/9 | 0.57 | no |
| part_of | two upgrades of the same library to the same version | reject | 9/9 | 0.72 | no (≈20 more) |
| part_of | two sub-tasks of the same parent | reject | 5/7 | 0.34 | no |
| duplicate | two sub-tasks of the same parent | reject | 4/5 | 0.34 | no |
| related | two failing or flaky test reports | accept | 5/5 | 0.55 | no (≈24 more) |
| part_of | two tickets with the same title | reject | 3/3 | 0.37 | no (≈26 more) |
| part_of | two failing or flaky test reports | reject | 3/3 | 0.37 | no (≈26 more) |
| part_of | the earlier ticket is already the new ticket's parent | accept | 2/2 | 0.22 | no (≈27 more) |
| related | two upgrades of the same library to the same version | accept | 1/1 | 0.05 | no (≈28 more) |

Leave-one-out: auto-resolved 202 of 732, right 201 (lower bound 0.98)

*List price: DBU per 1M tokens from databricks.com (fetched 2026-09-27) × an ASSUMED $0.07/DBU. Our actual cost on Free Edition: $0.

## Live router (normal = alone; stress = alongside 32 evaluation calls)

```
{
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
| related | other | 621 | 39 | 0 | 582 |
| duplicate | other | 490 | 193 | 242 | 55 |
| part_of | other | 452 | 0 | 299 | 153 |
| related | siblings | 333 | 333 | 0 | 0 |
| part_of | siblings | 193 | 0 | 193 | 0 |
| related | bump-same-lib-diff-version | 161 | 23 | 0 | 138 |
| related | both-test-failures | 158 | 7 | 0 | 151 |
| duplicate | same-title | 141 | 89 | 29 | 23 |
| duplicate | bump-same-lib-diff-version | 136 | 3 | 133 | 0 |
| part_of | bump-same-lib-diff-version | 121 | 0 | 111 | 10 |
| duplicate | both-test-failures | 103 | 17 | 63 | 23 |
| part_of | candidate-is-parent | 88 | 88 | 0 | 0 |
| duplicate | siblings | 69 | 2 | 67 | 0 |
| duplicate | bump-same-lib-same-version | 68 | 46 | 19 | 3 |
| related | bump-same-lib-same-version | 18 | 1 | 0 | 17 |
| part_of | both-test-failures | 12 | 0 | 5 | 7 |
| part_of | bump-same-lib-same-version | 12 | 0 | 10 | 2 |
| related | same-title | 8 | 0 | 0 | 8 |
| part_of | same-title | 7 | 0 | 3 | 4 |
| duplicate | candidate-is-parent | 4 | 0 | 4 | 0 |
| related | candidate-is-parent | 1 | 1 | 0 | 0 |
| any | cross-project | 99 | 0 | 45 | 54 |
